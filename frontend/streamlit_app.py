import streamlit as st
import pandas as pd
import requests
import plotly.express as px

BACKEND_URL = "http://127.0.0.1:8000/run-eda"

st.set_page_config(
    page_title="Automated Data Science Agent",
    layout="wide"
)

st.title(" Automated Data Science Agent")
st.caption("Prompt-driven Exploratory Data Analysis powered by ScaleDown")

st.sidebar.header(" Upload Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Upload CSV or Parquet file",
    type=["csv", "parquet"]
)

df = None
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_parquet(uploaded_file)
        st.sidebar.success("Dataset loaded successfully")
    except Exception as e:
        st.sidebar.error(f"Failed to load dataset: {e}")

st.sidebar.header(" Analysis Prompt")

user_prompt = st.sidebar.text_area(
    "What do you want to analyze?",
    value="Perform EDA, detect anomalies, and recommend a suitable model"
)

target_column = None
if df is not None:
    st.sidebar.header(" AutoML Target (Optional)")
    target_column = st.sidebar.selectbox(
        "Select target column",
        options=["None"] + list(df.columns)
    )
    if target_column == "None":
        target_column = None

run_btn = st.sidebar.button(" Run Analysis")

if df is not None:
    st.subheader(" Dataset Preview")
    st.write(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    st.dataframe(df.head())

if run_btn:
    if df is None:
        st.warning("Please upload a dataset first.")
    else:
        with st.spinner("Running automated EDA agent..."):
            try:
                response = requests.post(
                    BACKEND_URL,
                    json={
                        "prompt": user_prompt,
                        "data": df.to_dict(),
                        "target": target_column
                    },
                    timeout=300
                )

                if response.status_code != 200:
                    st.error(f"Backend error: {response.text}")
                    st.stop()

                result = response.json()

            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to backend: {e}")
                st.stop()

        st.subheader(" Key Insights")
        insights = result.get("insights", [])
        if insights:
            for insight in insights:
                st.markdown(f"- {insight}")
        else:
            st.info("No insights generated.")

        st.subheader(" Anomaly Detection")
        st.json(result.get("anomalies", {}))

        st.subheader(" Visualizations")
        numeric_cols = df.select_dtypes("number").columns.tolist()

        if numeric_cols:
            for col in numeric_cols[:3]:
                fig = px.histogram(df, x=col, title=f"Distribution of {col}")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No numeric columns available for visualization.")

        st.subheader(" Model Recommendation")

        automl_result = result.get("automl")
        if automl_result:
            st.json(automl_result)
        else:
            st.info("AutoML was skipped (no target column selected).")

        st.subheader(" ScaleDown Compression")

        scaledown = result.get("scaledown")
        if isinstance(scaledown, dict):
            ratio = scaledown.get("compression_ratio")
            if ratio is not None:
                st.metric("Metadata Reduction", f"{int(ratio * 100)}%")
            st.json(scaledown)
        else:
            st.info("ScaleDown statistics not available.")

        st.subheader(" Data Profiling Report")

        profile_path = result.get("profile_html")
        if profile_path:
            st.success(f"Profile report generated: {profile_path}")
        else:
            st.info("Profile report not generated.")