import os
import shutil
import hashlib
import json
import datetime
import zlib

BASE_ROM = r"..\..\roms\base\Shatterhand (USA).nes"
WORK_ROM = r"..\..\roms\work\Shatterhand_LosSantos.nes"
BUILDS_DIR = r"..\..\roms\builds"


def hash_file(path):
    with open(path, "rb") as f:
        data = f.read()
    return {
        "md5": hashlib.md5(data).hexdigest(),
        "sha1": hashlib.sha1(data).hexdigest(),
        "crc32": format(zlib.crc32(data) & 0xFFFFFFFF, "08x"),
        "size": len(data)
    }


def get_next_version():
    if not os.path.exists(BUILDS_DIR):
        os.makedirs(BUILDS_DIR)

    builds = []
    for d in os.listdir(BUILDS_DIR):
        full = os.path.join(BUILDS_DIR, d)
        if os.path.isdir(full) and d.startswith("v"):
            builds.append(d)

    if not builds:
        return "v0.1.0"

    def parse_version(v):
        return tuple(map(int, v[1:].split(".")))

    builds.sort(key=parse_version)
    major, minor, patch = parse_version(builds[-1])
    patch += 1
    return f"v{major}.{minor}.{patch}"


def compare_roms(base_path, work_path):
    with open(base_path, "rb") as f:
        base_data = f.read()

    with open(work_path, "rb") as f:
        work_data = f.read()

    min_len = min(len(base_data), len(work_data))
    diffs = []

    for i in range(min_len):
        if base_data[i] != work_data[i]:
            diffs.append((i, base_data[i], work_data[i]))

    size_diff = len(work_data) - len(base_data)

    lines = []
    lines.append("===== ROM DIFF REPORT =====")
    lines.append(f"Tamaño ROM base:       {len(base_data)} bytes")
    lines.append(f"Tamaño ROM modificada: {len(work_data)} bytes")
    lines.append(f"Diferencia de tamaño:  {size_diff} bytes")
    lines.append(f"Bytes diferentes:      {len(diffs)}")
    lines.append("")

    preview = 50
    if diffs:
        lines.append(f"Primeros {min(preview, len(diffs))} cambios:")
        for offset, old, new in diffs[:preview]:
            lines.append(f"Offset 0x{offset:06X}: {old:02X} -> {new:02X}")
    else:
        lines.append("No se encontraron diferencias.")

    lines.append("===========================")
    return "\n".join(lines)


def create_ips_patch(base_path, hack_path, output_path):
    with open(base_path, "rb") as f:
        base = f.read()

    with open(hack_path, "rb") as f:
        hack = f.read()

    patch = bytearray()
    patch.extend(b"PATCH")

    i = 0
    max_len = min(len(base), len(hack))

    while i < max_len:
        if base[i] != hack[i]:
            start = i
            chunk = bytearray()

            while i < max_len and base[i] != hack[i] and len(chunk) < 65535:
                chunk.append(hack[i])
                i += 1

            patch.extend(start.to_bytes(3, "big"))
            patch.extend(len(chunk).to_bytes(2, "big"))
            patch.extend(chunk)
        else:
            i += 1

    if len(hack) > len(base):
        start = len(base)
        extra = hack[len(base):]

        idx = 0
        while idx < len(extra):
            chunk = extra[idx:idx + 65535]
            patch.extend((start + idx).to_bytes(3, "big"))
            patch.extend(len(chunk).to_bytes(2, "big"))
            patch.extend(chunk)
            idx += len(chunk)

    patch.extend(b"EOF")

    with open(output_path, "wb") as f:
        f.write(patch)


def create_build():
    if not os.path.exists(BASE_ROM):
        print(f"No se encontró la ROM base: {BASE_ROM}")
        return

    if not os.path.exists(WORK_ROM):
        print(f"No se encontró la ROM de trabajo: {WORK_ROM}")
        return

    version = get_next_version()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    build_path = os.path.join(BUILDS_DIR, version)

    os.makedirs(build_path, exist_ok=True)

    base_copy = os.path.join(build_path, "base.nes")
    work_copy = os.path.join(build_path, "hack.nes")
    manifest_path = os.path.join(build_path, "manifest.json")
    diff_path = os.path.join(build_path, "diff_report.txt")
    ips_path = os.path.join(build_path, "patch.ips")

    shutil.copy2(BASE_ROM, base_copy)
    shutil.copy2(WORK_ROM, work_copy)

    diff_report = compare_roms(BASE_ROM, WORK_ROM)
    create_ips_patch(BASE_ROM, WORK_ROM, ips_path)

    manifest = {
        "version": version,
        "timestamp": timestamp,
        "base_rom": os.path.abspath(BASE_ROM),
        "work_rom": os.path.abspath(WORK_ROM),
        "base_hash": hash_file(base_copy),
        "hack_hash": hash_file(work_copy),
        "diff_report_file": os.path.abspath(diff_path),
        "ips_patch_file": os.path.abspath(ips_path)
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4, ensure_ascii=False)

    with open(diff_path, "w", encoding="utf-8") as f:
        f.write(diff_report)

    print(f"Build creada correctamente: {version}")
    print(f"Ruta: {os.path.abspath(build_path)}")
    print(f"Manifest: {os.path.abspath(manifest_path)}")
    print(f"Diff report: {os.path.abspath(diff_path)}")
    print(f"IPS patch: {os.path.abspath(ips_path)}")


if __name__ == "__main__":
    create_build()