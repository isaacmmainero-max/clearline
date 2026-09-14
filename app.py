import json
import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="ClearLine", layout="wide", initial_sidebar_state="collapsed")

# 2. Apple Minimalist & Glassmorphism CSS
st.markdown("""
    <style>
    /* Global Background */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #eef2f5 100%);
        color: #1d1d1f;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Glassmorphism Containers */
    .glass-card {
        background: rgba(255, 255, 255, 0.65);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.5);
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
        padding: 24px;
        margin-bottom: 24px;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
    
    /* Typography */
    h1, h2, h3 {
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Initialize Session State (Memory)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "extracted_data" not in st.session_state:
    st.session_state.extracted_data = None
if "raw_text" not in st.session_state:
    st.session_state.raw_text = ""

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 4. Header Section
st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>ClearLine</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #86868b; font-size: 1.2rem; margin-bottom: 40px;'>Interactive Mortgage Disclosure & Compliance Companion</p>", unsafe_allow_html=True)

# 5. File Upload & Processing (Only show if data hasn't been extracted yet)
if not st.session_state.extracted_data:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload your Loan Estimate or Closing Disclosure (PDF)", type=["pdf"])
    
    if uploaded_file and st.button("Audit Document", type="primary"):
        with st.spinner("Extracting and analyzing document..."):
            try:
                # Read PDF
                reader = PdfReader(uploaded_file)
                raw_text = "".join([page.extract_text() or "" for page in reader.pages])
                st.session_state.raw_text = raw_text
                
                # Ask OpenAI for JSON
                system_prompt = (
                    "You are a mortgage compliance expert. Analyze the provided Loan Estimate (LE) or Closing Disclosure (CD). "
                    "Respond ONLY with a valid JSON object containing exactly these keys: "
                    "'loan_amount', 'interest_rate', 'monthly_payment', 'total_closing_costs', 'cash_to_close', and 'summary_notes'."
                )
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": raw_text}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                
                # Save parsed data to memory
                st.session_state.extracted_data = json.loads(response.choices[0].message.content)
                st.rerun() # Refresh app to show dashboard
                
            except Exception as e:
                st.error(f"Error during analysis: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# 6. Dashboard & Chat Interface (Shows after successful extraction)
if st.session_state.extracted_data:
    data = st.session_state.extracted_data
    
    # --- Top Metrics (Glass Cards) ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='glass-card'><h4>Loan Amount</h4><h2>${data.get('loan_amount', '0'):,}</h2></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='glass-card'><h4>Interest Rate</h4><h2>{data.get('interest_rate', '0')}%</h2></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='glass-card'><h4>Monthly Payment</h4><h2>${data.get('monthly_payment', '0'):,}</h2></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='glass-card'><h4>Cash to Close</h4><h2>${data.get('cash_to_close', '0'):,}</h2></div>", unsafe_allow_html=True)

    # --- Clear Workspace Button ---
    if st.button("Upload a Different Document"):
        st.session_state.extracted_data = None
        st.session_state.chat_history = []
        st.rerun()

    st.divider()

    # --- Interactive Chat Section ---
    st.markdown("### Ask ClearLine About Your Loan")
    
    # Display existing chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat Input Box
    if user_question := st.chat_input("E.g., Why are my closing costs so high?"):
        # Show user message
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.write(user_question)

        # Get AI Response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                chat_prompt = (
                    f"You are ClearLine, a helpful mortgage advisor. Answer the user's question based strictly on this extracted document data:\n{json.dumps(data, indent=2)}\n"
                    f"And this raw text if needed:\n{st.session_state.raw_text[:2000]}..."
                )
                
                # Build message list for memory
                messages = [{"role": "system", "content": chat_prompt}] + st.session_state.chat_history
                
                chat_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.5
                )
                
                answer = chat_response.choices[0].message.content
                st.write(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
