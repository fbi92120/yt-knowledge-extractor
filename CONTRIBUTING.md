# Contributing to YT Knowledge Extractor

Thanks for your interest! This project welcomes contributions.

## Before you start

- Read `SPECS.md` — it defines the non-negotiable rules (Bloc 0 Constitution) and the exact output template (Bloc 3). Any code change must respect these rules.
- Read `PLAN.md` — it shows the sequenced implementation approach used to build the project.
- Read `CLAUDE.md` at the repo root — it tracks the current state and known transversal issues.

## How to contribute

### Report a bug

Open an issue with:
- The YouTube URL that triggered the bug
- The exact command you ran
- The full error output
- Your `config.yml` (with the API key redacted)

### Suggest a feature

Open an issue describing:
- What problem you're trying to solve
- How your suggestion fits (or doesn't) with the rules in `SPECS.md` Bloc 0
- A short example of expected behavior

### Submit a pull request

1. Fork the repo and create a feature branch
2. Follow the existing code style (no linter configured yet — match the surrounding code)
3. Add or update tests — no PR should reduce test coverage
4. Run `pytest tests/` locally and confirm 8/8 pass
5. Keep the PR focused: one change per PR
6. Update `README.md` and `README.fr.md` if you touch user-facing behavior

## Development setup

```bash
git clone https://github.com/fbi92120/yt-knowledge-extractor.git
cd yt-knowledge-extractor
pip install -r requirements.txt
cp config.yml.example config.yml
cp .env.example .env
# Add your GEMINI_API_KEY in .env
pytest tests/
```

## Adding a new LLM provider

Providers live in `src/llm/`. To add one:

1. Create `src/llm/[name].py` that defines a class inheriting from `LLMProvider`
2. Implement `generate(self, system_prompt, user_prompt) -> LLMResponse`
3. Populate `CONTEXT_WINDOWS` with the models you support
4. Register the provider in `src/llm/__init__.py` (`PROVIDERS` dict)
5. Update `.env.example` and `config.yml.example` with the new env variable
6. Update the provider table in both READMEs

No LLM SDK dependencies — use `requests` directly. Look at `src/llm/gemini.py` or `src/llm/groq.py` for a reference implementation.

## Code conventions

- Code, variable names, function names, docstrings: **English or French, consistent within a file** (current code is in French)
- User-facing CLI output: **French**
- Keep `extract.py` free of business logic — everything goes into `src/`
- Never introduce paid-only providers as default
- Never break the Bloc 0 rules in `SPECS.md`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
