# Repo: jdepoix/youtube-transcript-api

## Source: jdepoix/youtube-transcript-api
**URL:** https://github.com/jdepoix/youtube-transcript-api
**License:** MIT | **Language:** Python 3.8+

## File Summary

| File | Description |
|------|-------------|
| `README.md` | Full documentation (inline below) |
| `pyproject.toml` | Project config with poetry build system (inline below) |
| `youtube_transcript_api/__main__.py` | CLI entry point, delegates to `_cli.py` (inline below) |
| `youtube_transcript_api/_cli.py` | argparse-based CLI with proxy support, transcript listing/fetching/translation (inline below) |
| `youtube_transcript_api/_api.py` | Core `YouTubeTranscriptApi` class wrapping transcript fetching and listing |
| `youtube_transcript_api/_transcripts.py` | Core dataclasses: `FetchedTranscript`, `FetchedTranscriptSnippet`, `TranscriptList`, `Transcript`; handles YouTube Innertube API calls, XML parsing, translation |
| `youtube_transcript_api/_errors.py` | Exception hierarchy: `VideoUnavailable`, `NoTranscriptFound`, `TranscriptsDisabled`, `IpBlocked`, `RequestBlocked`, `AgeRestricted`, `PoTokenRequired`, etc. |
| `youtube_transcript_api/formatters.py` | `FormatterLoader` supporting: `pretty`, `text`, `json`, `srt`, `vtt` output formats |
| `youtube_transcript_api/proxies.py` | `ProxyConfig`, `GenericProxyConfig`, `WebshareProxyConfig` for proxy support |
| `youtube_transcript_api/_settings.py` | YouTube API constants: `WATCH_URL`, `INNERTUBE_API_URL`, `INNERTUBE_CONTEXT` |
| `youtube_transcript_api/__init__.py` | Public API exports: `YouTubeTranscriptApi`, `FetchedTranscript`, `FetchedTranscriptSnippet` |

---

## README (full)

```markdown
<h1 align="center">
  ✨ YouTube Transcript API ✨
</h1>

This is a python API which allows you to retrieve the transcript/subtitles for a given YouTube video. It also works for automatically generated subtitles, supports translating subtitles and it does not require a headless browser, like other selenium based solutions do!

## Install
pip install youtube-transcript-api

## API
from youtube_transcript_api import YouTubeTranscriptApi
ytt_api = YouTubeTranscriptApi()
ytt_api.fetch(video_id)

# list available transcripts
transcript_list = ytt_api.list('video_id')
for transcript in transcript_list:
    print(transcript.fetch())
    print(transcript.translate('en').fetch())

# filter by language
transcript = transcript_list.find_transcript(['de', 'en'])
transcript = transcript_list.find_manually_created_transcript(['de', 'en'])
transcript = transcript_list.find_generated_transcript(['de', 'en'])
```

## pyproject.toml (full)

```toml
[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.poetry]
name = "youtube-transcript-api"
version = "1.2.4"
description = "Python API to get YouTube transcripts/subtitles. Works with auto-generated subtitles, supports translation, no headless browser needed."
readme = "README.md"
license = "MIT"
authors = ["Jonas Depoix <jonas.depoix@web.de>"]
homepage = "https://github.com/jdepoix/youtube-transcript-api"
repository = "https://github.com/jdepoix/youtube-transcript-api"

[tool.poetry.dependencies]
python = ">=3.8,<3.15"
requests = "*"
defusedxml = "^0.7.1"

[tool.poetry.scripts]
youtube_transcript_api = "youtube_transcript_api.__main__:main"
```

## __main__.py (full)

```python
import sys
import logging
from ._cli import YouTubeTranscriptCli

def main():
    logging.basicConfig()
    print(YouTubeTranscriptCli(sys.argv[1:]).run())

if __name__ == "__main__":
    main()
```

## _cli.py (full)

```python
import argparse
from importlib.metadata import PackageNotFoundError, version
from typing import List
from .proxies import GenericProxyConfig, WebshareProxyConfig
from .formatters import FormatterLoader
from ._api import YouTubeTranscriptApi, FetchedTranscript, TranscriptList

class YouTubeTranscriptCli:
    def run(self) -> str:
        # Parse args, configure proxy if provided, fetch transcripts for each video_id
        # Supports: --list-transcripts, --languages, --exclude-generated,
        #   --exclude-manually-created, --format, --translate,
        #   --webshare-proxy-username/--webshare-proxy-password,
        #   --http-proxy, --https-proxy
        parsed_args = self._parse_args()
        proxy_config = None
        if parsed_args.http_proxy != "" or parsed_args.https_proxy != "":
            proxy_config = GenericProxyConfig(http_url=parsed_args.http_proxy, https_url=parsed_args.https_proxy)
        if parsed_args.webshare_proxy_username is not None:
            proxy_config = WebshareProxyConfig(proxy_username=parsed_args.webshare_proxy_username,
                                               proxy_password=parsed_args.webshare_proxy_password)
        ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config)
        for video_id in parsed_args.video_ids:
            transcript_list = ytt_api.list(video_id)
            if parsed_args.list_transcripts:
                transcripts.append(transcript_list)
            else:
                transcripts.append(self._fetch_transcript(parsed_args, transcript_list))
        # Output formatted transcripts or errors
        return "\n\n".join(print_sections)

    def _fetch_transcript(self, parsed_args, transcript_list):
        if parsed_args.exclude_manually_created:
            transcript = transcript_list.find_generated_transcript(parsed_args.languages)
        elif parsed_args.exclude_generated:
            transcript = transcript_list.find_manually_created_transcript(parsed_args.languages)
        else:
            transcript = transcript_list.find_transcript(parsed_args.languages)
        if parsed_args.translate:
            transcript = transcript.translate(parsed_args.translate)
        return transcript.fetch()

    def _parse_args(self):
        parser = argparse.ArgumentParser(
            description="Python API to get YouTube transcripts/subtitles. Works with auto-generated subtitles and does not require a headless browser!")
        parser.add_argument("--version", ...)
        parser.add_argument("--list-transcripts", action="store_const", const=True)
        parser.add_argument("video_ids", nargs="+", type=str)
        parser.add_argument("--languages", nargs="*", default=["en"])
        parser.add_argument("--exclude-generated", action="store_const", const=True)
        parser.add_argument("--exclude-manually-created", action="store_const", const=True)
        parser.add_argument("--format", type=str, default="pretty", choices=(...))
        parser.add_argument("--translate", default="")
        parser.add_argument("--webshare-proxy-username", ...)
        parser.add_argument("--webshare-proxy-password", ...)
        parser.add_argument("--http-proxy", default="")
        parser.add_argument("--https-proxy", default="")
        return self._sanitize_video_ids(parser.parse_args(self._args))
```

---

## Key Architectural Notes

- **No headless browser required** — uses YouTube's Innertube API directly via `requests`
- **Thread-safety warning**: `YouTubeTranscriptApi` is not thread-safe; use one instance per thread
- **Proxy support**: Generic HTTP/HTTPS proxies and Webshare-specific proxy auth
- **Error handling**: Rich exception hierarchy for different failure modes (IP blocked, age-restricted, no transcript, etc.)
- **Formatter system**: Pluggable formatters for pretty/text/json/srt/vtt output
- **Poetry-based** build with `poe` task runner for test/format/lint
