import streamlit as st

st.set_page_config(
    page_title="Test Sidebar",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar
with st.sidebar:
    st.markdown("### Sidebar is Working!")
    st.button("Test Button")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")

# Main
st.title("Main Content")
st.write("If you see this, the app is running.")
st.write("Check if sidebar is visible on the left.")
