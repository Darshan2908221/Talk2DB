# import re
# import uuid
# from datetime import date

# import pandas as pd
# import requests
# import streamlit as st

# # ---------- CONFIGURATION ----------
# BACKEND_URL = "http://127.0.0.1:8000/sql"
# USER_ID = 5452
# UPLOAD_DATABASE = "useruploads"

# st.set_page_config(
#     page_title="TALK2DB",
#     page_icon="DB",
#     layout="wide",
# )


# # ---------- API FUNCTIONS ----------

# @st.cache_data(ttl=600)
# def get_databases():
#     try:
#         response = requests.get(f"{BACKEND_URL}/databases", timeout=10)
#         response.raise_for_status()
#         return response.json()
#     except Exception:
#         return ["No database found"]


# def get_database_options():
#     database_options = list(get_databases())
#     if "No database found" in database_options:
#         return database_options
#     if UPLOAD_DATABASE not in database_options:
#         database_options.append(UPLOAD_DATABASE)
#     return database_options


# def get_database_catalog(p_refresh: bool = False):
#     try:
#         response = requests.get(
#             f"{BACKEND_URL}/database_catalog",
#             params={"refresh": p_refresh},
#             timeout=30,
#         )
#         response.raise_for_status()
#         return response.json()
#     except Exception:
#         return {}


# def get_database_names(p_user_id: int):
#     try:
#         response = requests.get(f"{BACKEND_URL}/db_name/{p_user_id}", timeout=5)
#         response.raise_for_status()
#         return response.json()
#     except Exception:
#         return {}


# def get_chatnames(p_user_id: int):
#     try:
#         response = requests.get(f"{BACKEND_URL}/chatnames/{p_user_id}", timeout=5)
#         response.raise_for_status()
#         return response.json()
#     except Exception:
#         return {}


# def get_chathistory(p_user_id: int, p_chat_id: str):
#     payload = {"user_id": p_user_id, "chat_id": p_chat_id}
#     try:
#         response = requests.post(f"{BACKEND_URL}/chat_history", json=payload, timeout=10)
#         response.raise_for_status()
#         return response.json()
#     except Exception:
#         return []


# def normalize_table_name(p_table_name: str):
#     table_name = re.sub(r"[^a-zA-Z0-9]+", "_", str(p_table_name)).strip("_").lower()
#     if not table_name:
#         table_name = "uploaded_file"
#     if table_name[0].isdigit():
#         table_name = f"file_{table_name}"
#     return table_name[:50]


# def upload_user_file(p_user_id: int, p_chat_id: str, p_database: str, p_uploaded_file):
#     file_type = p_uploaded_file.name.rsplit(".", 1)[-1].lower()
#     table_name = normalize_table_name(p_uploaded_file.name.rsplit(".", 1)[0])
#     files = {
#         "file": (
#             p_uploaded_file.name,
#             p_uploaded_file.getvalue(),
#             p_uploaded_file.type or "application/octet-stream",
#         )
#     }
#     data = {
#         "user_id": str(p_user_id),
#         "chat_id": p_chat_id,
#         "database": p_database,
#         "table_name": table_name,
#         "file_type": file_type,
#     }
#     response = requests.post(f"{BACKEND_URL}/upload_file", data=data, files=files, timeout=60)
#     response.raise_for_status()
#     return response.json()


# def insert_conversation(
#     p_user_id: int,
#     p_chat_id: str,
#     p_chat_name: str,
#     p_database: str,
#     p_role: str,
#     p_message: str,
#     p_sql_query: str = "null",
# ):
#     payload = {
#         "user_id": p_user_id,
#         "chat_id": p_chat_id,
#         "chat_name": p_chat_name,
#         "database": p_database,
#         "role": p_role,
#         "message": str(p_message),
#         "sql_query": str(p_sql_query),
#     }
#     response = requests.post(f"{BACKEND_URL}/insert_conversation", json=payload, timeout=10)
#     response.raise_for_status()
#     return response.json()


# def delete_chathistory(p_user_id: int, p_chat_id: str):
#     payload = {"user_id": p_user_id, "chat_id": p_chat_id}
#     response = requests.delete(f"{BACKEND_URL}/delete_chathistory", json=payload, timeout=10)
#     response.raise_for_status()
#     return response.json()


# def has_csv_result(p_result: dict):
#     return bool(str(p_result.get("csv_file", "")).strip())


# def render_csv_download(p_result: dict, p_key: str):
#     if has_csv_result(p_result):
#         st.download_button(
#             label="Download CSV",
#             data=p_result.get("csv_file", ""),
#             file_name=f"talk2db_result_{date.today()}.csv",
#             mime="text/csv",
#             key=p_key,
#         )


# # ---------- SESSION STATE INITIALIZATION ----------

# if "chat_sessions" not in st.session_state:
#     st.session_state.chat_sessions = {}

# if "chat_namings" not in st.session_state:
#     st.session_state.chat_namings = get_chatnames(p_user_id=USER_ID)

# if "db_names" not in st.session_state:
#     st.session_state.db_names = get_database_names(p_user_id=USER_ID)

# if "naming_mode" not in st.session_state:
#     st.session_state.naming_mode = False

# if "upload_mode" not in st.session_state:
#     st.session_state.upload_mode = False

# if "temp_db_name" not in st.session_state:
#     st.session_state.temp_db_name = "Yet to select"

# if "conv_manager" not in st.session_state:
#     st.session_state.conv_manager = []

# if "database_catalog" not in st.session_state:
#     st.session_state.database_catalog = {}


# # ---------- SIDEBAR UI ----------

# chat_id = st.session_state.get("chat_selector")

# with st.sidebar:
#     st.title("DBNavigator")

#     active_chat_id = st.session_state.get("chat_selector")
#     if not active_chat_id and st.session_state.chat_namings:
#         active_chat_id = list(st.session_state.chat_namings.keys())[0]
#         st.session_state.chat_selector = active_chat_id

#     if active_chat_id:
#         st.session_state.temp_db_name = st.session_state.db_names.get(
#             active_chat_id,
#             "NO DATABASE ASSOCIATED",
#         )

#     tab1, tab2 = st.tabs(["Workflows", "Metrics"])

#     with tab1:
#         st.subheader("Workflow Manager")
#         st.write("Target Database")
#         st.info(st.session_state.temp_db_name)

#         with st.expander("Database Scan"):
#             if st.button("Refresh Scan", key="refresh_database_scan"):
#                 get_databases.clear()
#                 st.session_state.database_catalog = get_database_catalog(p_refresh=True)
#             elif not st.session_state.database_catalog:
#                 st.session_state.database_catalog = get_database_catalog(p_refresh=False)

#             if st.session_state.database_catalog:
#                 scanned_databases = sorted(st.session_state.database_catalog.keys())
#                 st.caption(f"{len(scanned_databases)} databases scanned")
#                 selected_catalog_db = st.selectbox(
#                     "Database",
#                     options=scanned_databases,
#                     key="catalog_database_selector",
#                 )
#                 selected_schema = st.session_state.database_catalog.get(selected_catalog_db, {})
#                 if "error" in selected_schema:
#                     st.warning(selected_schema["error"])
#                 else:
#                     st.caption(f"{len(selected_schema)} tables found")
#                     for table_name, table_schema in selected_schema.items():
#                         columns = table_schema.get("columns", {})
#                         st.markdown(f"**{table_name}** ({len(columns)} columns)")
#                         st.caption(", ".join(columns.keys()) or "No columns found")
#             else:
#                 st.caption("No database metadata available.")

#         st.divider()

#         if st.button("New Chat"):
#             st.session_state.naming_mode = True
#             st.session_state.upload_mode = False

#         if st.button("Upload File"):
#             st.session_state.upload_mode = True
#             st.session_state.naming_mode = False
#             st.session_state.temp_db_name = UPLOAD_DATABASE

#         if st.session_state.naming_mode:
#             selected_db = st.selectbox("Select Target Database", options=get_database_options())
#             st.session_state.temp_db_name = selected_db

#             new_name = st.text_input("Enter Chat Name", key="new_chat_input")
#             if new_name:
#                 new_id = str(uuid.uuid4())
#                 st.session_state.chat_namings[new_id] = new_name
#                 st.session_state.db_names[new_id] = st.session_state.temp_db_name
#                 st.session_state.chat_sessions[new_id] = []
#                 st.session_state.chat_selector = new_id
#                 st.session_state.naming_mode = False
#                 st.rerun()

#         if st.session_state.upload_mode:
#             st.info(f"Target Database: {UPLOAD_DATABASE}")
#             uploaded_files_for_new_chat = st.file_uploader(
#                 label="Upload CSV or Excel files",
#                 accept_multiple_files=True,
#                 type=["csv", "xlsx"],
#                 key="new_upload_chat_files",
#             )
#             upload_chat_name = st.text_input("Enter Chat Name", key="new_upload_chat_name")

#             if uploaded_files_for_new_chat:
#                 st.caption(
#                     "Tables: "
#                     + ", ".join(
#                         normalize_table_name(uploaded_file.name.rsplit(".", 1)[0])
#                         for uploaded_file in uploaded_files_for_new_chat
#                     )
#                 )

#             if st.button("Create Upload Chat", key="create_upload_chat"):
#                 if not upload_chat_name.strip():
#                     st.warning("Please enter a chat name.")
#                 elif not uploaded_files_for_new_chat:
#                     st.warning("Please upload at least one file.")
#                 else:
#                     new_id = str(uuid.uuid4())
#                     upload_results = []
#                     with st.spinner("Uploading files..."):
#                         try:
#                             for uploaded_file in uploaded_files_for_new_chat:
#                                 upload_results.append(
#                                     upload_user_file(
#                                         p_user_id=USER_ID,
#                                         p_chat_id=new_id,
#                                         p_database=UPLOAD_DATABASE,
#                                         p_uploaded_file=uploaded_file,
#                                     )
#                                 )

#                             uploaded_tables = ", ".join(
#                                 result.get("table_name", "uploaded_file")
#                                 for result in upload_results
#                             )
#                             upload_message = f"Uploaded tables: {uploaded_tables}"
#                             insert_conversation(
#                                 p_user_id=USER_ID,
#                                 p_chat_id=new_id,
#                                 p_chat_name=upload_chat_name.strip(),
#                                 p_database=UPLOAD_DATABASE,
#                                 p_role="assistant",
#                                 p_message=upload_message,
#                             )

#                             st.session_state.chat_namings[new_id] = upload_chat_name.strip()
#                             st.session_state.db_names[new_id] = UPLOAD_DATABASE
#                             st.session_state.chat_sessions[new_id] = [
#                                 {"role": "assistant", "message": upload_message}
#                             ]
#                             st.session_state.chat_selector = new_id
#                             st.session_state.temp_db_name = UPLOAD_DATABASE
#                             st.session_state.upload_mode = False
#                             st.session_state.database_catalog = get_database_catalog(p_refresh=True)
#                             st.success(f"Uploaded successfully: {uploaded_tables}")
#                             st.rerun()
#                         except Exception as e:
#                             st.error(f"File upload failed: {e}")

#         st.divider()
#         st.markdown("Your Conversations")

#         if st.session_state.chat_namings:
#             if st.session_state.get("chat_selector") not in st.session_state.chat_namings:
#                 st.session_state.chat_selector = list(st.session_state.chat_namings.keys())[0]

#             chat_id = st.radio(
#                 "Select a Chat",
#                 options=list(st.session_state.chat_namings.keys()),
#                 format_func=lambda x: str(st.session_state.chat_namings.get(x, "Untitled")),
#                 key="chat_selector",
#             )

#             if chat_id in st.session_state.db_names:
#                 st.session_state.temp_db_name = st.session_state.db_names.get(
#                     chat_id,
#                     "NO DATABASE ASSOCIATED",
#                 )

#             if st.button("Delete Chat History", key=f"delete_chathistory_{chat_id}"):
#                 try:
#                     delete_chathistory(USER_ID, chat_id)
#                     st.session_state.chat_sessions.pop(chat_id, None)
#                     st.session_state.chat_namings.pop(chat_id, None)
#                     st.session_state.db_names.pop(chat_id, None)
#                     st.session_state.chat_namings = get_chatnames(p_user_id=USER_ID)
#                     st.session_state.db_names = get_database_names(p_user_id=USER_ID)
#                     st.success("Chat history deleted successfully.")
#                     st.rerun()
#                 except Exception as e:
#                     st.error(f"An error occurred while deleting chat history: {e}")

#             if st.session_state.temp_db_name == UPLOAD_DATABASE:
#                 st.divider()
#                 st.markdown("Add More Files")
#                 st.caption(f"Files are stored as tables in the {UPLOAD_DATABASE} database.")
#                 uploaded_files = st.file_uploader(
#                     label="Upload CSV or Excel files",
#                     accept_multiple_files=True,
#                     type=["csv", "xlsx"],
#                     key=f"file_uploader_{chat_id}",
#                 )
#                 if uploaded_files:
#                     st.caption(
#                         "Tables: "
#                         + ", ".join(
#                             normalize_table_name(uploaded_file.name.rsplit(".", 1)[0])
#                             for uploaded_file in uploaded_files
#                         )
#                     )
#                     if st.button("Upload Files", key=f"upload_files_{chat_id}"):
#                         upload_results = []
#                         with st.spinner("Uploading files..."):
#                             try:
#                                 for uploaded_file in uploaded_files:
#                                     upload_results.append(
#                                         upload_user_file(
#                                             p_user_id=USER_ID,
#                                             p_chat_id=chat_id,
#                                             p_database=UPLOAD_DATABASE,
#                                             p_uploaded_file=uploaded_file,
#                                         )
#                                     )
#                                 uploaded_tables = ", ".join(
#                                     result.get("table_name", "uploaded_file")
#                                     for result in upload_results
#                                 )
#                                 upload_message = f"Uploaded tables: {uploaded_tables}"
#                                 insert_conversation(
#                                     p_user_id=USER_ID,
#                                     p_chat_id=chat_id,
#                                     p_chat_name=st.session_state.chat_namings[chat_id],
#                                     p_database=UPLOAD_DATABASE,
#                                     p_role="assistant",
#                                     p_message=upload_message,
#                                 )
#                                 st.session_state.chat_sessions.setdefault(chat_id, []).append(
#                                     {"role": "assistant", "message": upload_message}
#                                 )
#                                 st.session_state.database_catalog = get_database_catalog(p_refresh=True)
#                                 st.success(f"Uploaded successfully: {uploaded_tables}")
#                                 st.rerun()
#                             except Exception as e:
#                                 st.error(f"File upload failed: {e}")

#             if chat_id and chat_id not in st.session_state.chat_sessions:
#                 with st.spinner("Syncing messages..."):
#                     st.session_state.chat_sessions[chat_id] = get_chathistory(USER_ID, chat_id)
#             elif chat_id and not st.session_state.chat_sessions.get(chat_id):
#                 st.write("NO CHATHISTORY AVAILABLE FOR THIS CHAT")
#         else:
#             st.info("No active workflows.")

#     with tab2:
#         st.header("Metrics")
#         if st.session_state.conv_manager:
#             last_res = st.session_state.conv_manager[-1]
#             st.metric("Rows Impacted", last_res.get("row_count", 0))
#             with st.expander("View SQL Query"):
#                 st.code(last_res.get("mysql_query", ""), language="sql")
#             with st.expander("Analysis", expanded=True):
#                 st.write(last_res.get("business_metrics", "No analysis provided."))
#             render_csv_download(last_res, "sidebar_download_csv")
#             if last_res.get("data200"):
#                 st.dataframe(pd.DataFrame(last_res["data200"]))
#         else:
#             st.caption("Execute a query to see performance metrics.")


# # ---------- MAIN CHAT AREA ----------

# if chat_id:
#     for msg in st.session_state.chat_sessions.get(chat_id, []):
#         with st.chat_message(msg["role"]):
#             st.markdown(msg["message"])
# else:
#     st.info("Create or select a chat to begin.")

# if st.session_state.conv_manager:
#     latest_result = st.session_state.conv_manager[-1]
#     st.divider()
#     st.subheader("Latest Result")
#     render_csv_download(latest_result, "main_download_csv")
#     if latest_result.get("data200"):
#         st.dataframe(pd.DataFrame(latest_result["data200"]))

# query = st.chat_input("Enter your query...", disabled=not bool(chat_id))

# if query and chat_id:
#     current_chat_name = st.session_state.chat_namings[chat_id]
#     current_database = st.session_state.db_names.get(chat_id, st.session_state.temp_db_name)

#     with st.chat_message("user"):
#         st.markdown(query)

#     st.session_state.chat_sessions.setdefault(chat_id, []).append(
#         {"role": "user", "message": query}
#     )

#     try:
#         insert_conversation(
#             p_user_id=USER_ID,
#             p_chat_id=chat_id,
#             p_chat_name=current_chat_name,
#             p_database=current_database,
#             p_role="user",
#             p_message=query,
#         )

#         with st.spinner("Getting answer for you..."):
#             payload = {
#                 "database": current_database,
#                 "user_id": USER_ID,
#                 "chat_id": chat_id,
#                 "user_query": query,
#                 "chat_history": st.session_state.chat_sessions[chat_id],
#             }
#             response = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=120)
#             response.raise_for_status()
#             result_data = response.json()
#             st.session_state.conv_manager.append(result_data)

#             assistant_message = str(result_data.get("ai_msg", "No response generated."))
#             st.session_state.chat_sessions[chat_id].append(
#                 {"role": "assistant", "message": assistant_message}
#             )

#             insert_conversation(
#                 p_user_id=USER_ID,
#                 p_chat_id=chat_id,
#                 p_chat_name=current_chat_name,
#                 p_database=current_database,
#                 p_role="assistant",
#                 p_message=assistant_message,
#                 p_sql_query=str(result_data.get("mysql_query")),
#             )

#         with st.chat_message("assistant"):
#             st.markdown(st.session_state.chat_sessions[chat_id][-1]["message"])
#         render_csv_download(result_data, f"query_download_csv_{len(st.session_state.conv_manager)}")
#         st.rerun()
#     except Exception as e:
#         st.error(f"Failed to communicate with backend: {e}")


# # ---------- FOOTER ----------
# st.divider()
# st.caption(f"Project: Talk2DB | Developer: Darshan Rajeev Naik | {date.today()} | Emp_Code: 5452")



import re
import uuid
from datetime import date
import pandas as pd
import requests
import streamlit as st

# ---------- CONFIGURATION ----------
BACKEND_URL = "http://127.0.0.1:8000/sql"
USER_ID = 5452
UPLOAD_DATABASE = "useruploads"

st.set_page_config(
    page_title="TALK2DB",
    page_icon="DB",
    layout="wide",
)

# Global variables initialized to prevent NameErrors
chat_id = None

# ---------- API FUNCTIONS ----------

@st.cache_data(ttl=600)
def get_databases():
    try:
        response = requests.get(f"{BACKEND_URL}/databases", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return ["No database found"]

def get_database_options():
    database_options = list(get_databases())
    if "No database found" in database_options:
        return database_options
    if UPLOAD_DATABASE not in database_options:
        database_options.append(UPLOAD_DATABASE)
    return database_options

def get_database_catalog(p_refresh: bool = False):
    try:
        response = requests.get(
            f"{BACKEND_URL}/database_catalog",
            params={"refresh": p_refresh},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}

def get_database_names(p_user_id: int):
    try:
        response = requests.get(f"{BACKEND_URL}/db_name/{p_user_id}", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}

def get_chatnames(p_user_id: int):
    try:
        response = requests.get(f"{BACKEND_URL}/chatnames/{p_user_id}", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}

def get_chathistory(p_user_id: int, p_chat_id: str):
    payload = {"user_id": p_user_id, "chat_id": p_chat_id}
    try:
        response = requests.post(f"{BACKEND_URL}/chat_history", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return []

def normalize_table_name(p_table_name: str):
    table_name = re.sub(r"[^a-zA-Z0-9]+", "_", str(p_table_name)).strip("_").lower()
    if not table_name:
        table_name = "uploaded_file"
    if table_name[0].isdigit():
        table_name = f"file_{table_name}"
    return table_name[:50]

def upload_user_file(p_user_id: int, p_chat_id: str, p_database: str, p_uploaded_file):
    file_type = p_uploaded_file.name.rsplit(".", 1)[-1].lower()
    table_name = normalize_table_name(p_uploaded_file.name.rsplit(".", 1)[0])
    files = {
        "file": (
            p_uploaded_file.name,
            p_uploaded_file.getvalue(),
            p_uploaded_file.type or "application/octet-stream",
        )
    }
    data = {
        "user_id": str(p_user_id),
        "chat_id": p_chat_id,
        "database": p_database,
        "table_name": table_name,
        "file_type": file_type,
    }
    response = requests.post(f"{BACKEND_URL}/upload_file", data=data, files=files, timeout=60)
    response.raise_for_status()
    return response.json()

def insert_conversation(
    p_user_id: int,
    p_chat_id: str,
    p_chat_name: str,
    p_database: str,
    p_role: str,
    p_message: str,
    p_sql_query: str = "null",
):
    payload = {
        "user_id": p_user_id,
        "chat_id": p_chat_id,
        "chat_name": p_chat_name,
        "database": p_database,
        "role": p_role,
        "message": str(p_message),
        "sql_query": str(p_sql_query),
    }
    try:
        response = requests.post(f"{BACKEND_URL}/insert_conversation", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None

def delete_chathistory(p_user_id: int, p_chat_id: str):
    payload = {"user_id": p_user_id, "chat_id": p_chat_id}
    response = requests.delete(f"{BACKEND_URL}/delete_chathistory", json=payload, timeout=10)
    response.raise_for_status()
    return response.json()

def render_csv_download(p_result: dict, p_key: str):
    csv_data = p_result.get("csv_file", "")
    if csv_data and str(csv_data).strip():
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"talk2db_result_{date.today()}.csv",
            mime="text/csv",
            key=p_key,
        )

# ---------- SESSION STATE INITIALIZATION ----------

if "chat_sessions" not in st.session_state: st.session_state.chat_sessions = {}
if "chat_namings" not in st.session_state: st.session_state.chat_namings = get_chatnames(USER_ID)
if "db_names" not in st.session_state: st.session_state.db_names = get_database_names(USER_ID)
if "naming_mode" not in st.session_state: st.session_state.naming_mode = False
if "upload_mode" not in st.session_state: st.session_state.upload_mode = False
if "temp_db_name" not in st.session_state: st.session_state.temp_db_name = "Yet to select"
if "conv_manager" not in st.session_state: st.session_state.conv_manager = []
if "database_catalog" not in st.session_state: st.session_state.database_catalog = {}
if "last_chat_id" not in st.session_state: st.session_state.last_chat_id = None


# ---------- SIDEBAR UI ----------

with st.sidebar:
    st.title("DBNavigator")

    active_chat_id = st.session_state.get("chat_selector")
    if not active_chat_id and st.session_state.chat_namings:
        active_chat_id = list(st.session_state.chat_namings.keys())[0]
        st.session_state.chat_selector = active_chat_id

    # LOGIC: Clear tabular data instantly when switching chats
    if active_chat_id != st.session_state.last_chat_id:
        st.session_state.conv_manager = []
        st.session_state.last_chat_id = active_chat_id

    if active_chat_id:
        st.session_state.temp_db_name = st.session_state.db_names.get(
            active_chat_id, "NO DATABASE ASSOCIATED"
        )

    tab1, tab2 = st.tabs(["Workflows", "Metrics"])

    with tab1:
        st.subheader("Workflow Manager")
        st.write("Target Database")
        st.info(st.session_state.temp_db_name)

        with st.expander("Database Scan"):
            if st.button("Refresh Scan"):
                get_databases.clear()
                st.session_state.database_catalog = get_database_catalog(p_refresh=True)
            elif not st.session_state.database_catalog:
                st.session_state.database_catalog = get_database_catalog(p_refresh=False)

            if st.session_state.database_catalog:
                scanned_dbs = sorted(st.session_state.database_catalog.keys())
                selected_catalog_db = st.selectbox("Database", options=scanned_dbs)
                schema = st.session_state.database_catalog.get(selected_catalog_db, {})
                for table_name, table_schema in schema.items():
                    st.markdown(f"**{table_name}**")
                    st.caption(", ".join(table_schema.get("columns", {}).keys()))

        st.divider()
        if st.button("New Chat"):
            st.session_state.naming_mode, st.session_state.upload_mode = True, False

        if st.button("Upload File"):
            st.session_state.upload_mode, st.session_state.naming_mode = True, False
            st.session_state.temp_db_name = UPLOAD_DATABASE

        if st.session_state.naming_mode:
            selected_db = st.selectbox("Select Target Database", options=get_database_options())
            new_name = st.text_input("Enter Chat Name")
            if new_name:
                new_id = str(uuid.uuid4())
                st.session_state.chat_namings[new_id] = new_name
                st.session_state.db_names[new_id] = selected_db
                st.session_state.chat_selector = new_id
                st.session_state.naming_mode = False
                st.rerun()

        if st.session_state.upload_mode:
            uploaded_file_obj = st.file_uploader("Upload CSV or Excel", accept_multiple_files=False, type=["csv", "xlsx"])
            upload_chat_name = st.text_input("Enter Chat Name")

            if uploaded_file_obj:
                # Wrapped in list to handle 'bytes' object vs 'UploadedFile' object logic
                files_preview = [uploaded_file_obj]
                st.caption("Tables: " + ", ".join([normalize_table_name(f.name.rsplit(".", 1)[0]) for f in files_preview]))

            if st.button("Create Upload Chat") and upload_chat_name and uploaded_file_obj:
                new_id = str(uuid.uuid4())
                with st.spinner("Uploading..."):
                    try:
                        res = upload_user_file(USER_ID, new_id, UPLOAD_DATABASE, uploaded_file_obj)
                        table_name = res.get("table_name", "uploaded_file")
                        msg = f"Uploaded table: {table_name}"
                        insert_conversation(USER_ID, new_id, upload_chat_name, UPLOAD_DATABASE, "assistant", msg)
                        st.session_state.chat_namings[new_id] = upload_chat_name
                        st.session_state.db_names[new_id] = UPLOAD_DATABASE
                        st.session_state.chat_selector = new_id
                        st.session_state.upload_mode = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"Upload failed: {e}")

        st.divider()
        if st.session_state.chat_namings:
            chat_id = st.radio(
                "Select a Chat",
                options=list(st.session_state.chat_namings.keys()),
                format_func=lambda x: str(st.session_state.chat_namings.get(x, "Untitled")),
                key="chat_selector",
            )
            if st.button("Delete Chat"):
                delete_chathistory(USER_ID, chat_id)
                st.session_state.chat_namings.pop(chat_id, None)
                st.rerun()

    with tab2:
        st.header("Metrics")
        if st.session_state.conv_manager:
            last_res = st.session_state.conv_manager[-1]
            st.metric("Rows Found", last_res.get("row_count", 0))
            with st.expander("SQL Query"): st.code(last_res.get("mysql_query", ""), language="sql")
            st.write(last_res.get("business_metrics", "No analysis available."))
            if last_res.get("data200"): st.dataframe(pd.DataFrame(last_res["data200"]))

# ---------- MAIN CHAT AREA ----------

if chat_id:
    # Ensure session history is synced
    if chat_id not in st.session_state.chat_sessions:
        st.session_state.chat_sessions[chat_id] = get_chathistory(USER_ID, chat_id)
    
    # Render historical messages
    for msg in st.session_state.chat_sessions.get(chat_id, []):
        with st.chat_message(msg["role"]): st.markdown(msg["message"])

    # Show result table in main screen for the current query
    if st.session_state.conv_manager:
        latest_result = st.session_state.conv_manager[-1]
        st.divider()
        st.subheader("Query Results")
        render_csv_download(latest_result, "main_download")
        if latest_result.get("data200"):
            st.dataframe(pd.DataFrame(latest_result["data200"]))
else:
    st.info("Please select or create a chat to begin.")

# ---------- CHAT INPUT ----------

query = st.chat_input("Ask about your data...", disabled=not bool(chat_id))

if query and chat_id:
    current_chat_name = st.session_state.chat_namings[chat_id]
    current_database = st.session_state.db_names.get(chat_id, st.session_state.temp_db_name)

    with st.chat_message("user"): st.markdown(query)
    st.session_state.chat_sessions[chat_id].append({"role": "user", "message": query})
    insert_conversation(USER_ID, chat_id, current_chat_name, current_database, "user", query)

    with st.spinner("Talking to DB..."):
        try:
            payload = {
                "database": current_database,
                "user_id": USER_ID,
                "chat_id": chat_id,
                "user_query": query,
                "chat_history": st.session_state.chat_sessions[chat_id],
            }
            response = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=120)
            response.raise_for_status()
            result_data = response.json()
            
            # Store only the latest result for tabular display
            st.session_state.conv_manager = [result_data]
            
            ai_msg = result_data.get("ai_msg", "No answer provided.")
            st.session_state.chat_sessions[chat_id].append({"role": "assistant", "message": ai_msg})
            insert_conversation(USER_ID, chat_id, current_chat_name, current_database, "assistant", ai_msg, result_data.get("mysql_query"))
            st.rerun()
        except Exception as e:
            st.error(f"Backend Error: {e}")

# ---------- FOOTER ----------
st.divider()
st.caption(f"Project: Talk2DB | Developer: Darshan Rajeev Naik | {date.today()} | Emp_Code: 5452")

# streamlit run frontend\main.py
