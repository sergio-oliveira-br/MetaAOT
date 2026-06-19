# webapp/services/sbom/codebuild_runner.py

import time
import boto3

s3 = boto3.client("s3")
codebuild = boto3.client("codebuild")
PROJECT_NAME = "sbom-generator"

def start_sbom_build(owner, repo, bucket, key):
    response = codebuild.start_build(
        projectName=PROJECT_NAME,
        environmentVariablesOverride=[
            {
                "name": "OWNER",
                "value": owner,
                "type": "PLAINTEXT"
            },
            {
                "name": "REPO",
                "value": repo,
                "type": "PLAINTEXT"
            },
            {
                "name": "S3_BUCKET",
                "value": bucket,
                "type": "PLAINTEXT"
            },
            {
                "name": "S3_KEY",
                "value": key,
                "type": "PLAINTEXT"
            }
        ]
    )
    return response["build"]["id"]


def wait_for_build(build_id):
    while True:
        response = codebuild.batch_get_builds(
            ids=[build_id]
        )
        build = response["builds"][0]
        status = build["buildStatus"]

        if status == "SUCCEEDED":
            return True

        if status in ["FAILED", "FAULT", "STOPPED", "TIMED_OUT"]:
            raise Exception(f"CodeBuild failed: {status}")

        time.sleep(5)


def download_sbom(bucket, key):
    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )
    return response["Body"].read().decode("utf-8")


def generate_sbom(owner, repo):
    bucket = "sbom-analysis-storage"
    key = f"sboms/{owner}-{repo}-{int(time.time())}.json"
    build_id = start_sbom_build(
        owner,
        repo,
        bucket,
        key
    )
    wait_for_build(build_id)
    return download_sbom(
        bucket,
        key)
