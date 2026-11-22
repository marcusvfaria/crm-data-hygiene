"""Gera uma base sintética de leads de captação (ensino superior) com "sujeira" realista.

Nenhum dado é real: nomes, e-mails e telefones são combinações aleatórias.
A sujeira injetada imita o que aparece em bases de CRM de verdade:
duplicatas com grafias diferentes, telefones em formatos variados,
cidades abreviadas ou sem acento, e-mails inválidos e campos vazios.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import pandas as pd

FIRST_NAMES = [
    "Ana", "Bruno", "Camila", "Daniel", "Eduarda", "Felipe", "Gabriela", "Henrique",
    "Isabela", "João", "Larissa", "Lucas", "Mariana", "Mateus", "Natália", "Pedro",
    "Rafaela", "Rodrigo", "Sofia", "Thiago", "Valentina", "Vinícius", "Beatriz", "Gustavo",
]
LAST_NAMES = [
    "Silva", "Souza", "Oliveira", "Santos", "Pereira", "Lima", "Carvalho", "Ferreira",
    "Rodrigues", "Almeida", "Costa", "Gomes", "Martins", "Araújo", "Ribeiro", "Barbosa",
]
CITIES = [
    ("Belo Horizonte", "MG"), ("Juiz de Fora", "MG"), ("Muriaé", "MG"), ("Ubá", "MG"),
    ("São Paulo", "SP"), ("Campinas", "SP"), ("Rio de Janeiro", "RJ"), ("Niterói", "RJ"),
    ("Vitória", "ES"), ("Curitiba", "PR"),
]
# Variações "sujas" que aparecem em formulários reais
CITY_VARIANTS = {
    "Belo Horizonte": ["belo horizonte", "BH", "B. Horizonte", "Belo Horizonte "],
    "São Paulo": ["sao paulo", "SP", "S. Paulo", "São paulo"],
    "Rio de Janeiro": ["rio de janeiro", "RJ", "Rio", "Rio De Janeiro"],
    "Juiz de Fora": ["juiz de fora", "JF", "Juiz De Fora"],
    "Muriaé": ["muriae", "Muriae", "MURIAÉ"],
    "Niterói": ["niteroi", "Niteroi"],
    "Vitória": ["vitoria", "Vitoria"],
    "Ubá": ["uba", "Uba"],
}
SOURCES = ["Google Ads", "Meta Ads", "Orgânico", "Indicação", "Evento", "Site"]
SOURCE_WEIGHTS = [0.25, 0.25, 0.15, 0.10, 0.10, 0.15]
COURSES = ["Administração", "Direito", "Enfermagem", "Engenharia Civil", "Psicologia", "Sistemas de Informação"]

STAGES = ["Lead", "Inscrito", "Prova realizada", "Aprovado", "Matriculado"]
# Probabilidade de avançar de uma etapa para a seguinte, por origem
ADVANCE_PROB = {
    "Google Ads": [0.45, 0.70, 0.80, 0.55],
    "Meta Ads": [0.35, 0.60, 0.75, 0.45],
    "Orgânico": [0.50, 0.75, 0.80, 0.60],
    "Indicação": [0.65, 0.85, 0.85, 0.75],
    "Evento": [0.55, 0.75, 0.80, 0.60],
    "Site": [0.45, 0.70, 0.80, 0.55],
}


def _strip_accents_sometimes(text: str, rng: random.Random) -> str:
    if rng.random() < 0.3:
        table = str.maketrans("áàâãéêíóôõúçÁÉÍÓÚÇ", "aaaaeeiooouc" + "AEIOUC")
        return text.translate(table)
    return text


def _messy_phone(ddd: str, number: str, rng: random.Random) -> str:
    formats = [
        f"({ddd}) {number[:5]}-{number[5:]}",
        f"{ddd}{number}",
        f"+55 {ddd} {number}",
        f"0{ddd} {number[:5]} {number[5:]}",
        f"{ddd} {number[:5]}-{number[5:]}",
    ]
    return rng.choice(formats)


def _messy_name(name: str, rng: random.Random) -> str:
    variant = _strip_accents_sometimes(name, rng)
    roll = rng.random()
    if roll < 0.15:
        return variant.upper()
    if roll < 0.30:
        return variant.lower()
    if roll < 0.40:
        return "  " + variant.replace(" ", "  ") + " "
    return variant


def generate_leads(n: int = 2000, duplicate_rate: float = 0.12, seed: int = 42) -> pd.DataFrame:
    """Gera `n` leads únicos e injeta duplicatas e ruído."""
    rng = random.Random(seed)
    start = datetime(2026, 6, 1)
    rows = []

    for i in range(n):
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        name = f"{first} {last}"
        email_user = f"{first}.{last}{rng.randint(1, 999)}".lower()
        email_user = email_user.translate(str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc"))
        email = f"{email_user}@{rng.choice(['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com.br'])}"
        city, uf = rng.choice(CITIES)
        ddd = {"MG": "32", "SP": "11", "RJ": "21", "ES": "27", "PR": "41"}[uf]
        number = "9" + "".join(str(rng.randint(0, 9)) for _ in range(8))
        source = rng.choices(SOURCES, SOURCE_WEIGHTS)[0]
        created = start + timedelta(days=rng.randint(0, 150), hours=rng.randint(0, 23))

        # Avanço no funil
        stage_idx = 0
        stage_dates = {STAGES[0]: created}
        current = created
        for step, prob in enumerate(ADVANCE_PROB[source]):
            if rng.random() < prob:
                current = current + timedelta(days=rng.randint(1, 20))
                stage_idx = step + 1
                stage_dates[STAGES[stage_idx]] = current
            else:
                break

        rows.append({
            "lead_id": f"L{i + 1:05d}",
            "nome": name,
            "email": email,
            "telefone": _messy_phone(ddd, number, rng),
            "cidade": city,
            "uf": uf,
            "origem": source,
            "curso_interesse": rng.choice(COURSES),
            "etapa": STAGES[stage_idx],
            "data_criacao": created,
            "data_ultima_etapa": stage_dates[STAGES[stage_idx]],
            "consentimento_lgpd": rng.random() < 0.93,
        })

    df = pd.DataFrame(rows)

    # Duplicatas: o mesmo lead cadastrado de novo, com grafia diferente
    n_dup = int(n * duplicate_rate)
    dup_rows = []
    for k, idx in enumerate(rng.sample(range(n), n_dup)):
        dup = df.iloc[idx].to_dict()
        dup["lead_id"] = f"L{n + k + 1:05d}"
        dup["nome"] = _messy_name(dup["nome"], rng)
        if rng.random() < 0.5:
            dup["email"] = "  " + dup["email"].upper() + " "
        digits = "".join(c for c in dup["telefone"] if c.isdigit())[-11:]
        dup["telefone"] = _messy_phone(digits[:2], digits[2:], rng)
        # Duplicata costuma ficar parada numa etapa anterior
        dup["etapa"] = STAGES[0]
        dup["data_criacao"] = dup["data_criacao"] + timedelta(days=rng.randint(0, 30))
        dup["data_ultima_etapa"] = dup["data_criacao"]
        dup_rows.append(dup)
    df = pd.concat([df, pd.DataFrame(dup_rows)], ignore_index=True)

    # Ruído geral
    for idx in df.index:
        r = rng.random()
        if r < 0.20:
            df.at[idx, "nome"] = _messy_name(df.at[idx, "nome"], rng)
        city = df.at[idx, "cidade"]
        if city in CITY_VARIANTS and rng.random() < 0.35:
            df.at[idx, "cidade"] = rng.choice(CITY_VARIANTS[city])
        if rng.random() < 0.03:
            df.at[idx, "email"] = df.at[idx, "email"].replace("@", "")  # e-mail inválido
        if rng.random() < 0.04:
            df.at[idx, "telefone"] = None
        if rng.random() < 0.05:
            df.at[idx, "uf"] = df.at[idx, "uf"].lower()

    return df.sample(frac=1, random_state=seed).reset_index(drop=True)
