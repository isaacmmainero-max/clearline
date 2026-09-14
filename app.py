import json
import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="ClearLine", layout="wide", initial_sidebar_state="collapsed")

# 2. Sleek Gray & White Minimalist CSS - improved contrast & dark text
st.markdown("""
    <style>
    /* Global Background - sophisticated gray */
    .stApp {
        background: #f0f2f5;
        color: #333333;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Clear, high-contrastcontainers */
    .glass-card {
        background: #ffffff;
        border-radius: 16px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
        padding: 24px;
        margin-bottom: 24px;
    }

    /* typography on dark-ish page */
    h1, h2, h3 {
        font-weight: 600;
        letter-spacing: -0.5px;
        color: #1a1a1a;
    }
    h4 { color: #666666; }

    /* Fix text visibility in chat input */
    div[data-baseweb="input"] input {
        color: #333333 !important;
    }
    /* Placeholder color */
    div[data-baseweb="input"] input::placeholder {
        color: #999999 !important;
    }

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
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
st.markdown("<p style='text-align: center; color: #555555; font-size: 1.2rem; margin-bottom: 40px;'>Interactive Mortgage Disclosure & Compliance Companion</p>", unsafe_allow_html=True)

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

                # Ask OpenAI for JSON - NEW EXTRACTION PROMPT
                system_prompt = (
                    "You are 'ClearLine', an expert AI mortgage compliance analyst. "
                    "Your task is to analyze the provided text of a TRID Loan Estimate (LE) or Closing Disclosure (CD). "
                    "Extract *all* financial values and compliance-relevant information strictly into a valid JSON object. "
                    "Deeply nest *every single individual fee* within main section lists (e.g., 'fee_name', 'amount', 'section'). "
                    "SCHEMA: Provide a JSON with main keys like: 'origination_charges_borrower_paid_list', "
                    "'services_cannot_shop_borrower_paid_list', 'services_can_shop_borrower_paid_list', 'prepaids_list', etc. "
                    "Also include main keys: 'loan_amount', 'interest_rate', 'monthly_payment', 'cash_to_close', 'APR', "
                    "'total_closing_costs', 'loan_term_years'. "
                    "Create a detailed quantitative summary log in a final key called 'compliance_audit_log' of any fee that seems high or regulatory-violating based on TRID tolerances and industry norms."
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

        # Get AI Response - NEW CHAT PROMPT
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                chat_prompt = (
                    "You are 'ClearLine', an expert AI mortgage regulatory compliance analyst and consumer advocate. "
                    "Perform a detailed, quantitative analysis based *strictly* on the comprehensive JSON extracted data "
                    "and the provided raw document text. Do NOT provide general answers. Perform a detailed, root-cause "
                    "analysis. Explicitly state the top 3 driving factors with dollar amounts, fee names, and sections. "
                    "Mention specific potential tolerance issues against TRID rules and industry norms. Give specific, "
                    "quantitative data and actionable insights.\n\n"
                    f"--- EXTRACTED COMPREHENSIVE DOCUMENT DATA (JSON) ---\n{json.dumps(data, indent=2)}\n\n"
                    f"--- RAW DOCUMENT TEXT ---\n{st.session_state.raw_text[:8000]}..." # provide even more raw text
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
