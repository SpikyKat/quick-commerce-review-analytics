"""Paths, loaders and a JSON helper shared by the scripts."""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
RAW, OUT, INTERIM, PBI = ROOT / "data" / "raw", ROOT / "outputs", ROOT / "data" / "interim", ROOT / "data" / "powerbi"
for p in (OUT / "results", OUT / "tables", OUT / "figures", INTERIM, PBI):
    p.mkdir(parents=True, exist_ok=True)

BRAND = {"blinkit": "Blinkit", "jiomart": "JioMart", "zepto": "Zepto", "swiggy instamart": "Swiggy Instamart"}


def load_reviews() -> pd.DataFrame:
    """App-store style reviews: whitespace collapsed, dates parsed, platform names standardised."""
    df = pd.read_csv(RAW / "reviews.csv")
    df["text"] = df.review.map(lambda s: re.sub(r"\s+", " ", str(s)).strip())
    df["date"] = pd.to_datetime(df["date"], format="%d %B %Y")
    df["platform"] = df.platform.str.strip().str.lower().map(BRAND)
    df["chars"] = df.text.str.len()
    return df.drop(columns="review")


def load_orders() -> pd.DataFrame:
    df = pd.read_csv(RAW / "Ecommerce_Delivery_Analytics_New.csv")
    df.columns = ["order_id", "customer_id", "platform", "order_time_raw", "delivery_min", "category", "order_value",
                  "feedback", "rating", "delay_flag", "refund_flag"]
    df["delayed"] = df.delay_flag.eq("Yes")
    df["refund"] = df.refund_flag.eq("Yes")
    return df


def load_agents() -> pd.DataFrame:
    df = pd.read_csv(RAW / "Fast Delivery Agent Reviews.csv")
    df.columns = ["platform", "rating", "review_text", "delivery_min", "city", "order_type", "feedback_type", "price_range",
                  "discount", "availability", "service_rating", "accuracy"]
    return df


def to_py(o):
    if isinstance(o, dict):
        return {str(k): to_py(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [to_py(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (pd.Timestamp,)):
        return o.isoformat()
    if isinstance(o, pd.Period):
        return str(o)
    return o


def save_json(name: str, obj) -> None:
    (OUT / "results" / f"{name}.json").write_text(json.dumps(to_py(obj), indent=1), encoding="utf-8")


def load_json(name: str) -> dict:
    return json.loads((OUT / "results" / f"{name}.json").read_text(encoding="utf-8"))
