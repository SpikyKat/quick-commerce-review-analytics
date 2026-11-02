# Quick commerce: customer complaints, platform comparison and a data-validity audit

Analysis of three public Kaggle files about Blinkit, JioMart, Zepto and Swiggy Instamart. Read `docs/case_study.md` first.

**What it found, in short.** In 4,620 app reviews, the topics most tied to 1-2 star ratings are about service after the
order (support, cancellation, refunds, trust), not speed. Platforms differ in Oct-Dec 2024 (Blinkit 2.55 stars vs
JioMart 1.64 and Zepto 1.53), with sampling caveats. The two other files are synthetic: in the 100,000-order file the
delay flag is exactly "over 40 minutes" and the platforms are indistinguishable, so no delivery conclusions are drawn.

## Layout

```
src/qcmod/      complaint themes, statistics helpers
scripts/        01_audit, 02_review_themes, 03_text_model, 04_orders_audit, 05_powerbi_export
tests/          pytest
docs/           case study, data card, Power BI build guide, career kit
```

## Run

Put the three CSVs in `data/raw/` (names in `docs/data_card.md`), then:

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.\run_all.ps1
```

Tables for Power BI are written to `data/powerbi/`; follow `docs/POWERBI_BUILD_GUIDE.md`.

## Status and limits

Raw data, derived tables and figures are git-ignored. Review text is never published. Kaggle licences are still to be
recorded in `docs/data_card.md` before the repository is made public. The Power BI report is not built yet.
