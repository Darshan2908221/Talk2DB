import streamlit as st
import pandas as pd
import requests
import os
from datetime import date

# page setup
st.set_page_config(
    page_title="Talk2DB",
    page_icon="T2D",
    layout="wide",
)

# UI Header
st.title("Talk2DB")
st.write("Talk2DB is an AI-Powered application, Takes your question to database and get back you the answer.")
st.write(
    """
        Guidelines to structure your question:\n
        --Use 'List' when you want to see just data Eg: List Employees working Enventure, List employees from Plumbing Discipline.\n
        --If referring to dates then mention year Eg: What was the sales in last quarter 2026, List Employees joined in January 2024.
         """
)

# Backend URL
BACKEND_BASE = "http://127.0.0.1:8000/sql"


# Database_schema function
@st.cache_data(ttl=600)
def fetch_dbschemas() -> list[str]:
    """Fetch database schemas from backend."""
    default_db = os.getenv("DB_NAME","hr")
    try:
        response = requests.get(f"{BACKEND_BASE}/databases", timeout=10)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and data:
            return data
        return [default_db]

    except requests.RequestException:
        return [default_db]


# Fetching databases
databases = fetch_dbschemas()

# Sidebar settings
with st.sidebar:
    st.title("DB_Selection")
    selected_db = st.selectbox(
        label="Target_DB",
        options=databases,
        help="You are choosing this DataBase for Interaction",
    )

    st.divider()
    st.success(f"Connected to: **{selected_db}**")
    st.info("API Status: **Online**")
    st.caption("v1.0.1 | Stable")

# Query Input Area
query_input = st.text_area(
    "Describe the data you need:",
    placeholder="e.g., List the names of employees working in Employees",
    height=120,
)

# Execution Button
col1, _ = st.columns([1, 4])
with col1:
    run_btn = st.button("Generate & Run", type="primary", width="content")

st.divider()

# Execution Logic
if run_btn:
    if not query_input.strip():
        st.warning("Please enter your question first")
    else:
        with st.spinner("Answer to your query is getting ready"):
            try:
                payload = {
                    "user_query": query_input,
                    "database": selected_db,
                }

                # Backend Call
                response = requests.post(
                    url=f"{BACKEND_BASE}/ask",
                    json=payload,
                    timeout=15,
                )

                if response.status_code == 200:
                    result = response.json()
                    if "mysql_query" in result:
                        with st.expander("SQL Query generated to answer this query:", expanded=False):
                            st.code(result["mysql_query"], language="SQL")

                    data = result.get("data", [])
                    if not data:
                        st.info("The query was successful, but no records were found.")
                    else:
                        st.markdown(f"Result set: {result.get('row_count', 0)} rows")

                        # converting to dataframe
                        df = pd.DataFrame(data)

                        # Interactive table display
                        st.dataframe(
                            data=df,
                            use_container_width=True,
                            hide_index=True,
                        )

                        # Export data to CSV
                        csv = df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="Export Results to CSV",
                            data=csv,
                            file_name=f"{selected_db}_data.csv",
                            mime="text/csv",
                        )

                elif response.status_code == 422:
                    st.error("Validation Error: Your input does not meet the requirements (min 5 characters).")
                else:
                    try:
                        err_detail = response.json().get("detail", "Backend Error")
                    except ValueError:
                        err_detail = response.text or "Backend Error"
                    st.error(f"Engine Error: {err_detail}")

            except requests.exceptions.ConnectionError:
                st.error("Connection Refused: Ensure the Backend server (uvicorn) is running on port 8000.")
            except Exception as e:
                st.error(f"Unexpected Error: {str(e)}")

# Footer
st.divider()
st.caption(f"Project: Talk2DB | Developer: Darshan Rajeev Naik | {date.today()} | Emp_Code: 5452")

# streamlit run frontend/main.py 