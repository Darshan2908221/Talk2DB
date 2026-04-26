# import streamlit as st
# import requests
# import os
# import pandas as pd
# from langchain_core.messages import AIMessage, HumanMessage
# from datetime import date

# # --- 1. CONFIG & SETUP ---
# BACKEND_URL = "http://127.0.0.1:8000/sql"

# st.set_page_config(
#     page_title="TALK2DB",
#     page_icon="🗣️",
#     layout="wide"
# )

# # --- 2. SESSION STATE INITIALIZATION ---
# # CRITICAL: We only initialize these if they don't exist yet
# if "chat_history" not in st.session_state:
#     st.session_state.chat_history = []

# if "last_result" not in st.session_state:
#     # We store the last API response here to keep Tab 2 populated
#     st.session_state.last_result = None

# # --- 3. DATABASE FETCHING ---
# @st.cache_data(ttl=600)
# def get_databases():
#     try:
#         response = requests.get(f"{BACKEND_URL}/databases", timeout=10)
#         response.raise_for_status()
#         return response.json()
#     except Exception as e:
#         st.sidebar.warning("Using default DB. Backend unreachable.")
#         return [os.getenv("DB_NAME", "hr")]

# fetched_databases = get_databases()

# # --- 4. SIDEBAR UI ---
# with st.sidebar:
#     st.title("Talk2DB_Menu")
#     tab1, tab2 = st.tabs(["DB_Selection", "Output_Fields"])
    
#     with tab1:
#         selected_db = st.selectbox(
#             label="Target_DB", 
#             options=fetched_databases, 
#             help="Select the database you want to interact with.",
#             placeholder="Select Database"
#         )
        
#         if st.button("Clear Chat History", use_container_width=True):
#             st.session_state.chat_history = []
#             st.session_state.last_result = None
#             st.rerun()
            
#         st.divider()
#         st.success(f"Connected: **{selected_db}**")
#         st.info("API Status: **Online**")

#     with tab2:
#         # We only show data if a query has been successfully run
#         if st.session_state.last_result:
#             res = st.session_state.last_result
#             st.metric("Rows Found", res.get("row_count", 0))
            
#             with st.expander("Generated SQL"):
#                 st.code(res.get("mysql_query", ""), language="sql")
            
#             with st.expander("Business Metrics"):
#                 st.write(res.get("business_metrics", "No metrics available"))
            
#             with st.expander("Raw Data View"):
#                 if res.get("data200"):
#                     df = pd.DataFrame(res["data200"])
#                     st.dataframe(df)
#                 else:
#                     st.write("No data returned.")
#         else:
#             st.write("Perform a query to see details here.")

# # --- 5. MAIN CHAT INTERFACE ---
# st.title("Talk2DB Dashboard")

# # Display previous messages
# for message in st.session_state.chat_history:
#     role = "user" if isinstance(message, HumanMessage) else "assistant"
#     with st.chat_message(role):
#         st.markdown(message.content)

# # Chat Input Logic
# if user_input := st.chat_input("Enter your query..."):
#     # 1. Immediately show user message and save to state
#     with st.chat_message("user"):
#         st.markdown(user_input)
#     st.session_state.chat_history.append(HumanMessage(content=user_input))

#     # 2. Call Backend
#     with st.spinner("Analyzing database..."):
#         try:
#             payload = {
#                 "user_query": user_input,
#                 "database": selected_db
#             }
            
#             response = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=45)
#             response.raise_for_status()
#             result = response.json()

#             # 3. Save result for Tab 2 and History
#             st.session_state.last_result = result
#             ai_response = result.get("ai_msg", "No response received.")
            
#             with st.chat_message("assistant"):
#                 st.markdown(ai_response)
            
#             st.session_state.chat_history.append(AIMessage(content=ai_response))
            
#             # Optional: Rerun to refresh the Sidebar (Tab 2) metrics immediately
#             st.rerun()

#         except Exception as e:
#             st.error(f"Error connecting to backend: {e}")

# # --- 6. FOOTER ---
# st.divider()
# st.caption(f"Project: Talk2DB | Developer: Darshan Rajeev Naik | {date.today()} | Emp_Code: 5452")










#Chat History
#Graph
#Table correction
#prompt changes




'''

#Imports
import streamlit as st
from datetime import date
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
import uuid
import requests

#BACKEND URL
BACKEND_URL = "http://127.0.0.1:8000/sql"

# ----------MAIN UI----------

#Pagesetup
st.set_page_config(
    page_title="TALK2DB",
    page_icon="🗣️",
    layout="wide"
)


#Database calls

#Get Databases
@st.cache_data(ttl=600)
def get_databases():
    """This function fetches the database"""
    try:
        response=requests.get(f"{BACKEND_URL}/databases", timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.sidebar.warning("Backend Unreachable or no databases")
        return ["No database"]
        
#Get Database function call
databases=get_databases()

#Get chathistory
def get_chathistory(p_user_id:int, p_session_id:str):
    payload=dict(user_id=p_user_id, session_id=p_session_id)
    try:
        response=requests.post(f"{BACKEND_URL}/chat_history",json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.warning("Backend unreachable or missmatch in userid and sessionid")
        return []

#Get chatnames
def get_chatnames(p_user_id:int):
    try:
        response=requests.get(f"{BACKEND_URL}/chatnames/{p_user_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.warning("No previous conversations found")
        return {}

#Get chatnames and user_id



# #Chatsessions and Chatnaming sessionstate
# if "chat_sessions" not in st.session_state:
#     st.session_state.chat_sessions={}

# if "chat_namings" not in st.session_state:
#     st.session_state.chat_sessions={}

#Sidebar
with st.sidebar:
    st.header("DBNavigator")
    tab1, tab2= st.tabs(["Tab1", "Tab2"])

    #Tab1
    with tab1:
        st.header("Workflow Manager")

        #Database selection
        st.selectbox(
            label="Target Database",
            placeholder="Select database to interact with",
            options=databases
        )

        #Initializing naming modes
        if "chat_sessions" not in st.session_state:
            st.session_state.chat_sessions = {}

        if "chat_namings" not in st.session_state:
            st.session_state.chat_namings = get_chatnames(p_user_id=5452)
            st.session_state.initial_chatname_load=False

        if "naming_mode" not in st.session_state:
            st.session_state.naming_mode = False

        if "chat_session_active" not in st.session_state:
            st.session_state.chat_session_active=False
                
        #Conversations
        if st.session_state.chat_namings:
            session_id=st.radio("Your Conversations", 
                                options=list(st.session_state.chat_namings.keys()),
                                format_func=lambda x: str(st.session_state.chat_namings[x]))
            if session_id:
                # st.session_state.initial_chatname_load=True
            #check wheather a session is available in chat_sessions
                if session_id not in st.session_state.chat_sessions:
                    st.session_state.chat_sessions[session_id]=get_chathistory(p_user_id=5452, p_session_id=session_id)
                    st.session_state.chat_session_active=True
        else:
            st.write("No conversations yet start a new one")
                

        #New Chat Button
        newchat_opted=st.button(label="Newchat")

        if newchat_opted:
            #Naming Creation
            st.session_state.naming_mode=True
            
        if st.session_state.naming_mode:
            chat_name=st.sidebar.text_input(label="Enter the chat name")

            if chat_name:               
                #Chat History Creation
                new_chat_history:list[BaseMessage]=[]
                thread_id=str(uuid.uuid4())
                st.session_state["chat_sessions"][thread_id]=new_chat_history
                st.session_state["chat_namings"][thread_id]=chat_name
                st.session_state.naming_mode=False
                st.rerun()

    #Tab2
    with tab2:
        st.header("Metrics")

        #Row Count
        st.metric("Row Count", 1000, border=True)

        #MySql Query
        with st.expander(label="Mysql Query"):
            st.code(body="select * from chat", language="sql")

        #Business Metrics
        with st.expander(label="Business Metrics", expanded=True):
            st.write({"Utilization":"120%", "Billed hour":95})

        #Generate Visualization
        st.button("Generate Visualization")

        #First 200 rows
        with st.expander("Sample Data Below", expanded=True):
            st.dataframe(data=[10,12,14,16,18])
        



#Chatinput
st.chat_input(placeholder="Enter your query")
for convo in st.session_state.chat_sessions["1dh"]:
    with st.chat_message(name=convo["role"]):
         st.markdown(convo["message"])





#Footer
st.divider()
st.caption(f"Project: Talk2DB | Developer: Darshan Rajeev Naik | {date.today()} | Emp_Code: 5452")

'''

import streamlit as st
from datetime import date
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
import uuid
import requests
import pandas as pd

# BACKEND URL
BACKEND_URL = "http://127.0.0.1:8000/sql"

# ---------- PAGE SETUP ----------
st.set_page_config(
    page_title="TALK2DB",
    page_icon="🗣️",
    layout="wide"
)

# ---------- API FUNCTIONS ----------

@st.cache_data(ttl=600)
def get_databases():
    """Fetches list of databases for the dropdown."""
    try:
        response = requests.get(f"{BACKEND_URL}/databases", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return ["No database found"]

def get_chatnames(p_user_id: int):
    """Fetches the metadata (IDs and Names) for the sidebar."""
    try:
        response = requests.get(f"{BACKEND_URL}/chatnames/{p_user_id}")
        response.raise_for_status()
        return response.json()  # Returns {session_id: chat_name}
    except Exception:
        st.sidebar.warning("Issue in fetching chatnames")
        return {}

def get_chathistory(p_user_id: int, p_session_id: str):
    """Fetches actual messages for a specific session."""
    # CRITICAL FIX: Use json=payload to match FastAPI Pydantic models
    payload = {"user_id": p_user_id, "session_id": p_session_id}
    try:
        response = requests.post(f"{BACKEND_URL}/chat_history", json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.sidebar.error(f"Failed to fetch history for {p_session_id}")
        return []

# ---------- SESSION STATE INITIALIZATION ----------

if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}  # Stores {session_id: [messages]}

if "chat_namings" not in st.session_state:
    # Initial load of names from DB
    st.session_state.chat_namings = get_chatnames(p_user_id=5452)    #Stores {"session_id":[chat_names]}

if "naming_mode" not in st.session_state:
    st.session_state.naming_mode = False

if "conv_manager" not in st.session_state:
    st.session_state.conv_manager=[]

# ---------- SIDEBAR UI ----------

with st.sidebar:
    st.title("DBNavigator")
    tab1, tab2 = st.tabs(["Workflows", "Metrics"])

    with tab1:
        st.subheader("Workflow Manager")

        # Database Selection
        databases = get_databases()
        selected_db = st.selectbox(
            label="Target Database",
            options=databases,
            placeholder="Select database"
        )

        st.divider()
        st.markdown("🗣️Your Conversations")
        
        # 1. RADIO BUTTONS: Selection logic
        session_id = None
        if st.session_state.chat_namings:
            session_id = st.radio(
                "Select a Chat",
                options=list(st.session_state.chat_namings.keys()),
                format_func=lambda x: str(st.session_state.chat_namings[x])
            )
            
            # 2. LAZY LOADING: Fetch history only if it's not in memory
            if session_id:
                if session_id not in st.session_state.chat_sessions or not st.session_state.chat_sessions[session_id]:
                    with st.spinner("Loading messages..."):
                        history = get_chathistory(p_user_id=5452, p_session_id=session_id)
                        st.session_state.chat_sessions[session_id] = history
        else:
            st.info("No conversations yet. Start a new one below!")

        # 3. NEW CHAT LOGIC
        if st.button("➕ New Chat"):
            st.session_state.naming_mode = True
        
        if st.session_state.naming_mode:
            new_name = st.text_input("Enter Chat Name", key="new_chat_name_input")
            if new_name:
                new_id = str(uuid.uuid4())
                # Update both state dictionaries
                st.session_state.chat_namings[new_id] = new_name
                st.session_state.chat_sessions[new_id] = []
                st.session_state.naming_mode = False
                st.rerun()

    with tab2:
        st.header("Metrics")
        if st.session_state.conv_manager:
            res = st.session_state.conv_manager[-1]
            st.metric("Rows Found", res.get("row_count", 0))
            
            with st.expander("Generated SQL"):
                st.code(res.get("mysql_query", ""), language="sql")
            
            with st.expander("Business Metrics", expanded=True):
                st.write(res.get("business_metrics", "No metrics available"))
            
            with st.expander("Raw Data View First 200 rows"):
                if res.get("data200"):
                    df = pd.DataFrame(res["data200"])
                    st.dataframe(df)
                
                else:
                    st.write("No data returned.")

            csv_file=st.download_button(
                label="Download full data retrieved CSV",
                data=res.get(
                    "csv_file", "no_csv_file"),
                    file_name="data.csv",
                    mime="text/csv",
                    icon=":material/download:"
                    )   
        
        else:
            st.write("Perform a query to see details here.")


# ---------- MAIN CHAT AREA ----------

# Display existing messages for the selected session
if session_id and session_id in st.session_state.chat_sessions:
    chat_container = st.container()
    with chat_container:
        for convo in st.session_state.chat_sessions[session_id]:
            role = convo.get("role", "assistant")
            text_content = convo.get("message", "")
            with st.chat_message(role):
                st.markdown(text_content)

# Chat Input
query = st.chat_input("Enter your query...")

if query and session_id:
    # 1. Display user message immediately
    with st.chat_message("user"):
        st.markdown(query)
    
    # 2. Appending to local session state
    st.session_state.chat_sessions[session_id].append({"role": "user", "message": query})

    payload={
        "user_id":5452,
        "session_id":session_id,
        "chat_name":st.session_state.chat_namings[session_id],
        "role":"user", 
        "message":str(query)
    }
        
    # 3.Inserting Human message in database
    response = requests.post(f"{BACKEND_URL}/insert_conversation", json=payload)

    #writing message to Main UI
    # with st.chat_message(name="user"):
        # st.markdown(st.session_state.chat_sessions[session_id][-1]["message"])

    with st.spinner("Getting Answer for you..."):

        #querying database
        try:
            payload={"database":selected_db, "user_query":query, "chat_history":st.session_state.chat_sessions[session_id]}
            response=requests.post(f"{BACKEND_URL}/ask", json=payload)
            response.raise_for_status()
            result_data=response.json()
            st.session_state.conv_manager.append(result_data)

            #Appending message to chatsession
            st.session_state.chat_sessions[session_id].append({"role": "assistant", "message": result_data["ai_msg"]})
            payload_ai={
                "user_id":5452,
                "session_id":session_id,
                "chat_name":st.session_state.chat_namings[session_id],
                "role":"assistant", 
                "message":str(result_data["ai_msg"])
                }
            
            # 3.Inserting AI message in database
            response = requests.post(f"{BACKEND_URL}/insert_conversation", json=payload_ai)

        
        except Exception as e:
            st.error(f"Failed to communicate with backend: {e}") 


        #writing message to Main UI
        with st.chat_message(name="assistant"):
            st.markdown(st.session_state.chat_sessions[session_id][-1]["message"])
            st.rerun()


# ---------- FOOTER ----------
st.divider()
st.caption(f"Project: Talk2DB | Developer: Darshan Rajeev Naik | {date.today()} | Emp_Code: 5452")













        
# streamlit run frontend/main.py