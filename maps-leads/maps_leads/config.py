"""Load the TOML campaign config and environment settings."""
import os
import tomllib

DEFAULTS = {
    "market": {"categories": [], "country": "us", "language": "en"},
    "areas": {"mode": "postal", "zoom": 13, "cell_km": 3.0},
    "scrape": {"max_pages": 3, "workers": 8, "cost_per_1k_searches": 1.0},
    "qualify": {
        "require_website": True,
        "min_reviews": 10,
        "min_rating": 0.0,
        "max_rating": 5.0,
        "max_locations": 3,
        "category_keywords": [],
        "exclude_name_keywords": [],
    },
    "enrich": {"workers": 16, "max_pages_per_site": 4, "timeout": 10, "verify": True},
    "score": {
        "tier_a": 60,
        "tier_b": 35,
        "points": {
            "hiring": 10,
            "runs_ads": 6,
            "review_growth": 10,
        },
        "keyword_signals": [],
    },
    "export": {"dir": "exports"},
}


def _merge(base, over):
    out = dict(base)
    for k, v in over.items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def load_config(path):
    with open(path, "rb") as f:
        cfg = _merge(DEFAULTS, tomllib.load(f))
    if not cfg["market"]["categories"]:
        raise SystemExit(f"{path}: [market] categories must list at least one search term")
    if cfg["areas"]["mode"] not in ("postal", "grid"):
        raise SystemExit(f"{path}: [areas] mode must be 'postal' or 'grid'")
    return cfg


def load_env(path=".env"):
    """Minimal .env reader: KEY=VALUE lines, existing environment wins."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))
