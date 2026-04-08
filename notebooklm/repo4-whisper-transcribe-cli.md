# Repo: siddhesh-desai/whisper-transcribe-cli

## Source: siddhesh-desai/whisper-transcribe-cli
**URL:** https://github.com/siddhesh-desai/whisper-transcribe-cli
**License:** MIT | **Language:** Python 3.8+

## File Summary

| File | Description |
|------|-------------|
| `README.md` | Documentation (see below) |
| `constants.py` | Top-level constants: `MODEL = "tiny"`, `AVAILABLE_EXTENSIONS` tuple |
| `main.py` | Standalone test/demo: processes folder, runs transcription, uses `watchdog.Observer` for file watching |
| `whisper-transcribe-cli/pyproject.toml` | setuptools build, dependencies: `typer[all]`, `watchdog`, `openai-whisper` |
| `whisper-transcribe-cli/setup.py` | setuptools setup with `find_packages()`, entry point: `whisper-transcribe=transcriptor.cli:app` |
| `whisper-transcribe-cli/transcriptor/__init__.py` | Package init |
| `whisper-transcribe-cli/transcriptor/cli.py` | Typer-based CLI (`app.transcribe-files`) with `process_folder()`, `transcribe()`, `TranscriptorHandler` |
| `whisper-transcribe-cli/transcriptor/constants.py` | Same constants as top-level: `MODEL = "tiny"`, `AVAILABLE_EXTENSIONS` tuple |

---

## README (full)

```markdown
# whisper-transcribe-cli

A CLI tool to transcribe video and audio files using OpenAI's Whisper model.
Useful for batch transcription of large numbers of files in nested folders.
Outputs .txt files at the same location as source files.

## Installation
pip install whisper-transcribe-cli==0.1.1

## Usage
whisper-transcribe PATH [WHISPER_MODEL] --watch
whisper-transcribe . --watch
whisper-transcribe D:\Music base --no-watch

## Parameters
- PATH: folder containing files to transcribe (default: ".")
- WHISPER_MODEL: tiny|base|small|medium|large|turbo (default: tiny)
- --watch: detect changes and transcribe new files as added
- --no-watch: run once and exit (default)
```

## constants.py (both root and transcriptor/)

```python
MODEL = "tiny"

AVAILABLE_EXTENSIONS = (
    ".mp3", ".wav", ".flac", ".aac", ".ogg",
    ".mp4", ".mkv", ".avi", ".mov", ".flv", ".m4a",
)
```

## main.py (standalone demo/test)

```python
# Entry: hardcoded folder "D:\\Music"
# 1. process_folder() - walks directory, collects files with AVAILABLE_EXTENSIONS
# 2. transcribe() - loads whisper model, calls model.transcribe() per file,
#                   writes result["text"] to .txt file at same location
# 3. TranscriptorHandler (FileSystemEventHandler):
#      on_modified: re-transcribes modified media files
#      on_deleted: deletes corresponding .txt file
# 4. watchdog.Observer schedules handler, recursive=True
# 5. Blocks on observer.join() until KeyboardInterrupt
```

## transcriptor/cli.py (main CLI)

```python
app = typer.Typer()

@app.command("transcribe-files")
def start(
    folder_to_transcribe: str = typer.Argument(".", help="Folder to transcribe"),
    watch: bool = typer.Option(False, help="Watch for new files"),
    whisper_model: str = typer.Argument(constants.MODEL, help="tiny|base|small|medium|large|turbo"),
):
    # Validates path exists and is directory
    # process_folder() -> collect files
    # transcribe() -> load model, transcribe each, write .txt
    # If watch: start watchdog.Observer with TranscriptorHandler
    # Blocks until KeyboardInterrupt

def process_folder(folderPath: str):
    # os.walk, filter by AVAILABLE_EXTENSIONS

def transcribe(fileList: list):
    # whisper.load_model(model_name)
    # model.transcribe(file) -> result["text"]
    # write to os.path.splitext(file)[0] + ".txt"

class TranscriptorHandler(FileSystemEventHandler):
    def on_modified(event): transcribe([src_path])
    def on_deleted(event): delete corresponding .txt
```

## pyproject.toml

```toml
[build-system]
requires = ["setuptools", "wheel"]

[project]
name = "whisper-transcribe-cli"
version = "0.1.2"
description = "CLI to transcribe video/audio using OpenAI Whisper"
requires-python = ">=3.8"
dependencies = ["typer[all]", "watchdog", "openai-whisper"]
entry_points = ["console_scripts": ["whisper-transcribe=transcriptor.cli:app"]]
```

---

## Key Architectural Notes

- **Dependencies**: `typer[all]`, `watchdog`, `openai-whisper`
- **Entry point**: `whisper-transcribe` command maps to `transcriptor.cli:app`
- **Watch mode**: Uses `watchdog.Observer` to monitor folder recursively for file changes
- **Supported formats**: mp3, wav, flac, aac, ogg, mp4, mkv, avi, mov, flv, m4a
- **Output**: One .txt file per media file, same directory, same base name
- **Model loading**: Loads model once per batch (not per file) for efficiency
- **Default model**: `tiny` (fastest, lowest quality)
- **Nested folders**: Recursive processing via `os.walk`
- **Note**: `main.py` at root is a standalone demo with hardcoded path; the actual CLI is in `whisper-transcribe-cli/transcriptor/cli.py`
