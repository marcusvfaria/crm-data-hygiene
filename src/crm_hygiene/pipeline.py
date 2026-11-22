"""Executa o pipeline completo: gerar → higienizar → deduplicar → pontuar → funil → relatório.

Uso:
    python -m crm_hygiene.pipeline                 # gera dados sintéticos e roda tudo
    python -m crm_hygiene.pipeline --input base.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .clean import clean_leads
from .dedupe import dedupe_leads
from .funnel import funnel_by_source, funnel_counts
from .generate import generate_leads
from .scoring import score_leads


def quality_summary(raw: pd.DataFrame, clean: pd.DataFrame, final: pd.DataFrame) -> dict:
    return {
        "registros_brutos": len(raw),
        "emails_invalidos": int(clean["email_valido"].isna().sum()),
        "telefones_invalidos_ou_vazios": int(clean["telefone_e164"].isna().sum()),
        "variacoes_de_cidade_antes": int(raw["cidade"].nunique()),
        "cidades_depois": int(final["cidade"].nunique()),
        "duplicatas_removidas": len(raw) - len(final),
        "leads_unicos": len(final),
        "sem_consentimento_lgpd": int((~final["consentimento_lgpd"]).sum()),
    }


def _md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def build_report(summary: dict, funnel: pd.DataFrame, by_source: pd.DataFrame, scored: pd.DataFrame) -> str:
    faixas = scored["faixa"].value_counts().reindex(["A", "B", "C", "Convertido"]).fillna(0).astype(int)
    q = "\n".join(f"| {k.replace('_', ' ')} | {v} |" for k, v in summary.items())
    return f"""# Relatório de qualidade e funil

## Qualidade da base
| Indicador | Valor |
|---|---|
{q}

## Funil
{_md_table(funnel)}

## Desempenho por origem
{_md_table(by_source)}

## Lead scoring (leads em aberto)
| Faixa | Leads | Ação sugerida |
|---|---|---|
| A (70–100) | {faixas['A']} | Contato do consultor em até 24 h |
| B (40–69) | {faixas['B']} | Régua de nutrição + follow-up semanal |
| C (0–39) | {faixas['C']} | Régua automática de baixo custo |
| Convertido | {faixas['Convertido']} | Fora da priorização (já matriculado) |
"""


def run(input_path: str | None, out_dir: str = "output", data_dir: str = "data") -> dict:
    out, data = Path(out_dir), Path(data_dir)
    out.mkdir(exist_ok=True)
    data.mkdir(exist_ok=True)

    if input_path:
        raw = pd.read_csv(input_path)
    else:
        raw = generate_leads()
        raw.to_csv(data / "leads_brutos.csv", index=False)

    clean = clean_leads(raw)
    final = score_leads(dedupe_leads(clean))
    funnel = funnel_counts(final)
    by_source = funnel_by_source(final)
    summary = quality_summary(raw, clean, final)

    final.to_csv(out / "leads_tratados.csv", index=False)
    funnel.to_csv(out / "funil.csv", index=False)
    by_source.to_csv(out / "funil_por_origem.csv", index=False)
    (out / "relatorio.md").write_text(build_report(summary, funnel, by_source, final), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", help="CSV de leads (sem isso, gera dados sintéticos)")
    parser.add_argument("--out", default="output", help="pasta de saída")
    args = parser.parse_args()
    summary = run(args.input, args.out)
    for k, v in summary.items():
        print(f"{k.replace('_', ' '):<32} {v}")
    print(f"\nArquivos gerados em ./{args.out}/")


if __name__ == "__main__":
    main()
