import streamlit as st
from search import search_catalog, format_response

st.title("Library Book Finder") # header

user_query = st.chat_input("Ask about a book...") # What the user sees in the query box

if user_query:
    with st.spinner("Searching..."): # Enable a loading spinner
        try:
            result = search_catalog(user_query) # Error Handling
            answer = format_response(result)
        except Exception:
            answer = "Sorry, the assistant is temporarily unavailable. Please try again shortly."

    st.chat_message("assistant").write(answer)
