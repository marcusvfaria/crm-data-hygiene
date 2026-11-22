# CRM Data Hygiene & Funnel Analytics

Pipeline em Python que pega uma base de leads "suja", do jeito que ela sai de formulários, planilhas e integrações, e entrega uma base pronta para operar no CRM: higienizada, sem duplicatas, com lead scoring e métricas de funil.

O cenário é a **captação de alunos no ensino superior**: lead → inscrição → prova → aprovação → matrícula. É o mesmo fluxo que se opera em CRMs educacionais como Rubeus.

> Todos os dados são **sintéticos**, gerados pelo próprio projeto. Nenhum dado pessoal real é usado.

## O problema

Uma base de CRM sem tratamento costuma ter:

- o mesmo lead cadastrado várias vezes, com o nome escrito de jeitos diferentes;
- telefones em 5 formatos (`(32) 99123-4567`, `+55 32 991234567`, `032 99123 4567`…);
- cidades como "BH", "belo horizonte" e "B. Horizonte" contadas como lugares diferentes;
- e-mails inválidos que derrubam a entregabilidade das réguas.

O resultado são métricas de funil infladas, réguas disparando em duplicidade e um time comercial que não confia no CRM.

## O que o pipeline faz

| Etapa | O que acontece | Módulo |
|---|---|---|
| 1. Geração | Cria uma base sintética com ~12% de duplicatas e ruído realista | `generate.py` |
| 2. Higienização | Padroniza nomes, valida e-mails, converte telefones para E.164, unifica cidades | `clean.py` |
| 3. Deduplicação | Liga registros pelo e-mail **ou** pelo telefone (union-find, ligação transitiva) e consolida num registro mestre | `dedupe.py` |
| 4. Lead scoring | Pontuação de 0 a 100 por regras explicáveis: origem, etapa, completude do contato, recência | `scoring.py` |
| 5. Funil | Conversão etapa a etapa e desempenho por canal de origem | `funnel.py` |
| 6. Relatório | CSVs prontos para Power BI e um relatório em Markdown | `pipeline.py` |

### Regras de consolidação (deduplicação)

- **Registro mestre** = o cadastro mais antigo (preserva a data real de entrada).
- **Origem** = a do primeiro contato (atribuição first-touch).
- **Etapa** = a mais avançada entre os registros duplicados.
- **Consentimento LGPD** = verdadeiro se qualquer registro tiver consentimento.

## Resultado na base de exemplo

| Indicador | Valor |
|---|---|
| Registros brutos | 2.240 |
| Duplicatas removidas | 238 |
| Leads únicos | 2.002 |
| Variações de cidade → cidades reais | 34 → 10 |
| E-mails inválidos sinalizados | 66 |

Leitura do funil por origem: **Indicação** converte em matrícula 5× mais que **Meta Ads** (28,3% contra 5,7%). Com essa informação, dá para rever a distribuição de verba e criar um programa de indicação.

O relatório completo está em [`output/relatorio.md`](output/relatorio.md).

## Como rodar

```bash
git clone https://github.com/marcusvfaria/crm-data-hygiene.git
cd crm-data-hygiene
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

python -m crm_hygiene.pipeline                    # gera dados sintéticos e roda tudo
python -m crm_hygiene.pipeline --input sua_base.csv  # ou roda sobre uma base própria
pytest                                            # testes
```

Arquivos gerados em `output/`:

- `leads_tratados.csv`: base final com score, faixa e rastreio dos IDs mesclados
- `funil.csv` e `funil_por_origem.csv`: prontos para importar no Power BI
- `relatorio.md`: resumo de qualidade e funil

## Stack

Python 3.10+ · pandas · pytest

## Próximos passos

- [ ] Dashboard em Power BI a partir dos CSVs de saída
- [ ] Sincronização com Google Sheets via `gspread`
- [ ] Deduplicação aproximada de nomes (fuzzy matching) para casos sem e-mail e sem telefone

---

Marcus Vinicius Faria · CRM Ops & RevOps · [linkedin.com/in/mvcaf](https://www.linkedin.com/in/mvcaf/)
