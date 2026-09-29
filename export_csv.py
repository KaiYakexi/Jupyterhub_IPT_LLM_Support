"""
Exports MongoDB collections to CSV with EVERY field that appears anywhere
in the data -- not a fixed/curated column list. Handles documents with
different shapes (e.g. "noSupport" rows vs "adaptiveSupport" rows in
loggedData_data) by taking the UNION of all keys across all documents as
the CSV header, leaving a cell blank wherever a given document doesn't
have that field. Nested/list values (rare, but e.g. a traceback list) are
JSON-stringified so they survive as a single CSV cell.

Run from your project folder (the one with docker-compose.yml) like this,
piping this script's own source into the jupyterhub container over stdin
-- no need to copy it into the image or rebuild anything:

    docker compose exec -T jupyterhub python3 - < export_csv.py

That writes the CSVs to /srv/jupyterhub/data/ inside the container (the
jupyterhub_data volume). Pull them onto your machine with:

    docker compose cp jupyterhub:/srv/jupyterhub/data/loggedData_data_export.csv ./loggedData_data_export.csv
    docker compose cp jupyterhub:/srv/jupyterhub/data/afmAttempts_export.csv ./afmAttempts_export.csv

(docker compose cp needs a fairly recent Compose version; if it's not
available, `docker cp jupyterhub-ipt-container:/srv/jupyterhub/data/<file> .`
does the same thing using the container name directly.)
"""

import csv
import json
import os

from bson import ObjectId
from pymongo import MongoClient


def read_secret(name, env_fallback=None):
    """Same convention as logService.py/fit_afm.py: docker secret file, else env var."""
    secret_path = f"/run/secrets/{name}"
    if os.path.isfile(secret_path):
        with open(secret_path) as f:
            return f.read().strip()
    if env_fallback:
        val = os.environ.get(env_fallback)
        if val:
            return val
    raise RuntimeError(f"Secret {name} not found at {secret_path} or env {env_fallback}")


def get_db():
    client = MongoClient(
        host="mongodb",
        port=27017,
        username=read_secret("mongo_username", "MONGO_INITDB_ROOT_USERNAME"),
        password=read_secret("mongo_password", "MONGO_INITDB_ROOT_PASSWORD"),
        authSource="admin",
    )
    return client["loggedData"]


def flatten_value(v):
    if isinstance(v, ObjectId):
        return str(v)
    if isinstance(v, (dict, list)):
        return json.dumps(v, default=str)
    return v


def export_collection(db, collection_name, out_path):
    docs = list(db[collection_name].find({}))

    rows = []
    fieldnames = set()
    for d in docs:
        row = {k: flatten_value(v) for k, v in d.items()}
        fieldnames.update(row.keys())
        rows.append(row)

    fieldnames = sorted(fieldnames)

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"{collection_name}: wrote {len(rows)} rows, {len(fieldnames)} columns -> {out_path}")


def main():
    db = get_db()
    os.makedirs("/srv/jupyterhub/data", exist_ok=True)
    export_collection(db, "loggedData_data", "/srv/jupyterhub/data/loggedData_data_export.csv")
    export_collection(db, "afmAttempts", "/srv/jupyterhub/data/afmAttempts_export.csv")


if __name__ == "__main__":
    main()
