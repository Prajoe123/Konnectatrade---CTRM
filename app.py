import streamlit as st
from google import genai

st.set_page_config(
    page_title="Konnectatrade - CTRM Operations Center",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌾 Konnectatrade - CTRM Operations Center")
st.write("Commodity Trading & Risk Management | Agricultural Softs, Grains & Raw Materials")

# Sidebar for Global Settings / Connection status
with st.sidebar:
    st.header("⚙️ System Status")
    if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
        st.success("API Key: Loaded (Secrets)")
    else:
        st.error("API Key: Missing in Secrets")
        
    st.markdown("---")
    st.markdown("**Active Portfolio:**")
    st.markdown("- ICUMSA 45 Sugar")
    st.markdown("- Soybeans (GMO / Non-GMO)")
    st.markdown("- 1121 Basmati Rice")
    st.markdown("- Yellow Corn")
    st.markdown("- Frozen Protein Products")

# Organize app into professional operational tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Market Intelligence", 
    "📐 Risk & Exposure Calculator", 
    "🚢 Contract & Incoterms Pricing", 
    "🔑 API Connection Test"
])

# --- TAB 1: MARKET INTELLIGENCE ---
with tab1:
    st.header("Agricultural Commodity Market Intelligence")
    st.write("Generate real-time AI market analysis, risk factors, and trade structuring insights.")

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
        with st.spinner("Compiling market intelligence..."):
            try:
                client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

                prompt = f"""
                Provide a concise, professional commodity market intelligence brief for:
                - Commodity: {selected_commodity}
                - Focus: {analysis_focus}
                - Note: {user_query if user_query else 'General overview'}

                Keep the response structured and punchy with:
                1. Market Outlook & Sentiment
                2. Key Price Drivers
                3. Risk & Hedging Summary
                4. Trade Structuring & Incoterm Advice
                """

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
                st.error(f"Connection failed: {e}")

# --- TAB 2: RISK & EXPOSURE CALCULATOR ---
with tab2:
    st.header("Trade Risk & Price Exposure Management")
    st.write("Evaluate volume exposure, basis risk, and hedging buffers.")
    
    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        cargo_tons = st.number_input("Cargo Volume (Metric Tons)", min_value=100, value=12500, step=500)
    with r_col2:
        contract_price = st.number_input("Contract Unit Price ($/MT)", min_value=1.0, value=480.0, step=10.0)
    with r_col3:
        volatility_pct = st.slider("Estimated Volatility (%)", min_value=1.0, max_value=50.0, value=12.5)

    total_exposure = cargo_tons * contract_price
    st.metric(label="Total Contract Value Exposure", value=f"${total_exposure:,.2f}")
    
    st.info("💡 Tip: Use Tab 1 to generate specific hedging recommendations for this exposure level.")

# --- TAB 3: CONTRACT PRICING & INCOTERMS ---
with tab3:
    st.header("Incoterms & Freight Cost Structuring")
    st.write("Calculate FOB vs. CFR/CIF cost buildup factors.")

    incoterm = st.selectbox("Select Incoterm", ["FOB (Free on Board)", "CFR (Cost and Freight)", "CIF (Cost, Insurance & Freight)"])
    base_fob = st.number_input("Base FOB Price ($/MT)", value=450.0)
    
    if incoterm in ["CFR (Cost and Freight)", "CIF (Cost, Insurance & Freight)"]:
        freight_cost = st.number_input("Ocean Freight Cost ($/MT)", value=45.0)
    else:
        freight_cost = 0.0

    if incoterm == "CIF (Cost, Insurance & Freight)":
        insurance_cost = st.number_input("Marine Insurance Cost ($/MT)", value=3.5)
    else:
        insurance_cost = 0.0

    total_landed_cost = base_fob + freight_cost + insurance_cost
    st.success(f"Estimated Total Landed Price ({incoterm}): **${total_landed_cost:,.2f} / MT**")

# --- TAB 4: API CONNECTION TEST ---
with tab4:
    st.header("Gemini API Diagnostic Center")
    if st.button("Run Full API Connection Test"):
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents="Say 'Gemini API is connected and working!'"
            )
            st.success(f"🤖 API Response: {response.text}")
        except Exception as e:
            st.error(f"Connection failed: {e}")