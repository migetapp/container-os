#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parent.parent
DIGEST_STATE = ROOT / "manifests" / "ubuntu_digests.json"

def load_state() -> Dict[str, str]:
    if DIGEST_STATE.exists():
        return json.loads(DIGEST_STATE.read_text(encoding="utf-8"))
    return {}

def save_state(state: Dict[str, str]) -> None:
    DIGEST_STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

def fetch_digest(tag: str) -> str:
    cmd = [
        "docker",
        "manifest",
        "inspect",
        f"ubuntu:{tag}",
    ]
    output = subprocess.check_output(cmd, text=True)
    data = json.loads(output)
    # Find the amd64 linux manifest digest
    for manifest in data.get("manifests", []):
        platform = manifest.get("platform", {})
        if platform.get("architecture") == "amd64" and platform.get("os") == "linux":
            return manifest["digest"]
    raise RuntimeError(f"Digest not found in manifest output for ubuntu:{tag}")

def main(version: str, record: bool) -> int:
    state = load_state()
    current_digest = fetch_digest(version)
    previous_digest = state.get(version)

    if previous_digest != current_digest:
        print(f"Digest update detected for ubuntu:{version}")
        print(f"Old: {previous_digest}")
        print(f"New: {current_digest}")
        if record:
            state[version] = current_digest
            save_state(state)
        return 1

    print(f"No digest change for ubuntu:{version}")
    return 0

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Ubuntu base image digest updates")
    parser.add_argument("version", help="Ubuntu tag (e.g., 24.04)")
    parser.add_argument("--record", action="store_true", help="Record the current digest")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(main(args.version, args.record))
