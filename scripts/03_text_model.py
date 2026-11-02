"""Step 3: do the words in a review explain a low rating, and does that carry to a platform or month the model has not seen?

Target: low star (1 or 2 stars). Phrases like "1 star" are removed first so the model cannot read the answer off the text.
Two harder tests than random folds: hold out a whole platform, and train on October-November to predict December.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline

from common import OUT, load_reviews, save_json
from qcmod.themes import COMPLAINT_THEMES, POSITIVE_THEMES, hide_star_talk, tag_themes

plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False, "axes.spines.right": False})
rv = load_reviews()
rv["clean"] = rv.text.map(hide_star_talk)
rv["y"] = (rv.rating <= 2).astype(int)
themes = pd.DataFrame([tag_themes(t) for t in rv.text]).astype(int)
theme_cols = list(COMPLAINT_THEMES) + list(POSITIVE_THEMES)
res = {"rows": len(rv), "low_star_rate": float(rv.y.mean())}


def text_model():
    return Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=3, sublinear_tf=True, stop_words="english")),
                     ("lr", LogisticRegression(C=1.0, max_iter=2000, class_weight="balanced"))])


def score(y, p):
    return {"auc": float(roc_auc_score(y, p)), "ap": float(average_precision_score(y, p)), "base_rate": float(np.mean(y)), "n_test": int(len(y))}


def fit_predict(make, Xtr, ytr, Xte):
    return make().fit(Xtr, ytr).predict_proba(Xte)[:, 1]


# ordinary folds, then the two harder splits, for three models
makers = {"majority": lambda: DummyClassifier(strategy="prior"),
          "keyword themes only": lambda: LogisticRegression(max_iter=2000, class_weight="balanced"),
          "text tf-idf": text_model}
res["tests"] = {}
for name, make in makers.items():
    X = themes[theme_cols].values if name == "keyword themes only" else (rv.clean.values if name == "text tf-idf" else np.zeros((len(rv), 1)))
    out = {}
    p = np.zeros(len(rv))
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=0).split(X, rv.y):
        p[te] = fit_predict(make, X[tr], rv.y.values[tr], X[te])
    out["random_folds"] = score(rv.y, p)
    for plat in rv.platform.unique():
        te = (rv.platform == plat).values
        pp = fit_predict(make, X[~te], rv.y.values[~te], X[te])
        out[f"hold_out_{plat}"] = score(rv.y.values[te], pp)
    train = (rv.date < "2024-12-01").values
    test = (rv.date >= "2024-12-01").values
    out["train_before_dec_test_dec"] = score(rv.y.values[test], fit_predict(make, X[train], rv.y.values[train], X[test]))
    res["tests"][name] = out
tab = pd.DataFrame({m: {k: v["auc"] for k, v in d.items()} for m, d in res["tests"].items()})
tab.round(3).to_csv(OUT / "tables" / "text_model_auc.csv")
print(tab.round(3).to_string())

# which words push toward a low or a high rating (fitted on everything)
full = text_model().fit(rv.clean.values, rv.y.values)
vocab = np.array(full.named_steps["tfidf"].get_feature_names_out())
coef = full.named_steps["lr"].coef_[0]
order = np.argsort(coef)
res["top_words_low_star"] = [(str(vocab[i]), float(coef[i])) for i in order[::-1][:25]]
res["top_words_high_star"] = [(str(vocab[i]), float(coef[i])) for i in order[:25]]
print("low:", [w for w, _ in res["top_words_low_star"]])
print("high:", [w for w, _ in res["top_words_high_star"]])

# adjusted association of each theme with a low rating (odds ratios, platform included), bootstrap intervals
design = pd.concat([themes[theme_cols], pd.get_dummies(rv.platform, drop_first=True).astype(int)], axis=1)
rng = np.random.default_rng(0)
ors = []
for _ in range(200):
    idx = rng.integers(0, len(rv), len(rv))
    m = LogisticRegression(C=100, max_iter=2000).fit(design.values[idx], rv.y.values[idx])
    ors.append(np.exp(m.coef_[0]))
ors = np.array(ors)
base = np.exp(LogisticRegression(C=100, max_iter=2000).fit(design.values, rv.y.values).coef_[0])
res["theme_odds_ratios_low_star"] = {c: {"odds_ratio": float(base[i]), "ci": (float(np.percentile(ors[:, i], 2.5)), float(np.percentile(ors[:, i], 97.5)))}
                                     for i, c in enumerate(design.columns)}
res["theme_or_note"] = "Associations with a low rating, adjusted for the other themes and platform. Not causal."
save_json("text_model", res)
for c, v in res["theme_odds_ratios_low_star"].items():
    print(f"{c:30s} OR {v['odds_ratio']:.2f}  ({v['ci'][0]:.2f}-{v['ci'][1]:.2f})")

fig, ax = plt.subplots(figsize=(7, 4))
orr = pd.DataFrame(res["theme_odds_ratios_low_star"]).T
orr = orr.loc[theme_cols].sort_values("odds_ratio")
ax.errorbar(orr.odds_ratio, range(len(orr)), xerr=[orr.odds_ratio - orr.ci.str[0], orr.ci.str[1] - orr.odds_ratio], fmt="o", color="#2f6f9f", ecolor="#999")
ax.axvline(1, color="grey", ls="--")
ax.set_xscale("log")
ax.set_yticks(range(len(orr)))
ax.set_yticklabels([c.replace("_", " ") for c in orr.index], fontsize=8)
ax.set_xlabel("odds ratio for a 1-2 star review (log scale)")
ax.set_title("Which mentions go with a low rating")
plt.tight_layout()
plt.savefig(OUT / "figures" / "theme_odds_ratios.png")
plt.close()
