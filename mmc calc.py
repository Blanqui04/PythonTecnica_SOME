def input_float(prompt, default=None):
    while True:
        try:
            val = input(f"{prompt} [{default}]: ")
            if val == "" and default is not None:
                return float(default)
            return float(val)
        except ValueError:
            print("Introdueix un valor numèric vàlid.")

print("Calculadora de Tolerància Posicional amb Condició de Material Màxim (MMC)")
print("-" * 60)
print("Aquesta eina et permet calcular la tolerància posicional total tenint en compte:")
print("- La mida real de la característica")
print("- La condició de material màxim (MMC)")
print("- Els bonus aplicables")
print("- I també els datums amb MMC (si s'apliquen)")
print("-" * 60)

print("\n🔧 Característica principal")
nominal = input_float("Diàmetre nominal (mm)", 5.4)
tol = input_float("Tolerància ± (mm)", 0.1)
measured = input_float("Diàmetre mesurat (mm)", 5.45)
pos_tol = input_float("Tolerància posicional bàsica (mm)", 0.4)

mmc = nominal - tol
bonus = max(0.0, measured - mmc)
total_tol = pos_tol + bonus

print(f"\n➤ MMC (Material Màxim): {mmc:.3f} mm")
print(f"➤ Bonus de tolerància: {bonus:.3f} mm")
print(f"➤ Tolerància total disponible: {total_tol:.3f} mm")

print("\n📐 Datums amb MMC (opcional)")
while True:
    try:
        datum_count = int(input("Nombre de datums amb MMC [0]: ") or "0")
        if 0 <= datum_count <= 3:
            break
        print("Introdueix un valor entre 0 i 3.")
    except ValueError:
        print("Introdueix un valor numèric vàlid.")

datum_bonus_total = 0.0
for i in range(datum_count):
    print(f"\nDatum {chr(65+i)}")
    d_nom = input_float(f"  Nominal datum {chr(65+i)} (mm)")
    d_tol = input_float(f"  Tolerància ± datum {chr(65+i)} (mm)")
    d_meas = input_float(f"  Mida mesurada datum {chr(65+i)} (mm)")
    d_mmc = d_nom - d_tol
    d_bonus = max(0.0, d_meas - d_mmc)
    datum_bonus_total += d_bonus
    print(f"    - MMC datum {chr(65+i)}: {d_mmc:.3f} mm")
    print(f"    - Bonus datum {chr(65+i)}: {d_bonus:.3f} mm")

print("\n📊 Resultat Final")
final_tol = total_tol + datum_bonus_total

print(f"\n### ✅ Tolerància posicional total amb datums: {final_tol:.3f} mm")
print("> Inclou:")
print(f"- Tolerància bàsica: {pos_tol:.3f} mm")
print(f"- Bonus de la característica: {bonus:.3f} mm")
print(f"- Bonus total dels datums: {datum_bonus_total:.3f} mm")
