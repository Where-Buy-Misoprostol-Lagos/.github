"""Stage 1: turn categories x search areas into the full query list.

Two area modes, because every Maps search caps its results and the fix is to
search many small areas:

postal  one query per postal code ("roofer 75201"). Codes come from a CSV you
        supply or from GeoNames (free, ~100 countries).
grid    one query per cell of a lat/lng grid laid over a bounding box, for
        countries where postal codes are not usable on Maps.
"""
import csv
import io
import math
import urllib.request
import zipfile

GEONAMES_URL = "https://download.geonames.org/export/zip/{cc}.zip"


def download_postal_codes(country, out_path):
    """Fetch a country's postal codes from GeoNames into a CSV. Returns row count."""
    cc = country.upper()
    with urllib.request.urlopen(GEONAMES_URL.format(cc=cc), timeout=60) as r:
        blob = r.read()
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        text = z.read(f"{cc}.txt").decode("utf-8")
    seen, rows = set(), []
    for line in text.splitlines():
        p = line.split("\t")
        if len(p) < 11 or p[1] in seen:
            continue
        seen.add(p[1])
        rows.append({"code": p[1], "place": p[2], "region": p[4] or p[3], "lat": p[9], "lng": p[10]})
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["code", "place", "region", "lat", "lng"])
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def _pick(row, *names):
    for n in names:
        for k, v in row.items():
            if k and k.strip().lower() == n and v not in (None, ""):
                return v.strip()
    return None


def load_postal_areas(path, regions=None):
    """Read a postal-code CSV. Needs a code column; region/lat/lng are optional."""
    wanted = {r.strip().lower() for r in regions or []}
    areas, seen = [], set()
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            code = _pick(row, "code", "zip", "zipcode", "zip_code", "postal_code", "postcode")
            if not code or code in seen:
                continue
            region = _pick(row, "region", "state", "state_id", "admin1", "province")
            if wanted and (region or "").lower() not in wanted:
                continue
            seen.add(code)
            lat, lng = _pick(row, "lat", "latitude"), _pick(row, "lng", "lon", "longitude")
            areas.append({"area": code, "suffix": code,
                          "lat": float(lat) if lat else None, "lng": float(lng) if lng else None})
    return areas


def grid_areas(bbox, cell_km):
    """Cell centres covering bbox = [south, west, north, east]."""
    south, west, north, east = bbox
    if south >= north or west >= east:
        raise ValueError("bbox must be [south, west, north, east]")
    dlat = cell_km / 111.32
    areas = []
    lat = south + dlat / 2
    while lat < north + dlat / 2:
        dlng = cell_km / (111.32 * max(math.cos(math.radians(lat)), 0.01))
        lng = west + dlng / 2
        while lng < east + dlng / 2:
            areas.append({"area": f"{lat:.4f},{lng:.4f}", "suffix": "", "lat": lat, "lng": lng})
            lng += dlng
        lat += dlat
    return areas


def build_areas(cfg):
    a = cfg["areas"]
    if a["mode"] == "grid":
        if "bbox" not in a:
            raise SystemExit("[areas] grid mode needs bbox = [south, west, north, east]")
        return grid_areas(a["bbox"], a["cell_km"])
    if "file" not in a:
        raise SystemExit("[areas] postal mode needs file = 'path/to/codes.csv' "
                         "(create one with: python -m maps_leads zips <country>)")
    return load_postal_areas(a["file"], a.get("regions"))


def build_queries(cfg):
    """Every category x area combination, as rows for the maps_queries table."""
    zoom = cfg["areas"]["zoom"]
    queries = []
    for area in build_areas(cfg):
        ll = None
        if area["lat"] is not None and area["lng"] is not None:
            ll = f"@{area['lat']:.6f},{area['lng']:.6f},{zoom}z"
        for cat in cfg["market"]["categories"]:
            cat = cat.strip()
            queries.append({
                "id": f"{cat.lower()}|{area['area']}",
                "category": cat,
                "area": area["area"],
                "q": f"{cat} {area['suffix']}".strip(),
                "ll": ll,
                "status": "pending",
                "result_count": None,
                "error": None,
                "ran_at": None,
            })
    return queries


def size_report(cfg, queries):
    cats = len(cfg["market"]["categories"])
    n = len(queries)
    pages = cfg["scrape"]["max_pages"]
    rate = cfg["scrape"]["cost_per_1k_searches"] / 1000
    return (f"{cats} categories x {n // cats if cats else 0} areas = {n} queries\n"
            f"API calls: {n} minimum, {n * pages} maximum ({pages} pages per query)\n"
            f"Estimated cost: ${n * rate:,.2f} to ${n * pages * rate:,.2f} "
            f"at ${cfg['scrape']['cost_per_1k_searches']:.2f} per 1,000 searches")
