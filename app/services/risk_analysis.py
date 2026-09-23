from dataclasses import dataclass


@dataclass
class RiskAnalysisResult:
    score: int
    nivel: str
    factores: list[str]
    recomendacion: str


def analyze_symptoms(symptom) -> RiskAnalysisResult:
    score = 0
    factores = []

    # Dolor
    if symptom.nivel_dolor is not None:
        if symptom.nivel_dolor >= 8:
            score += 3
            factores.append("Dolor intenso")
        elif symptom.nivel_dolor >= 5:
            score += 2
            factores.append("Dolor moderado")
        

    # Temperatura
    if symptom.temperatura is not None:
        if symptom.temperatura >= 39:
            score += 3
            factores.append("Temperatura elevada")
        elif symptom.temperatura >= 38:
            score += 2
            factores.append("Temperatura por encima de lo habitual")

    # Calidad del sueño
    if symptom.calidad_sueno is not None:
        if symptom.calidad_sueno <= 2:
            score += 2
            factores.append("Alteración importante del sueño")
        elif symptom.calidad_sueno <= 4:
            score += 1
            factores.append("Alteración del sueño")

    # Apetito
    if symptom.apetito is not None:
        apetito = symptom.apetito.lower()

        if apetito == "muy bajo":
            score += 2
            factores.append("Apetito muy bajo")
        elif apetito == "bajo":
            score += 1
            factores.append("Apetito bajo")

    # Estado de ánimo
    if symptom.estado_animo is not None:
        estado = symptom.estado_animo.lower()

        if estado in ["decaído", "decaida", "decaído/a"]:
            score += 2
            factores.append("Estado de ánimo decaído")
        elif estado in ["triste", "ansioso", "ansiosa"]:
            score += 1
            factores.append("Cambio en el estado de ánimo")

    # Nivel de gravedad registrado por el cuidador
    if symptom.nivel_gravedad is not None:
        gravedad = symptom.nivel_gravedad.lower()

        if gravedad == "grave":
            score += 3
            factores.append("Gravedad registrada como alta")
        elif gravedad == "moderado":
            score += 2
            factores.append("Gravedad registrada como moderada")

    # Resultado final
    if score >= 7:
        nivel = "alto"
        recomendacion = (
            "Se recomienda una revisión prioritaria de la situación "
            "por parte de un profesional de salud."
        )
    elif score >= 4:
        nivel = "medio"
        recomendacion = (
            "Se recomienda realizar seguimiento cercano de la evolución "
            "del paciente."
        )
    else:
        nivel = "bajo"
        recomendacion = (
            "Continuar con el seguimiento habitual y registrar "
            "cualquier cambio relevante."
        )

    return RiskAnalysisResult(
        score=score,
        nivel=nivel,
        factores=factores,
        recomendacion=recomendacion
    )