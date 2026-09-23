from app.services.risk_analysis import analyze_symptoms


class SymptomTest:
    nivel_dolor = 6
    temperatura = 37.8
    calidad_sueno = 4
    apetito = "bajo"
    estado_animo = "estable"
    nivel_gravedad = "moderado"


symptom = SymptomTest()

result = analyze_symptoms(symptom)

print("Puntuación:", result.score)
print("Nivel:", result.nivel)
print("Factores:")

for factor in result.factores:
    print("-", factor)

print("Recomendación:")
print(result.recomendacion)