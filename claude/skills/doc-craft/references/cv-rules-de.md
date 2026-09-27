# German CV Rules (Lebenslauf, Nominalstil): DACH region

Use for a German-language Lebenslauf only. Don't import these rules into an English CV: the
conventions differ by design. German hiring culture rewards precision and modesty over a selling
tone. Where this file and the general references disagree, this file wins for a Lebenslauf.

**Which CV to send:** an English-language ad gets the English CV, even from a German company. A
German-language ad gets the Lebenslauf, unless the candidate's German is clearly below what the
role needs (then it's a go/no-go question first).

## Language rules

- **Nominalstil**: noun-based phrasing. "Implementierung von …", not "Ich habe … implementiert."
- No "um zu" constructions, no abstract phrases, no emotional value judgments, no consultant-speak.
- No hyperbole ("leidenschaftlich", "visionär"). Sober, factual, professional.
- No US-style selling tone. Focus on responsibility and competence, not persuasion.
- No STAR/CAR anecdotes in bullets: describe responsibilities and contribution, with numbers
  where the field expects them.
- Translate informal input into formal business German.
- **Mirror the ad's German nouns literally** ("Datenanalyse", "Reporting", "Kennzahlen"), where
  true. Large-company ATS systems often match literally.

## Formatting rules

- **Kurzprofil:** a 3–4 line paragraph that opens the Lebenslauf, before Berufserfahrung. Sober
  and factual, numbers from the fact base; tailored versions echo the ad's German nouns in the
  last sentence. Insert it with `docproof add-summary <in> <out> KURZPROFIL "<text>" BERUFSERFAHRUNG`.
- **Dates:** `MM/JJJJ` with a four-digit year (`03/2022 – 08/2025`, degree `09/2022`). Never `MM/JJ`.
- **No period at the end of bullets.**
- **Bold only the position title.** Never bold the leading noun of a bullet.
- Entry header pattern: `MM/JJJJ – MM/JJJJ  Positionsbezeichnung, Organisation, Ort`, the same
  pattern for degrees. If the base document uses a different but consistent layout (title line,
  then company/date line), keep it; consistency matters more than the exact pattern.
- **Section order:** Kurzprofil → Berufserfahrung → Ausbildung → Sprachen → Kenntnisse →
  Projekte → (Interessen). Reorder with `docproof reorder`.
- **Sprachen:** CEFR levels, never rounded up. B1 is B1, in German too.
- **Personal data:** date of birth, nationality and marital status are optional under the AGG
  and add no selling value. Leave them out unless the user wants them.
- **Photo:** still common in German-speaking markets and legally optional. Follow the user's
  choice.
- **Address:** a street address in the header is normal for a Lebenslauf. A domestic address
  needs no country name.

## Mittelstand vs. Konzern

- **Mittelstand:** lead with hands-on tool and KPI evidence (SQL, Excel, BI, sales/ops metrics);
  keep AI and tooling claims to one line; few Anglicisms.
- **Konzern:** mirror the ad's nouns literally; cut projects that don't serve the role; check for
  a required German level (C1, "verhandlungssicher", "muttersprachlich") before applying.
- An Anschreiben still matters for Mittelstand, Konzern and agencies: one page. Write it only
  when the user asks, and in a language the candidate can also interview in.

## Quantification logic

- Business, sales, marketing, finance, analytics roles: use KPIs and quantified output.
- Social and educational roles: avoid artificial KPI self-marketing; describe qualitative
  steering and organisational reliability instead.

## The Schlüsselerfolg line (optional)

A closing line per role titled *Schlüsselerfolg*, in italics, never bold. Use it only when
tailoring for a specific ATS and only when it adds something the bullets don't; on a base CV it
tends to repeat the bullet above it. Keep it concrete (process, finance, customer, or learning
level), never hollow.

## Vocabulary bank (lead bullets with these nominalisations)

- **Leitung:** Steuerung, Delegation, Reorganisation, Koordination, Ausrichtung
- **Kommunikation:** Moderation, Verhandlung, Synthese, Erstellung, Abstimmung
- **Analyse:** Auswertung, Systematisierung, Validierung, Identifikation, Prüfung
- **Technik/Prozess:** Automatisierung, Optimierung, Standardisierung, Verschlankung, Modernisierung
- **Soziales/Coaching:** Befähigung, Unterstützung, Anleitung, Einarbeitung
- **Organisation:** Implementierung, Strukturierung, Verifizierung, Zentralisierung

Avoid "Orchestrierung": overused.

## Example (fictional candidate)

```
KURZPROFIL
Product Analyst mit drei Jahren Erfahrung in einer Abo-App: über 40 A/B-Tests, davon über 30
produktiv übernommen. Aufbau einer KPI-Schicht (SQL, dbt) für 5 Teams und Automatisierung des
wöchentlichen Reportings. M.Sc. Business Analytics. Schwerpunkt: Experimentation und Retention.

BERUFSERFAHRUNG
03/2022 – 08/2025  Product Analyst, Northwind Apps, London
- Durchführung von über 40 A/B-Tests, davon über 30 in das Produkt übernommen
- Aufbau einer KPI-Schicht auf Basis von SQL und dbt, genutzt von 5 Teams
- Automatisierung des wöchentlichen KPI-Reportings: Vorbereitung von ca. 6 Stunden auf ca. 45 Minuten reduziert
- Entwicklung eines Churn-Prognosemodells (logistische Regression) zur gezielteren Aussteuerung von Halteangeboten
```

## Honesty rules still apply

The same fact-base ceiling as the English CV: tenure worded as the fact base says, skill depth
never inflated, Known-gaps terms never claimed, language levels never rounded up, including
inside a CV written in German. Run `docproof verify` on the Lebenslauf like any other document.
