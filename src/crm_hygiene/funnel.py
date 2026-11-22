"""Métricas de funil: volume por etapa, conversão etapa a etapa e por origem."""

from __future__ import annotations

import pandas as pd

from .dedupe import STAGE_RANK, STAGES


def funnel_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Quantos leads chegaram a cada etapa (quem está em 'Aprovado' também passou por 'Inscrito')."""
    rank = df["etapa"].map(STAGE_RANK)
    rows = []
    for i, stage in enumerate(STAGES):
        reached = int((rank >= i).sum())
        rows.append({"etapa": stage, "leads": reached})
    out = pd.DataFrame(rows)
    out["conversao_etapa_anterior_%"] = (out["leads"] / out["leads"].shift(1) * 100).round(1).fillna(100.0)
    out["conversao_total_%"] = (out["leads"] / out["leads"].iloc[0] * 100).round(1)
    return out


def funnel_by_source(df: pd.DataFrame) -> pd.DataFrame:
    rank = df["etapa"].map(STAGE_RANK)
    g = df.assign(_matriculado=rank >= STAGE_RANK["Matriculado"], _inscrito=rank >= STAGE_RANK["Inscrito"])
    out = g.groupby("origem").agg(
        leads=("lead_id", "count"),
        inscritos=("_inscrito", "sum"),
        matriculados=("_matriculado", "sum"),
        score_medio=("score", "mean"),
    )
    out["taxa_inscricao_%"] = (out["inscritos"] / out["leads"] * 100).round(1)
    out["taxa_matricula_%"] = (out["matriculados"] / out["leads"] * 100).round(1)
    out["score_medio"] = out["score_medio"].round(1)
    return out.sort_values("taxa_matricula_%", ascending=False).reset_index()
