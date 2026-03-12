# Conference Review Bidder

Score conference paper relevance to your research interests using LLMs.

## Setup

```bash
uv sync
export OPENAI_API_KEY="your-key"
```

## Data Layout

- Put input files in `data/raw/`
- Put scored outputs in `data/output/`
- The entire `data/` folder is ignored by git for local-only datasets and results

## Input Format

Your input file can be **JSON** (array of objects) or **CSV**. It must have `title` and `abstract` columns. CSV column names are case-insensitive.

## CLI Usage

```bash
uv run python scorer.py data/raw/papers.json --topics "computational social science, NLP, misinformation" --output data/output/scored.csv
```

Options:
- `--max-workers N` — number of parallel API calls (default: 5)
- `--model MODEL` — OpenAI model to use (default: gpt-4.1-mini)

## Streamlit App

```bash
uv run streamlit run app.py
```

Upload a JSON or CSV file, enter your research interests, and click "Score Papers". Results can be filtered by score and downloaded.
