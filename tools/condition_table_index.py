"""Exact English condition metadata; names do not imply application or stat deltas."""
import hashlib
import struct

PAYLOAD_OFFSET = 0x13F659
PAYLOAD_SIZE = 8963
PAYLOAD_SHA256 = '89d228d22acdb8bf3f064e4e0f921d29ca97d67ca457d8987639c96bb5908289'
ROW_START = 248
ROW_SIZE = 88
STRING_START = 248 + 52 * 88 + 70 * 8 + 14 * 104


def parse_payload(data):
    if len(data) != PAYLOAD_SIZE or hashlib.sha256(data).hexdigest() != PAYLOAD_SHA256:
        raise ValueError('English condition payload does not match the validated build')
    if data[:8] != b'#TBL\x03\x00\x00\x00':
        raise ValueError('Invalid condition table header')
    for i, expected in enumerate((('ConditionInfoTableData', 88, 52),
                                  ('ConditionTypeParam', 8, 70), ('OverDriveEffect', 104, 14))):
        at = 8 + i * 80
        found = (data[at:at + 64].split(b'\0')[0].decode('ascii'),
                 *struct.unpack_from('<II', data, at + 72))
        if found != expected:
            raise ValueError('Invalid condition section layout')
    result = {}
    for i in range(52):
        at = ROW_START + i * ROW_SIZE
        key = struct.unpack_from('<I', data, at)[0]
        name_at = struct.unpack_from('<Q', data, at + 8)[0]
        end = data.find(b'\0', name_at)
        if not STRING_START <= name_at < len(data) or end < 0 or key in result:
            raise ValueError('Invalid or duplicate condition identity')
        result[key] = dict(rawKey=key, tableRow=i,
            nameCandidate=data[name_at:end].decode('utf-8'), tablePayloadSha256=PAYLOAD_SHA256,
            provenance='inline-condition-key/native-7E470/exact-English-ConditionInfoTableData-candidate')
    return result


def read_rows(pac):
    with pac.open('rb') as stream:
        stream.seek(PAYLOAD_OFFSET)
        return parse_payload(stream.read(PAYLOAD_SIZE))
