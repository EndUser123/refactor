# Repo: lawwu/yt-transcript

## Source: lawwu/yt-transcript
**URL:** https://github.com/lawwu/yt-transcript
**License:** MIT | **Language:** Python

## File Summary

| File | Description |
|------|-------------|
| `README.md` | Documentation (see README section below) |
| `pyproject.toml` | Python package config (pip installable) |
| `requirements.txt` | Dependencies list |
| `yt_transcript/__init__.py` | Package init, exports `yt_transcript_cli` |
| `yt_transcript/__main__.py` | CLI entry point, calls `yt_transcript_cli()` |
| `yt_transcript/cli.py` | Click-based CLI: `yt_transcript_cli()` with --summarize, --markdown, --chapters, --no-cache flags |
| `yt_transcript/transcript_fetcher.py` | `TranscriptFetcher` class: fetches via `youtube_transcript_api`, caches to `~/.yt-transcript-cache/`, uses `yt_dlp` for video info/chapters |
| `yt_transcript/summarizer.py` | `summarize_transcript()` using OpenAI GPT-4o-mini; chapter extraction (YouTube chapters or 10-min fallback); `generate_markdown_summary()` |

---

## README (key sections)

```markdown
# yt-transcript

A CLI tool to fetch, cache, and summarize YouTube video transcripts. Optionally generate AI-powered summaries.

## Features
- Fetch official or auto-generated YouTube transcripts
- Cache transcripts locally to avoid repeated network calls
- Generate AI-powered summaries using OpenAI GPT
- Extract or generate chapter markers
- Export to JSON or Markdown formats

## Installation
pip install yt-transcript
export OPENAI_API_KEY=<your-openai-api-key>

## CLI Usage
yt-transcript https://youtube.com/watch?v=VIDEO_ID
yt-transcript https://youtube.com/watch?v=VIDEO_ID --summarize --markdown
yt-transcript https://youtube.com/watch?v=VIDEO_ID --chapters

## Dependencies
- youtube_transcript_api (fetches transcripts)
- yt_dlp (fetches video metadata/chapters)
- openai (GPT summarization)
- click (CLI framework)
```

## __init__.py (full)

```python
"""YouTube Transcript CLI tool."""
from .cli import yt_transcript_cli

if __name__ == "__main__":
    yt_transcript_cli()
```

## __main__.py (full)

```python
from .cli import yt_transcript_cli

if __name__ == "__main__":
    yt_transcript_cli()
```

## cli.py (key content)

```python
@click.command()
@click.argument("url", required=False)
@click.option("--verbose", is_flag=True)
@click.option("--no-cache", is_flag=True)
@click.option("--summarize", is_flag=True)
@click.option("--markdown", is_flag=True)
@click.option("--output-file", "-o", help="Output file for summary")
@click.option("--no-save-transcript", is_flag=True)
@click.option("--transcript-file", help="Output file for transcript")
@click.option("--chapters", is_flag=True)
def yt_transcript_cli(url, verbose, no_cache, summarize, markdown, output_file,
                      no_save_transcript, transcript_file, chapters):
    # Extracts video_id from URL (supports youtube.com and youtu.be)
    # Uses TranscriptFetcher to get transcript
    # If --summarize: calls summarize_transcript() with GPT-4o-mini
    # If --markdown: outputs markdown formatted summary
    # Saves transcript to {video_id}_transcript.txt by default
```

## transcript_fetcher.py (key content)

```python
class TranscriptFetcher:
    def __init__(self, cache_dir="~/.yt-transcript-cache"):
        self.cache_dir = os.path.expanduser(cache_dir)
        # Uses youtube_transcript_api.YouTubeTranscriptApi
        # Uses yt_dlp for video info (yt-dlp for metadata/chapters)

    def fetch_transcript(video_id, use_cache=True, language=None, no_cache=False):
        # Returns list of dicts: [{"text": "...", "start": float, "duration": float}, ...]
        # Caches to ~/.yt-transcript-cache/{video_id}.json

    def get_video_info(video_id):
        # Returns {"title": str, "channel_name": str, "video_id": str,
        #          "chapters": [{"title": str, "start": float, "end": float}, ...]}
        # Uses yt-dlp extract_flat for non-downloading metadata
```

## summarizer.py (key content)

```python
def summarize_transcript(video_info, transcript):
    # Uses GPT-4o-mini via OpenAI API
    # extract_chapters(): uses YouTube chapters if available,
    #                       else falls back to 10-minute segments
    # summarize_chapter(): calls GPT-4o-mini per chapter
    # Returns {"chapters": [{"title": str, "start": float, "end": float,
    #                        "text": str, "summary": str}, ...]}

def generate_markdown_summary(video_info, summary_data):
    # Formats output as: # Title\n\nChannel: ...\n\n## Summary\n\n
    # ### [Chapter Title](youtube_link&t=seconds) (HH:MM:SS)\n\nsummary text
```

---

## Key Architectural Notes

- **Dependencies**: `youtube_transcript_api`, `yt_dlp`, `openai`, `click`
- **Caching**: JSON cache in `~/.yt-transcript-cache/` keyed by video_id
- **Chapter extraction**: Prefers YouTube chapters; falls back to 10-minute segments
- **Summarization**: GPT-4o-mini, one call per chapter, sequential
- **TODO**: Local Whisper fallback for videos without transcripts, parallelize LLM calls
- **CLI framework**: Click (not argparse)
- **OpenAI dependency**: Requires `OPENAI_API_KEY` env var
