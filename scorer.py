import argparse

import pandas as pd
from openai import OpenAI
from pydantic import BaseModel, Field
from tqdm.contrib.concurrent import thread_map


class RelevanceScore(BaseModel):
    score: int = Field(
        description="Relevance score from 1 to 5. "
        "1 = not relevant at all, "
        "2 = slightly relevant, "
        "3 = moderately relevant, "
        "4 = very relevant, "
        "5 = directly in reviewer's area of expertise."
    )
    explanation: str = Field(
        description="Brief explanation (1-2 sentences) of why this paper is or is not relevant."
    )


SYSTEM_PROMPT = """You are an expert academic reviewer helping a researcher decide which conference papers to bid on for peer review.

Given a paper's title and abstract, and the reviewer's research interests, rate how relevant the paper is to the reviewer's expertise on a scale of 1-5:
- 1: Not relevant at all — completely outside the reviewer's area
- 2: Slightly relevant — tangential overlap with reviewer's interests
- 3: Moderately relevant — some overlap, reviewer could provide a reasonable review
- 4: Very relevant — strong overlap with reviewer's research area
- 5: Core expertise — directly in the reviewer's primary research area

Be calibrated: most papers should score 1-3. Reserve 4-5 for genuine strong matches."""

USER_INSTRUCTION_TEMPLATE = """Paper Title: {title}

Paper Abstract: {abstract}

Reviewer's Research Interests: {topics}

Rate the relevance of this paper to the reviewer's research interests."""


def load_papers(path: str) -> pd.DataFrame:
    if path.endswith(".json"):
        df = pd.read_json(path)
    else:
        df = pd.read_csv(path)
        df.columns = df.columns.str.lower().str.strip()
    if "title" not in df.columns or "abstract" not in df.columns:
        raise ValueError(
            f"Input file must have 'title' and 'abstract' columns. "
            f"Found columns: {list(df.columns)}"
        )
    return df


def score_paper(
    paper: dict, topics: str, client: OpenAI, model: str = "gpt-4.1-mini"
) -> dict:
    try:
        user_instruction = USER_INSTRUCTION_TEMPLATE.format(
            title=paper["title"],
            abstract=paper["abstract"],
            topics=topics,
        )
        response = client.responses.parse(
            model=model,
            temperature=0.0,
            instructions=SYSTEM_PROMPT,
            input=user_instruction,
            text_format=RelevanceScore,
        )
        result = response.output_parsed
        return {"score": result.score, "explanation": result.explanation}
    except Exception as e:
        return {"score": 0, "explanation": f"Error: {e}"}


def score_papers(
    df: pd.DataFrame,
    topics: str,
    max_workers: int = 5,
    model: str = "gpt-4.1-mini",
) -> pd.DataFrame:
    client = OpenAI()

    def process(idx):
        row = df.iloc[idx]
        paper = {"title": row["title"], "abstract": row["abstract"]}
        return score_paper(paper, topics, client, model)

    results = thread_map(
        process, range(len(df)), max_workers=max_workers, desc="Scoring papers"
    )

    scores = [r["score"] for r in results]
    explanations = [r["explanation"] for r in results]

    result_df = df.copy()
    result_df["score"] = scores
    result_df["explanation"] = explanations
    result_df = result_df.sort_values("score", ascending=False).reset_index(drop=True)
    return result_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Score conference papers for review bidding"
    )
    parser.add_argument("input_path", help="Path to JSON or CSV file with title and abstract columns")
    parser.add_argument(
        "--topics", required=True, help="Your research interests/topics"
    )
    parser.add_argument(
        "--output", default="scored_papers.csv", help="Output CSV path"
    )
    parser.add_argument(
        "--max-workers", type=int, default=5, help="Number of parallel API calls"
    )
    parser.add_argument(
        "--model", default="gpt-4.1-mini", help="OpenAI model to use"
    )
    args = parser.parse_args()

    df = load_papers(args.input_path)
    print(f"Loaded {len(df)} papers")
    results = score_papers(
        df, args.topics, max_workers=args.max_workers, model=args.model
    )
    results.to_csv(args.output, index=False)
    print(f"Results saved to {args.output}")
