#!/usr/bin/env python3
"""Upload slices to NotebookLM notebook."""

import subprocess
import time
from pathlib import Path

NOTEBOOK_ID = "48447569-de9b-4a13-ab8f-c30234355136"
SLICE_DIRS = [
    (
        "zilliztech/claude-context",
        "/tmp/gitingest_zilliztech_claude-context/notebooklm",
    ),
    (
        "anthropics/claude-plugins-official",
        "/tmp/gitingest_anthropics_claude-plugins-official/notebooklm",
    ),
    ("farion1231/cc-switch", "/tmp/gitingest_farion1231_cc-switch/notebooklm"),
    (
        "affaan-m/everything-claude-code",
        "/tmp/gitingest_everything-claude-code/notebooklm",
    ),
    (
        "ComposioHQ/awesome-claude-skills",
        "/tmp/gitingest_ComposioHQ_awesome-claude-skills/notebooklm",
    ),
    (
        "sickn33/antigravity-awesome-skills",
        "/tmp/gitingest_sickn33_antigravity-awesome-skills/notebooklm",
    ),
]

RATE_LIMIT_SECONDS = 2


def upload_file(slice_path: str) -> bool:
    """Upload a single file to NotebookLM."""
    result = subprocess.run(
        ["nlm", "source", "add", NOTEBOOK_ID, "--file", slice_path, "--wait"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.returncode == 0


def main():
    total_uploaded = 0
    total_failed = 0

    for repo_name, slice_dir in SLICE_DIRS:
        dir_path = Path(slice_dir)
        if not dir_path.exists():
            print(f"[SKIP] {repo_name}: directory not found")
            continue

        slices = sorted(dir_path.glob("repo-index-part-*.md"))
        if not slices:
            print(f"[SKIP] {repo_name}: no slices found")
            continue

        print(f"Uploading {len(slices)} slices from {repo_name}...")
        repo_uploaded = 0
        repo_failed = 0

        for i, slice_file in enumerate(slices):
            success = upload_file(str(slice_file))
            if success:
                repo_uploaded += 1
                total_uploaded += 1
            else:
                repo_failed += 1
                total_failed += 1
                print(f"  [FAIL] {slice_file.name}")

            # Rate limiting
            if i < len(slices) - 1:
                time.sleep(RATE_LIMIT_SECONDS)

        print(f"  {repo_name}: {repo_uploaded} uploaded, {repo_failed} failed")

    print(f"\nTotal: {total_uploaded} uploaded, {total_failed} failed")


if __name__ == "__main__":
    main()
