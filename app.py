import os

import pandas as pd
import streamlit as st

from scorer import load_papers, score_papers

st.set_page_config(page_title="Conference Review Bidder", layout="wide")
st.title("Conference Review Bidder")

with st.sidebar:
    st.header("Settings")

    api_key = st.text_input(
        "OpenAI API Key (optional, falls back to env var)", type="password"
    )

    uploaded_file = st.file_uploader("Upload paper list (JSON or CSV)", type=["json", "csv"])

    topics = st.text_area(
        "Your Research Interests",
        placeholder="e.g., computational social science, NLP, social media analysis, misinformation...",
        height=150,
    )

    max_workers = st.slider("Parallel API calls", min_value=1, max_value=10, value=5)

    score_button = st.button(
        "Score Papers", type="primary", disabled=not (uploaded_file and topics)
    )

if "results_df" not in st.session_state:
    st.session_state.results_df = None

if score_button:
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    if uploaded_file.name.endswith(".json"):
        df = pd.read_json(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.lower().str.strip()

    if "title" not in df.columns or "abstract" not in df.columns:
        st.error("Input file must have 'title' and 'abstract' columns")
    else:
        with st.spinner(f"Scoring {len(df)} papers..."):
            st.session_state.results_df = score_papers(
                df, topics, max_workers=max_workers
            )
        st.success(f"Scored {len(df)} papers!")

if st.session_state.results_df is not None:
    results = st.session_state.results_df

    st.subheader("Score Distribution")
    score_counts = results["score"].value_counts().sort_index()
    st.bar_chart(score_counts)

    min_score = st.slider(
        "Minimum relevance score", min_value=0, max_value=5, value=0
    )
    filtered = results[results["score"] >= min_score]

    st.subheader(f"Papers ({len(filtered)} shown)")
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
    )

    csv_data = filtered.to_csv(index=False)
    st.download_button(
        label="Download filtered results as CSV",
        data=csv_data,
        file_name="scored_papers.csv",
        mime="text/csv",
    )
