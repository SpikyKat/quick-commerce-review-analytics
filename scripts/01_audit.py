"""Step 1: audit the three Kaggle files. What is in them, what is wrong, and which can carry real conclusions.

Includes tests that a file is rule-generated: if one column is an exact function of another, or unrelated columns
have zero correlation, that is evidence about how the data was made, not about customers.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import OUT, load_agents, load_orders, load_reviews, save_json
from qcmod.stats import wilson

plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False, "axes.spines.right": False})
res = {}

# ------------------------------------------------------------------ reviews.csv
rv = load_reviews()
r = {"rows": len(rv), "columns": list(rv.columns), "missing": int(rv.isna().sum().sum()),
     "duplicate_texts": int(rv.text.duplicated().sum()), "date_min": rv.date.min(), "date_max": rv.date.max()}
r["platform_counts"] = rv.platform.value_counts().to_dict()
r["rating_counts"] = rv.rating.value_counts().sort_index().to_dict()
r["share_one_star"] = float((rv.rating == 1).mean())
r["share_h2_2024"] = float((rv.date >= "2024-07-01").mean())
r["reviews_before_2024_07"] = int((rv.date < "2024-07-01").sum())
r["chars_median"], r["chars_max"] = float(rv.chars.median()), int(rv.chars.max())
r["share_at_or_near_500_chars"] = float((rv.chars >= 480).mean())
q = rv.assign(q=rv.date.dt.to_period("Q").astype(str))
tab = q.groupby(["q", "platform"]).size().unstack(fill_value=0)
r["platform_by_quarter_since_2024q3"] = tab.loc["2024Q3":].to_dict("index")
h2 = rv[rv.date >= "2024-07-01"]
r["h2_2024_platform_counts"] = h2.platform.value_counts().to_dict()
r["h2_2024_platform_mean_rating"] = h2.groupby("platform").rating.mean().round(3).to_dict()
r["h2_2024_by_month_platform"] = {str(k): v for k, v in h2.groupby([h2.date.dt.to_period("M"), "platform"]).size().unstack(fill_value=0).to_dict("index").items()}
res["reviews"] = r

# ------------------------------------------------------------------ Ecommerce_Delivery_Analytics_New.csv
od = load_orders()
o = {"rows": len(od), "customers": int(od.customer_id.nunique()), "missing": int(od.isna().sum().sum()),
     "duplicate_rows": int(od.duplicated().sum()), "order_id_unique": bool(od.order_id.is_unique),
     "time_field_distinct_values": int(od.order_time_raw.nunique()), "time_field_sample": od.order_time_raw.head(5).tolist()}
o["platform_counts"] = od.platform.value_counts().to_dict()
o["delay_exact_rule"] = {"min_minutes_when_delayed": int(od[od.delayed].delivery_min.min()),
                         "max_minutes_when_not_delayed": int(od[~od.delayed].delivery_min.max()),
                         "rows_breaking_rule_over_40": int((od.delayed != (od.delivery_min > 40)).sum())}
by_fb = od.groupby("feedback").agg(n=("rating", "size"), rating_min=("rating", "min"), rating_max=("rating", "max"),
                                   refund_rate=("refund", "mean"), delayed_rate=("delayed", "mean"))
o["feedback_phrases"] = int(len(by_fb))
o["phrases_with_single_rating"] = int((by_fb.rating_min == by_fb.rating_max).sum())
o["phrases_with_refund_rate_0_or_1"] = int(by_fb.refund_rate.isin([0.0, 1.0]).sum())
o["phrase_share_range"] = [float(by_fb.n.min() / len(od)), float(by_fb.n.max() / len(od))]
o["corr_rating_vs_delivery_min"] = float(od.rating.corr(od.delivery_min))
o["corr_value_vs_delivery_min"] = float(od.order_value.corr(od.delivery_min))
o["delayed_rate_by_platform"] = od.groupby("platform").delayed.mean().round(4).to_dict()
o["feedback_table"] = by_fb.round(3).reset_index().to_dict("records")
by_fb.round(3).to_csv(OUT / "tables" / "orders_feedback_rules.csv")
res["orders"] = o

# ------------------------------------------------------------------ Fast Delivery Agent Reviews.csv
ag = load_agents()
a = {"rows": len(ag), "missing": int(ag.isna().sum().sum()), "duplicate_rows": int(ag.duplicated().sum()),
     "distinct_review_texts": int(ag.review_text.nunique())}
num = ag[["rating", "delivery_min", "service_rating"]]
a["correlations"] = {"rating_vs_delivery_min": float(num.rating.corr(num.delivery_min)),
                     "rating_vs_service_rating": float(num.rating.corr(num.service_rating)),
                     "delivery_min_vs_service_rating": float(num.delivery_min.corr(num.service_rating))}
a["mean_rating_by_feedback_type"] = ag.groupby("feedback_type").rating.mean().round(3).to_dict()
a["mean_rating_by_accuracy"] = ag.groupby("accuracy").rating.mean().round(3).to_dict()
a["mean_delivery_min_by_platform"] = ag.groupby("platform").delivery_min.mean().round(2).to_dict()
a["mean_rating_by_platform"] = ag.groupby("platform").rating.mean().round(3).to_dict()
a["rating_by_stock_status"] = ag.groupby("availability").rating.mean().round(3).to_dict()
# are the review texts ordinary language? count a few very common English words
common = {"the", "and", "was", "not", "very", "delivery", "order", "good", "late", "app"}
tok = ag.review_text.str.lower().str.findall(r"[a-z]+")
a["share_reviews_with_any_common_review_word"] = float(tok.map(lambda t: bool(common & set(t))).mean())
a["sample_text"] = ag.review_text.head(2).tolist()
res["agents"] = a
save_json("audit", res)

# ------------------------------------------------------------------ figures
fig, ax = plt.subplots(figsize=(7, 3.4))
dist = rv.groupby(["platform", "rating"]).size().unstack(fill_value=0)
(dist.div(dist.sum(axis=1), axis=0) * 100).plot(kind="bar", stacked=True, ax=ax, colormap="RdYlGn", width=0.6)
ax.set_ylabel("% of reviews")
ax.set_xlabel("")
ax.set_title("Star ratings in the review sample, by platform")
plt.xticks(rotation=0)
ax.legend(title="stars", bbox_to_anchor=(1.01, 1), frameon=False)
plt.tight_layout()
plt.savefig(OUT / "figures" / "audit_review_ratings.png")
plt.close()

fig, ax = plt.subplots(figsize=(7, 3))
m = rv.groupby(rv.date.dt.to_period("M")).size()
ax.bar(m.index.astype(str), m.values, color="#2f6f9f")
ax.set_xticks(range(0, len(m), 6))
ax.set_xticklabels(m.index.astype(str)[::6], rotation=45, ha="right", fontsize=7)
ax.set_title("Reviews per month: the sample is almost all Jul-Dec 2024")
plt.tight_layout()
plt.savefig(OUT / "figures" / "audit_review_dates.png")
plt.close()

fig, axs = plt.subplots(1, 2, figsize=(9, 3.3))
bands = pd.cut(od.delivery_min, range(0, 85, 5))
axs[0].bar(range(len(bands.cat.categories)), od.groupby(bands, observed=False).delayed.mean().values * 100, color="#c0392b")
axs[0].set_xticks(range(len(bands.cat.categories)))
axs[0].set_xticklabels([f"{int(i.left)}-{int(i.right)}" for i in bands.cat.categories], rotation=60, fontsize=6)
axs[0].set_title("Order file: % flagged delayed by minutes")
axs[1].scatter(ag.delivery_min, ag.rating, s=3, alpha=0.3, color="#2f6f9f")
axs[1].set_xlabel("delivery minutes")
axs[1].set_ylabel("rating")
axs[1].set_title("Agent file: rating vs minutes")
plt.tight_layout()
plt.savefig(OUT / "figures" / "audit_synthetic_evidence.png")
plt.close()

for k in ("rows", "date_min", "date_max", "duplicate_texts", "share_h2_2024", "reviews_before_2024_07", "share_at_or_near_500_chars",
          "h2_2024_platform_counts", "h2_2024_platform_mean_rating", "h2_2024_by_month_platform"):
    print("reviews", k, r[k])
print("orders", {k: v for k, v in o.items() if k not in ("feedback_table",)})
print("agents", {k: v for k, v in a.items()})
