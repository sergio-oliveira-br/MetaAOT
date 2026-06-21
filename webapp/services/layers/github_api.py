# webapp/services/layers/github_api.py
import logging

import requests
import os
from dotenv import load_dotenv
from functools import lru_cache

GITHUB_API = (
    "https://api.github.com/repos/"
    "oracle/graalvm-reachability-metadata/"
    "contents/metadata"
)

load_dotenv()
logger = logging.getLogger(__name__)

@lru_cache(maxsize=5000)
def get_available_versions(group_id, artifact_id):
    url = (
        f"{GITHUB_API}/"
        f"{group_id}/{artifact_id}")

    headers = {"User-Agent": "MetaAOT", "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"}
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 404:
        return {"found": False,"versions": []}

    if response.status_code != 200:
        return {"found": False, "versions": []}

    data = response.json()
    versions = []

    for item in data:
        if item.get("type") != "dir":
            continue
        name = item["name"]
        if any(char.isdigit() for char in name):
            versions.append(name)

    return {"found": True,"versions": versions}