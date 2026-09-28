"""Read-only PE/string cross-reference scan for the current Sora 2 executable.

Install prerequisites with: python -m pip install pefile capstone
The script also uses .research-deps/ if the packages were installed there.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".research-deps"))

import capstone  # type: ignore[import-not-found]
import pefile  # type: ignore[import-not-found]


NAMES = (
    "btlsys.BattleInit",
    "btlsys.BattleStart",
    "btlsys.BattlePreEnd",
    "btlsys.BattleEnd",
    "btlsys.BattleDead",
    "btlsys.BattleTurnBegin",
    "btlsys.BattleCommandBegin",
    "btlsys.BattleTurnEnd",
    "BattleCheckResult",
    "btlcom.OnAttackHit",
    "btlcom.AniBtlDamageTargetsSkip",
    "btlcom.AniBtlRegene",
    "btlcom.AniBtlAttrAbsorbEffect",
    "btlcom.OnFieldAttackReflect",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path, help="Path to sora_2nd.exe")
    args = parser.parse_args()

    raw = args.exe.read_bytes()
    pe = pefile.PE(data=raw)
    base = pe.OPTIONAL_HEADER.ImageBase
    text = next(section for section in pe.sections if section.Name.startswith(b".text"))
    code = text.get_data()[: text.Misc_VirtualSize]
    ranges = sorted((entry.struct.BeginAddress, entry.struct.EndAddress)
                    for entry in pe.DIRECTORY_ENTRY_EXCEPTION)
    starts = [start for start, _ in ranges]

    print("SHA-256:", hashlib.sha256(raw).hexdigest())
    print("Image base:", hex(base), "entry RVA:", hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint))
    print("RVA addresses below are offsets from the loaded module base.")
    print("Name | string RVA | instruction RVA | containing function RVA | end RVA | entry bytes")

    targets: dict[int, str] = {}
    absent: list[str] = []
    for name in NAMES:
        found = False
        cursor = 0
        while (cursor := raw.find(name.encode("ascii") + b"\0", cursor)) >= 0:
            targets[pe.get_rva_from_offset(cursor)] = name
            found = True
            cursor += 1
        if not found:
            absent.append(name)

    references: dict[int, list[int]] = {target: [] for target in targets}
    for index in range(len(code) - 7):
        # x64 LEA r64, [RIP+disp32], including all REX register variants.
        if not (0x48 <= code[index] <= 0x4F and code[index + 1] == 0x8D
                and code[index + 2] & 0xC7 == 0x05):
            continue
        target = text.VirtualAddress + index + 7 + struct.unpack_from("<i", code, index + 3)[0]
        if target in references:
            references[target].append(text.VirtualAddress + index)

    decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    for name in absent:
        print(f"{name} | absent")
    for string_rva, name in targets.items():
        matches = references[string_rva]
        if not matches:
            print(f"{name} | {string_rva:#x} | no direct code LEA reference")
            continue

        for reference_rva in matches:
            position = bisect.bisect_right(starts, reference_rva) - 1
            if position < 0 or reference_rva >= ranges[position][1]:
                print(f"{name} | {string_rva:#x} | {reference_rva:#x} | no unwind range")
                continue
            start, end = ranges[position]
            # Decode from a trusted function boundary to reject matches in data
            # or in the middle of another instruction.
            instructions = decoder.disasm(pe.get_data(start, end - start), base + start)
            if not any(insn.address - base == reference_rva and insn.mnemonic == "lea"
                       for insn in instructions):
                print(f"{name} | {string_rva:#x} | {reference_rva:#x} | unverified alignment")
                continue
            entry = pe.get_data(start, 12).hex(" ")
            print(f"{name} | {string_rva:#x} | {reference_rva:#x} | {start:#x} | {end:#x} | {entry}")


if __name__ == "__main__":
    main()
