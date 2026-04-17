import os
import shutil
import hashlib
import json
import datetime
import zlib
import argparse
import subprocess

BASE_ROM = r"..\..\roms\base\Shatterhand (USA).nes"
WORK_ROM = r"..\..\roms\work\Shatterhand_LosSantos.nes"
BUILDS_DIR = r"..\..\roms\builds"
PATCHES_DIR = r"..\..\patches"


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def get_versions():
    if not os.path.exists(BUILDS_DIR):
        return []
    return sorted([d for d in os.listdir(BUILDS_DIR) if d.startswith("v")])


def get_next_version():
    versions = get_versions()
    if not versions:
        return "v0.1.0"
    last = versions[-1]
    major, minor, patch = map(int, last[1:].split("."))
    return f"v{major}.{minor}.{patch+1}"


def get_latest_version():
    versions = get_versions()
    return versions[-1] if versions else None


def hash_file(path):
    with open(path, "rb") as f:
        data = f.read()
    return hashlib.sha1(data).hexdigest()


def create_ips(base_path, hack_path, output_path):
    with open(base_path, "rb") as f:
        base = f.read()
    with open(hack_path, "rb") as f:
        hack = f.read()

    patch = bytearray(b"PATCH")

    i = 0
    while i < len(base):
        if base[i] != hack[i]:
            start = i
            chunk = bytearray()
            while i < len(base) and base[i] != hack[i]:
                chunk.append(hack[i])
                i += 1
            patch += start.to_bytes(3, "big")
            patch += len(chunk).to_bytes(2, "big")
            patch += chunk
        else:
            i += 1

    patch += b"EOF"

    with open(output_path, "wb") as f:
        f.write(patch)


def apply_ips(base_path, patch_path, output_path):
    with open(base_path, "rb") as f:
        rom = bytearray(f.read())
    with open(patch_path, "rb") as f:
        patch = f.read()

    pos = 5
    while patch[pos:pos+3] != b"EOF":
        offset = int.from_bytes(patch[pos:pos+3], "big")
        pos += 3
        size = int.from_bytes(patch[pos:pos+2], "big")
        pos += 2
        data = patch[pos:pos+size]
        pos += size
        rom[offset:offset+size] = data

    with open(output_path, "wb") as f:
        f.write(rom)


def create_build():
    version = get_next_version()
    build_path = os.path.join(BUILDS_DIR, version)

    ensure_dir(build_path)

    base_copy = os.path.join(build_path, "base.nes")
    hack_copy = os.path.join(build_path, "hack.nes")
    patch_path = os.path.join(build_path, "patch.ips")
    rebuilt = os.path.join(build_path, "rebuilt.nes")

    shutil.copy2(BASE_ROM, base_copy)
    shutil.copy2(WORK_ROM, hack_copy)

    create_ips(BASE_ROM, WORK_ROM, patch_path)
    apply_ips(BASE_ROM, patch_path, rebuilt)

    manifest = {
        "version": version,
        "base_sha1": hash_file(base_copy),
        "hack_sha1": hash_file(hack_copy),
        "rebuilt_sha1": hash_file(rebuilt),
        "timestamp": str(datetime.datetime.now())
    }

    with open(os.path.join(build_path, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=4)

    print(f"Build creada: {version}")


def verify_build(version):
    if version == "latest":
        version = get_latest_version()

    path = os.path.join(BUILDS_DIR, version)

    base = os.path.join(path, "base.nes")
    hack = os.path.join(path, "hack.nes")
    patch = os.path.join(path, "patch.ips")
    rebuilt = os.path.join(path, "rebuilt_verify.nes")

    apply_ips(base, patch, rebuilt)

    ok = hash_file(hack) == hash_file(rebuilt)

    print(f"Verify {version}: {'OK' if ok else 'ERROR'}")


def release_build(version):
    if version == "latest":
        version = get_latest_version()

    src = os.path.join(BUILDS_DIR, version, "patch.ips")
    ensure_dir(PATCHES_DIR)

    dst = os.path.join(PATCHES_DIR, f"LosSantos_{version}.ips")
    shutil.copy2(src, dst)

    print(f"Release lista: {dst}")


def publish_build(version):
    if version == "latest":
        version = get_latest_version()

    path = os.path.join(BUILDS_DIR, version)
    patch = os.path.join(path, "patch.ips")

    print("Subiendo a GitHub...")

    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", f"release {version}"])
    subprocess.run(["git", "push"])

    subprocess.run([
        "gh", "release", "create", version,
        patch,
        "--title", f"Los Santos {version}",
        "--notes", f"Release automática {version}"
    ])

    print("Publicado en GitHub 🚀")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("build")

    v = sub.add_parser("verify")
    v.add_argument("version")

    r = sub.add_parser("release")
    r.add_argument("version")

    p = sub.add_parser("publish")
    p.add_argument("version")

    args = parser.parse_args()

    if args.cmd == "build":
        create_build()
    elif args.cmd == "verify":
        verify_build(args.version)
    elif args.cmd == "release":
        release_build(args.version)
    elif args.cmd == "publish":
        publish_build(args.version)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()