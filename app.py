import streamlit as st
from google import genai

st.set_page_config(
    page_title="Konnect A Trade - Operations Center",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌾 Konnectatrade - CTRM Operations Center")
st.write("Commodity Trading & Risk Management | Agricultural Softs, Grains & Raw Materials")

# 1. Connection Test Expander (Collapsible)
with st.expander("🔑 Test Gemini API Key Connection", expanded=False):
    if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
        if st.button("Test Gemini API Call"):
            try:
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents="Say 'Gemini API is connected and working!'"
                )
                st.success(f"🤖 API Response: {response.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}")
    else:
        st.warning("GEMINI_API_KEY not found in Streamlit secrets.")

st.markdown("---")

# 2. Agricultural Commodity Market Analysis Module
st.header("📊 Agricultural Commodity Market Intelligence")
st.write("Generate real-time AI market analysis, risk factors, and trade structuring insights for softs and grains.")

col1, col2 = st.columns(2)

with col1:
    selected_commodity = st.selectbox(
        "Select Commodity",
        [
            "ICUMSA 45 Sugar",
            "GMO Soybeans",
            "Non-GMO Soybeans",
            "1121 Basmati Rice",
            "Yellow Corn",
            "Frozen Protein Products",
        ]
    )

with col2:
    analysis_focus = st.selectbox(
        "Analysis Focus",
        [
            "Global Supply & Demand Outlook",
            "Price Volatility & Risk Assessment",
            "Logistics & Shipping Cost Factors",
            "Contract & Trade Terms Recommendations"
        ]
    )

user_query = st.text_area(
    "Specific Trade Question or Market Condition (Optional)",
    placeholder="e.g., Evaluate CIF freight cost impact from South America or current export quota pressures."
)

if st.button("Generate AI Market Intelligence"):
    with st.spinner("Analyzing global trade data and market trends..."):
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

            prompt = f"""
            You are an expert senior commodity trading analyst and risk manager specializing in international agricultural softs and grains.
            
            Provide a professional market analysis report for:
            - Commodity: {selected_commodity}
            - Primary Focus: {analysis_focus}
            - Specific User Note: {user_query if user_query else 'Standard market overview'}

            Structure your response clearly with:
            1. Executive Summary & Market Sentiment
            2. Key Price Drivers & Supply Chain Factors
            3. Risk Management & Hedging Considerations
            4. Actionable Trade Structuring Advice (Incoterms, Payment Terms like LC)
            """

            # Automatic fallback model logic to prevent 503 traffic spikes
            try:
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt
                )
            except Exception:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )

            st.success("Analysis generated successfully!")
            st.markdown("---")
            st.markdown(response.text)

        except Exception as e:
            st.error(f"Failed to generate analysis: {e}")