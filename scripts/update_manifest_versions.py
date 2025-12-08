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

OS_PACKAGE_COMMANDS = {
    "ubuntu": (
        ["apt-get", "update"],
        "apt-cache policy {package} | awk '/Candidate/ {{print $2}}'",
    ),
    "alpine": (
        ["apk", "update"],
        "apk search -e {package}",
    ),
}

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

def extract_package_version(os_name: str, raw_output: str, package: str) -> Optional[str]:
    if os_name == "ubuntu":
        for line in raw_output.splitlines():
            if line.startswith("Candidate: "):
                version = line.split("Candidate: ", 1)[1].strip()
                return version or None
        if raw_output:
            return raw_output.splitlines()[-1].strip() or None
        return None
    if os_name == "alpine":
        for line in raw_output.splitlines():
            if line.startswith(f"{package}-"):
                return line.split(f"{package}-", 1)[1].strip() or None
        if raw_output:
            parts = raw_output.split("-", 1)
            if len(parts) == 2:
                return parts[1].strip() or None
        return None
    return None

def fetch_package_version(os_name: str, version: str, package: str) -> Optional[str]:
    pre_cmd, query_template = OS_PACKAGE_COMMANDS[os_name]
    pre_command = " ".join(pre_cmd)
    query_command = query_template.format(package=package)
    full_command = f"{pre_command} >/dev/null 2>&1 && {query_command}"
    output = run_container(os_name, version, full_command)
    return extract_package_version(os_name, output, package)

def bump_patch_version(current: str) -> str:
    major, minor, patch = current.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"

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

            for bucket, packages in pkg_data.items():
                bucket_versions = pkg_versions.setdefault(bucket, {})
                for package in packages:
                    version_value = fetch_package_version(os_name, metadata["base"], package)
                    if not version_value:
                        continue
                    if bucket_versions.get(package) != version_value:
                        bucket_versions[package] = version_value
                        package_updates[(os_name, version_key, package)] = version_value

    manifest_version_bumped = False
    if alias_updates or package_updates:
        manifest_version_bumped = True
        manifest["version"] = bump_patch_version(manifest["version"])
        manifest.setdefault("metadata", {})["last_updated"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    return UpdateResult(alias_updates, package_updates, manifest_version_bumped)

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
        print(f"Manifest version bumped to {manifest['version']}")
    else:
        print("No updates detected.")

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
