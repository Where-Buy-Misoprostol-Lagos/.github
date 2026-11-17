"""Score Google Business Profile listings (DataForSEO business listings JSON) out of 100.

Usage: python3 score.py OUT.csv RAW1.json [RAW2.json ...]
"""
import csv
import json
import sys

MAX = {"claimed": 15, "website": 15, "phone": 5, "description": 10,
       "hours": 10, "photos": 15, "review_count": 20, "rating": 10}


def load(path):
    data = json.loads(open(path, encoding="utf-8").read())
    if isinstance(data, list):  # MCP wrapper: [{"type": "text", "text": "<json>"}]
        data = json.loads(data[0]["text"])
    return data.get("items") or []


def band(value, steps):
    """steps: [(threshold, points), ...] highest threshold first."""
    for threshold, points in steps:
        if value >= threshold:
            return points
    return 0


def score(item):
    rating = item.get("rating") or {}
    votes = rating.get("votes_count") or 0
    stars = rating.get("value") or 0
    photos = item.get("total_photos") or 0
    timetable = ((item.get("work_time") or {}).get("work_hours") or {}).get("timetable")
    parts = {
        "claimed": 15 if item.get("is_claimed") else 0,
        "website": 15 if (item.get("url") or item.get("domain")) else 0,
        "phone": 5 if item.get("phone") else 0,
        "description": 10 if (item.get("description") or "").strip() else 0,
        "hours": 10 if timetable else 0,
        "photos": band(photos, [(10, 15), (3, 9), (1, 4)]),
        "review_count": band(votes, [(50, 20), (20, 15), (5, 10), (1, 5)]),
        "rating": band(stars, [(4.5, 10), (4.0, 7), (3.5, 4)]) if votes else 0,
    }
    return parts, votes, stars, photos


def main(out, paths):
    seen, rows = set(), []
    for path in paths:
        for item in load(path):
            cid = item.get("cid")
            if cid in seen:
                continue
            seen.add(cid)
            parts, votes, stars, photos = score(item)
            info = item.get("address_info") or {}
            rows.append({
                "name": item.get("title"),
                "area": info.get("borough") or info.get("city") or "",
                "address": item.get("address") or "",
                "phone": item.get("phone") or "",
                "website": item.get("url") or item.get("domain") or "",
                "claimed": "yes" if item.get("is_claimed") else "not shown",
                "rating": stars or "",
                "reviews": votes,
                "photos": photos,
                **{f"pts_{k}": v for k, v in parts.items()},
                "score": sum(parts.values()),
                "top_fixes": "; ".join(
                    k for k, _ in sorted(
                        ((k, MAX[k] - v) for k, v in parts.items() if MAX[k] - v > 0),
                        key=lambda kv: -kv[1])[:3]),
                "maps_url": item.get("check_url") or "",
            })
    rows.sort(key=lambda r: (-r["score"], -r["reviews"]))
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    fields = ["rank"] + [k for k in rows[0] if k != "rank"]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} listings -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
