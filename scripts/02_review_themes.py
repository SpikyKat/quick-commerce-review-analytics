"""Step 2: what do reviewers complain about, and do the platforms really differ?

The audit showed the three platforms were collected in different months (Zepto and Blinkit are mostly Oct-Dec 2024,
JioMart starts in July), so platform comparisons are made in the Oct-Dec 2024 window where all three are present, and
then repeated month by month. A difference that disappears inside a month is a sampling artefact, not a platform effect.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import INTERIM, OUT, PBI, load_reviews, save_json
from qcmod.stats import bootstrap_diff, chi2_groups, holm, wilson
from qcmod.themes import ALL_THEMES, COMPLAINT_THEMES, tag_themes

plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False, "axes.spines.right": False})
rv = load_reviews()
flags = pd.DataFrame([tag_themes(t) for t in rv.text])
rv = pd.concat([rv, flags], axis=1)
rv["low_star"] = rv.rating <= 2
rv["any_complaint_theme"] = rv[list(COMPLAINT_THEMES)].any(axis=1)
rv["review_id"] = np.arange(1, len(rv) + 1)
win = rv[(rv.date >= "2024-10-01") & (rv.date <= "2024-12-31")].copy()
res = {"window": "2024-10-01 to 2024-12-31", "window_rows": len(win), "window_platform_counts": win.platform.value_counts().to_dict()}

# ---------------------------------------------------------------- how often is each theme mentioned
rows = []
for th in ALL_THEMES:
    k_all, k_low = int(rv[th].sum()), int(rv[rv.low_star][th].sum())
    rows.append({"theme": th, "kind": "complaint" if th in COMPLAINT_THEMES else "praise",
                 "all_reviews": k_all, "share_all": k_all / len(rv), "ci_all": wilson(k_all, len(rv)),
                 "share_low_star": k_low / int(rv.low_star.sum()), "ci_low": wilson(k_low, int(rv.low_star.sum())),
                 "mean_rating_when_mentioned": float(rv[rv[th]].rating.mean()), "mean_rating_when_not": float(rv[~rv[th]].rating.mean()),
                 "low_star_rate_when_mentioned": float(rv[rv[th]].low_star.mean()), "low_star_rate_when_not": float(rv[~rv[th]].low_star.mean())})
prev = pd.DataFrame(rows).sort_values("share_low_star", ascending=False)
prev.to_csv(OUT / "tables" / "theme_prevalence.csv", index=False)
res["theme_prevalence"] = prev.to_dict("records")
res["low_star_reviews"] = int(rv.low_star.sum())
res["low_star_with_no_complaint_theme"] = float((~rv[rv.low_star].any_complaint_theme).mean())
print(prev[["theme", "all_reviews", "share_low_star", "mean_rating_when_mentioned", "mean_rating_when_not"]].round(3).to_string(index=False))

# ---------------------------------------------------------------- platform comparison inside the common window
cmp_rows, pvals = [], {}
for th in list(COMPLAINT_THEMES) + ["any_complaint_theme"]:
    g = win.groupby("platform")[th].agg(["sum", "count"])
    t = chi2_groups(g["sum"].values, g["count"].values)
    pvals[th] = t["p"]
    cmp_rows.append({"theme": th, **{f"{p}": g.loc[p, "sum"] / g.loc[p, "count"] for p in g.index}, "chi2_p": t["p"], "cramers_v": t["cramers_v"]})
adj = holm(pvals)
cmp = pd.DataFrame(cmp_rows)
cmp["holm_p"] = cmp.theme.map(adj)
cmp.to_csv(OUT / "tables" / "theme_by_platform_window.csv", index=False)
res["theme_by_platform_window"] = cmp.to_dict("records")
print(cmp.round(3).to_string(index=False))

# star ratings in the window
g = win.groupby("platform").agg(n=("rating", "size"), mean=("rating", "mean"), one_star=("rating", lambda s: (s == 1).sum()))
res["window_rating"] = {p: {"n": int(r.n), "mean": float(r["mean"]), "one_star_share": r.one_star / r.n, "one_star_ci": wilson(int(r.one_star), int(r.n))} for p, r in g.iterrows()}
res["window_one_star_chi2"] = chi2_groups(g.one_star.values, g.n.values)
pairs = {}
for a, b in (("Blinkit", "JioMart"), ("Blinkit", "Zepto"), ("JioMart", "Zepto")):
    d, lo, hi = bootstrap_diff(win[win.platform == a].rating, win[win.platform == b].rating)
    pairs[f"{a} - {b}"] = {"mean_diff": d, "ci": (lo, hi)}
res["window_rating_pair_diffs"] = pairs
print(g, pairs)

# the same comparison inside each month
mon = win.assign(month=win.date.dt.to_period("M").astype(str)).groupby(["month", "platform"]).rating.agg(["mean", "count"]).round(3)
res["window_rating_by_month_platform"] = {f"{m}|{p}": {"mean": float(r["mean"]), "n": int(r["count"])} for (m, p), r in mon.iterrows()}
print(mon.unstack())

# ---------------------------------------------------------------- does truncation bias themes?
rv["truncated"] = rv.chars >= 480
res["truncated_share"] = float(rv.truncated.mean())
res["theme_share_truncated_vs_not"] = {th: [float(rv[rv.truncated][th].mean()), float(rv[~rv.truncated][th].mean())] for th in COMPLAINT_THEMES}

# ---------------------------------------------------------------- co-occurrence among low-star reviews
low = rv[rv.low_star]
co = pd.DataFrame({a: {b: float((low[a] & low[b]).sum() / max(low[a].sum(), 1)) for b in COMPLAINT_THEMES} for a in COMPLAINT_THEMES})
co.round(2).to_csv(OUT / "tables" / "theme_cooccurrence_low_star.csv")
res["post_order_service_themes_in_low_star"] = float(low[["customer_support_mentioned", "refund_problem", "cancellation_issue"]].any(axis=1).mean())
res["delivery_experience_themes_in_low_star"] = float(low[["late_or_not_delivered", "missing_item", "wrong_item", "quality_or_expiry", "delivery_partner_behaviour"]].any(axis=1).mean())
res["fees_pricing_in_low_star"] = float(low.fees_and_pricing.mean())

# ---------------------------------------------------------------- spot-check sample for a human read
with open(INTERIM / "theme_spotcheck.txt", "w", encoding="utf-8") as f:
    for th in COMPLAINT_THEMES:
        f.write(f"\n##### {th}\n")
        for t in rv[rv[th]].sample(8, random_state=4).text:
            f.write(f"- {t[:230]}\n")
save_json("review_themes", res)

# ---------------------------------------------------------------- Power BI export (no review text)
keep = ["review_id", "date", "platform", "rating", "low_star", "chars", "truncated", *ALL_THEMES, "any_complaint_theme"]
rv["in_common_window"] = rv.index.isin(win.index)
rv[keep + ["in_common_window"]].to_csv(PBI / "reviews_tagged.csv", index=False)

# ---------------------------------------------------------------- figures
order = prev[prev.kind == "complaint"].sort_values("share_low_star")
fig, ax = plt.subplots(figsize=(7, 3.8))
ax.barh(order.theme.str.replace("_", " "), order.share_low_star * 100, color="#c0392b",
        xerr=[(order.share_low_star - order.ci_low.str[0]) * 100, (order.ci_low.str[1] - order.share_low_star) * 100],
        error_kw={"ecolor": "#555", "lw": 0.8})
ax.set_xlabel("% of 1-2 star reviews that mention it (95% interval)")
ax.set_title("What unhappy reviewers write about")
plt.tight_layout()
plt.savefig(OUT / "figures" / "themes_low_star.png")
plt.close()

fig, ax = plt.subplots(figsize=(7.5, 3.6))
sub = cmp[cmp.theme != "any_complaint_theme"].set_index("theme")[["Blinkit", "JioMart", "Zepto"]] * 100
sub = sub.loc[order.theme]
sub.plot(kind="barh", ax=ax, color=["#f1c40f", "#2f6f9f", "#8e44ad"], width=0.8)
ax.set_xlabel("% of reviews (Oct-Dec 2024)")
ax.set_ylabel("")
ax.set_title("Theme mentions by platform, common window")
ax.legend(frameon=False, fontsize=7)
plt.tight_layout()
plt.savefig(OUT / "figures" / "themes_by_platform.png")
plt.close()

fig, ax = plt.subplots(figsize=(6.5, 3.3))
m = win.assign(month=win.date.dt.to_period("M").astype(str)).groupby(["month", "platform"]).rating.mean().unstack()
m.plot(marker="o", ax=ax, color=["#f1c40f", "#2f6f9f", "#8e44ad"])
ax.set_ylabel("mean stars")
ax.set_xlabel("")
ax.set_title("Mean rating by month: is the platform gap stable?")
ax.legend(frameon=False)
plt.tight_layout()
plt.savefig(OUT / "figures" / "rating_by_month_platform.png")
plt.close()

