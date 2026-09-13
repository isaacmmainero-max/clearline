import json
import streamlit as st
from anthropic import Anthropic
from pypdf import PdfReader

st.set_page_config(page_title="ClearLine - Mortgage Document Analyzer", layout="wide")
st.title("ClearLine: Interactive Mortgage Disclosure & Compliance Companion")
st.markdown("Upload your Loan Estimate (LE) or Closing Disclosure (CD) PDF for an instant compliance audit.")

uploaded_file = st.file_uploader("Upload Mortgage Document (PDF)", type=["pdf"])

raw_doc_text = ""
if uploaded_file is not None:
    try:
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                raw_doc_text += extracted + "\n"
        st.success(f"Successfully extracted text from {uploaded_file.name}!")
    except Exception as e:
        st.error(f"Error reading PDF file: {e}")
else:
    raw_doc_text = st.text_area("Or Paste Raw Document Text Here:", height=200)

if st.button("Analyze Document", type="primary"):
    if not raw_doc_text:
        st.warning("Please upload a PDF or enter document text to analyze.")
    else:
        with st.spinner("Analyzing document structure and checking compliance rules..."):
            try:
                api_key = st.secrets["ANTHROPIC_API_KEY"]
                client = Anthropic(api_key=api_key)
                system_prompt = (
                    "You are 'ClearLine', an expert AI mortgage compliance analyst and consumer advocate. "
                    "Your task is to analyze the provided text of a TRID Loan Estimate (LE) or Closing Disclosure (CD). "
                    "Extract all financial values, fees, and tolerance buckets strictly into a valid JSON schema format "
                    "containing loan_overview, closing_costs_summary, and fee_tolerance_buckets."
                )

                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1500,
                    system=system_prompt,
                    messages=[{"role": "user", "content": f"Please parse this mortgage document text:\n\n{raw_doc_text}"}]
                )
                
                st.subheader("Analysis Results & Compliance Audit")
                st.code(response.content[0].text, language="json")
            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")