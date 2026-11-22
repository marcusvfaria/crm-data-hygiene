import pandas as pd

from crm_hygiene.clean import clean_leads, normalize_city, normalize_email, normalize_name, normalize_phone
from crm_hygiene.dedupe import dedupe_leads
from crm_hygiene.funnel import funnel_counts
from crm_hygiene.generate import generate_leads
from crm_hygiene.scoring import score_leads


def test_normalize_name():
    assert normalize_name("  JOÃO  DA silva ") == "João da Silva"
    assert normalize_name("") is None


def test_normalize_email():
    assert normalize_email("  Ana.Lima@Gmail.COM ") == "ana.lima@gmail.com"
    assert normalize_email("ana.limagmail.com") is None


def test_normalize_phone_formats():
    expected = "+5532991234567"
    for raw in ["(32) 99123-4567", "32991234567", "+55 32 991234567", "032 99123 4567"]:
        assert normalize_phone(raw) == expected
    assert normalize_phone("1234") is None


def test_normalize_city():
    assert normalize_city("sao paulo") == "São Paulo"
    assert normalize_city("BH") == "Belo Horizonte"
    assert normalize_city("muriae") == "Muriaé"


def test_dedupe_links_by_email_or_phone():
    raw = pd.DataFrame([
        {"lead_id": "L1", "nome": "Ana Lima", "email": "ana@x.com", "telefone": "(32) 99123-4567",
         "cidade": "Muriaé", "uf": "MG", "origem": "Site", "curso_interesse": "Direito",
         "etapa": "Lead", "data_criacao": "2026-06-01", "data_ultima_etapa": "2026-06-01", "consentimento_lgpd": True},
        {"lead_id": "L2", "nome": "ANA LIMA", "email": " ANA@X.COM ", "telefone": None,
         "cidade": "muriae", "uf": "mg", "origem": "Meta Ads", "curso_interesse": "Direito",
         "etapa": "Inscrito", "data_criacao": "2026-06-05", "data_ultima_etapa": "2026-06-10", "consentimento_lgpd": True},
        {"lead_id": "L3", "nome": "Ana L.", "email": None, "telefone": "32991234567",
         "cidade": "Muriaé", "uf": "MG", "origem": "Site", "curso_interesse": "Direito",
         "etapa": "Lead", "data_criacao": "2026-06-07", "data_ultima_etapa": "2026-06-07", "consentimento_lgpd": False},
    ])
    out = dedupe_leads(clean_leads(raw))
    assert len(out) == 1
    row = out.iloc[0]
    assert row["lead_id"] == "L1"          # registro mais antigo vira o mestre
    assert row["etapa"] == "Inscrito"      # etapa mais avançada prevalece
    assert row["origem"] == "Site"         # origem do primeiro contato
    assert row["registros_mesclados"] == 3


def test_full_pipeline_invariants():
    raw = generate_leads(n=500, seed=1)
    final = score_leads(dedupe_leads(clean_leads(raw)))
    assert len(final) < len(raw)
    assert final["score"].between(0, 100).all()
    funnel = funnel_counts(final)
    assert funnel["leads"].is_monotonic_decreasing
