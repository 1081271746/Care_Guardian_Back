from app.services.note_analysis import analyze_caregiver_note


texto = """
Hoy el paciente estuvo más cansado de lo normal.
Casi no quiso comer y durante la noche se despertó
varias veces. También estuvo un poco triste.
"""


resultado = analyze_caregiver_note(texto)


print("📝 ANÁLISIS DE NOTA")
print("----------------------")
print(f"Puntuación: {resultado.score}")
print(f"Nivel: {resultado.nivel}")

print("\nFactores detectados:")

for factor in resultado.factores:
    print(f"- {factor}")

print("\nResumen:")
print(resultado.resumen)

print("\nRecomendación:")
print(resultado.recomendacion)