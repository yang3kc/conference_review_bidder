# Conference Review Bidder

Score conference paper relevance to your research interests using LLMs.

## Setup

```bash
uv sync
export OPENAI_API_KEY="your-key"
```

## CSV Format

Your input CSV must have `title` and `abstract` columns (case-insensitive).

## CLI Usage

```bash
uv run python scorer.py papers.csv --topics "computational social science, NLP, misinformation" --output scored.csv
```

Options:
- `--max-workers N` — number of parallel API calls (default: 5)
- `--model MODEL` — OpenAI model to use (default: gpt-4.1-mini)

## Streamlit App

```bash
uv run streamlit run app.py
```

Upload a CSV, enter your research interests, and click "Score Papers". Results can be filtered by score and downloaded.
