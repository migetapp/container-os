#!/usr/bin/env python3

import json
import re
from pathlib import Path

def load_manifests():
    base_dir = Path(__file__).parent.parent
    
    with open(base_dir / "manifests/targets.json") as f:
        targets = json.load(f)
    
    with open(base_dir / "manifests/package_versions.json") as f:
        versions = json.load(f)
    
    return targets, versions

def get_version(versions, os_name, os_version, package, engine=None):
    try:
        os_versions = versions[os_name][os_version]
        
        if "common" in os_versions and package in os_versions["common"]:
            return os_versions["common"][package]
        
        if engine and engine in os_versions and package in os_versions[engine]:
            return os_versions[engine][package]
        
        return "-"
    except (KeyError, TypeError):
        return "-"

def generate_table(targets, versions):
    compose_version = targets["docker_compose_version"]
    release_version = targets["version"]
    
    columns = []
    for os_name in ["ubuntu", "alpine"]:
        if os_name not in targets["targets"]:
            continue
        
        for os_version in sorted(targets["targets"][os_name].keys()):
            for engine in ["dockerd", "podman"]:
                os_display = f"{os_name.title()} {os_version}"
                columns.append({
                    "os": os_name,
                    "version": os_version,
                    "engine": engine,
                    "display": f"{os_display}<br/>{engine}"
                })
    
    header = "| Component |"
    separator = "|-----------|"
    for col in columns:
        header += f" {col['display']} |"
        separator += ":----------:|"
    
    def get_docker_version(os, ver, eng):
        if eng != "dockerd":
            return "-"
        pkg = "docker-ce" if os == "ubuntu" else "docker"
        return get_version(versions, os, ver, pkg, eng)
    
    components = [
        ("Docker Compose", lambda os, ver, eng: compose_version),
        ("Docker CE", get_docker_version),
        ("Podman", lambda os, ver, eng: get_version(versions, os, ver, "podman", eng) if eng == "podman" else "-"),
        ("Containerd", lambda os, ver, eng: get_version(versions, os, ver, "containerd.io" if os == "ubuntu" else "containerd", eng) if eng == "dockerd" else "-"),
        ("OpenSSH", lambda os, ver, eng: get_version(versions, os, ver, "openssh-server" if os == "ubuntu" else "openssh", eng)),
        ("Supervisor", lambda os, ver, eng: get_version(versions, os, ver, "supervisor", eng)),
    ]
    
    rows = []
    for component_name, version_func in components:
        row = f"| **{component_name}** |"
        for col in columns:
            version = version_func(col["os"], col["version"], col["engine"])
            # Escape tildes to prevent Markdown strikethrough
            version = version.replace("~", "\\~")
            row += f" {version} |"
        rows.append(row)
    
    table = "\n".join([header, separator] + rows)
    
    return release_version, table

def update_readme(release_version, table):
    base_dir = Path(__file__).parent.parent
    readme_path = base_dir / "README.md"
    
    with open(readme_path, "r") as f:
        content = f.read()
    
    content = re.sub(
        r"## Current Release: [\d.]+",
        f"## Current Release: {release_version}",
        content
    )
    
    pattern = r"(### Component Versions\n\n)(.*?)(\n\n>|\n\n##|\Z)"
    replacement = rf"\1{table}\3"
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(readme_path, "w") as f:
        f.write(content)
    
    print(f"✓ Updated README.md with release {release_version}")
    print(f"✓ Updated component versions table")

def main():
    targets, versions = load_manifests()
    release_version, table = generate_table(targets, versions)
    update_readme(release_version, table)

if __name__ == "__main__":
    main()
