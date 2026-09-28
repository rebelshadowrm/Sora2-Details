"""Research lookup for enemy skill names in this exact English script archive.

The script's SkillTable bytecode has a tagged skill ID followed by tagged
string offsets. A live enemy effect's low 16-bit ID is useful only after a
separate, unique unit-key match selects the correct per-monster AI script.
"""

import argparse
import hashlib
from pathlib import Path
import re
import struct
import sys


ARCHIVE_SHA256 = "6ee144495df231a17803b8e61fb68060f53924ca9c33b463280f49873682b286"
ARCHIVE_ENTRY_COUNT = 1082
UNIT_KEY = re.compile(r"mon[a-zA-Z0-9_]+\Z")


class EnemyAiSkillIndex:
    def __init__(self, pac_path):
        self.pac_path = Path(pac_path)
        with self.pac_path.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != ARCHIVE_SHA256:
                raise ValueError("English script archive does not match the validated build")
            stream.seek(0)
            header = stream.read(24)
            if header[:4] != b"FPAC" or struct.unpack_from("<I", header, 4)[0] != ARCHIVE_ENTRY_COUNT:
                raise ValueError("Unexpected English script archive index")
            entries = [struct.unpack("<QQQQ", stream.read(32))
                       for _ in range(ARCHIVE_ENTRY_COUNT)]
            total = self.pac_path.stat().st_size
            self.entries = {}
            for name_offset, size, data_offset, _ in entries:
                if not 16 + ARCHIVE_ENTRY_COUNT * 32 <= name_offset < total:
                    raise ValueError("Invalid script filename offset")
                if data_offset + size > total:
                    raise ValueError("Invalid script payload bounds")
                stream.seek(name_offset)
                name = stream.read(160).split(b"\0", 1)[0].decode("ascii")
                if name in self.entries:
                    raise ValueError("Duplicate script archive entry")
                self.entries[name] = (data_offset, size)
        self.cache = {}

    @staticmethod
    def _cstring(data, offset):
        if offset >= len(data):
            return None
        end = data.find(b"\0", offset)
        if end < 0 or end - offset > 100:
            return None
        try:
            value = data[offset:end].decode("utf-8")
        except UnicodeDecodeError:
            return None
        return value if value and all(char.isprintable() for char in value) else None

    @classmethod
    def _skill_rows(cls, data):
        if not data.startswith(b"#scp") or b"SkillTable\0" not in data:
            return {}
        found = {}
        for offset in range(len(data) - 0x26):
            tagged_id = struct.unpack_from("<I", data, offset)[0]
            if tagged_id >> 30 != 1 or not 1000 <= (tagged_id & 0x3FFFFFFF) < 2000:
                continue
            # These bytecode entries use opcode 0x0c; the following argument
            # marker differs across scripts and is not a skill-name key.
            if data[offset + 4] != 0x0C:
                continue
            name_pointer = struct.unpack_from("<I", data, offset + 0x1E)[0]
            if name_pointer >> 30 != 3:
                continue
            name = cls._cstring(data, name_pointer & 0x3FFFFFFF)
            if name:
                found.setdefault(tagged_id & 0x3FFFFFFF, set()).add(name)
        return {skill_id: sorted(names) for skill_id, names in found.items()}

    def skill_names(self, unit_key):
        if not UNIT_KEY.fullmatch(unit_key):
            return {}
        if unit_key not in self.cache:
            entry = self.entries.get(f"script_en/ai/ai_{unit_key}.dat")
            if entry is None:
                self.cache[unit_key] = {}
            else:
                offset, size = entry
                with self.pac_path.open("rb") as stream:
                    stream.seek(offset)
                    self.cache[unit_key] = self._skill_rows(stream.read(size))
        return self.cache[unit_key]


def main():
    sys.stdout.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pac", type=Path)
    parser.add_argument("unit_key", help="Exact t_status unit key, such as mon5031")
    args = parser.parse_args()
    names = EnemyAiSkillIndex(args.pac).skill_names(args.unit_key)
    for skill_id, candidates in sorted(names.items()):
        print(f"{skill_id}: {', '.join(candidates)}")
    print(f"{len(names)} ID(s); a unique live enemy unit key is still required")


if __name__ == "__main__":
    main()
