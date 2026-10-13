import streamlit as st
from google import genai
import pandas as pd
import datetime

# Try importing OpenAI for multi-vendor backup
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

st.set_page_config(
    page_title="Konnectatrade - CTRM Operations Center",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🌾 Konnectatrade - CTRM Operations Center")
st.write("Commodity Trading & Risk Management | Global Softs, Grains, Rice & Proteins")

# Helper class to standardize AI responses across providers
class AIResponse:
    def __init__(self, text):
        self.text = text

# Multi-Vendor Robust Fallback Engine (Gemini -> OpenAI Backup)
def call_ai_with_failover(prompt):
    # 1. Try Google Gemini Models First
    if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            gemini_models = ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-2.5-flash"]
            for model_name in gemini_models:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    if response and response.text:
                        return response
                except Exception:
                    continue
        except Exception:
                    pass

    # 2. If Gemini fails or is busy (503), failover to OpenAI if configured
    if OPENAI_AVAILABLE and "OPENAI_API_KEY" in st.secrets and st.secrets["OPENAI_API_KEY"]:
        try:
            openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            completion = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            reply_text = completion.choices[0].message.content
            return AIResponse(reply_text)
        except Exception as e:
            raise Exception(f"All AI providers busy. Gemini 503 and OpenAI error: {e}")

    raise Exception("No valid API keys configured in st.secrets (Gemini or OpenAI).")

# Sidebar System Status & Quick Catalog Reference
with st.sidebar:
    st.header("⚙️ System Status")
    gemini_ok = "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]
    openai_ok = OPENAI_AVAILABLE and "OPENAI_API_KEY" in st.secrets and st.secrets["OPENAI_API_KEY"]
    
    if gemini_ok:
        st.success("Gemini API: Ready (Primary)")
    else:
        st.warning("Gemini API: Not Configured")

    if openai_ok:
        st.success("OpenAI API: Ready (Backup)")
    else:
        st.info("OpenAI API: Optional Backup")
        
    st.markdown("---")
    st.markdown("### 📋 Active Portfolio Categories")
    st.markdown("- **Sugar:** ICUMSA 45, ICUMSA 150, Refined Granulated, Brown, Organic")
    st.markdown("- **Grains & Oilseeds:** GMO/Non-GMO Soybeans, Yellow Corn")
    st.markdown("- **Rice:** Basmati (1121, 1509, Sharbati, US), Non-Basmati (Sona Masoori, Ponni, Samba, Matta, Idly, Kaima, Swarna), US Long-Grain, Calrose, Jasmine")
    st.markdown("- **Proteins:** Frozen Chicken, Beef & Pork")

# Comprehensive Multi-Tab Dashboard Structure
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Market Intelligence", 
    "✍️ Buyer Outreach & Messages", 
    "📄 Quotation & PDF Generator", 
    "📇 Contact CRM & Spreadsheet", 
    "📐 Risk & Incoterms Calculator", 
    "🔑 API Diagnostic"
])

# --- TAB 1: MARKET INTELLIGENCE ---
with tab1:
    st.header("Agricultural Commodity Market Intelligence")
    st.write("Generate real-time AI market analysis, price drivers, and trade structuring insights.")

    col1, col2 = st.columns(2)

    with col1:
        commodity_category = st.selectbox(
            "Select Commodity Category",
            ["Sugar Varieties", "Rice Varieties", "Grains & Oilseeds", "Frozen Meats"],
            key="cat_select"
        )

        if commodity_category == "Sugar Varieties":
            selected_commodity = st.selectbox(
                "Select Sugar Type",
                [
                    "Refined White Sugar (ICUMSA 45)",
                    "Crystal Sugar (ICUMSA 150)",
                    "Refined Granulated Sugar (Açúcar Refinado)",
                    "Brown Sugar (Açúcar Mascavo)",
                    "Organic Sugar (Açúcar Orgânico)"
                ],
                key="sugar_select"
            )
        elif commodity_category == "Rice Varieties":
            selected_commodity = st.selectbox(
                "Select Rice Variety",
                [
                    "Pusa Basmati 1121",
                    "Pusa Basmati 1509",
                    "Sharbati Basmati",
                    "Sona Masoori",
                    "Ponni (Raw & Boiled)",
                    "Jeera Samba / Seeraga Samba",
                    "Palakkad Matta (Rose Matta)",
                    "Idly Rice",
                    "Jeerakasala / Kaima",
                    "Swarna",
                    "Carolina Gold",
                    "Charleston Gold",
                    "Standard Long-Grain White Rice",
                    "Calrose Rice",
                    "U.S. Basmati & Texmati",
                    "U.S. Jasmine"
                ],
                key="rice_select"
            )
        elif commodity_category == "Grains & Oilseeds":
            selected_commodity = st.selectbox(
                "Select Grain / Oilseed",
                ["GMO Soybeans", "Non-GMO Soybeans", "Yellow Corn"],
                key="grain_select"
            )
        else:
            selected_commodity = st.selectbox(
                "Select Protein Product",
                ["Frozen Chicken Products", "Frozen Beef Products", "Frozen Pork Products"],
                key="protein_select"
            )

    with col2:
        analysis_focus = st.selectbox(
            "Analysis Focus",
            [
                "Global Supply & Demand Outlook",
                "Price Volatility & Risk Assessment",
                "Logistics & Shipping Cost Factors",
                "Contract & Trade Terms Recommendations"
            ],
            key="focus_select"
        )

    user_query = st.text_area(
        "Specific Trade Question or Market Condition (Optional)",
        placeholder="e.g., Evaluate CIF freight cost impact from origin ports or current export quota pressures.",
        key="market_query"
    )

    if st.button("Generate AI Market Intelligence", key="btn_market"):
        with st.spinner("Compiling market intelligence via multi-vendor failover..."):
            try:
                prompt = f"""
                You are an expert senior commodity trading analyst and risk manager specializing in international agricultural trade.
                
                Provide a concise, professional commodity market intelligence brief for:
                - Commodity: {selected_commodity}
                - Focus: {analysis_focus}
                - Note: {user_query if user_query else 'General overview'}

                Structure your response clearly with:
                1. Market Outlook & Sentiment
                2. Key Price Drivers & Supply Factors
                3. Risk & Hedging Summary
                4. Trade Structuring & Incoterm Advice (FOB/CIF, Payment terms like L/C at sight)
                """

                response = call_ai_with_failover(prompt)

                st.success("Analysis generated successfully!")
                st.markdown("---")
                st.markdown(response.text)

            except Exception as e:
                st.error(f"Connection failed: {e}")

# --- TAB 2: BUYER OUTREACH & MESSAGING ---
with tab2:
    st.header("AI Buyer Outreach & Prospecting Messages")
    st.write("Generate tailored B2B outreach messages for global procurement managers and sourcing decision-makers.")

    m_col1, m_col2 = st.columns(2)
    with m_col1:
        buyer_persona = st.selectbox(
            "Target Buyer Persona",
            ["Global Food Importer", "Supermarket Chain Sourcing Director", "Wholesale Grain/Sugar Distributor", "Food Processing Plant Manager"],
            key="buyer_pers"
        )
        target_commodity_msg = st.text_input("Promoted Commodity", value="ICUMSA 45 Sugar / Basmati Rice", key="msg_comm")
    with m_col2:
        outreach_channel = st.selectbox("Outreach Channel", ["LinkedIn Connection Request / InMail", "Cold Email Proposal", "Follow-up Message"], key="out_chan")
        tone = st.selectbox("Tone", ["Professional & Formal", "Direct & Commercial", "Consultative & Value-Driven"], key="out_tone")

    if st.button("Generate Outreach Message", key="btn_outreach"):
        with st.spinner("Drafting high-conversion trade message..."):
            try:
                msg_prompt = f"""
                Draft a professional B2B commodity trading outreach message for Konnectatrade (konnectatrade.com).
                - Target Persona: {buyer_persona}
                - Promoted Commodity: {target_commodity_msg}
                - Channel: {outreach_channel}
                - Tone: {tone}
                - Business: Connecting verified global suppliers with buyers under secure terms (LC at sight, FOB/CIF).
                Keep it engaging, concise, and structured with a clear call to action.
                """
                response = call_ai_with_failover(msg_prompt)
                st.success("Outreach message generated!")
                st.markdown("---")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Failed to generate message: {e}")

# --- TAB 3: QUOTATION & PDF GENERATOR ---
with tab3:
    st.header("Professional Trade Quotation Generator")
    st.write("Create formal, headed price quotations for buyers with export terms and banking conditions.")

    q_col1, q_col2 = st.columns(2)
    with q_col1:
        client_name = st.text_input("Buyer / Company Name", value="Global Procurement Corp", key="q_client")
        quotation_commodity = st.text_input("Commodity & Specification", value="Refined White Sugar ICUMSA 45", key="q_spec")
        quantity_mt = st.number_input("Quantity (Metric Tons)", value=12500.0, key="q_qty")
    with q_col2:
        unit_price = st.number_input("Unit Price ($/MT CIF)", value=485.00, key="q_price")
        incoterm_q = st.selectbox("Incoterm", ["CIF Destination Port", "FOB Origin Port", "CFR Port of Discharge"], key="q_inc")
        payment_term = st.selectbox("Payment Terms", ["Irrevocable, Confirmed L/C at Sight", "100% TT against shipping docs", "25% Advance, 75% against BL copy"], key="q_pay")

    total_quote_value = quantity_mt * unit_price

    quotation_text = f"""
==================================================
KONNECTATRADE - OFFICIAL COMMERCIAL QUOTATION
Website: www.konnectatrade.com | Dublin, Ireland
Date: {datetime.date.today().strftime('%B %d, %Y')}
==================================================

TO: {client_name}

We are pleased to submit our formal commercial offer as follows:

- Commodity: {quotation_commodity}
- Quantity: {quantity_mt:,.0f} Metric Tons (MT)
- Unit Price: ${unit_price:,.2f} / MT ({incoterm_q})
- Total Estimated Value: ${total_quote_value:,.2f} USD
- Payment Terms: {payment_term}
- Shipment: As per agreed contract schedule.

This quotation is valid for 5 banking days from issuance.

Authorized by Konnectatrade Operations Center
==================================================
"""

    st.text_area("Quotation Preview", value=quotation_text, height=250, key="q_preview")

    st.download_button(
        label="📥 Download Quotation (.txt / Print to PDF)",
        data=quotation_text,
        file_name=f"Konnectatrade_Quotation_{client_name.replace(' ', '_')}.txt",
        mime="text/plain",
        key="btn_download"
    )

# --- TAB 4: CONTACT CRM & SPREADSHEET ---
with tab4:
    st.header("Contact CRM & Spreadsheet Integration")
    st.write("Upload or link your procurement contact database (Excel/CSV) to manage buyer and supplier relationships.")

    uploaded_file = st.file_uploader("Upload Contact Spreadsheet (.csv or .xlsx)", type=["csv", "xlsx"], key="file_crm")
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_contacts = pd.read_csv(uploaded_file)
            else:
                df_contacts = pd.read_excel(uploaded_file)
            
            st.success(f"Successfully loaded {len(df_contacts)} contacts from spreadsheet!")
            st.dataframe(df_contacts, use_container_width=True)
        except Exception as e:
            st.error(f"Error reading file: {e}")
    else:
        st.info("💡 Tip: Upload your CSV or Excel contact file here to instantly view, search, and manage global buyers and suppliers directly inside your CTRM platform.")
        
        sample_df = pd.DataFrame({
            "Company": ["Global Foods Ltd", "EuroGrain S.A.", "Middle East Imports"],
            "Contact Person": ["John Smith", "Marie Dupont", "Ahmed Al-Mansoor"],
            "Commodity Interest": ["ICUMSA 45 Sugar", "Non-GMO Soybeans", "1121 Basmati Rice"],
            "Status": ["Active Negotiation", "Prospecting", "Contract Signed"]
        })
        st.write("**Sample Contact Directory Preview:**")
        st.dataframe(sample_df, use_container_width=True)

# --- TAB 5: RISK & INCOTERMS CALCULATOR ---
with tab5:
    st.header("Risk Exposure & Incoterms Cost Buildup")
    st.write("Calculate cargo financial exposure and FOB vs. CFR/CIF price buildups.")

    r_col1, r_col2 = st.columns(2)
    with r_col1:
        st.subheader("Cargo Exposure Calculator")
        cargo_tons = st.number_input("Cargo Volume (MT)", min_value=100.0, value=12500.0, step=500.0, key="exp_tons")
        contract_price = st.number_input("Unit Price ($/MT)", min_value=1.0, value=480.0, step=10.0, key="exp_price")
        total_exposure = cargo_tons * contract_price
        st.metric(label="Total Contract Value", value=f"${total_exposure:,.2f}")

    with r_col2:
        st.subheader("Incoterms Price Buildup")
        base_fob = st.number_input("Base FOB Price ($/MT)", value=450.0, key="inc_fob")
        freight_cost = st.number_input("Ocean Freight ($/MT)", value=45.0, key="inc_freight")
        insurance_cost = st.number_input("Marine Insurance ($/MT)", value=3.5, key="inc_ins")
        total_cif = base_fob + freight_cost + insurance_cost
        st.success(f"Calculated CIF Landed Price: **${total_cif:,.2f} / MT**")

# --- TAB 6: API DIAGNOSTIC ---
with tab6:
    st.header("Multi-Vendor API Diagnostic Center")
    if st.button("Run Full Multi-Vendor Connection Test", key="btn_diag"):
        try:
            prompt_diag = "Say 'Konnectatrade multi-vendor failover AI engine is connected and working!'"
            response = call_ai_with_failover(prompt_diag)
            st.success(f"🤖 AI Response: {response.text}")
        except Exception as e:
            st.error(f"Connection failed across all providers: {e}")