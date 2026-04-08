import os

BASE_ROM = r"..\..\roms\base\Shatterhand (USA).nes"
WORK_ROM = r"..\..\roms\work\Shatterhand_LosSantos.nes"

def compare_roms(base_path, work_path):
    if not os.path.exists(base_path):
        print(f"No se encontró la ROM base: {base_path}")
        return

    if not os.path.exists(work_path):
        print(f"No se encontró la ROM modificada: {work_path}")
        return

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

    print("\n===== ROM DIFF REPORT =====")
    print(f"Tamaño ROM base:       {len(base_data)} bytes")
    print(f"Tamaño ROM modificada: {len(work_data)} bytes")
    print(f"Diferencia de tamaño:  {size_diff} bytes")
    print(f"Bytes diferentes:      {len(diffs)}")

    preview = 20
    if diffs:
        print(f"\nPrimeros {min(preview, len(diffs))} cambios:")
        for offset, old, new in diffs[:preview]:
            print(f"Offset 0x{offset:06X}: {old:02X} -> {new:02X}")
    else:
        print("\nNo se encontraron diferencias.")

    print("===========================\n")

if __name__ == "__main__":
    compare_roms(BASE_ROM, WORK_ROM)