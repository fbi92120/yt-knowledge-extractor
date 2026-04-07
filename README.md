# YT Knowledge Extractor

Extract structured knowledge from YouTube videos into Markdown notes — ready for your Obsidian vault or local folder.

*[Version française disponible](README.fr.md)*

## What it does

Given a YouTube URL, this CLI tool:

1. Fetches the timestamped transcript and metadata
2. Sends the full transcript to an LLM (Gemini by default)
3. Generates a structured knowledge note in Markdown with:
   - Central thesis
   - Inferred chapter breakdown with clickable timestamp links
   - Idea map
   - Key concepts (defined by the author)
   - Notable verbatim quotes
   - Open questions
   - Empty personal notes section
   - Filtered sources from the video description
   - Full timestamped transcript (reserved for v2 cross-video search)

All content is anchored to real timestamps — no approximations, no invented links.

## Requirements

- Python 3.10+ (works on 3.9 with a deprecation warning)
- A free API key for one of: **Gemini** (recommended), Groq, Anthropic, OpenAI — or a local Ollama instance

## Installation

```bash
git clone https://github.com/fbi92120/yt-knowledge-extractor.git
cd yt-knowledge-extractor
pip install -r requirements.txt
```

## Configuration

```bash
cp config.yml.example config.yml
cp .env.example .env
```

Edit `.env` and add your API key:

```
GEMINI_API_KEY=AIza...
```

Get a free Gemini API key at [ai.google.dev](https://ai.google.dev/).

Edit `config.yml` to set your output mode (`obsidian` or `local`) and the path of your Obsidian vault or local folder.

## Obsidian setup

If you want generated notes to land directly in an Obsidian vault synced across Mac and mobile:

1. **Install Obsidian on desktop** — https://obsidian.md/download
2. **Install Obsidian mobile** — App Store (iOS) or Google Play (Android)
3. **Create a vault in Obsidian's native iCloud folder**
   - On Mac, the path is: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/`
   - Create a subfolder `YT-Knowledge` there (this will be your vault)
4. **Update `vault_path` in `config.yml`** to point to that subfolder:
   ```yaml
   vault_path: /Users/[user]/Library/Mobile Documents/iCloud~md~obsidian/Documents/YT-Knowledge
   ```
5. **Open Obsidian mobile** and select the vault
   - *Open existing vault → iCloud → Connected to iCloud*
   - Select `YT-Knowledge`

Your notes will sync automatically between Mac and mobile through iCloud.

## Usage

Two ways to invoke the tool:

**Interactive mode (recommended)** — no quoting headaches with shell special characters:

```bash
yt
# Entrez le lien YouTube : <paste URL here>
```

**Direct mode** — pass the URL as an argument (must be quoted because YouTube URLs contain `?` and sometimes `&`):

```bash
yt "https://www.youtube.com/watch?v=VIDEO_ID"
# or without the alias:
python extract.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

**Accepted URL formats:**

```
https://youtu.be/VIDEO_ID
https://www.youtube.com/watch?v=VIDEO_ID
https://www.youtube.com/shorts/VIDEO_ID
```

The tool shows a spinner with the current step and confirms the output path at the end:

```
✓ Fiche créée : file:///path/to/vault/channel-slug/2026-04-02-claude-mythos...md
```

On macOS Terminal, the `file://` path is clickable and opens the note directly.

## LLM providers

The project supports multiple LLM providers via a unified interface. Switch provider by editing `config.yml`.

| Provider | Model example | Free tier | Notes |
|---|---|---|---|
| **Gemini** (default) | `gemini-2.5-flash` | Yes, generous | 1M token context, handles long transcripts easily |
| Groq | `llama-3.3-70b-versatile` | Limited | Free tier caps requests at ~6k tokens — unusable for videos > ~5 min |
| Anthropic | `claude-sonnet-4-5` | No | Stub only, implementation pending |
| OpenAI | `gpt-4o` | No | Stub only, implementation pending |
| Ollama | any local model | Local | Stub only, implementation pending |

**Why Gemini by default?** Google AI Studio offers a free tier with a 1M token context window. Groq's free tier, despite advertising 128k context on the model side, applies a per-request limit around 6k tokens that makes it unusable for most YouTube videos.

## Output structure

```
[vault_path]/
  └── [channel-slug]/
        └── [YYYY-MM-DD]-[title-slug].md
```

Each note contains 10 sections (see `SPECS.md` Bloc 3 for the exact template).

## Testing

```bash
pytest tests/
```

Tests are skipped if `GEMINI_API_KEY` is not defined, so they work in CI environments without secrets.

The reference test video is [`T_GqhyYqTD4`](https://youtu.be/T_GqhyYqTD4) from the [@SamouraiDansant](https://www.youtube.com/@SamouraiDansant) channel.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
