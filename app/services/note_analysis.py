from dataclasses import dataclass


NEGATION_WORDS = {"no", "sin", "nunca", "tampoco", "ni"}
LINKING_VERBS = {"está", "esta", "estuvo", "tiene", "tuvo", "presenta", "presentó", "presento",
                 "se", "ha", "hay", "parece", "siente", "sintió", "sintio"}


def _negated(before: str) -> bool:
    words = before.replace(",", " ").split()[-2:]
    if words and words[-1] in NEGATION_WORDS:
        return True
    return len(words) == 2 and words[0] in NEGATION_WORDS and words[1] in LINKING_VERBS


def _mentions(texto: str, patrones) -> bool:
    """True when a pattern appears without a negation right before it.

    "no tiene fiebre", "sin fiebre" or "no está triste" must not raise an
    alert, while "no quiso comer" or "no pudo dormir" are themselves
    negative patterns and keep matching.
    """
    for patron in patrones:
        start = texto.find(patron)
        while start != -1:
            own_negation = patron.split()[0] in NEGATION_WORDS
            if own_negation or not _negated(texto[max(0, start - 30):start]):
                return True
            start = texto.find(patron, start + 1)
    return False


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

    if _mentions(texto_limpio, patrones_sueno):
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

    if _mentions(texto_limpio, patrones_apetito):
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

    if _mentions(texto_limpio, patrones_cansancio):
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

    if _mentions(texto_limpio, patrones_dolor):
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

    if _mentions(texto_limpio, patrones_animo):
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

    if _mentions(texto_limpio, patrones_desorientacion):
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

    if _mentions(texto_limpio, patrones_fiebre):
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