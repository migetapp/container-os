#!/usr/bin/env python3
"""
Detect significant changes in package versions by comparing working tree against HEAD.
Returns exit code 0 if changes detected (should bump version), 1 otherwise.
"""

import json
import subprocess
import sys
from pathlib import Path

def load_json(filepath):
    with open(filepath) as f:
        return json.load(f)

def load_json_from_git(filepath):
    """Load JSON file content from the last committed version (HEAD)."""
    try:
        result = subprocess.run(
            ["git", "show", f"HEAD:{filepath}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None

def get_significant_packages():
    return [
        "docker-ce",
        "docker",
        "podman",
        "containerd.io",
        "containerd",
        "docker-compose-plugin",
        "docker-cli-compose",
    ]

def check_for_changes():
    base_dir = Path(__file__).parent.parent
    
    # Load current (working tree) versions
    versions_file = base_dir / "manifests/package_versions.json"
    current_versions = load_json(versions_file)
    
    targets_file = base_dir / "manifests/targets.json"
    current_targets = load_json(targets_file)
    
    # Load previous (HEAD) versions for comparison
    prev_versions = load_json_from_git("manifests/package_versions.json")
    prev_targets = load_json_from_git("manifests/targets.json")
    
    significant_packages = get_significant_packages()
    changes = []
    
    # Check docker-compose version change
    current_compose = current_targets.get("docker_compose_version", "")
    prev_compose = prev_targets.get("docker_compose_version", "") if prev_targets else ""
    if current_compose and current_compose != prev_compose:
        changes.append({
            "type": "docker-compose",
            "old_version": prev_compose,
            "new_version": current_compose
        })
    
    # Check alias_patch changes (base OS version updates like alpine 3.19.8 -> 3.19.9)
    for os_name, os_versions in current_targets.get("targets", {}).items():
        for version_key, metadata in os_versions.items():
            current_patch = metadata.get("alias_patch", "")
            prev_patch = ""
            if prev_targets:
                prev_patch = (
                    prev_targets
                    .get("targets", {})
                    .get(os_name, {})
                    .get(version_key, {})
                    .get("alias_patch", "")
                )
            if current_patch and current_patch != prev_patch:
                changes.append({
                    "type": "alias_patch",
                    "os": os_name,
                    "os_version": version_key,
                    "old_version": prev_patch,
                    "new_version": current_patch
                })
    
    # Check package version changes
    for os_name, os_versions in current_versions.items():
        if os_name == "docker_compose_version":
            continue
            
        for os_version, sections in os_versions.items():
            for section, packages in sections.items():
                if not isinstance(packages, dict):
                    continue
                    
                for package, version in packages.items():
                    if package in significant_packages:
                        # Get previous version for comparison
                        prev_version = None
                        if prev_versions:
                            prev_version = (
                                prev_versions
                                .get(os_name, {})
                                .get(os_version, {})
                                .get(section, {})
                                .get(package)
                            )
                        
                        # Only report if version actually changed
                        if version != prev_version:
                            changes.append({
                                "type": "package",
                                "os": os_name,
                                "os_version": os_version,
                                "section": section,
                                "package": package,
                                "old_version": prev_version,
                                "new_version": version
                            })
    
    return changes

def main():
    changes = check_for_changes()
    
    if changes:
        print("Significant changes detected:")
        for change in changes:
            if change["type"] == "docker-compose":
                print(f"  - Docker Compose: {change['old_version']} → {change['new_version']}")
            elif change["type"] == "alias_patch":
                old = change['old_version'] or '(new)'
                print(f"  - {change['os']} {change['os_version']} base: {old} → {change['new_version']}")
            else:
                old = change['old_version'] or '(new)'
                print(f"  - {change['os']} {change['os_version']} ({change['section']}): {change['package']} {old} → {change['new_version']}")
        print("has_changes=true")
    else:
        print("No significant changes detected")
        print("has_changes=false")

if __name__ == "__main__":
    main()
