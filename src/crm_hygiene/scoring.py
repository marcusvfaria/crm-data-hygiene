"""Lead scoring por regras explicáveis (0–100).

Regras simples e auditáveis, no espírito do que se configura em Rubeus ou RD Station:
cada ponto tem um motivo que o time comercial entende.
"""

from __future__ import annotations

import pandas as pd

SOURCE_POINTS = {"Indicação": 25, "Evento": 20, "Orgânico": 18, "Site": 15, "Google Ads": 15, "Meta Ads": 10}
STAGE_POINTS = {"Lead": 0, "Inscrito": 20, "Prova realizada": 35, "Aprovado": 45, "Matriculado": 45}


def score_leads(df: pd.DataFrame, reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    out = df.copy()
    ref = reference_date or out["data_ultima_etapa"].max()

    origem = out["origem"].map(SOURCE_POINTS).fillna(0)
    etapa = out["etapa"].map(STAGE_POINTS).fillna(0)
    completude = out["email"].notna() * 7 + out["telefone"].notna() * 8  # contato completo = até 15
    dias_parado = (ref - out["data_ultima_etapa"]).dt.days
    recencia = pd.cut(dias_parado, bins=[-1, 7, 30, 60, 10_000], labels=[15, 10, 5, 0]).astype(int)

    out["score"] = (origem + etapa + completude + recencia).clip(0, 100).astype(int)
    faixa = pd.cut(out["score"], bins=[-1, 39, 69, 100], labels=["C", "B", "A"]).astype(str)
    # Quem já matriculou não precisa de priorização comercial
    out["faixa"] = faixa.where(out["etapa"] != "Matriculado", "Convertido")
    out["dias_sem_avanco"] = dias_parado
    return out
