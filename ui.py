import streamlit as st
import requests

# Point to your running FastAPI backend
API_URL = "http://127.0.0.1:8080"

st.set_page_config(page_title="AI Knowledge Assistant", layout="wide")
st.title("🧠 AI Knowledge Assistant")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR: KNOWLEDGE BASE BUILDER ---
with st.sidebar:
    st.header("📚 Knowledge Base")
    st.write("Upload context for the AI:")

    uploaded_files = st.file_uploader("Upload Documents (PDF, TXT, CSV, Audio)", accept_multiple_files=True)
    link = st.text_input("Web Link")
    text = st.text_area("Paste Text Directly")

    if st.button("Process Knowledge", type="primary", use_container_width=True):
        with st.spinner("Processing documents and building vector database..."):
            # Prepare files for the multipart/form-data request
            files_data = [("files", (f.name, f.getvalue(), f.type)) for f in uploaded_files] if uploaded_files else None

            # Prepare text/link form data
            form_data = {}
            if link.strip(): form_data["link"] = link.strip()
            if text.strip(): form_data["text"] = text.strip()

            if not files_data and not form_data:
                st.warning("Please provide at least one input.")
            else:
                try:
                    response = requests.post(f"{API_URL}/process", files=files_data, data=form_data)
                    if response.status_code == 200:
                        data = response.json()
                        st.success(data["status"])
                        with st.expander("View Summary"):
                            st.write(data["summary"])
                    else:
                        # SAFELY HANDLE ERRORS SO THE UI DOESN'T CRASH
                        try:
                            error_msg = response.json().get('detail', 'Unknown error')
                        except Exception:
                            error_msg = response.text or "Internal Server Error"

                        st.error(f"Backend Error ({response.status_code}): {error_msg}")
                        st.info("💡 Check the terminal running your FastAPI server for the exact code error.")
                except requests.exceptions.ConnectionError:
                    st.error("Failed to connect to backend. Is your FastAPI server running?")

# --- MAIN CHAT INTERFACE ---
# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Fetch and show AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                res = requests.post(f"{API_URL}/qa", data={"question": prompt})
                if res.status_code == 200:
                    answer = res.json()["answer"]
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error("⚠️ Please process some knowledge in the sidebar first, or check for errors!")
            except requests.exceptions.ConnectionError:
                st.error("Failed to connect to backend. Is your FastAPI server running?")