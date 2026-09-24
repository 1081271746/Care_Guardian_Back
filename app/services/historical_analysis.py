from dataclasses import dataclass


@dataclass
class HistoricalAnalysisResult:
    score: int
    nivel: str
    tendencias: list[str]
    registros_analizados: int
    recomendacion: str


def analyze_patient_history(symptoms) -> HistoricalAnalysisResult:
    """
    Analiza los registros recientes de síntomas de un paciente
    para detectar cambios o tendencias.
    """

    if not symptoms:
        return HistoricalAnalysisResult(
            score=0,
            nivel="bajo",
            tendencias=[],
            registros_analizados=0,
            recomendacion="No hay suficientes registros para realizar un análisis."
        )

    score = 0
    tendencias = []

    registros = list(reversed(symptoms))

    
    # Tendencia del sueño
    

    sueno = [
        s.calidad_sueno
        for s in registros
        if s.calidad_sueno is not None
    ]

    if len(sueno) >= 2:
        if sueno[-1] < sueno[0]:
            diferencia = sueno[0] - sueno[-1]

            if diferencia >= 3:
                score += 2
                tendencias.append(
                    "Se observa un deterioro importante en la calidad del sueño."
                )
            elif diferencia >= 1:
                score += 1
                tendencias.append(
                    "Se observa una disminución en la calidad del sueño."
                )

    
    # Tendencia del dolor
    

    dolor = [
        s.nivel_dolor
        for s in registros
        if s.nivel_dolor is not None
    ]

    if len(dolor) >= 2:
        if dolor[-1] > dolor[0]:
            diferencia = dolor[-1] - dolor[0]

            if diferencia >= 3:
                score += 2
                tendencias.append(
                    "Se observa un aumento importante del nivel de dolor."
                )
            elif diferencia >= 1:
                score += 1
                tendencias.append(
                    "Se observa un aumento del nivel de dolor."
                )

    
    # Tendencia de temperatura
    
    temperatura = [
        s.temperatura
        for s in registros
        if s.temperatura is not None
    ]

    if temperatura:
        ultima_temperatura = temperatura[-1]

        if ultima_temperatura >= 39:
            score += 3
            tendencias.append(
                "Se registra una temperatura elevada."
            )
        elif ultima_temperatura >= 38:
            score += 2
            tendencias.append(
                "Se registra una temperatura por encima de lo habitual."
            )

    
    # Apetito
    

    apetitos = [
        s.apetito.lower()
        for s in registros
        if s.apetito is not None
    ]

    if apetitos:
        ultimo_apetito = apetitos[-1]

        if ultimo_apetito == "muy bajo":
            score += 2
            tendencias.append(
                "Se registra un apetito muy bajo."
            )
        elif ultimo_apetito == "bajo":
            score += 1
            tendencias.append(
                "Se registra una disminución del apetito."
            )

    # Estado de ánimo

    estados = [
        s.estado_animo.lower()
        for s in registros
        if s.estado_animo is not None
    ]

    if len(estados) >= 2:
        estado_actual = estados[-1]

        if estado_actual in ["decaído", "decaida"]:
            score += 2
            tendencias.append(
                "Se registra un estado de ánimo decaído."
            )
        elif estado_actual in ["triste", "ansioso", "ansiosa"]:
            score += 1
            tendencias.append(
                "Se registra un cambio desfavorable en el estado de ánimo."
            )

    # Determinar nivel

    if score >= 7:
        nivel = "alto"
        recomendacion = (
            "Se recomienda una revisión prioritaria de la evolución "
            "del paciente por parte de un profesional de salud."
        )

    elif score >= 4:
        nivel = "medio"
        recomendacion = (
            "Se recomienda realizar un seguimiento cercano "
            "de la evolución del paciente."
        )

    else:
        nivel = "bajo"
        recomendacion = (
            "Continuar con el seguimiento habitual y registrar "
            "cualquier cambio relevante."
        )

    return HistoricalAnalysisResult(
        score=score,
        nivel=nivel,
        tendencias=tendencias,
        registros_analizados=len(registros),
        recomendacion=recomendacion
    )