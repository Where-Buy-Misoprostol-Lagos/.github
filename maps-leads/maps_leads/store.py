"""Storage: Supabase (PostgREST) in production, SQLite for local dev and tests.

Both backends expose the same two operations, upsert and select, and every row
is written with the table's full column set so partial writes never clobber
or fail on missing columns.
"""
import json
import os
import sqlite3
import urllib.error
import urllib.parse
import urllib.request

# table -> (primary key, columns, json columns). Mirrors supabase/migrations.
TABLES = {
    "maps_queries": ("id", [
        "id", "category", "area", "q", "ll", "status", "result_count", "error", "ran_at",
    ], []),
    "maps_businesses": ("place_id", [
        "place_id", "name", "clean_name", "address", "phone", "phone_norm", "website", "domain",
        "rating", "review_count", "prev_review_count", "category", "categories", "maps_url",
        "lat", "lng", "found_by", "first_seen", "last_seen", "duplicate_of", "location_count",
        "status", "reject_reason", "enriched_at", "site_status", "signals", "socials",
        "fit_score", "intent_score", "score", "tier",
    ], ["categories", "found_by", "signals", "socials"]),
    "maps_contacts": ("email", [
        "email", "place_id", "kind", "source_url", "verify", "also_on", "found_at",
    ], ["also_on"]),
}


def _full(table, row):
    return {c: row.get(c) for c in TABLES[table][1]}


def _chunks(items, n):
    for i in range(0, len(items), n):
        yield items[i:i + n]


class SQLiteStore:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        for table, (pk, cols, _) in TABLES.items():
            defs = ", ".join(f"{c} PRIMARY KEY" if c == pk else c for c in cols)
            self.db.execute(f"CREATE TABLE IF NOT EXISTS {table} ({defs})")
        self.db.commit()

    def upsert(self, table, rows):
        if not rows:
            return
        _, cols, jcols = TABLES[table]
        sql = (f"INSERT OR REPLACE INTO {table} ({', '.join(cols)}) "
               f"VALUES ({', '.join('?' for _ in cols)})")
        data = []
        for row in rows:
            row = _full(table, row)
            data.append([json.dumps(row[c]) if c in jcols and row[c] is not None else row[c]
                         for c in cols])
        self.db.executemany(sql, data)
        self.db.commit()

    def select(self, table, where=None, in_=None):
        pk, _, jcols = TABLES[table]
        out = []
        for values in (_chunks(list(in_[1]), 500) if in_ else [None]):
            conds, params = [], []
            for k, v in (where or {}).items():
                conds.append(f"{k} = ?")
                params.append(v)
            if values is not None:
                conds.append(f"{in_[0]} IN ({', '.join('?' for _ in values)})")
                params += values
            sql = f"SELECT * FROM {table}"
            if conds:
                sql += " WHERE " + " AND ".join(conds)
            for r in self.db.execute(sql + f" ORDER BY {pk}", params):
                row = dict(r)
                for c in jcols:
                    if row[c] is not None:
                        row[c] = json.loads(row[c])
                out.append(row)
        return out


class SupabaseStore:
    PAGE = 1000

    def __init__(self, url, key):
        self.base = url.rstrip("/") + "/rest/v1/"
        self.headers = {"apikey": key, "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json"}

    def _request(self, method, path, body=None, prefer=None):
        headers = dict(self.headers)
        if prefer:
            headers["Prefer"] = prefer
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read()
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Supabase {method} {path.split('?')[0]} failed: "
                               f"{e.code} {e.read().decode(errors='replace')[:300]}") from None
        return json.loads(raw) if raw else None

    def upsert(self, table, rows):
        pk = TABLES[table][0]
        for batch in _chunks([_full(table, r) for r in rows], 500):
            self._request("POST", f"{table}?on_conflict={pk}", batch,
                          prefer="resolution=merge-duplicates,return=minimal")

    def select(self, table, where=None, in_=None):
        pk = TABLES[table][0]
        out = []
        for values in (_chunks(list(in_[1]), 100) if in_ else [None]):
            params = [("select", "*"), ("order", pk)]
            for k, v in (where or {}).items():
                params.append((k, f"eq.{v}"))
            if values is not None:
                quoted = ",".join('"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'
                                  for v in values)
                params.append((in_[0], f"in.({quoted})"))
            offset = 0
            while True:
                page = self._request("GET", f"{table}?" + urllib.parse.urlencode(
                    params + [("limit", self.PAGE), ("offset", offset)]))
                out += page
                if len(page) < self.PAGE:
                    break
                offset += self.PAGE
        return out


def open_store():
    url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_KEY")
    if url and key:
        return SupabaseStore(url, key)
    if url or key:
        raise SystemExit("Set both SUPABASE_URL and SUPABASE_SERVICE_KEY, or neither.")
    return SQLiteStore(os.environ.get("MAPS_LEADS_DB", "maps_leads.db"))
