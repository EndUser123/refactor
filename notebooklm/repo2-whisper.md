# Repo: openai/whisper

## Source: openai/whisper
**URL:** https://github.com/openai/whisper
**License:** MIT | **Language:** Python 3.8+

## File Summary

| File | Description |
|------|-------------|
| `README.md` | Full documentation (see below) |
| `pyproject.toml` | setuptools build, depends on torch, tiktoken, numba, triton (inline below) |
| `model-card.md` | Model card with training details and benchmarks |
| `whisper/__init__.py` | `load_model()`, `available_models()`, model download URLs for tiny/base/small/medium/large/turbo |
| `whisper/__main__.py` | Entry point: calls `whisper.transcribe.cli()` |
| `whisper/transcribe.py` | `transcribe()` function and `cli()` argparse-based CLI for transcription/translation |
| `whisper/model.py` | `Whisper` nn.Module, `ModelDimensions` dataclass, custom layers with fp32/bf16 casting |
| `whisper/audio.py` | `load_audio()`, `log_mel_spectrogram()`, `pad_or_trim()` for audio preprocessing |
| `whisper/decoding.py` | `decode()`, `detect_language()`, `DecodingOptions`, `DecodingResult` dataclasses |
| `whisper/tokenizer.py` | `LANGUAGES` dict, `TO_LANGUAGE_CODE`, `get_tokenizer()` for tokenization |
| `whisper/timing.py` | `add_word_timestamps()` for word-level timing via cross-attention and DTW |
| `whisper/utils.py` | Output writers (txt/vtt/srt/tsv/json), formatting helpers, safe string helpers |
| `whisper/normalizers/basic.py` | Basic text normalizer |
| `whisper/normalizers/english.py` | English-specific text normalizer |
| `whisper/version.py` | Version string |

---

## README (key sections)

```markdown
# Whisper

Whisper is a general-purpose speech recognition model trained on a large dataset
of diverse audio. It performs multilingual speech recognition, speech translation,
and language identification.

## Available models

| Size  | Parameters | English-only | Multilingual | VRAM  | Speed  |
|-------|-----------|-------------|--------------|-------|--------|
| tiny  |   39 M    | tiny.en     | tiny         | ~1 GB | ~10x   |
| base  |   74 M    | base.en     | base         | ~1 GB | ~7x    |
| small |  244 M    | small.en    | small        | ~2 GB | ~4x    |
| medium |  769 M   | medium.en   | medium       | ~5 GB | ~2x    |
| large | 1550 M   | N/A         | large        | ~10GB | 1x     |
| turbo |  809 M   | N/A         | turbo        | ~6 GB | ~8x    |

## CLI usage

whisper audio.flac --model turbo
whisper japanese.wav --language Japanese
whisper japanese.wav --model medium --language Japanese --task translate

## Python usage

import whisper
model = whisper.load_model("turbo")
result = model.transcribe("audio.mp3")
```

## pyproject.toml (full)

```toml
[build-system]
requires = ["setuptools>=61.2"]
build-backend = "setuptools.build_meta"

[project]
name = "openai-whisper"
description = "Robust Speech Recognition via Large-Scale Weak Supervision"
requires-python = ">=3.8"
dependencies = [
  "more-itertools", "numba", "numpy", "tiktoken",
  "torch", "tqdm",
  "triton>=2; (platform_machine=='x86_64' and sys_platform=='linux') or sys_platform=='linux2'",
]
scripts.whisper = "whisper.transcribe:cli"
```

## __init__.py key content

```python
_MODELS = {
    "tiny.en": "https://openaipublic.azureedge.net/.../tiny.en.pt",
    "tiny": "https://openaipublic.azureedge.net/.../tiny.pt",
    "base.en": "https://openaipublic.azureedge.net/.../base.en.pt",
    "base": "https://openaipublic.azureedge.net/.../base.pt",
    "small.en": "https://openaipublic.azureedge.net/.../small.en.pt",
    "small": "https://openaipublic.azureedge.net/.../small.pt",
    "medium.en": "https://openaipublic.azureedge.net/.../medium.en.pt",
    "medium": "https://openaipublic.azureedge.net/.../medium.pt",
    "large-v1/v2/v3": "...large-v*.pt...",
    "large": "...large-v3.pt",
    "large-v3-turbo": "...large-v3-turbo.pt",
    "turbo": "...large-v3-turbo.pt",
}

def load_model(name, device=None, download_root=None, in_memory=False):
    # Downloads from Azure CDN if not cached, loads via torch.load
    # Returns Whisper model on specified device

def available_models() -> List[str]:
    return list(_MODELS.keys())
```

## transcribe.py CLI signature (key options)

```python
# argparse options from whisper/transcribe.py:cli()
# --model {tiny,base,small,medium,large,large-v3-turbo,turbo,...}
# --device (cuda/cpu)
# --output_dir, --output_format (txt/vtt/srt/tsv/json/all)
# --task (transcribe/translate)
# --language (None=detect, or specific language)
# --temperature (0.0 to 1.0, can be tuple for fallback)
# --best_of, --beam_size, --patience
# --word_timestamps (experimental word-level timing)
# --condition_on_previous_text
# --initial_prompt, --carry_initial_prompt
# --clip_timestamps, --hallucination_silence_threshold
# --output_format, --verbose
```

## model.py key architecture

```python
@dataclass
class ModelDimensions:
    n_mels: int       # 80 for whisper
    n_audio_ctx: int  # 1500 audio context tokens
    n_audio_state: int
    n_audio_head: int
    n_audio_layer: int
    n_vocab: int      # ~51865 for multilingual
    n_text_ctx: int   # 448 text context tokens
    n_text_state: int
    n_text_head: int
    n_text_layer: int

class Whisper(nn.Module):
    # Encoder: mel spectrogram -> transformer encoder
    # Decoder: autoregressive transformer decoder
    # Supports fp16/bf16 casting via custom Linear/LayerNorm/Conv1d layers
    # Uses scaled_dot_product_attention (SDPA) when available
    def set_alignment_heads(self, alignment_heads): ...
```

---

## Key Architectural Notes

- **Multitask seq2seq**: Jointly trained on speech recognition, translation, language ID, and voice activity detection via special tokens
- **Audio preprocessing**: 80-bin log-mel spectrogram, 30ms window, 10ms hop, 30Hz frame rate
- **Autoregressive decoding**: Beam search or greedy, with temperature-based fallback loop
- **Word timestamps**: Cross-attention pattern + dynamic time warping (DTW) for word-level timing
- **Model downloads**: From Azure CDN with SHA256 verification
- **Triton ops**: Custom Triton kernels for fast inference on supported platforms
- **Tokenizer**: tiktoken-based, supports all 99 languages
- **Normalizers**: Basic (strip/normalise whitespace) and English-specific (expand numbers, abbreviations)
