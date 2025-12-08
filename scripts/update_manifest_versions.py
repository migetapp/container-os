#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from packaging.version import Version

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "manifests" / "targets.json"
PACKAGE_VERSIONS_PATH = ROOT / "manifests" / "package_versions.json"

DOCKER_HUB_REPOS = {
    "alpine": "library/alpine",
}

# Packages that require adding Docker's apt repository on Ubuntu
DOCKER_APT_PACKAGES = {
    "docker-ce",
    "docker-ce-cli",
    "containerd.io",
    "docker-buildx-plugin",
    "docker-compose-plugin",
}

DOCKER_APT_SETUP = (
    "apt-get install -y ca-certificates curl gnupg lsb-release >/dev/null 2>&1 && "
    "install -m 0755 -d /etc/apt/keyrings && "
    "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && "
    "chmod a+r /etc/apt/keyrings/docker.gpg && "
    'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] '
    'https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list && '
    "apt-get update >/dev/null 2>&1"
)

VERSION_PATTERN = re.compile(r"^(?:\d+)(?:\.\d+)*$")

@dataclass
class UpdateResult:
    alias_updates: Dict[Tuple[str, str], str]
    package_updates: Dict[Tuple[str, str, str], str]
    manifest_version_bumped: bool

class UpdateError(Exception):
    pass

def load_json(path: Path) -> Dict:
    if not path.exists():
        raise UpdateError(f"Required file missing: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)

def save_json(path: Path, data: Dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def fetch_latest_tag(os_name: str, prefix: str) -> str:
    repo = DOCKER_HUB_REPOS.get(os_name)
    if not repo:
        return prefix

    url = f"https://hub.docker.com/v2/repositories/{repo}/tags"
    params = {"page_size": 100, "name": prefix}
    candidates: List[str] = []

    while url:
        response = requests.get(url, params=params if url.endswith("/tags") else None, timeout=30)
        response.raise_for_status()
        payload = response.json()
        for result in payload.get("results", []):
            tag_name = result.get("name", "")
            if not tag_name.startswith(prefix):
                continue
            if not VERSION_PATTERN.match(tag_name):
                continue
            candidates.append(tag_name)
        url = payload.get("next")
        params = None

    if not candidates:
        return prefix

    try:
        return str(max((Version(tag) for tag in candidates)))
    except Exception as exc:
        raise UpdateError(f"Failed to determine latest tag for {os_name}:{prefix}: {exc}") from exc

def run_container(os_name: str, version: str, command: str) -> str:
    image = f"{os_name}:{version}"
    exec_cmd = ["docker", "run", "--rm", image, "/bin/sh", "-c", command]
    completed = subprocess.run(exec_cmd, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise UpdateError(
            f"Command failed in {image}: {' '.join(exec_cmd)}\nstdout: {completed.stdout}\nstderr: {completed.stderr}"
        )
    return completed.stdout.strip()

def fetch_all_package_versions(os_name: str, version: str, packages: List[str]) -> Dict[str, Optional[str]]:
    """Fetch versions for all packages in a single container run."""
    if not packages:
        return {}

    # Check if any packages need Docker apt repo (Ubuntu only)
    needs_docker_repo = os_name == "ubuntu" and any(p in DOCKER_APT_PACKAGES for p in packages)

    # Build a script that queries all packages and outputs JSON
    if os_name == "ubuntu":
        setup = "apt-get update >/dev/null 2>&1"
        if needs_docker_repo:
            setup += f" && {DOCKER_APT_SETUP}"

        # Build query commands for each package
        queries = []
        for pkg in packages:
            # Output format: PACKAGE_NAME=VERSION
            queries.append(
                f'echo "{pkg}=$(apt-cache policy {pkg} 2>/dev/null | awk \'/Candidate:/{{print $2}}\')"'
            )
        script = f"{setup} && " + " && ".join(queries)

    elif os_name == "alpine":
        setup = "apk update >/dev/null 2>&1"
        queries = []
        for pkg in packages:
            # Output format: PACKAGE_NAME=VERSION (extract version from apk search output)
            queries.append(
                f'echo "{pkg}=$(apk search -e {pkg} 2>/dev/null | sed -n "s/^{pkg}-//p")"'
            )
        script = f"{setup} && " + " && ".join(queries)

    else:
        return {pkg: None for pkg in packages}

    try:
        output = run_container(os_name, version, script)
    except UpdateError as e:
        print(f"Warning: Failed to fetch packages for {os_name}:{version}: {e}", file=sys.stderr)
        return {pkg: None for pkg in packages}

    # Parse output
    results: Dict[str, Optional[str]] = {}
    for line in output.splitlines():
        if "=" in line:
            pkg_name, pkg_version = line.split("=", 1)
            pkg_version = pkg_version.strip()
            # Filter out empty or "(none)" versions
            if pkg_version and pkg_version != "(none)":
                results[pkg_name] = pkg_version
            else:
                results[pkg_name] = None

    # Ensure all requested packages have an entry
    for pkg in packages:
        if pkg not in results:
            results[pkg] = None

    return results

def update_manifest(manifest: Dict, package_versions: Dict) -> UpdateResult:
    alias_updates: Dict[Tuple[str, str], str] = {}
    package_updates: Dict[Tuple[str, str, str], str] = {}

    for os_name, versions in manifest.get("targets", {}).items():
        for version_key, metadata in versions.items():
            latest_tag = fetch_latest_tag(os_name, metadata["base"])
            if metadata.get("alias_patch") != latest_tag:
                metadata["alias_patch"] = latest_tag
                alias_updates[(os_name, version_key)] = latest_tag

            pkg_data = metadata.get("packages", {})
            pkg_versions = package_versions.setdefault(os_name, {}).setdefault(version_key, {})

            # Collect all packages for this OS/version
            all_packages: List[str] = []
            package_to_bucket: Dict[str, str] = {}
            for bucket, packages in pkg_data.items():
                for package in packages:
                    all_packages.append(package)
                    package_to_bucket[package] = bucket

            # Fetch all versions in one container run
            print(f"Fetching package versions for {os_name}:{version_key}...")
            fetched_versions = fetch_all_package_versions(os_name, metadata["base"], all_packages)

            # Update package versions
            for package, version_value in fetched_versions.items():
                if not version_value:
                    continue
                bucket = package_to_bucket[package]
                bucket_versions = pkg_versions.setdefault(bucket, {})
                if bucket_versions.get(package) != version_value:
                    bucket_versions[package] = version_value
                    package_updates[(os_name, version_key, package)] = version_value

    # Update last_updated timestamp if there were any changes
    has_updates = bool(alias_updates or package_updates)
    if has_updates:
        manifest.setdefault("metadata", {})["last_updated"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    # Note: Version bumping is handled separately by bump_version.py in the workflow
    return UpdateResult(alias_updates, package_updates, has_updates)

def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Refresh manifest versions from upstream sources")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    parser.add_argument("--package-versions", default=str(PACKAGE_VERSIONS_PATH))
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    package_versions_path = Path(args.package_versions)

    manifest = load_json(manifest_path)
    package_versions = load_json(package_versions_path)

    try:
        result = update_manifest(manifest, package_versions)
    except UpdateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    save_json(manifest_path, manifest)
    save_json(package_versions_path, package_versions)

    if result.alias_updates:
        print("Updated alias patches:")
        for (os_name, version), tag in sorted(result.alias_updates.items()):
            print(f"  - {os_name} {version} -> {tag}")
    if result.package_updates:
        grouped: Dict[Tuple[str, str], List[Tuple[str, str]]] = defaultdict(list)
        for (os_name, version, package), pkg_version in result.package_updates.items():
            grouped[(os_name, version)].append((package, pkg_version))
        print("Updated package versions:")
        for (os_name, version), entries in sorted(grouped.items()):
            print(f"  - {os_name} {version}:")
            for package, pkg_version in sorted(entries):
                print(f"      {package}: {pkg_version}")
    if result.manifest_version_bumped:
        print("Updates detected - version bump needed")
    else:
        print("No updates detected.")

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
