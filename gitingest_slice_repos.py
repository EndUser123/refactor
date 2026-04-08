#!/usr/bin/env python3
"""Generate NotebookLM slices from cloned git repos."""

import os
import sys
from pathlib import Path

MAX_LINES_PER_SLICE = 150


def get_file_summary(repo_path: Path, file_path: str) -> str:
    """Get a 1-3 sentence summary of a file."""
    full_path = repo_path / file_path
    if not full_path.exists():
        return f"[File not found: {file_path}]"

    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        return f"[Error reading {file_path}: {e}]"

    lines = content.split("\n")
    ext = file_path.split(".")[-1].lower() if "." in file_path else ""

    if ext == "md":
        heading_lines = [l for l in lines if l.strip().startswith("#")][:5]
        if heading_lines:
            headings = " | ".join([h.strip() for h in heading_lines])
            size_kb = len(content) / 1024
            return f"[MD] {headings} ({size_kb:.0f}KB, {len(lines)} lines)"
        size_kb = len(content) / 1024
        return f"[MD] {size_kb:.0f}KB, {len(lines)} lines"

    if ext in ("py", "ts", "js", "tsx", "jsx"):
        func_lines = [
            l.strip()
            for l in lines
            if l.strip().startswith(
                ("def ", "class ", "function ", "const ", "export ")
            )
        ][:5]
        if func_lines:
            return f"[{ext.upper()}] {' | '.join(func_lines[:3])}"
        size_kb = len(content) / 1024
        return f"[{ext.upper()}] {size_kb:.0f}KB, {len(lines)} lines"

    if ext in ("json", "yaml", "yml", "toml", "cfg", "ini", "conf"):
        size_kb = len(content) / 1024
        return f"[CFG] {ext.upper()} config ({size_kb:.0f}KB)"

    size_kb = len(content) / 1024
    return f"[{ext.upper()}] {size_kb:.0f}KB, {len(lines)} lines"


def is_entry_point(file_path: str) -> bool:
    """Check if file is an entry point that should be inlined."""
    basename = os.path.basename(file_path).lower()
    name_without_ext = basename.rsplit(".", 1)[0] if "." in basename else basename
    entry_points = {
        "readme",
        "index",
        "main",
        "app",
        "cli",
        "server",
        "__main__",
        "__init__",
        "setup",
        "install",
        "package",
        "config",
        "conf",
        "settings",
    }
    if name_without_ext in entry_points:
        return True
    if "/" not in file_path and not file_path.startswith("."):
        if any(
            file_path.endswith(ext) for ext in [".md", ".py", ".ts", ".js", ".json"]
        ):
            return True
    return False


def should_inline_full(file_path: str) -> bool:
    """Check if file should be fully inlined."""
    if file_path.lower().startswith("readme"):
        return True
    if "/docs/" in file_path or file_path.startswith("docs/"):
        return True
    if "/doc/" in file_path or file_path.startswith("doc/"):
        return True
    if is_entry_point(file_path):
        return True
    if file_path.endswith(".md") and "/" not in file_path:
        return True
    if any(file_path.startswith(p) for p in ["CLAUDE", "AGENTS"]):
        return True
    return False


def generate_slices(
    repo_path: Path, file_list_path: Path, output_dir: Path, repo_name: str
) -> list:
    """Generate slices for a repo. Returns list of slice file paths."""
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(file_list_path, "r") as f:
        files = [line.strip() for line in f if line.strip()]

    md_files = [f for f in files if f.endswith(".md")]
    code_files = [
        f
        for f in files
        if any(f.endswith(ext) for ext in [".py", ".ts", ".js", ".tsx", ".jsx"])
    ]
    config_files = [
        f
        for f in files
        if any(
            f.endswith(ext)
            for ext in [".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".conf"]
        )
    ]
    other_files = [f for f in files if f not in md_files + code_files + config_files]

    slices = []
    current_lines = []
    part_num = 1

    def flush_slice(lines, title, category):
        nonlocal current_lines, part_num
        if not lines:
            return
        slice_path = output_dir / f"repo-index-part-{part_num}.md"
        with open(slice_path, "w", encoding="utf-8") as f:
            f.write(f"# {repo_name} - {title}\n\n")
            f.write(f"**Category:** {category} | **Files in slice:** {len(lines)}\n\n")
            f.write("---\n\n")
            f.write("\n\n".join(lines))
        slices.append(slice_path)
        part_num += 1
        current_lines = []

    # README files (inlined)
    for md_file in sorted(md_files):
        if not should_inline_full(md_file):
            continue
        full_path = repo_path / md_file
        if not full_path.exists():
            continue
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            continue
        lines_count = len(content.split("\n"))
        if lines_count > MAX_LINES_PER_SLICE * 3:
            chunk_lines = content.split("\n")
            chunk_num = 1
            for i in range(0, len(chunk_lines), MAX_LINES_PER_SLICE * 2):
                chunk = "\n".join(chunk_lines[i : i + MAX_LINES_PER_SLICE * 2])
                current_lines.append(
                    f"## {md_file} (chunk {chunk_num})\n\n{chunk[:4000]}"
                )
                chunk_num += 1
                if len(current_lines) >= 2:
                    flush_slice(
                        current_lines,
                        f"README Chunks (part {part_num})",
                        "Documentation",
                    )
        else:
            entry = f"## {md_file}\n\n{content[:5000]}"
            current_lines.append(entry)
            if len(current_lines) >= 2:
                flush_slice(
                    current_lines, f"Documentation (part {part_num})", "Documentation"
                )
    if current_lines:
        flush_slice(current_lines, "Documentation", "Documentation")

    # Remaining markdown (summarized)
    remaining_md = [f for f in md_files if not should_inline_full(f)]
    for md_file in sorted(remaining_md):
        summary = get_file_summary(repo_path, md_file)
        current_lines.append(f"## {md_file}\n\n{summary}")
        if len(current_lines) >= 8:
            flush_slice(current_lines, f"Markdown Index (part {part_num})", "Markdown")
    if current_lines:
        flush_slice(current_lines, "Markdown Index", "Markdown")

    # Code entry points (inlined)
    entry_code = [f for f in code_files if should_inline_full(f)]
    other_code = [f for f in code_files if f not in entry_code]

    for code_file in sorted(entry_code):
        full_path = repo_path / code_file
        if not full_path.exists():
            continue
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except:
            continue
        lines_count = len(content.split("\n"))
        if lines_count > MAX_LINES_PER_SLICE * 2:
            content = (
                "\n".join(content.split("\n")[: MAX_LINES_PER_SLICE * 2])
                + f"\n\n... [truncated, {lines_count} total lines]"
            )
        current_lines.append(f"## {code_file}\n\n```\n{content[:3000]}\n```")
        if len(current_lines) >= 2:
            flush_slice(current_lines, f"Code Entry Points (part {part_num})", "Code")
    if current_lines:
        flush_slice(current_lines, "Code Entry Points", "Code")

    # Other code (summarized)
    for code_file in sorted(other_code):
        summary = get_file_summary(repo_path, code_file)
        current_lines.append(f"## {code_file}\n\n{summary}")
        if len(current_lines) >= 10:
            flush_slice(current_lines, f"Code Index (part {part_num})", "Code")
    if current_lines:
        flush_slice(current_lines, "Code Index", "Code")

    # Config files
    for cfg_file in sorted(config_files):
        summary = get_file_summary(repo_path, cfg_file)
        current_lines.append(f"## {cfg_file}\n\n{summary}")
        if len(current_lines) >= 10:
            flush_slice(current_lines, f"Config Index (part {part_num})", "Config")
    if current_lines:
        flush_slice(current_lines, "Config Index", "Config")

    # Other files
    for other_file in sorted(other_files):
        summary = get_file_summary(repo_path, other_file)
        current_lines.append(f"## {other_file}\n\n{summary}")
        if len(current_lines) >= 10:
            flush_slice(current_lines, f"Other Files (part {part_num})", "Other")
    if current_lines:
        flush_slice(current_lines, "Other Files", "Other")

    return slices


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(
            "Usage: python gitingest_slice_repos.py <repo_path> <file_list_path> <output_dir> <repo_name>"
        )
        sys.exit(1)

    repo_path = Path(sys.argv[1])
    file_list_path = Path(sys.argv[2])
    output_dir = Path(sys.argv[3])
    repo_name = sys.argv[4]

    slices = generate_slices(repo_path, file_list_path, output_dir, repo_name)
    print(f"Generated {len(slices)} slices for {repo_name}:")
    for s in slices:
        print(f"  {s}")
