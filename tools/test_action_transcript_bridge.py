import json
from pathlib import Path
import tempfile
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import os
import ctypes
import threading
from action_transcript_bridge import publish


class BridgeChecks(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows PowerShell launcher readiness')
    def test_launcher_waits_for_published_armed_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            # The hosted runner's TEMP can use an 8.3 alias. A parent segment
            # reproduces the same difference from publish()'s canonical path.
            (Path(directory) / 'staging').mkdir()
            trace = Path(directory) / 'staging' / '..' / 'action-stream-batch.jsonl'
            output = Path(directory) / 'ledger.json'
            launcher = Path(__file__).with_name('start_action_stream.ps1').resolve()
            def quote(value):
                return "'" + str(value).replace("'", "''") + "'"
            # Execute the actual launcher's readiness branch with a living helper
            # substitute. All trace/ledger reads use real files and bridge output.
            script = f"""
            $errors = $null; $tokens = $null
            $ast = [Management.Automation.Language.Parser]::ParseFile({quote(launcher)}, [ref]$tokens, [ref]$errors)
            if ($errors.Count) {{ throw 'Launcher parse failed' }}
            $branch = $ast.Find({{ param($node)
                $node -is [Management.Automation.Language.IfStatementAst] -and
                $node.Extent.Text.StartsWith('if ($manifest.requestId')
            }}, $true)
            if (-not $branch) {{ throw 'Readiness branch missing' }}
            function Get-Process {{ param($Id, $ErrorAction) return @{{ Id = $Id }} }}
            $batchId = 'batch'; $launcher = @{{ Id = 777 }}
            $trace = {quote(trace)}
            $manifest = @{{ requestId = 'batch'; serverPid = 777; bridgePid = 888; ledgerPath = {quote(output)} }}
            Invoke-Expression $branch.Extent.Text
            exit 3
            """
            def ready():
                return subprocess.run(['powershell.exe', '-NoProfile', '-Command', script],
                    capture_output=True, text=True, timeout=15)
            self.assertEqual(3, ready().returncode, 'missing first snapshot is not ready')
            trace.write_text('{"kind":"module"}\n', encoding='utf-8')
            publish(trace, output)
            self.assertEqual(3, ready().returncode, 'pre-arm snapshot is not ready')
            with trace.open('a', encoding='utf-8') as stream:
                stream.write('{"kind":"armed"}\n')
            publish(trace, output)
            result = ready()
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn('Recording action stream', result.stdout)
            wrong_batch = json.loads(output.read_text())
            wrong_batch['batchId'] = 'action-stream-some-other-batch'
            output.write_text(json.dumps(wrong_batch), encoding='utf-8')
            self.assertEqual(3, ready().returncode, 'another armed batch is not ready')

    @unittest.skipUnless(os.name == 'nt', 'Windows file sharing regression')
    def test_windows_reader_temporarily_denies_atomic_replacement(self):
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
            ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        kernel.CreateFileW.restype = ctypes.c_void_p
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / 'raw.jsonl'
            output = Path(directory) / 'ledger.json'
            trace.write_bytes(b'{}\n')
            publish(trace, output)
            # Read/write sharing is allowed, but delete/replace sharing is denied.
            handle = kernel.CreateFileW(str(output), 0x80000000, 3, None, 3, 0, None)
            self.assertNotEqual(ctypes.c_void_p(-1).value, handle)
            def release():
                time.sleep(.15)
                kernel.CloseHandle(handle)
            reader = threading.Thread(target=release)
            reader.start()
            trace.write_bytes(b'{}\n{"kind":"unknown-item"}\n')
            replace = os.replace
            denials = []
            def tracked_replace(source, destination):
                try:
                    return replace(source, destination)
                except PermissionError as error:
                    denials.append(error.winerror)
                    raise
            try:
                with patch('action_transcript_bridge.os.replace', side_effect=tracked_replace):
                    result = publish(trace, output)
            finally:
                reader.join()
            self.assertTrue(denials, 'actual Windows replace denial reproduced')
            self.assertEqual(2, len(result['observations']))
            self.assertEqual('unknown-item', json.loads(output.read_text())['observations'][-1]['raw']['kind'])

    def test_transient_replace_denial_retries_same_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / 'raw.jsonl'
            output = Path(directory) / 'ledger.json'
            trace.write_bytes(b'{"kind":"unknown-item"}\n')
            replace = os.replace
            attempts = []
            def deny_then_replace(source, destination):
                attempts.append((source, destination))
                if len(attempts) < 3:
                    raise PermissionError('sharing violation')
                return replace(source, destination)
            with patch('action_transcript_bridge.os.replace', side_effect=deny_then_replace), \
                    patch('action_transcript_bridge.time.sleep'):
                publish(trace, output)
            self.assertEqual(3, len(attempts))
            self.assertEqual(attempts[0], attempts[2])
            self.assertEqual('unknown-item', json.loads(output.read_text())['observations'][0]['raw']['kind'])
            self.assertEqual([], list(Path(directory).glob('*.tmp-*')))

    def test_persistent_replace_denial_preserves_last_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / 'raw.jsonl'
            output = Path(directory) / 'ledger.json'
            trace.write_bytes(b'{}\n')
            publish(trace, output)
            before = output.read_bytes()
            trace.write_bytes(b'{}\n{"kind":"unknown-item"}\n')
            with patch('action_transcript_bridge.os.replace', side_effect=PermissionError('still locked')) as replace, \
                    patch('action_transcript_bridge.time.sleep'):
                with self.assertRaises(PermissionError):
                    publish(trace, output)
                self.assertEqual(21, replace.call_count)
            self.assertEqual(before, output.read_bytes())
            self.assertEqual([], list(Path(directory).glob('*.tmp-*')))

    def test_watch_waits_for_source_and_finishes_only_on_detach(self):
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / 'raw.jsonl'
            output = Path(directory) / 'ledger.json'
            process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).with_name('action_transcript_bridge.py')),
                str(trace), '--output', str(output), '--watch'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                trace.write_text('{"kind":"armed"}\n', encoding='utf-8')
                deadline = time.monotonic() + 5
                while not output.exists() and time.monotonic() < deadline:
                    time.sleep(.05)
                self.assertTrue(output.exists())
                self.assertIsNone(process.poll())
                with trace.open('a', encoding='utf-8') as stream:
                    stream.write('{"kind":"detached"}\n')
                stdout, stderr = process.communicate(timeout=5)
                self.assertEqual(0, process.returncode, stderr.decode())
                self.assertTrue(json.loads(output.read_text())['captureDetached'])
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()

    def test_partial_line_waits_and_unknown_records_survive_append(self):
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / 'raw.jsonl'
            output = Path(directory) / 'ledger.json'
            first = {'kind': 'future-event', 'payload': {'unknown': [1, 2]}}
            encoded = (json.dumps(first) + '\n').encode()
            trace.write_bytes(encoded + b'{"kind": "det')
            result = publish(trace, output)
            self.assertEqual(len(encoded), result['traceCommittedLength'])
            self.assertEqual(first, result['observations'][0]['raw'])
            self.assertFalse(result['captureDetached'])
            trace.write_bytes(encoded + b'{"kind": "detached"}\n')
            result = publish(trace, output)
            self.assertTrue(result['captureDetached'])
            self.assertEqual(2, len(json.loads(output.read_text())['observations']))
            self.assertEqual([], list(Path(directory).glob('*.tmp-*')))

    def test_source_overwrite_and_malformed_committed_record_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / 'raw.jsonl'
            output = Path(directory) / 'ledger.json'
            trace.write_bytes(b'{}\n')
            publish(trace, output)
            before = output.read_bytes()
            with self.assertRaises(ValueError):
                publish(trace, trace)
            trace.write_bytes(b'{broken}\n')
            with self.assertRaises(json.JSONDecodeError):
                publish(trace, output)
            self.assertEqual(before, output.read_bytes())


if __name__ == '__main__':
    unittest.main()
