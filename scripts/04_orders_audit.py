"""Step 4: the 100,000-order file. KPIs with intervals, the delay-threshold sensitivity check, and tests for any real structure.

The audit showed the delay flag and the rating are rule-generated, so this script does two things: reports the KPIs the
dashboard needs, and checks whether platform, category or order value explain anything beyond those rules.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, kruskal

from common import OUT, PBI, load_orders, save_json
from qcmod.stats import chi2_groups, wilson

plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False, "axes.spines.right": False})
od = load_orders()
res = {"rows": len(od)}


def kpis(d):
    n = len(d)
    k = int(d.delayed.sum())
    r = int(d.refund.sum())
    return {"orders": n, "delay_rate": k / n, "delay_ci": wilson(k, n), "refund_rate": r / n, "refund_ci": wilson(r, n),
            "avg_minutes": float(d.delivery_min.mean()), "median_minutes": float(d.delivery_min.median()),
            "p90_minutes": float(d.delivery_min.quantile(0.9)), "avg_rating": float(d.rating.mean()),
            "share_4plus_stars": float((d.rating >= 4).mean()), "avg_order_value": float(d.order_value.mean()),
            "order_value_total": int(d.order_value.sum()), "refund_order_value": int(d[d.refund].order_value.sum())}


res["overall"] = kpis(od)
res["by_platform"] = {p: kpis(g) for p, g in od.groupby("platform")}
res["by_category"] = {c: kpis(g) for c, g in od.groupby("category")}
res["refund_value_share_of_order_value"] = res["overall"]["refund_order_value"] / res["overall"]["order_value_total"]

# are the platforms different at all?
g = od.groupby("platform")
res["tests_platform"] = {
    "delay_rate": chi2_groups(g.delayed.sum().values, g.size().values),
    "refund_rate": chi2_groups(g.refund.sum().values, g.size().values),
    "minutes_kruskal_p": float(kruskal(*[x.delivery_min.values for _, x in g]).pvalue),
    "rating_kruskal_p": float(kruskal(*[x.rating.values for _, x in g]).pvalue),
    "order_value_kruskal_p": float(kruskal(*[x.order_value.values for _, x in g]).pvalue)}
gc = od.groupby("category")
res["tests_category"] = {"delay_rate": chi2_groups(gc.delayed.sum().values, gc.size().values),
                         "refund_rate": chi2_groups(gc.refund.sum().values, gc.size().values),
                         "minutes_kruskal_p": float(kruskal(*[x.delivery_min.values for _, x in gc]).pvalue),
                         "order_value_kruskal_p": float(kruskal(*[x.order_value.values for _, x in gc]).pvalue)}
res["feedback_by_platform_chi2_p"] = float(chi2_contingency(pd.crosstab(od.feedback, od.platform))[1])
res["feedback_by_category_chi2_p"] = float(chi2_contingency(pd.crosstab(od.feedback, od.category))[1])

# analytical threshold sensitivity (the dataset's own flag is minutes over 40)
sens = []
for t in (25, 30, 35, 40, 45, 50):
    flag = od.delivery_min > t
    row = {"threshold_min": t, "overall": float(flag.mean())}
    row.update({p: float(flag[od.platform == p].mean()) for p in sorted(od.platform.unique())})
    row["spread_between_platforms"] = max(row[p] for p in od.platform.unique()) - min(row[p] for p in od.platform.unique())
    sens.append(row)
sens = pd.DataFrame(sens)
sens.to_csv(OUT / "tables" / "orders_threshold_sensitivity.csv", index=False)
res["threshold_sensitivity"] = sens.round(4).to_dict("records")

# complaints and refunds
fb = od.groupby("feedback").agg(orders=("rating", "size"), rating=("rating", "first"), refund_rate=("refund", "mean"),
                                delayed_rate=("delayed", "mean"), avg_minutes=("delivery_min", "mean"),
                                avg_order_value=("order_value", "mean"), refunded_value=("order_value", lambda s: s[od.loc[s.index, "refund"]].sum()))
fb["kind"] = np.where(fb.refund_rate == 1, "complaint", "praise_or_neutral")
res["feedback_summary"] = fb.round(3).reset_index().to_dict("records")
res["delayed_orders_leading_to_complaint_phrases"] = float(od[od.delayed].refund.mean())
res["not_delayed_orders_refund_rate"] = float(od[~od.delayed].refund.mean())
res["late_phrase_vs_actual_delay"] = {
    "orders_saying_very_late": int((od.feedback == "Very late delivery, not happy.").sum()),
    "of_which_flagged_delayed": float(od[od.feedback == "Very late delivery, not happy."].delayed.mean()),
    "orders_flagged_delayed_that_say_something_praising": float(od[od.delayed & (od.rating >= 4)].shape[0] / od.delayed.sum())}
save_json("orders_audit", res)
print(pd.DataFrame(res["by_platform"]).T[["orders", "delay_rate", "refund_rate", "avg_minutes", "avg_rating", "avg_order_value"]].round(4))
print(res["tests_platform"], res["tests_category"], res["feedback_by_platform_chi2_p"], res["feedback_by_category_chi2_p"], sep="\n")
print(sens.round(4).to_string(index=False))
print(res["late_phrase_vs_actual_delay"], res["delayed_orders_leading_to_complaint_phrases"], res["not_delayed_orders_refund_rate"])
print("refund value share", res["refund_value_share_of_order_value"])

# ---------------------------------------------------------------- Power BI export
od_out = od[["order_id", "customer_id", "platform", "category", "delivery_min", "order_value", "feedback", "rating", "delayed", "refund"]].copy()
od_out["delay_over_40"] = od.delivery_min > 40
od_out["delivery_band"] = pd.cut(od.delivery_min, [0, 15, 25, 35, 40, 50, 100], labels=["<=15", "16-25", "26-35", "36-40", "41-50", "51+"]).astype(str)
od_out["feedback_kind"] = od_out.feedback.map(fb.kind)
od_out.to_csv(PBI / "orders_clean.csv", index=False)

# ---------------------------------------------------------------- figures
fig, axs = plt.subplots(1, 2, figsize=(9, 3.3))
pl = pd.DataFrame(res["by_platform"]).T
pl["delay_rate"].astype(float).mul(100).plot(kind="bar", ax=axs[0], color="#2f6f9f", yerr=[(pl.delay_rate - pl.delay_ci.str[0]).astype(float) * 100, (pl.delay_ci.str[1] - pl.delay_rate).astype(float) * 100])
axs[0].set_ylim(0, 20)
axs[0].set_ylabel("% orders over 40 min")
axs[0].set_title("Delay rate (95% interval)")
axs[0].tick_params(axis="x", rotation=0)
pl["refund_rate"].astype(float).mul(100).plot(kind="bar", ax=axs[1], color="#c0392b")
axs[1].set_ylim(0, 60)
axs[1].set_ylabel("% orders with refund")
axs[1].set_title("Refund rate")
axs[1].tick_params(axis="x", rotation=0)
plt.tight_layout()
plt.savefig(OUT / "figures" / "orders_platform_kpis.png")
plt.close()

fig, ax = plt.subplots(figsize=(6.5, 3.4))
for p, c in zip(sorted(od.platform.unique()), ["#f1c40f", "#2f6f9f", "#8e44ad"]):
    ax.plot(sens.threshold_min, sens[p] * 100, marker="o", label=p, color=c)
ax.set_xlabel("delay threshold (minutes)")
ax.set_ylabel("% of orders delayed")
ax.set_title("Threshold sensitivity: platform ranking is noise at every cut")
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig(OUT / "figures" / "orders_threshold_sensitivity.png")
plt.close()
