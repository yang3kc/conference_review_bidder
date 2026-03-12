import pandas as pd
import streamlit as st

REQUIRED_COLUMNS = {"title", "abstract", "score", "explanation"}
INTERNAL_COLUMNS = ["__row_id", "__original_order"]
PREFERRED_COLUMN_ORDER = [
    "user_rank",
    "score",
    "title",
    "explanation",
    "user_notes",
    "abstract",
]


def validate_scored_df(df: pd.DataFrame) -> str | None:
    missing_columns = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing_columns:
        return (
            "Input file must be a scored CSV containing: "
            "title, abstract, score, explanation. "
            f"Found columns: {list(df.columns)}"
        )
    return None


def initialize_review_df(df: pd.DataFrame) -> pd.DataFrame:
    review_df = df.copy()
    review_df["__row_id"] = range(len(review_df))
    review_df["__original_order"] = range(len(review_df))
    if "user_rank" not in review_df.columns:
        review_df["user_rank"] = range(1, len(review_df) + 1)
    if "user_notes" not in review_df.columns:
        review_df["user_notes"] = ""
    return review_df


def sort_review_df(df: pd.DataFrame) -> pd.DataFrame:
    working_df = df.copy()
    working_df["__rank_sort"] = pd.to_numeric(
        working_df["user_rank"], errors="coerce"
    )
    working_df["__score_sort"] = pd.to_numeric(working_df["score"], errors="coerce")
    working_df["__rank_missing"] = working_df["__rank_sort"].isna()
    working_df = working_df.sort_values(
        by=["__rank_missing", "__rank_sort", "__score_sort", "__original_order"],
        ascending=[True, True, False, True],
        kind="stable",
    )
    return working_df.drop(
        columns=["__rank_sort", "__score_sort", "__rank_missing"]
    )


def build_editor_df(df: pd.DataFrame) -> pd.DataFrame:
    sorted_df = sort_review_df(df)
    ordered_columns = [col for col in PREFERRED_COLUMN_ORDER if col in sorted_df.columns]
    remaining_columns = [
        col
        for col in sorted_df.columns
        if col not in ordered_columns and col not in INTERNAL_COLUMNS
    ]
    editor_columns = ["__row_id", *ordered_columns, *remaining_columns]
    return sorted_df[editor_columns].set_index("__row_id")


def sync_editor_changes(
    review_df: pd.DataFrame, edited_df: pd.DataFrame
) -> pd.DataFrame:
    updated_df = review_df.set_index("__row_id").copy()
    updated_df.loc[edited_df.index, "user_rank"] = edited_df["user_rank"]
    updated_df.loc[edited_df.index, "user_notes"] = edited_df["user_notes"]
    return updated_df.reset_index()


def load_review_df(uploaded_file) -> tuple[pd.DataFrame | None, str | None]:
    df = pd.read_csv(uploaded_file)
    validation_error = validate_scored_df(df)
    if validation_error:
        return None, validation_error
    return initialize_review_df(df), None


st.set_page_config(page_title="Conference Review Bidder", layout="wide")
st.title("Conference Review Bidder")
st.caption(
    "Score papers from the CLI first, then upload the scored CSV here to assign "
    "your review ranking."
)

uploaded_file = st.file_uploader("Upload scored CSV", type=["csv"])

if "results_df" not in st.session_state:
    st.session_state.results_df = None
if "loaded_file_key" not in st.session_state:
    st.session_state.loaded_file_key = None

if uploaded_file is None:
    st.info(
        "Run the CLI to generate a scored CSV in data/output/, then upload it here "
        "to rank papers."
    )
    st.stop()

file_key = f"{uploaded_file.name}:{uploaded_file.size}"
if st.session_state.loaded_file_key != file_key:
    review_df, validation_error = load_review_df(uploaded_file)
    if validation_error:
        st.session_state.results_df = None
        st.session_state.loaded_file_key = None
        st.error(validation_error)
        st.stop()
    st.session_state.results_df = review_df
    st.session_state.loaded_file_key = file_key
    st.success(f"Loaded {len(review_df)} scored papers")

results_df = st.session_state.results_df
score_series = pd.to_numeric(results_df["score"], errors="coerce")
score_counts = score_series.fillna(-1).value_counts().sort_index()

summary_col1, summary_col2, summary_col3 = st.columns(3)
summary_col1.metric("Papers", len(results_df))
summary_col2.metric("Scored Papers", int(score_series.notna().sum()))
summary_col3.metric("Score 0 Errors", int((score_series == 0).sum()))

st.subheader("Score Distribution")
st.bar_chart(score_counts)

st.subheader("Rank Papers")
st.caption(
    "Edit only user_rank and user_notes. The downloaded CSV will keep the scored "
    "fields and append your ranking columns."
)

editor_df = build_editor_df(results_df)
edited_df = st.data_editor(
    editor_df,
    key=f"review_editor_{file_key}",
    use_container_width=True,
    hide_index=True,
    disabled=[col for col in editor_df.columns if col not in {"user_rank", "user_notes"}],
    column_config={
        "user_rank": st.column_config.NumberColumn("User Rank", step=1),
        "score": st.column_config.NumberColumn("Score"),
        "title": st.column_config.TextColumn("Title", width="medium"),
        "explanation": st.column_config.TextColumn("Explanation", width="large"),
        "user_notes": st.column_config.TextColumn("User Notes", width="large"),
        "abstract": st.column_config.TextColumn("Abstract", width="large"),
    },
)

st.session_state.results_df = sync_editor_changes(results_df, edited_df)
download_df = sort_review_df(st.session_state.results_df).drop(columns=INTERNAL_COLUMNS)

st.download_button(
    label="Download ranked CSV",
    data=download_df.to_csv(index=False),
    file_name="ranked_scored_papers.csv",
    mime="text/csv",
)
