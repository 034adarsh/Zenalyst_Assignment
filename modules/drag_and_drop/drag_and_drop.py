import streamlit as st

def drag_and_drop_file():
    """Streamlit drag-and-drop file uploader."""
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
    if uploaded_file is not None:
        st.success(f"Uploaded file: {uploaded_file.name}")
        return uploaded_file
    return None 