"""Claves de cruce BeatStars x YouTube (insensible a acentos/caso/puntuacion)."""
import re
import unicodedata


def beat_key(name: str | None) -> str:
    s = unicodedata.normalize("NFKD", str(name or ""))
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def extract_beat_name(title: str) -> str:
    """Mejora del parser original: tambien entiende '"Beat" | resto' (sin ' - ')."""
    t = str(title).strip()
    if " - " in t:
        beat = t.split(" - ", maxsplit=1)[1]
        beat = beat.split("|", maxsplit=1)[0].strip()
        return beat.strip("\"' ").strip()
    m = re.search(r'"([^"]{1,60})"', t)
    if m:
        return m.group(1).strip()
    m = re.search(r"\|([^|]{1,60})\|", t)
    if m:
        cand = m.group(1).strip().strip("\"' ")
        if cand and len(cand.split()) <= 6:
            return cand
    return t
