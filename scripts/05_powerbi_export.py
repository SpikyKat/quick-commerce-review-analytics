"""Step 5: tidy tables for Power BI. Review text is not exported; only dates, ratings and theme flags."""
import pandas as pd

from common import PBI
from qcmod.themes import COMPLAINT_THEMES, POSITIVE_THEMES

rv = pd.read_csv(PBI / "reviews_tagged.csv", parse_dates=["date"])
dim = pd.DataFrame([{"theme": t, "theme_label": t.replace("_", " ").capitalize(), "kind": "Complaint"} for t in COMPLAINT_THEMES]
                   + [{"theme": t, "theme_label": t.replace("_", " ").capitalize(), "kind": "Praise"} for t in POSITIVE_THEMES])
dim.to_csv(PBI / "dim_theme.csv", index=False)

long = rv.melt(id_vars=["review_id"], value_vars=list(dim.theme), var_name="theme", value_name="mentioned")
long = long[long.mentioned].drop(columns="mentioned")
long.to_csv(PBI / "review_themes_long.csv", index=False)

rv["month"] = rv.date.dt.to_period("M").dt.to_timestamp()
rv.to_csv(PBI / "reviews_tagged.csv", index=False)
print({f.name: len(pd.read_csv(f)) for f in sorted(PBI.glob("*.csv"))})
