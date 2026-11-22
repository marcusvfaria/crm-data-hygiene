"""Deduplicação: agrupa registros da mesma pessoa e consolida num registro mestre.

Dois registros são da mesma pessoa se compartilham e-mail válido OU telefone válido.
A ligação é transitiva (A=B pelo e-mail, B=C pelo telefone → A, B e C são um só),
resolvida com union-find.
"""

from __future__ import annotations

import pandas as pd

STAGES = ["Lead", "Inscrito", "Prova realizada", "Aprovado", "Matriculado"]
STAGE_RANK = {s: i for i, s in enumerate(STAGES)}


class _UnionFind:
    def __init__(self, items):
        self.parent = {i: i for i in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def assign_clusters(df: pd.DataFrame) -> pd.Series:
    uf = _UnionFind(df.index)
    for key in ("email_valido", "telefone_e164"):
        for _, idxs in df.dropna(subset=[key]).groupby(key).groups.items():
            idxs = list(idxs)
            for other in idxs[1:]:
                uf.union(idxs[0], other)
    return pd.Series({i: uf.find(i) for i in df.index}, name="cluster")


def _merge_group(g: pd.DataFrame) -> dict:
    g = g.assign(_rank=g["etapa"].map(STAGE_RANK)).sort_values("data_criacao")
    best = g.sort_values(["_rank", "data_ultima_etapa"], ascending=False).iloc[0]
    first = g.iloc[0]

    def first_valid(col):
        vals = g[col].dropna()
        return vals.iloc[0] if len(vals) else None

    return {
        "lead_id": first["lead_id"],
        "nome": first_valid("nome"),
        "email": first_valid("email_valido"),
        "telefone": first_valid("telefone_e164"),
        "cidade": first_valid("cidade"),
        "uf": first_valid("uf"),
        "origem": first["origem"],  # primeira origem = canal que gerou o lead
        "curso_interesse": best["curso_interesse"],
        "etapa": best["etapa"],
        "data_criacao": first["data_criacao"],
        "data_ultima_etapa": best["data_ultima_etapa"],
        "consentimento_lgpd": bool(g["consentimento_lgpd"].any()),
        "registros_mesclados": len(g),
        "ids_mesclados": ";".join(g["lead_id"]),
    }


def dedupe_leads(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["cluster"] = assign_clusters(df)
    merged = [_merge_group(g) for _, g in df.groupby("cluster", sort=False)]
    return pd.DataFrame(merged).sort_values("lead_id").reset_index(drop=True)
