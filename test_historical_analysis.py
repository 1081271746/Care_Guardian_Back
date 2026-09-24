from app.services.historical_analysis import analyze_patient_history


class SymptomTest:
    def __init__(
        self,
        calidad_sueno,
        estado_animo,
        apetito,
        nivel_dolor,
        temperatura
    ):
        self.calidad_sueno = calidad_sueno
        self.estado_animo = estado_animo
        self.apetito = apetito
        self.nivel_dolor = nivel_dolor
        self.temperatura = temperatura


# Simulamos la evolución del paciente.
# Los registros están ordenados:
# MÁS ANTIGUO → MÁS RECIENTE

symptoms = [
    SymptomTest(
        calidad_sueno=8,
        estado_animo="estable",
        apetito="normal",
        nivel_dolor=2,
        temperatura=36.5
    ),

    SymptomTest(
        calidad_sueno=6,
        estado_animo="estable",
        apetito="normal",
        nivel_dolor=4,
        temperatura=36.8
    ),

    SymptomTest(
        calidad_sueno=4,
        estado_animo="decaído",
        apetito="bajo",
        nivel_dolor=7,
        temperatura=38.2
    )
]


# Ejecutar análisis histórico
result = analyze_patient_history(symptoms)


print("📊 ANÁLISIS HISTÓRICO")
print("----------------------")
print("Registros analizados:", result.registros_analizados)
print("Puntuación:", result.score)
print("Nivel:", result.nivel)

print("\nTendencias detectadas:")

if result.tendencias:
    for tendencia in result.tendencias:
        print("-", tendencia)
else:
    print("- No se detectaron tendencias relevantes.")

print("\nRecomendación:")
print(result.recomendacion)