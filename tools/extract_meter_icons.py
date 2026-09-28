"""Extract UI symbols and AT portraits from this exact game's archives.

Requires Pillow and lz4. No game archive is modified and no full texture is
copied into the project. The selected compressed payloads and index are hashed.
"""

import argparse
import hashlib
import io
import os
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".research-deps" / "py"))
import lz4.frame
from PIL import Image


ARCHIVE_SIZE = 16090761455
ENTRY_COUNT = 17782
INDEX_SHA256 = "2aab12491482bfc7262e76609f54f088d5192526e1a7fe07be580c1c0d6ee615"
SOURCES = {
    "icons.dds": "546240b9afa8d630dc27988dd720904c5b70259c9b8911f2d6bf82507e6839a1",
    "btl001.dds": "5564f3bd2dd1aa7be5f809bdff78cd22e40042517a4737559ef75cf34ee4383e",
    "btl002.dds": "5bab62fbd2209d82e9ebfadc1a1ccf637a79ce6cb7fd23ef0674dc5b0f3ad0c6",
}
PORTRAITS = {
    0: ("Estelle", "chr5000", "at_c5000.dds", "7e396fe0062ed3024ae289d6781eeaa8c558d57698d91ca4f4d34785b7ba4b1c"),
    1: ("Joshua", "chr0001", "at_c0001.dds", "4bd0e5c9e23e5285aa264f49d56935967fd170cbfd3e0bc2ed2d0036f2095fe5"),
    2: ("Scherazard", "chr5002", "at_c5002.dds", "e4935e593478aab913a14806dbbb011669586c8b26c1edf7438c9b405024fa13"),
    3: ("Olivier", "chr0003", "at_c0003.dds", "6b5b82904852eed0f60d5e127eb119c91d3d98741f7f109823fcabab25fcc670"),
    4: ("Kloe", "chr5004", "at_c5004.dds", "96579c4e81a0cb7ec049a361809687749c5e6331002144ba33d0d3bf677c3cd1"),
    5: ("Agate", "chr0005", "at_c0005.dds", "823bcc0654f56411f12b6f76121212375e7d5c2573106f4cfe464cf59af595dd"),
    6: ("Tita", "chr5006", "at_c5006.dds", "51716732e9bc3c4341d3e2449d9d3456787ea19b32d0f8996a0a95300f0f4841"),
    7: ("Zin", "chr0007", "at_c0007.dds", "e0e9ea8b114d68eedef4150ce0e1124d0780bf6ed90e54ca43d2f7c610eeefc6"),
    101: ("Anelace", "chr5101", "at_c5101.dds", "696d8d4714d85f5bbf107733dc701d9c18850e9b7575371deef5453ac488a09c"),
    119: ("Kevin", "chr0125", "at_c0125.dds", "6a90955be755645900cfe6c008200c6f9eb92f67b028a7d6a8dab9e18317988b"),
    106: ("Josette", "chr5106", "at_c5106.dds", "16fd4d7e5606ad1ca27dc8a82e28a46ed16f06ce73cd63106806d03815fb0dc9"),
}
CROPS = {
    "earth": ("icons.dds", (0, 98, 48, 146)),
    "water": ("icons.dds", (50, 98, 98, 146)),
    "fire": ("icons.dds", (100, 98, 148, 146)),
    "wind": ("icons.dds", (150, 98, 198, 146)),
    "time": ("icons.dds", (200, 98, 248, 146)),
    "space": ("icons.dds", (250, 98, 298, 146)),
    "mirage": ("icons.dds", (300, 98, 348, 146)),
    "attack": ("btl002.dds", (190, 0, 370, 180)),
    "craft": ("btl002.dds", (390, 0, 570, 180)),
    "scraft": ("btl001.dds", (640, 0, 760, 110)),
    "item": ("btl001.dds", (550, 0, 640, 110)),
}


def read_sources(pac_path, expected):
    if pac_path.stat().st_size != ARCHIVE_SIZE:
        raise ValueError("image.pac size differs from the validated archive")
    with pac_path.open("rb") as stream:
        header = stream.read(24)
        if header[:4] != b"FPAC" or struct.unpack_from("<I", header, 4)[0] != ENTRY_COUNT:
            raise ValueError("Unexpected image.pac header")
        entries = [struct.unpack("<QQQQ", stream.read(32)) for _ in range(ENTRY_COUNT)]
        first_payload = min(offset for _, _, offset, _ in entries)
        stream.seek(0)
        if hashlib.sha256(stream.read(first_payload)).hexdigest() != INDEX_SHA256:
            raise ValueError("image.pac index differs from the validated archive")
        selected = {}
        for name_offset, size, offset, _ in entries:
            if offset + size > ARCHIVE_SIZE:
                raise ValueError("Out-of-bounds image payload")
            stream.seek(name_offset)
            name = stream.read(160).split(b"\0", 1)[0].decode("ascii")
            basename = name.rsplit("/", 1)[-1]
            if name != f"asset/dx11/image/{basename}" or basename not in expected:
                continue
            stream.seek(offset)
            payload = stream.read(size)
            if hashlib.sha256(payload).hexdigest() != expected[basename]:
                raise ValueError(f"{basename} differs from the validated archive")
            selected[basename] = Image.open(io.BytesIO(lz4.frame.decompress(payload))).convert("RGBA")
        if set(selected) != set(expected):
            raise ValueError("Expected UI texture missing from image.pac")
        return selected


def verified_portraits(table_pac):
    from name_table_index import read_rows, unique_id_lookup

    names = unique_id_lookup(read_rows(table_pac))
    for character_id, (name, model, filename, digest) in PORTRAITS.items():
        row = names.get(character_id)
        if row is None or row["name"] != name or row["characterModelKey"] != model:
            raise ValueError(f"Portrait join differs for party ID {character_id}")
        if filename != "at_c" + model.removeprefix("chr") + ".dds":
            raise ValueError(f"Invalid AT texture join for {name}")
    return {filename: digest for _, _, filename, digest in PORTRAITS.values()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image_pac", type=Path)
    parser.add_argument("--output", type=Path,
                        default=Path(os.environ["LOCALAPPDATA"]) / "Sora2 Details" / "icons")
    parser.add_argument("--table-pac", type=Path,
                        help="English table_en.pac; defaults to the sibling archive")
    parser.add_argument("--portraits-output", type=Path,
                        default=Path(os.environ["LOCALAPPDATA"]) / "Sora2 Details" / "portraits")
    parser.add_argument("--overwrite-portraits", action="store_true",
                        help="Replace existing portrait PNGs, including custom portraits")
    args = parser.parse_args()
    table_pac = args.table_pac or args.image_pac.with_name("table_en.pac")
    portraits = verified_portraits(table_pac) if table_pac.exists() else {}
    sources = read_sources(args.image_pac, SOURCES | portraits)
    args.output.mkdir(parents=True, exist_ok=True)
    for key, (source, box) in CROPS.items():
        sources[source].crop(box).resize((64, 64), Image.Resampling.LANCZOS).save(args.output / f"{key}.png")
    print(f"Extracted {len(CROPS)} verified UI icons to {args.output}")
    if portraits:
        args.portraits_output.mkdir(parents=True, exist_ok=True)
        written = 0
        for name, _, filename, _ in PORTRAITS.values():
            target = args.portraits_output / f"{name}.png"
            if target.exists() and not args.overwrite_portraits:
                continue
            atlas = sources[filename]
            if atlas.size != (256, 128):
                raise ValueError(f"Unexpected AT portrait dimensions for {name}: {atlas.size}")
            atlas.crop((64, 0, 192, 128)).resize((64, 64), Image.Resampling.LANCZOS).save(target)
            written += 1
        print(f"Extracted {written} AT portraits to {args.portraits_output} ({len(portraits) - written} existing kept)")
    else:
        print(f"No {table_pac} found; AT portrait join skipped")


if __name__ == "__main__":
    main()
