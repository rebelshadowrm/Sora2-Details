"""Exercise host readiness without elevating or opening a game process."""
import argparse
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import elevated_probe_session as session


class HostReadinessTests(unittest.TestCase):
    def test_host_identity_and_clean_stop(self):
        for host_pid in (None, "12345"):
            with self.subTest(host_pid=host_pid), tempfile.TemporaryDirectory() as folder:
                directory = Path(folder)
                args = argparse.Namespace(session_dir=directory, pid=987, minutes=1)
                environment = dict(os.environ)
                environment.pop("SORA2_DETAILS_HOST_PID", None)
                if host_pid:
                    environment["SORA2_DETAILS_HOST_PID"] = host_pid
                observed = []

                def queue_stop(_seconds):
                    ready = json.loads((directory / "ready.json").read_text())
                    observed.append(ready)
                    (directory / "requests" / "abcdef.json").write_text(json.dumps({
                        "sessionId": ready["sessionId"], "action": "stop"}))

                with patch.dict(os.environ, environment, clear=True), \
                     patch.object(session, "verify_target") as verify, \
                     patch.object(session.time, "sleep", side_effect=queue_stop):
                    session.serve(args)
                verify.assert_called_once_with(987)
                self.assertEqual(len(observed), 1)
                self.assertEqual(observed[0]["hostPid"], int(host_pid or 0))
                self.assertEqual(observed[0]["serverPid"], os.getpid())
                self.assertEqual(observed[0]["targetPid"], 987)
                stopped = json.loads((directory / "ready.json").read_text())
                self.assertTrue(stopped["stopped"])
                result = json.loads((directory / "results" / "abcdef.json").read_text())
                self.assertTrue(result["stopping"])

    def test_startup_access_denied_is_recorded_before_readiness(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            args = argparse.Namespace(session_dir=directory, pid=987, minutes=1)
            with patch.object(session, "verify_target",
                              side_effect=OSError(5, "OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)")):
                with self.assertRaises(OSError):
                    session.serve(args)
            startup_error = json.loads((directory / "startup-error.json").read_text())
            self.assertEqual(startup_error["targetPid"], 987)
            self.assertIn("OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)",
                          startup_error["error"])
            self.assertFalse((directory / "ready.json").exists())


if __name__ == "__main__":
    unittest.main()
