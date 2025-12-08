#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "manifests" / "targets.json"

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 30
DELAY_BETWEEN_OPERATIONS = 2

def load_manifest(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)

def docker_login() -> None:
    """Log in to Docker Hub using environment credentials if available."""
    username = os.environ.get("DOCKERHUB_USERNAME")
    token = os.environ.get("DOCKERHUB_TOKEN")
    
    if not username or not token:
        print("Note: DOCKERHUB_USERNAME/DOCKERHUB_TOKEN not set, using existing Docker credentials")
        return
    
    print("Logging in to Docker Hub...")
    result = subprocess.run(
        ["docker", "login", "-u", username, "--password-stdin"],
        input=token.encode(),
        capture_output=True,
    )
    if result.returncode != 0:
        print(f"Warning: Docker login failed: {result.stderr.decode()}")
    else:
        print("Successfully logged in to Docker Hub")


def retag(source: str, target: str, repo: str, dry_run: bool = False) -> None:
    command = [
        "docker",
        "buildx",
        "imagetools",
        "create",
        "--tag",
        f"{repo}:{target}",
        f"{repo}:{source}",
    ]
    if dry_run:
        print("DRY-RUN:", " ".join(command))
        return

    for attempt in range(1, MAX_RETRIES + 1):
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Successfully tagged {repo}:{target}")
            return
        
        # Check for rate limit error
        if "429" in result.stderr or "Too Many Requests" in result.stderr:
            if attempt < MAX_RETRIES:
                wait_time = RETRY_DELAY_SECONDS * attempt
                print(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{MAX_RETRIES}...")
                time.sleep(wait_time)
                continue
        
        # Non-rate-limit error or final attempt
        print(f"Error: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, command)

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Update Docker Hub channel alias tags")
    parser.add_argument("--repo", default="miget/container-os")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    # Log in to Docker Hub for higher rate limits
    if not args.dry_run:
        docker_login()

    manifest = load_manifest(MANIFEST_PATH)

    first_operation = True
    for alias, cfg in manifest.get("channels", {}).items():
        os_name = cfg.get("os")
        version = cfg.get("version")
        engine = cfg.get("engine")

        os_versions = manifest.get("targets", {}).get(os_name, {})
        if not version or version not in os_versions:
            print(f"Skipping alias {alias}: version {version} not found")
            continue

        # Add delay between operations to avoid rate limiting
        if not first_operation and not args.dry_run:
            time.sleep(DELAY_BETWEEN_OPERATIONS)
        first_operation = False

        alias_patch = os_versions[version]["alias_patch"]
        source_tag = f"{manifest['version']}-{os_name}-{alias_patch}-{engine}"
        retag(source_tag, alias, args.repo, dry_run=args.dry_run)

    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
