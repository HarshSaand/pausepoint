import re
import unicodedata


PATTERNS = {
    "authority": re.compile(r"\b(bank|fraud team|police|government|security department)\b"),
    "urgency": re.compile(r"\b(immediately|urgent|right now|act now|within minutes)\b"),
    "isolation": re.compile(r"\b(do not tell|don't tell|keep this secret|stay on the line)\b"),
    "credential": re.compile(r"\b(otp|one time password|verification code|pin|password)\b"),
    "payment": re.compile(r"\b(transfer|send money|safe account|gift card|crypto|wallet)\b"),
}


def normalise(text: str) -> str:
    value = unicodedata.normalize("NFKC", text).lower()
    value = re.sub(r"\bo[.\s-]*t[.\s-]*p\b", "otp", value)
    value = re.sub(r"https?://\S+|www\.\S+", "<url>", value)
    return " ".join(value.split())


def extract(text: str) -> dict[str, bool]:
    cleaned = normalise(text)
    signals = {name: bool(pattern.search(cleaned)) for name, pattern in PATTERNS.items()}
    signals["url"] = "<url>" in cleaned
    signals["phone"] = bool(re.search(r"(?:\+?\d[\s-]?){8,}", cleaned))
    signals["amount"] = bool(re.search(r"(?:[$€£]\s?\d+|\b\d+(?:\.\d+)?\s?(?:dollars?|usd|sgd)\b)", cleaned))
    return signals
