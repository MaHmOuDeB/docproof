# Fact base — Jordan Rivera (fictional example)

Every claim in every document comes from this file. If a fact isn't here, it doesn't go in a
document — add it here first (with its source), then use it. `docproof verify` checks documents
against this file; `docproof match` maps job ads to it.

## Identity
- Name: Jordan Rivera
- Location: London, UK
- Email: jordan.rivera@example.com
- Phone: +44 20 7946 0123
- Website: jordanrivera.example
- Target roles: product analyst, experimentation analyst, growth analyst

## Experience

### Product Analyst — Northwind Apps, London — Mar 2022 – Aug 2025
Northwind Apps is a subscription language-learning app (fictional).
- Designed and analysed **40+** A/B tests on onboarding, paywall and notification flows, from
  hypothesis and power analysis to a ship/no-ship recommendation; **30+** shipped.
  Safe wording: "30+ shipped" (the product manager made the final call — say "recommendation").
- Built a SQL + dbt KPI layer (activation, retention, revenue) used by **5** product and marketing
  teams as their single source of truth.
- Automated the weekly KPI report with Python and scheduled dbt runs: preparation went from
  **~6 hours** to **~45 minutes**.
- Built a churn-prediction model (logistic regression) that ranked at-risk subscribers and improved
  save-offer targeting. No uplift figure was measured — never invent one.
- Defined the event tracking plan for the new onboarding flow with engineering: **18** events and
  their properties.
- Presented monthly experiment reviews to product leadership.

### Data Analyst Intern — Harbor Retail Group, London — Jun 2021 – Sep 2021
- Cleaned and reconciled **2** years of store sales data in Excel and SQL for the pricing team.
- Built a weekly Tableau dashboard of promotion performance for **4** category managers.

## Projects

### Churn Radar — Personal Project — 2025
- Open-source churn dashboard on a public telco dataset: survival curves, cohort retention and a
  gradient-boosting model (AUC **0.84** on a held-out set).
- Stack: Python, scikit-learn, DuckDB, Streamlit.
- Link: https://jordanrivera.example/churn-radar

## Education
- MSc Business Analytics — Northbridge University (fictional) — Sep 2021 – Sep 2022.
  Dissertation: uplift modelling for retention offers.
- BSc Economics — Kingsbridge College (fictional) — Sep 2018 – Jun 2021.

## Skills (with honest depth)
- SQL — professional, daily. dbt — professional. Python (pandas, scikit-learn) — professional.
- Tableau — built dashboards (internship). Looker Studio — used. Excel — advanced.
- A/B testing and power analysis — professional. Logistic regression, gradient boosting — professional/project.
- Event tracking plans — professional. Git — daily.
- AI-assisted analysis and coding: ChatGPT, GitHub Copilot.
- Stakeholder reporting to product leadership.

## Languages
- English — Native
- Spanish — C1
- German — A2

## Known gaps
Terms the documents must never claim (`docproof verify` flags them):
- Airflow
- Snowflake
- GA4
- Braze
- R
- Kubernetes
- people management

## Bullet variants
Alternates for tailoring — same facts, different emphasis.
- Stakeholder-led: "Presented monthly experiment reviews to product leadership; 30+ of 40+ tests shipped."
- Data-modelling-led: "Modelled activation, retention and revenue in dbt, giving 5 teams one source of truth."
