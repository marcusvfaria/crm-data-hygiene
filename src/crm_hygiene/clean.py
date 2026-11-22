"""Higienização: padroniza nomes, e-mails, telefones e cidades."""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

EMAIL_RE = re.compile(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$")

CANONICAL_CITIES = [
    "Belo Horizonte", "Juiz de Fora", "Muriaé", "Ubá", "São Paulo",
    "Campinas", "Rio de Janeiro", "Niterói", "Vitória", "Curitiba",
]
# Abreviações comuns que não se resolvem só tirando acento
CITY_ALIASES = {
    "bh": "Belo Horizonte",
    "b. horizonte": "Belo Horizonte",
    "jf": "Juiz de Fora",
    "sp": "São Paulo",
    "s. paulo": "São Paulo",
    "rj": "Rio de Janeiro",
    "rio": "Rio de Janeiro",
}
LOWERCASE_PARTICLES = {"de", "da", "do", "das", "dos", "e"}


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def _city_key(text: str) -> str:
    return re.sub(r"\s+", " ", strip_accents(text).strip().lower())


_CITY_LOOKUP = {_city_key(c): c for c in CANONICAL_CITIES} | CITY_ALIASES


def normalize_name(name: object) -> str | None:
    if not isinstance(name, str) or not name.strip():
        return None
    words = re.sub(r"\s+", " ", name.strip()).lower().split(" ")
    return " ".join(w if w in LOWERCASE_PARTICLES and i > 0 else w.capitalize() for i, w in enumerate(words))


def normalize_email(email: object) -> str | None:
    if not isinstance(email, str):
        return None
    email = email.strip().lower()
    return email if EMAIL_RE.match(email) else None


def normalize_phone(phone: object) -> str | None:
    """Converte para o formato E.164 brasileiro: +55DDD9XXXXXXXX."""
    if not isinstance(phone, str):
        return None
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("55") and len(digits) in (12, 13):
        digits = digits[2:]
    digits = digits.lstrip("0")
    if len(digits) == 11 and digits[2] == "9":
        return f"+55{digits}"
    return None


def normalize_city(city: object) -> str | None:
    if not isinstance(city, str) or not city.strip():
        return None
    return _CITY_LOOKUP.get(_city_key(city), city.strip().title())


def clean_leads(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["nome"] = out["nome"].map(normalize_name)
    out["email_valido"] = out["email"].map(normalize_email)
    out["telefone_e164"] = out["telefone"].map(normalize_phone)
    out["cidade"] = out["cidade"].map(normalize_city)
    out["uf"] = out["uf"].str.strip().str.upper()
    out["data_criacao"] = pd.to_datetime(out["data_criacao"])
    out["data_ultima_etapa"] = pd.to_datetime(out["data_ultima_etapa"])
    return out
