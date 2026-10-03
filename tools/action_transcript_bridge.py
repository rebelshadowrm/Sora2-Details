"""Project complete raw JSONL lines atomically; never edit the capture source."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import uuid

from reconcile_action_stream import reconcile, DescriptorLookup, RANGES, PAYLOAD_SHA256, NAME_PAYLOAD_SHA256
from action_stream_timeline import project_timeline
from name_table_index import read_rows, unique_id_lookup
from item_action_lookup import PAYLOAD_SHA256 as ITEM_PAYLOAD_SHA256
from condition_table_index import PAYLOAD_SHA256 as CONDITION_PAYLOAD_SHA256


def replace_snapshot(temporary, output):
    # A Windows reader or antivirus scan can briefly deny delete/replace access.
    # Retry the same complete snapshot; never truncate the published ledger.
    for attempt in range(21):
        try:
            os.replace(temporary, output)
            return
        except PermissionError:
            if attempt == 20:
                raise
            time.sleep(.05)


def committed_prefix(raw):
    end = raw.rfind(b'\n') + 1
    return raw[:end]


def publish(trace, output, lookup=None, names=None):
    if trace.resolve() == output.resolve():
        raise ValueError('Derived output must not overwrite the raw trace')
    raw = committed_prefix(trace.read_bytes())
    if not raw:
        return None
    records = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
    result = reconcile(records, trace.stem, lookup, names)
    result['actionTimeline'] = project_timeline(result, names)
    result.update(tracePath=str(trace.resolve()), traceSha256=hashlib.sha256(raw).hexdigest(),
                  traceCommittedLength=len(raw),
                  captureDetached=any(r.get('kind') == 'detached' for r in records),
                  lookupProvenance={'tablePayloadSha256': PAYLOAD_SHA256,
                                    'nameTablePayloadSha256': NAME_PAYLOAD_SHA256,
                                    'itemTablePayloadSha256': ITEM_PAYLOAD_SHA256,
                                    'conditionTablePayloadSha256': CONDITION_PAYLOAD_SHA256,
                                    'itemDescriptorGeneratorRva': '0x23E760',
                                    'comparedRanges': [list(r) for r in RANGES],
                                    'researchCandidatesOnly': True} if lookup else None)
    temporary = output.with_name(output.name + '.tmp-' + uuid.uuid4().hex)
    try:
        with temporary.open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        replace_snapshot(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--skill-pac', type=Path)
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args()
    lookup = DescriptorLookup(args.skill_pac) if args.skill_pac else None
    names = unique_id_lookup(read_rows(args.skill_pac)) if args.skill_pac else None
    previous = None
    while True:
        if args.trace.exists():
            signature = (args.trace.stat().st_size, args.trace.stat().st_mtime_ns)
            if signature != previous:
                result = publish(args.trace, args.output, lookup, names)
                previous = signature
                if result and result['captureDetached']:
                    return
        if not args.watch:
            return
        time.sleep(.5)


if __name__ == '__main__':
    main()
