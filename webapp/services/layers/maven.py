# webapp/services/layers/maven.py

import requests

def build_maven_central_url(group_id, artifact_id, version):
    group_path = group_id.replace(".", "/")
    return (
        f"https://repo1.maven.org/maven2/"
        f"{group_path}/"
        f"{artifact_id}/"
        f"{version}/"
        f"{artifact_id}-{version}.jar")


def download_jar(group_id, artifact_id, version):
    url = build_maven_central_url(group_id, artifact_id, version)
    response = requests.get(url, timeout=20)
    if response.status_code != 200:
        return None
    return response.content