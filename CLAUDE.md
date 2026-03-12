# Conference Review Bidder

Score conference paper relevance to a reviewer's research interests using LLM structured output.

## Architecture

- **`scorer.py`** — Core logic. `score_paper()` calls OpenAI's `responses.parse()` with the `RelevanceScore` Pydantic model for structured output. `score_papers()` parallelizes via `tqdm.contrib.concurrent.thread_map`. Also serves as CLI entry point.
- **`app.py`** — Streamlit UI wrapping `scorer.py`. Sidebar for inputs, main area for results table and chart.

## Key Patterns

- **Structured output:** Uses `client.responses.parse()` with `text_format=RelevanceScore` — not chat completions. Keep this pattern when adding new LLM calls.
- **Threading:** Uses `thread_map` from `tqdm.contrib.concurrent` with a single shared `OpenAI()` client (thread-safe). Do not switch to asyncio.
- **Column normalization:** CSV columns are lowercased and stripped on load. Always reference columns in lowercase.

## Development

```bash
uv sync                          # install deps
uv run python scorer.py <csv> --topics "..." --output scored.csv   # CLI
uv run streamlit run app.py      # web UI
```

## Conventions

- Python 3.12+, managed with `uv`
- Default model: `gpt-4.1-mini`
- Input CSV must have `title` and `abstract` columns (case-insensitive)
- Score 0 indicates an API error — do not treat as a valid relevance score
