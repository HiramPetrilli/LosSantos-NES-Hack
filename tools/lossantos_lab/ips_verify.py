import os
import hashlib

BUILD_DIR = r"..\..\roms\builds\v0.1.2"
BASE_ROM = os.path.join(BUILD_DIR, "base.nes")
HACK_ROM = os.path.join(BUILD_DIR, "hack.nes")
PATCH_FILE = os.path.join(BUILD_DIR, "patch.ips")
REBUILT_ROM = os.path.join(BUILD_DIR, "rebuilt_from_ips.nes")


def file_sha1(path):
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()


def apply_ips_patch(base_path, patch_path, output_path):
    with open(base_path, "rb") as f:
        rom = bytearray(f.read())

    with open(patch_path, "rb") as f:
        patch = f.read()

    if patch[:5] != b"PATCH":
        raise ValueError("Archivo IPS inválido: no inicia con PATCH")

    pos = 5

    while patch[pos:pos + 3] != b"EOF":
        offset = int.from_bytes(patch[pos:pos + 3], "big")
        pos += 3

        size = int.from_bytes(patch[pos:pos + 2], "big")
        pos += 2

        if size == 0:
            rle_size = int.from_bytes(patch[pos:pos + 2], "big")
            pos += 2
            value = patch[pos]
            pos += 1

            end = offset + rle_size
            if end > len(rom):
                rom.extend(b"\x00" * (end - len(rom)))
            rom[offset:end] = bytes([value]) * rle_size
        else:
            data = patch[pos:pos + size]
            pos += size

            end = offset + size
            if end > len(rom):
                rom.extend(b"\x00" * (end - len(rom)))
            rom[offset:end] = data

    with open(output_path, "wb") as f:
        f.write(rom)


def main():
    for path in [BASE_ROM, HACK_ROM, PATCH_FILE]:
        if not os.path.exists(path):
            print(f"No se encontró: {path}")
            return

    apply_ips_patch(BASE_ROM, PATCH_FILE, REBUILT_ROM)

    original_sha1 = file_sha1(HACK_ROM)
    rebuilt_sha1 = file_sha1(REBUILT_ROM)

    print("\n===== IPS VERIFY REPORT =====")
    print(f"Hack SHA1:     {original_sha1}")
    print(f"Rebuilt SHA1:  {rebuilt_sha1}")
    print(f"Archivo nuevo: {os.path.abspath(REBUILT_ROM)}")

    if original_sha1 == rebuilt_sha1:
        print("RESULTADO: OK, el patch.ips reconstruye exactamente hack.nes")
    else:
        print("RESULTADO: ERROR, el patch.ips NO reconstruye exactamente hack.nes")
    print("=============================\n")


if __name__ == "__main__":
    main()