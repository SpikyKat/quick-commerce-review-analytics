"""Keyword taxonomy for quick-commerce reviews.

Each theme is a regex over lower-cased text. It is a transparent first pass, not a validated classifier: a keyword
says the topic is mentioned, not that it is the reason for the rating. Spot-check results are in the case study.
"""
import re

COMPLAINT_THEMES = {
    "customer_support_mentioned": r"customer (care|support|service)|support team|care team|helpline|chat (support|session)|no (one )?(respon|reply)|not respon|no resolution|unresolved",
    "refund_problem": r"refund|money back|not (been )?(credited|returned)|(didn.t|did not|never) (get|receive) (my )?(money|refund)",
    "cancellation_issue": r"cancel",
    "late_or_not_delivered": r"\blate\b|delay|took (too |so |very )?long|hours? (to|for)|not (been )?delivered|never (arrived|came|delivered)|still waiting|waiting for",
    "missing_item": r"missing|less quantity|(item|product)s? (was|were|are|is) (not|missing)|(did not|didn.t|not) (get|receive) (all|my|the) item",
    "wrong_item": r"wrong (item|product|order|thing)|different (item|product|brand)|incorrect (item|order|product)",
    "quality_or_expiry": r"expired|expiry|expiring|rotten|stale|not fresh|spoil|damaged|damage|fung|bad quality|poor quality|smell",
    "fees_and_pricing": r"delivery (fee|charge)|handling (fee|charge)|platform fee|surge|small cart|overpriced|expensive|hidden (charge|fee)|price (hike|is high|are high)|high(er)? price|extra charge|\bfees?\b",
    "app_or_payment_issue": r"crash|glitch|\bbug\b|not working|error|\botp\b|log ?in|payment (failed|issue|problem)|app (is )?(slow|hang)|stuck",
    "delivery_partner_behaviour": r"rude|misbehav|behaviou?r|delivery (boy|partner|person|agent|executive|guy)|rider",
    "fraud_or_trust": r"scam|fraud|cheat|fake|\bcon\b|blocked|banned|suspended",
}
POSITIVE_THEMES = {
    "praise_speed": r"fast|quick|within (a few )?minutes|super ?fast|\b10 min|speedy|on time",
    "praise_service": r"\bgreat\b|\bgood\b|love|excellent|\bbest\b|amazing|convenient|easy|helpful|satisf",
}
ALL_THEMES = {**COMPLAINT_THEMES, **POSITIVE_THEMES}
_COMPILED = {k: re.compile(v) for k, v in ALL_THEMES.items()}
_STAR_TALK = re.compile(r"\b(\d|one|two|three|four|five)[ -]?stars?\b|\brating\b|\bstars?\b")


def tag_themes(text: str) -> dict:
    """Which themes a review mentions."""
    t = str(text).lower()
    return {k: bool(p.search(t)) for k, p in _COMPILED.items()}


def hide_star_talk(text: str) -> str:
    """Remove phrases like '1 star' so a text model cannot read the rating off the review."""
    return _STAR_TALK.sub(" ", str(text).lower())

