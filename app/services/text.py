"""Text normalization shared by the rule engines."""
import unicodedata


def normalize(value: str | None) -> str:
    """Lowercase, trim and remove accents: 'Decaída ' → 'decaida'."""
    if not value:
        return ""
    decomposed = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))
