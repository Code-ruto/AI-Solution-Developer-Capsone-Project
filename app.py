import streamlit as st
import chromadb
from config import CHROMA_DB_PATH
from search import search_catalog, format_response

st.set_page_config( # Setting page configuration
    page_title="Library Book Finder",
    page_icon="",
    layout="centered",
)


@st.cache_resource # Tells streamlit to run function below only once upon loading
def get_chroma_client(): 
    return chromadb.PersistentClient(path=str(CHROMA_DB_PATH)) # Initializes chromadb database and saves it locally to CHROMA_DB_PATH


client = get_chroma_client() # Instantiate client

st.title("📖 Library Book Finder")
st.caption("Ask me about a title, author, or topic and I'll point you to the shelf.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_query = st.chat_input("Ask about a book...") # What the user sees in the query box

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    with st.spinner("Searching the stacks..."):
        try:
            result = search_catalog(user_query, client)
            answer = format_response(result)
        except Exception:
            answer = "Sorry, the assistant is temporarily unavailable. Please try again shortly."

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.chat_message("assistant").write(answer)
