from dataclasses import dataclass
import re


@dataclass
class NoteAnalysisResult:
    score: int
    nivel: str
    factores: list[str]
    resumen: str
    recomendacion: str


def analyze_caregiver_note(texto: str) -> NoteAnalysisResult:
    """
    Analiza una nota escrita por el cuidador y detecta
    posibles factores de riesgo mediante procesamiento
    básico de lenguaje.
    """

    texto_limpio = texto.lower().strip()

    score = 0
    factores = []

    # SUEÑO

    patrones_sueno = [
    "durmió poco",
    "durmio poco",
    "durmió mal",
    "durmio mal",
    "no durmió",
    "no durmio",
    "no pudo dormir",
    "no ha podido dormir",
    "se despertó",
    "se desperto",
    "se despierta varias veces",
    "despertó varias veces",
    "desperto varias veces",
    "problemas para dormir",
    "dificultad para dormir",
    "insomnio"
]

    if any(patron in texto_limpio for patron in patrones_sueno):
        score += 2
        factores.append("Alteración del sueño")

    # APETITO

    patrones_apetito = [
        "no quiso comer",
        "no quiere comer",
        "comió poco",
        "comio poco",
        "poco apetito",
        "sin apetito",
        "no tiene apetito",
        "rechazó la comida",
        "rechazo la comida"
    ]

    if any(patron in texto_limpio for patron in patrones_apetito):
        score += 2
        factores.append("Disminución del apetito")

    # CANSANCIO

    patrones_cansancio = [
        "está cansado",
        "esta cansado",
        "estuvo cansado",
        "más cansado",
        "mas cansado",
        "muy cansado",
        "fatiga",
        "agotado",
        "agotada",
        "débil",
        "debil"
    ]

    if any(patron in texto_limpio for patron in patrones_cansancio):
        score += 2
        factores.append("Cansancio o debilidad")

    # DOLOR

    patrones_dolor = [
        "tiene dolor",
        "presenta dolor",
        "le duele",
        "dolor intenso",
        "dolor fuerte",
        "dolor moderado",
        "se queja de dolor"
    ]

    if any(patron in texto_limpio for patron in patrones_dolor):
        score += 2
        factores.append("Presencia de dolor")

    # ESTADO DE ÁNIMO

    patrones_animo = [
    "está triste",
    "esta triste",
    "estuvo triste",
    "un poco triste",
    "muy triste",
    "más triste",
    "mas triste",
    "triste",
    "decaído",
    "decaido",
    "decaída",
    "decaida",
    "desanimado",
    "desanimada",
    "está ansioso",
    "esta ansioso",
    "estuvo ansioso",
    "ansiedad",
    "está irritable",
    "esta irritable",
    "irritable"
]

    if any(patron in texto_limpio for patron in patrones_animo):
        score += 2
        factores.append("Cambio en el estado de ánimo")

    # DESORIENTACIÓN

    patrones_desorientacion = [
        "está confundido",
        "esta confundido",
        "confusión",
        "confusion",
        "desorientado",
        "desorientada",
        "no reconoce",
        "se olvidó",
        "se olvido"
    ]

    if any(patron in texto_limpio for patron in patrones_desorientacion):
        score += 3
        factores.append("Posible desorientación o confusión")

    # FIEBRE
    

    patrones_fiebre = [
        "tiene fiebre",
        "presenta fiebre",
        "fiebre alta",
        "temperatura alta",
        "temperatura elevada"
    ]

    if any(patron in texto_limpio for patron in patrones_fiebre):
        score += 3
        factores.append("Posible fiebre o temperatura elevada")

    # CLASIFICACIÓN

    if score >= 7:
        nivel = "alto"
        recomendacion = (
            "Se recomienda una revisión prioritaria de la situación "
            "por parte de un profesional de salud."
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

    # RESUMEN

    if factores:
        resumen = (
            "La nota contiene indicios relacionados con: "
            + ", ".join(factores)
            + "."
        )
    else:
        resumen = (
            "No se identificaron factores de riesgo relevantes "
            "en el texto analizado."
        )

    return NoteAnalysisResult(
        score=score,
        nivel=nivel,
        factores=factores,
        resumen=resumen,
        recomendacion=recomendacion
    )