import datetime
import io
import os
import urllib.parse
import feedparser
from fpdf import FPDF
from google import genai
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Konnect A Trade - Operations Center",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("💼 Konnect A Trade: Commodity Trading Operations Center")

# ---------------------------------------------------------
# GLOBAL CONFIGURATION & NAVIGATION
# ---------------------------------------------------------
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1UQ4kVTro1DLIkELVvZUQEoq-NpmlHZG58cGWclVckxE/edit?gid=0#gid=0"

module = st.sidebar.selectbox(
    "Select Operations Module",
    [
        "1. Incoterms Landed Cost & Margin Calculator",
        "2. PDF Trade Document Generator (SCO)",
        "3. Smart Buyer Due Diligence & Lead Scoring",
        "4. Message Assistant & 1-Click Action Triggers",
        "5. Automated Deal Pipeline & CRM Board",
        "6. Vessel Laycan & Demurrage Logistics Tracker",
        "7. Trade Finance, L/C Risk & Fraud Engine",
    ],
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔑 Gemini AI API Configuration")
gemini_api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")


# ---------------------------------------------------------
# HELPER CLASS 1: EXECUTIVE SCO PDF GENERATOR
# ---------------------------------------------------------
class SCO_PDF(FPDF):

    def __init__(self, logo_bytes=None):
        super().__init__()
        self.logo_bytes = logo_bytes

    def header(self):
        logo_rendered = False

        if self.logo_bytes:
            try:
                self.image(self.logo_bytes, 10, 8, w=40)
                logo_rendered = True
            except Exception:
                pass

        if not logo_rendered:
            if os.path.exists("logo.jpeg"):
                self.image("logo.jpeg", 10, 8, w=40)
                logo_rendered = True
            elif os.path.exists("logo.jpg"):
                self.image("logo.jpg", 10, 8, w=40)
                logo_rendered = True
            elif os.path.exists("logo.png"):
                self.image("logo.png", 10, 8, w=40)
                logo_rendered = True

        if logo_rendered:
            self.set_y(42)
        else:
            self.set_y(15)

        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(
            0,
            5,
            "Global Physical Commodity Sourcing & Trade Intermediation",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        self.ln(4)
        self.set_draw_color(15, 45, 90)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(
            0,
            10,
            f"Page {self.page_no()} | Confidential Soft Corporate Offer -"
            " Konnect A trade.com",
            align="C",
        )


def create_sco_pdf(data, logo_bytes=None):
    pdf = SCO_PDF(logo_bytes=logo_bytes)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_fill_color(240, 244, 250)
    pdf.set_draw_color(210, 220, 235)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(15, 45, 90)
    pdf.cell(
        0,
        10,
        "  SOFT CORPORATE OFFER (SCO)",
        border=1,
        fill=True,
        align="L",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(
        0,
        5,
        f"Ref Code: KNT-SCO-{data['date'].replace('-', '')}-001",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.cell(0, 5, f"Issue Date: {data['date']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(
        0, 5, f"Offer Validity: {data['validity']}", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 45, 90)
    pdf.cell(
        0, 6, "1. ISSUED TO (BUYER INFORMATION)", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(
        0,
        5,
        f"Buyer Representative: {data['buyer_name']}",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.cell(
        0,
        5,
        f"Company Name: {data['company_name']}",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 45, 90)
    pdf.cell(
        0,
        6,
        "2. COMMODITY & COMMERCIAL SPECIFICATIONS",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(15, 45, 90)
    pdf.set_text_color(255, 255, 255)
    pdf.set_draw_color(200, 200, 200)

    pdf.cell(
        60, 7, "  Parameter", border=1, fill=True, new_x="RIGHT", new_y="TOP"
    )
    pdf.cell(
        130,
        7,
        "  Specification / Trade Term",
        border=1,
        fill=True,
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.set_font("Helvetica", "", 9)
    table_data = [
        ("Commodity", str(data["commodity"])),
        ("Target Quantity", f"{data['quantity']:,.2f} MT (+/- 5%)"),
        ("Unit Price", f"${data['price']:,.2f} USD / MT"),
        ("Delivery Incoterm", f"{data['incoterm']} - {data['discharge_port']}"),
        ("Loading Port", str(data["load_port"])),
        ("Laycan Window", str(data["laycan"])),
        ("Quality Inspection", "SGS / Cotecna at Load Port (Seller expense)"),
        ("Payment Terms", str(data["payment_term"])),
    ]

    for idx, (item, val) in enumerate(table_data):
        if idx % 2 == 0:
            pdf.set_fill_color(248, 250, 253)
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.set_text_color(50, 50, 50)
        pdf.cell(60, 6.5, f"  {item}", border=1, fill=True, new_x="RIGHT", new_y="TOP")
        pdf.set_text_color(10, 10, 10)
        pdf.cell(
            130, 6.5, f"  {val}", border=1, fill=True, new_x="LMARGIN", new_y="NEXT"
        )

    pdf.ln(7)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 45, 90)
    pdf.cell(
        0, 6, "3. PROCEDURAL TERMS & CONDITIONS", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(70, 70, 70)
    terms_text = (
        "1. Buyer issues ICPO / LOI matching or accepting the parameters outlined"
        " in this SCO.\n2. Seller issues Full Corporate Offer (FCO) alongside"
        " draft Sales & Purchase Agreement (SPA).\n3. Both parties sign SPA;"
        " Buyer's bank opens operative financial instrument within 5 banking"
        " days.\n4. Quality & Quantity Inspection by SGS/Cotecna takes place at"
        " load port prior to vessel departure."
    )
    pdf.multi_cell(0, 4.5, terms_text)
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(15, 45, 90)
    pdf.cell(
        95, 5, "Issued by (Seller Representative):", new_x="RIGHT", new_y="TOP"
    )
    pdf.cell(
        95, 5, "Accepted & Confirmed by (Buyer):", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.ln(12)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        95,
        5,
        "________________________________________",
        new_x="RIGHT",
        new_y="TOP",
    )
    pdf.cell(
        95,
        5,
        "________________________________________",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(
        95, 5, "Konnect A trade.com Desk Officer", new_x="RIGHT", new_y="TOP"
    )
    pdf.cell(
        95,
        5,
        f"Authorized Signatory ({data['company_name']})",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    return bytes(pdf.output())


# ---------------------------------------------------------
# HELPER CLASS 2: LANDED COST ANALYSIS PDF GENERATOR
# ---------------------------------------------------------
class Cost_PDF(FPDF):

    def __init__(self, logo_bytes=None):
        super().__init__()
        self.logo_bytes = logo_bytes

    def header(self):
        logo_rendered = False
        if self.logo_bytes:
            try:
                self.image(self.logo_bytes, 10, 8, w=40)
                logo_rendered = True
            except Exception:
                pass

        if not logo_rendered:
            if os.path.exists("logo.jpeg"):
                self.image("logo.jpeg", 10, 8, w=40)
                logo_rendered = True
            elif os.path.exists("logo.jpg"):
                self.image("logo.jpg", 10, 8, w=40)
                logo_rendered = True
            elif os.path.exists("logo.png"):
                self.image("logo.png", 10, 8, w=40)
                logo_rendered = True

        if logo_rendered:
            self.set_y(42)
        else:
            self.set_y(15)

        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(
            0,
            5,
            "Global Physical Commodity Sourcing & Trade Intermediation",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.ln(4)
        self.set_draw_color(15, 45, 90)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(
            0,
            10,
            f"Page {self.page_no()} | Confidential Landed Cost Analysis - Konnect"
            " A trade.com",
            align="C",
        )


def create_landed_cost_pdf(breakdown_df, metrics_data, logo_bytes=None):
    pdf = Cost_PDF(logo_bytes=logo_bytes)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_fill_color(240, 244, 250)
    pdf.set_draw_color(210, 220, 235)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(15, 45, 90)
    pdf.cell(
        0,
        10,
        "  INCOTERMS LANDED COST & FINANCIAL MARGIN REPORT",
        border=1,
        fill=True,
        align="L",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 45, 90)
    pdf.cell(
        0,
        6,
        "1. EXECUTIVE SUMMARY & FINANCIAL METRICS",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(30, 30, 30)

    pdf.cell(
        95,
        6,
        f"Landed CIF Cost: ${metrics_data['cif_cost']:.2f} / MT",
        new_x="RIGHT",
        new_y="TOP",
    )
    pdf.cell(
        95,
        6,
        f"Proposed Buyer Quote: ${metrics_data['target_cif']:.2f} / MT",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.cell(
        95,
        6,
        f"Total Cost incl. Comm: ${metrics_data['total_cost']:.2f} / MT",
        new_x="RIGHT",
        new_y="TOP",
    )
    pdf.cell(
        95,
        6,
        f"Gross Profit Margin: ${metrics_data['margin_mt']:.2f} / MT",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.cell(
        95,
        6,
        f"Target Order Volume: {metrics_data['volume']:,.2f} MT",
        new_x="RIGHT",
        new_y="TOP",
    )
    pdf.cell(
        95,
        6,
        f"Total Shipment Profit: ${metrics_data['total_profit']:,.2f}",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 45, 90)
    pdf.cell(
        0, 6, "2. ITEMIZED COST STRUCTURE BREAKDOWN", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(15, 45, 90)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(
        70, 7, "  Cost Component", border=1, fill=True, new_x="RIGHT", new_y="TOP"
    )
    pdf.cell(
        60, 7, "  Per MT ($)", border=1, fill=True, new_x="RIGHT", new_y="TOP"
    )
    pdf.cell(
        60,
        7,
        "  Total Order Cargo ($)",
        border=1,
        fill=True,
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.set_font("Helvetica", "", 8.5)
    for idx, row in breakdown_df.iterrows():
        if idx % 2 == 0:
            pdf.set_fill_color(248, 250, 253)
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.set_text_color(50, 50, 50)
        pdf.cell(
            70,
            6.5,
            f"  {row['Component']}",
            border=1,
            fill=True,
            new_x="RIGHT",
            new_y="TOP",
        )
        pdf.cell(
            60,
            6.5,
            (
                f"  ${row['Per MT ($)'] if isinstance(row['Per MT ($)'], (int, float)) else row['Per MT ($)']}"
            ),
            border=1,
            fill=True,
            new_x="RIGHT",
            new_y="TOP",
        )
        pdf.cell(
            60,
            6.5,
            (
                f"  ${row['Total Order Cargo ($)']:,.2f}"
                if isinstance(row["Total Order Cargo ($)"], (int, float))
                else f"  {row['Total Order Cargo ($)']}"
            ),
            border=1,
            fill=True,
            new_x="LMARGIN",
            new_y="NEXT",
        )

    return bytes(pdf.output())


# ---------------------------------------------------------
# HELPER CLASS 3: TRADE FINANCE AUDIT PDF GENERATOR
# ---------------------------------------------------------
class Finance_PDF(FPDF):

    def __init__(self, logo_bytes=None):
        super().__init__()
        self.logo_bytes = logo_bytes

    def header(self):
        logo_rendered = False
        if self.logo_bytes:
            try:
                self.image(self.logo_bytes, 10, 8, w=40)
                logo_rendered = True
            except Exception:
                pass

        if not logo_rendered:
            if os.path.exists("logo.jpeg"):
                self.image("logo.jpeg", 10, 8, w=40)
                logo_rendered = True
            elif os.path.exists("logo.jpg"):
                self.image("logo.jpg", 10, 8, w=40)
                logo_rendered = True
            elif os.path.exists("logo.png"):
                self.image("logo.png", 10, 8, w=40)
                logo_rendered = True

        if logo_rendered:
            self.set_y(42)
        else:
            self.set_y(15)

        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(
            0,
            5,
            "Global Physical Commodity Sourcing & Trade Intermediation",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.ln(4)
        self.set_draw_color(15, 45, 90)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(
            0,
            10,
            f"Page {self.page_no()} | Confidential Trade Finance Audit - Konnect"
            " A trade.com",
            align="C",
        )


def create_trade_finance_pdf(lc_number, metrics_data, cost_breakdown_df, logo_bytes=None):
    pdf = Finance_PDF(logo_bytes=logo_bytes)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_fill_color(240, 244, 250)
    pdf.set_draw_color(210, 220, 235)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(15, 45, 90)
    pdf.cell(
        0,
        10,
        f"  TRADE FINANCE & L/C RISK AUDIT REPORT ({lc_number})",
        border=1,
        fill=True,
        align="L",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 45, 90)
    pdf.cell(
        0,
        6,
        "1. FINANCIAL YIELD & RISK SCORECARD",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(30, 30, 30)

    pdf.cell(
        95,
        6,
        f"Gross L/C Value: ${metrics_data['face_value']:,.2f}",
        new_x="RIGHT",
        new_y="TOP",
    )
    pdf.cell(
        95,
        6,
        f"Trade Risk Score: {metrics_data['risk_score']} / 100",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.cell(
        95,
        6,
        f"Financing & Bank Fees: -${metrics_data['total_fees']:,.2f}",
        new_x="RIGHT",
        new_y="TOP",
    )
    pdf.cell(
        95,
        6,
        f"UCP 600 Cut-Off: {metrics_data['cutoff']}",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.cell(
        95,
        6,
        f"Net Receivable Yield: ${metrics_data['net_proceeds']:,.2f}",
        new_x="RIGHT",
        new_y="TOP",
    )
    pdf.cell(
        95,
        6,
        f"Effective Cost Rate: {metrics_data['cost_pct']:.2f}%",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(15, 45, 90)
    pdf.cell(
        0, 6, "2. ITEMIZED FINANCING & BANK TARIFF DEDUCTIONS", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(15, 45, 90)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(
        120, 7, "  Fee / Tariff Category", border=1, fill=True, new_x="RIGHT", new_y="TOP"
    )
    pdf.cell(
        70, 7, "  Deduction Amount ($ USD)", border=1, fill=True, new_x="LMARGIN", new_y="NEXT"
    )

    pdf.set_font("Helvetica", "", 8.5)
    for idx, row in cost_breakdown_df.iterrows():
        if idx % 2 == 0:
            pdf.set_fill_color(248, 250, 253)
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.set_text_color(50, 50, 50)
        pdf.cell(
            120,
            6.5,
            f"  {row['Fee Category']}",
            border=1,
            fill=True,
            new_x="RIGHT",
            new_y="TOP",
        )
        pdf.cell(
            70,
            6.5,
            f"  ${row['Amount ($ USD)']:,.2f}",
            border=1,
            fill=True,
            new_x="LMARGIN",
            new_y="NEXT",
        )

    return bytes(pdf.output())


# ---------------------------------------------------------
# MODULE 1: INCOTERMS LANDED COST & MARGIN CALCULATOR
# ---------------------------------------------------------
if module == "1. Incoterms Landed Cost & Margin Calculator":
    st.header("🧮 Incoterms Landed Cost & Financial Margin Calculator")
    st.markdown(
        "Convert raw supplier FOB quotes into accurate CIF pricing and evaluate"
        " deal margins instantly."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📥 Input Commercial Variables")
        fob_price = st.number_input(
            "Base FOB Price ($/MT):", min_value=0.0, value=420.0, step=5.0
        )
        ocean_freight = st.number_input(
            "Bulk Vessel Ocean Freight ($/MT):", min_value=0.0, value=38.0, step=1.0
        )
        insurance_rate = (
            st.number_input(
                "Maritime Insurance Rate (%):",
                min_value=0.00,
                value=0.35,
                step=0.05,
            )
            / 100
        )
        insurance_coverage = (
            st.number_input(
                "Insurance Coverage Multiplier (%):",
                min_value=100.0,
                value=110.0,
                step=5.0,
            )
            / 100
        )
        commission = st.number_input(
            "Intermediary Commission ($/MT):", min_value=0.0, value=3.0, step=0.5
        )
        volume_mt = st.number_input(
            "Target Order Volume (MT):", min_value=1.0, value=12500.0, step=500.0
        )
        target_cif_quote = st.number_input(
            "Proposed Buyer CIF Price Quote ($/MT):",
            min_value=0.0,
            value=475.0,
            step=5.0,
        )

    cif_cost_per_mt = (fob_price + ocean_freight) + (
        (fob_price + ocean_freight) * insurance_coverage * insurance_rate
    )
    total_landed_cost_per_mt = cif_cost_per_mt + commission
    margin_per_mt = target_cif_quote - total_landed_cost_per_mt
    total_margin_usd = margin_per_mt * volume_mt
    gross_revenue_usd = target_cif_quote * volume_mt
    breakeven_cif_quote = total_landed_cost_per_mt

    with col2:
        st.subheader("📊 Output Financial Metrics")
        m1, m2 = st.columns(2)
        m1.metric("Landed CIF Cost ($/MT)", f"${cif_cost_per_mt:.2f}")
        m2.metric(
            "Total Cost incl. Comm ($/MT)", f"${total_landed_cost_per_mt:.2f}"
        )

        m3, m4 = st.columns(2)
        m3.metric(
            "Gross Profit Margin ($/MT)",
            f"${margin_per_mt:.2f}",
            delta=f"{margin_per_mt:.2f}",
        )
        m4.metric(
            "Total Shipment Profit ($)",
            f"${total_margin_usd:,.2f}",
            delta=f"${total_margin_usd:,.2f}",
        )

        st.metric(
            "Breakeven Quote Threshold ($/MT CIF)", f"${breakeven_cif_quote:.2f}"
        )

    st.markdown("---")
    st.subheader("📋 Comprehensive Cost Structure Breakdown")
    breakdown_df = pd.DataFrame({
        "Component": [
            "1. Base FOB Price",
            "2. Ocean Freight",
            "3. Maritime Insurance",
            "4. Net CIF Cost",
            "5. Intermediary Commission",
            "6. Total Landed Cost",
            "7. Proposed Sale Price",
            "8. Gross Profit Margin",
        ],
        "Per MT ($)": [
            fob_price,
            ocean_freight,
            cif_cost_per_mt - (fob_price + ocean_freight),
            cif_cost_per_mt,
            commission,
            total_landed_cost_per_mt,
            target_cif_quote,
            margin_per_mt,
        ],
        "Total Order Cargo ($)": [
            fob_price * volume_mt,
            ocean_freight * volume_mt,
            (cif_cost_per_mt - (fob_price + ocean_freight)) * volume_mt,
            cif_cost_per_mt * volume_mt,
            commission * volume_mt,
            total_landed_cost_per_mt * volume_mt,
            gross_revenue_usd,
            total_margin_usd,
        ],
    })
    st.table(breakdown_df)

    st.markdown("---")
    st.subheader("📄 Export Commercial Report")
    metrics_export = {
        "cif_cost": cif_cost_per_mt,
        "total_cost": total_landed_cost_per_mt,
        "margin_mt": margin_per_mt,
        "total_profit": total_margin_usd,
        "volume": volume_mt,
        "target_cif": target_cif_quote,
    }

    try:
        pdf_report_bytes = create_landed_cost_pdf(breakdown_df, metrics_export)
        st.download_button(
            label="📥 Download Landed Cost Analysis Report (PDF)",
            data=pdf_report_bytes,
            file_name=(
                f"Landed_Cost_Analysis_{datetime.date.today().strftime('%Y%m%d')}.pdf"
            ),
            mime="application/pdf",
        )
    except Exception as e:
        st.error(f"Error generating PDF report: {e}")


# ---------------------------------------------------------
# MODULE 2: PDF TRADE DOCUMENT GENERATOR (SCO)
# ---------------------------------------------------------
elif module == "2. PDF Trade Document Generator (SCO)":
    st.header("📄 Soft Corporate Offer (SCO) PDF Generator")
    st.markdown(
        "Generate official, legal-grade SCO documentation formatted for bulk"
        " buyers."
    )

    uploaded_logo = st.file_uploader(
        "Upload Company Logo (PNG or JPG, optional):", type=["png", "jpg", "jpeg"]
    )

    with st.form("sco_form"):
        c1, c2 = st.columns(2)
        with c1:
            buyer_name = st.text_input("Buyer Representative Name:", "John Doe")
            company_name = st.text_input(
                "Buyer Company Name:", "Global Grain Imports LLC"
            )
            commodity = st.selectbox(
                "Commodity:",
                [
                    "ICUMSA 45 Sugar",
                    "Non-Basmati Rice",
                    "Yellow Soybeans",
                    "Crude Palm Oil",
                    "Milling Wheat",
                ],
            )
            quantity = st.number_input(
                "Volume (Metric Tons):", min_value=100.0, value=12500.0, step=500.0
            )
            price = st.number_input(
                "Offered Unit Price ($/MT):", min_value=1.0, value=475.0, step=5.0
            )

        with c2:
            incoterm = st.selectbox("Incoterm 2020:", ["CIF", "FOB", "ASWP"])
            load_port = st.text_input("Loading Port:", "Santos, Brazil")
            discharge_port = st.text_input("Discharge Port:", "Jebel Ali, UAE")
            laycan = st.text_input(
                "Laycan Window:", "15 - 30 Days Post L/C Opening"
            )
            payment_term = st.selectbox(
                "Payment Instrument:",
                ["Irrevocable L/C at Sight", "Confirmed SBLC", "DLC / Escrow"],
            )
            date_str = st.date_input("Document Date").strftime("%Y-%m-%d")
            validity_str = st.date_input("Offer Validity Date").strftime("%Y-%m-%d")

        submit_sco = st.form_submit_button("🔨 Generate Official SCO PDF")

    if submit_sco:
        sco_data = {
            "buyer_name": buyer_name,
            "company_name": company_name,
            "commodity": commodity,
            "quantity": quantity,
            "price": price,
            "incoterm": incoterm,
            "load_port": load_port,
            "discharge_port": discharge_port,
            "laycan": laycan,
            "payment_term": payment_term,
            "date": date_str,
            "validity": validity_str,
        }

        logo_buffer = None
        if uploaded_logo is not None:
            logo_buffer = io.BytesIO(uploaded_logo.getvalue())

        try:
            pdf_bytes = create_sco_pdf(sco_data, logo_bytes=logo_buffer)
            st.success("Soft Corporate Offer (SCO) generated successfully!")

            st.download_button(
                label="📥 Download Official SCO PDF Document",
                data=pdf_bytes,
                file_name=f"SCO_{company_name.replace(' ', '_')}_{date_str}.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error(f"Error generating PDF: {e}")


# ---------------------------------------------------------
# MODULE 3: SMART BUYER DUE DILIGENCE & LEAD SCORING
# ---------------------------------------------------------
elif module == "3. Smart Buyer Due Diligence & Lead Scoring":
    st.header("🔍 Smart Buyer Verification & Lead Scoring Engine")
    st.markdown(
        "Screen prospective buyers to filter out daisy-chain brokers and focus on"
        " high-ticket importers."
    )

    if "lead_db" not in st.session_state:
        st.session_state["lead_db"] = []

    c1, c2 = st.columns([1, 1])

    with c1:
        st.subheader("📋 Lead Verification Checklist")
        lead_name = st.text_input("Lead Name / Contact:", "Ahmed Al-Maktoum")
        lead_company = st.text_input(
            "Lead Company:", "Middle East Commodity Trading"
        )

        check_domain = st.checkbox(
            "Corporate Email / Domain Verified (+20 pts)", value=True
        )
        check_loi = st.checkbox(
            "Official LOI / ICPO Provided on Letterhead (+30 pts)", value=True
        )
        buyer_type = st.radio(
            "Buyer Entity Type:",
            ["Verified Direct End-Buyer (+20 pts)", "Intermediary Broker (+5 pts)"],
        )
        check_bcl = st.checkbox(
            "Bank Comfort Letter (BCL) / RWA Issued (+30 pts)", value=False
        )

        score = 0
        if check_domain:
            score += 20
        if check_loi:
            score += 30
        if "Direct End-Buyer" in buyer_type:
            score += 20
        else:
            score += 5
        if check_bcl:
            score += 30

    with c2:
        st.subheader("📊 Qualification Result")
        st.metric("Total Qualification Score", f"{score} / 100")

        if score >= 80:
            status_badge = "🟢 Verified Importer (High Priority)"
            st.success(f"Status: {status_badge}")
            st.info(
                "Action: Issue Soft Corporate Offer (SCO) immediately and request"
                " LOI/ICPO verification."
            )
        elif score >= 50:
            status_badge = "🟡 Intermediary Broker (Proceed with Caution)"
            st.warning(f"Status: {status_badge}")
            st.info(
                "Action: Require non-circumvention agreement (NCNDA) before"
                " disclosing supplier specs."
            )
        else:
            status_badge = "🔴 High-Risk / Unverified Lead"
            st.error(f"Status: {status_badge}")
            st.info(
                "Action: Request proof of funds (BCL/RWA) before spending"
                " operational resources."
            )

        if st.button("💾 Save Lead Score to Session DB"):
            st.session_state["lead_db"].append({
                "Company": lead_company,
                "Contact": lead_name,
                "Score": score,
                "Status": status_badge,
            })
            st.success("Lead score record stored!")

    if st.session_state["lead_db"]:
        st.markdown("---")
        st.subheader("📋 Scored Leads Preview")
        st.dataframe(
            pd.DataFrame(st.session_state["lead_db"]), use_container_width=True
        )


# ---------------------------------------------------------
# MODULE 4: MESSAGE ASSISTANT & 1-CLICK ACTION TRIGGERS
# ---------------------------------------------------------
elif module == "4. Message Assistant & 1-Click Action Triggers":
    st.header("💬 Trade Response Generator & 1-Click Messaging")
    st.markdown(
        "Draft trade quotes using Gemini AI, then dispatch via 1-click WhatsApp"
        " or Gmail links."
    )

    col1, col2 = st.columns(2)

    with col1:
        buyer_name = st.text_input("Buyer Contact Name:", "Carlos Silva")
        recipient_email = st.text_input(
            "Recipient Email:", "carlos@buyercompany.com"
        )
        recipient_phone = st.text_input(
            "Recipient Phone (International format):", "+353871234567"
        )
        commodity = st.selectbox(
            "Commodity", ["ICUMSA 45 Sugar", "Soybeans", "Rice", "Edible Oils"]
        )
        quoted_price = st.number_input(
            "Quoted CIF Price ($/MT):", min_value=1.0, value=480.0
        )
        discharge_port = st.text_input("Destination Port:", "Rotterdam")

    with col2:
        incoming_inquiry = st.text_area(
            "Paste Incoming Buyer Message / Inquiry:",
            "Need 12,500 MT ICUMSA 45 Sugar CIF Rotterdam. What are your terms and"
            " payment instrument requirement?",
        )

    if st.button("⚡ Generate AI Trade Reply"):
        if not gemini_api_key:
            st.error("Please enter your Gemini API Key in the left sidebar!")
        else:
            try:
                client = genai.Client(api_key=gemini_api_key)
                prompt = (
                    "Act as a senior commodity trader at Konnect A Trade. Draft a"
                    f" professional trade message to buyer {buyer_name}.\nDetails:\n-"
                    f" Commodity: {commodity}\n- Quoted CIF Price: ${quoted_price}"
                    f" USD/MT to {discharge_port}\n- Payment Terms: Irrevocable L/C at"
                    f" Sight / SBLC\n- Incoming Inquiry: {incoming_inquiry}\n\nKeep the"
                    " reply concise, professional, and clear on next steps (asking for"
                    " LOI/ICPO)."
                )

                with st.spinner("Gemini 3.6 Flash is drafting response..."):
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt,
                    )
                    st.session_state["ai_reply_text"] = response.text
                    st.success("Reply generated successfully!")

            except Exception as e:
                st.error(f"Error calling Gemini API: {e}")

    if "ai_reply_text" in st.session_state:
        st.markdown("---")
        st.subheader("📋 Generated Reply:")
        st.text_area(
            "Generated Trade Message:",
            value=st.session_state["ai_reply_text"],
            height=200,
        )

        reply_text = st.session_state["ai_reply_text"]
        encoded_reply = urllib.parse.quote(reply_text)
        clean_phone = "".join(filter(str.isdigit, recipient_phone))

        wa_url = f"https://wa.me/{clean_phone}?text={encoded_reply}"
        mailto_url = (
            f"mailto:{recipient_email}?subject=Trade%20Inquiry%20Quote%20-%20Konnect%20A%20Trade&body={encoded_reply}"
        )

        st.subheader("🚀 1-Click Direct Action Dispatch")
        btn_col1, btn_col2 = st.columns(2)

        with btn_col1:
            st.link_button(
                "📲 Send via WhatsApp Web", wa_url, use_container_width=True
            )
        with btn_col2:
            st.link_button(
                "✉️ Send via Gmail / Email Client",
                mailto_url,
                use_container_width=True,
            )


# ---------------------------------------------------------
# MODULE 5: AUTOMATED DEAL PIPELINE & CRM BOARD
# ---------------------------------------------------------
elif module == "5. Automated Deal Pipeline & CRM Board":
    st.header("📊 Automated Commodity Deal Pipeline & CRM")
    st.markdown(
        "Manage ongoing multi-week trade cycles and sync status changes directly"
        " with Google Sheets."
    )

    PIPELINE_STAGES = [
        "1. Initial Contact",
        "2. LOI Received",
        "3. SCO Issued",
        "4. SPA Signed",
        "5. L/C Issued & Loading",
    ]

    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=GOOGLE_SHEET_URL, ttl=0)

        st.subheader("📋 Current Active Pipeline")
        st.dataframe(df, use_container_width=True)

        st.markdown("---")
        st.subheader("🔄 Update Deal Stage")

        if not df.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                row_index = st.selectbox(
                    "Select Buyer / Deal Row:",
                    df.index,
                    format_func=lambda x: (
                        f"Row {x}: {df.iloc[x].get('Name', 'Unknown')}"
                        f" ({df.iloc[x].get('Company', 'No Company')})"
                    ),
                )
            with col2:
                new_stage = st.selectbox("Select New Stage:", PIPELINE_STAGES)
            with col3:
                st.write("")
                st.write("")
                if st.button("💾 Push Status Update to Google Sheets"):
                    try:
                        df.at[row_index, "Stage"] = new_stage
                        conn.update(spreadsheet=GOOGLE_SHEET_URL, data=df)
                        st.success(
                            f"Updated Row {row_index} status to '{new_stage}' in Google"
                            " Sheets!"
                        )
                    except Exception as update_err:
                        st.error(f"Failed to update Google Sheet: {update_err}")
        else:
            st.warning("Google Sheet appears to be empty.")

    except Exception as e:
        st.error(f"Error connecting to Google Sheets CRM: {e}")


# ---------------------------------------------------------
# MODULE 6: VESSEL LAYCAN & DEMURRAGE LOGISTICS TRACKER
# ---------------------------------------------------------
elif module == "6. Vessel Laycan & Demurrage Logistics Tracker":
    st.header("🚢 Vessel Laycan & Demurrage Logistics Tracker")
    st.markdown(
        "Monitor vessel nominations, laycan compliance windows, and automated"
        " laytime demurrage/despatch financial exposure."
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📋 Vessel Nomination & Voyage Details")
        vessel_name = st.text_input("Vessel Name:", value="MV Ocean Fortune")
        imo_number = st.text_input("IMO Number:", value="9876543")

        c_port1, c_port2 = st.columns(2)
        with c_port1:
            origin_port = st.text_input("Origin Port (Load):", value="Santos, Brazil")
        with c_port2:
            dest_port = st.text_input(
                "Destination Port (Discharge):", value="Jebel Ali, UAE"
            )

        st.markdown("---")
        st.subheader("⏱️ Laycan & Laytime Parameters")
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            laycan_start = st.date_input(
                "Laycan Start Date:", value=datetime.date(2026, 10, 1)
            )
        with d_col2:
            laycan_end = st.date_input(
                "Laycan End Date:", value=datetime.date(2026, 10, 15)
            )

        h_col1, h_col2 = st.columns(2)
        with h_col1:
            allowed_hours = st.number_input(
                "Allowed Laytime (Hours):", min_value=1.0, value=72.0, step=6.0
            )
        with h_col2:
            actual_hours = st.number_input(
                "Actual Hours Spent Loading:", min_value=0.0, value=96.0, step=6.0
            )

        demurrage_rate = st.number_input(
            "Agreed Demurrage Rate ($/day):",
            min_value=0.0,
            value=20000.0,
            step=1000.0,
        )

    today = datetime.date.today()
    if today < laycan_start:
        status_badge = "🟢 On Schedule (Pre-Laycan)"
        status_state = "success"
    elif laycan_start <= today <= laycan_end:
        status_badge = "🟡 Laycan Window Active"
        status_state = "warning"
    else:
        status_badge = "🔴 Laycan Window Closed / Expired"
        status_state = "error"

    laytime_diff_hours = actual_hours - allowed_hours
    hourly_demurrage_rate = demurrage_rate / 24.0

    if laytime_diff_hours > 0:
        financial_status = "Demurrage Penalty Owed"
        net_financial_amount = laytime_diff_hours * hourly_demurrage_rate
    elif laytime_diff_hours < 0:
        financial_status = "Despatch Bonus Earned"
        despatch_hourly_rate = hourly_demurrage_rate * 0.5
        net_financial_amount = abs(laytime_diff_hours) * despatch_hourly_rate
    else:
        financial_status = "Exact Laytime Used (Zero Penalty)"
        net_financial_amount = 0.0

    laytime_efficiency = (
        (allowed_hours / actual_hours) * 100 if actual_hours > 0 else 100.0
    )

    with col2:
        st.subheader("📊 Operational & Financial Risk Summary")

        if status_state == "success":
            st.success(f"Vessel Status: {status_badge}")
        elif status_state == "warning":
            st.warning(f"Vessel Status: {status_badge}")
        else:
            st.error(f"Vessel Status: {status_badge}")

        m1, m2 = st.columns(2)
        m1.metric("Vessel / IMO", f"{vessel_name}", f"IMO: {imo_number}")
        m2.metric(
            "Laytime Efficiency",
            f"{laytime_efficiency:.1f}%",
            f"{laytime_diff_hours:+.1f} hrs vs allowed",
        )

        m3, m4 = st.columns(2)
        if financial_status == "Demurrage Penalty Owed":
            m3.metric(
                "Net Financial Exposure",
                f"-${net_financial_amount:,.2f}",
                financial_status,
                delta_color="inverse",
            )
        elif financial_status == "Despatch Bonus Earned":
            m3.metric(
                "Net Financial Exposure",
                f"+${net_financial_amount:,.2f}",
                financial_status,
                delta_color="normal",
            )
        else:
            m3.metric("Net Financial Exposure", "$0.00", financial_status)

        m4.metric("Voyage Route", f"{origin_port}", f"➡️ {dest_port}")

        st.markdown("---")
        st.subheader("📅 Cargo Shipping Milestone Schedule")

        milestones_df = pd.DataFrame({
            "Milestone Stage": [
                "1. Laycan Start Window",
                "2. Laycan Deadline Cut-off",
                "3. Vessel Arrival at Port (Estimated)",
                "4. Notice of Readiness (NOR) Tendered",
                "5. Loading Operations Completed",
                "6. Bill of Lading (B/L) Issuance",
            ],
            "Target / Event Date": [
                laycan_start.strftime("%Y-%m-%d"),
                laycan_end.strftime("%Y-%m-%d"),
                laycan_start.strftime("%Y-%m-%d"),
                laycan_start.strftime("%Y-%m-%d") + " +06:00 HRS",
                f"{actual_hours} Hours Total Laytime Logged",
                "Pending Port Captain Sign-off",
            ],
            "Operational Status": [
                "Confirmed",
                "Strict Deadline",
                "In Transit",
                "Pending Arrival",
                "Calculated",
                "Pending",
            ],
        })
        st.dataframe(milestones_df, use_container_width=True)


# ---------------------------------------------------------
# MODULE 7: TRADE FINANCE, L/C RISK & FRAUD ENGINE
# ---------------------------------------------------------
elif module == "7. Trade Finance, L/C Risk & Fraud Engine":
    st.header("💳 Trade Finance, L/C Risk & Fraud Mitigation Engine")
    st.markdown(
        "Monitor UCP 600 compliance timelines, evaluate usance discounting yields, "
        "and audit document consistency with beginner-friendly AI guidance."
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📥 L/C Instrument & Bank Parameters")
        lc_number = st.text_input("L/C Reference Number:", value="LC-2026-8891")
        lc_face_value = st.number_input(
            "Master L/C Face Value ($ USD):", min_value=1000.0, value=6000000.0, step=50000.0
        )
        
        bank_tier = st.selectbox(
            "Issuing Bank Standing:",
            [
                "Top 100 Global Prime Bank (Low Risk)",
                "Rated Investment Grade Bank (Medium Risk)",
                "Unrated / Offshore Bank (High Risk)",
            ],
        )
        
        lc_type = st.selectbox(
            "Payment Instrument Type:",
            [
                "Irrevocable Confirmed L/C at Sight",
                "Irrevocable Unconfirmed Usance L/C",
                "Transferable L/C at Sight",
                "Standby L/C (SBLC)",
            ],
        )

        usance_days = st.selectbox(
            "Usance Payment Tenure (Days Post-B/L):",
            [0, 30, 60, 90, 120, 180],
            index=2,
        )

        # Transferable L/C Margin Protection Sub-Calculator
        if "Transferable" in lc_type:
            st.markdown("---")
            st.subheader("🔄 Transferable L/C Margin Isolator")
            supplier_lc_value = st.number_input(
                "Transferred Supplier L/C Value ($ USD):",
                min_value=1000.0,
                value=5937500.0,
                step=50000.0,
            )
            retained_brokerage_margin = lc_face_value - supplier_lc_value
            st.info(f"💡 Retained Brokerage Margin: **${retained_brokerage_margin:,.2f} USD** (Protected via Invoice Substitution step)")

        st.markdown("---")
        st.subheader("⏱️ UCP 600 Timeline Parameters")
        
        c_date1, c_date2 = st.columns(2)
        with c_date1:
            bl_date = st.date_input("Expected / Actual B/L Date:", value=datetime.date(2026, 10, 5))
        with c_date2:
            lds_date = st.date_input("Latest Date of Shipment (LDS):", value=datetime.date(2026, 10, 12))

        lc_expiry_date = st.date_input("L/C Expiry Date:", value=datetime.date(2026, 11, 2))

    # Business Logic Calculations
    sofr_benchmark = 3.85 / 100
    bank_spread = 2.65 / 100
    total_usance_rate = sofr_benchmark + bank_spread

    discounting_cost = lc_face_value * total_usance_rate * (usance_days / 360.0)
    advising_fee = max(150.0, min(1500.0, lc_face_value * 0.00125))
    discrepancy_allowance = 150.0
    courier_swift_fee = 120.0

    if "Unrated" in bank_tier:
        confirmation_fee = lc_face_value * (0.025 * ((usance_days if usance_days > 0 else 30) / 360.0))
    elif "Rated Investment" in bank_tier:
        confirmation_fee = lc_face_value * (0.0075 * ((usance_days if usance_days > 0 else 30) / 360.0))
    else:
        confirmation_fee = 0.0

    total_financing_costs = discounting_cost + advising_fee + discrepancy_allowance + courier_swift_fee + confirmation_fee
    net_lc_proceeds = lc_face_value - total_financing_costs
    financing_cost_pct = (total_financing_costs / lc_face_value) * 100

    # UCP 600 Timeline & Cutoff
    presentation_cutoff = min(bl_date + datetime.timedelta(days=21), lc_expiry_date)
    days_to_lds = (lds_date - bl_date).days

    if days_to_lds >= 7:
        lds_status_badge = "🟢 Safe Shipment Timeline"
        lds_state = "success"
    elif 2 <= days_to_lds < 7:
        lds_status_badge = "🟡 Tight Loading Window"
        lds_state = "warning"
    else:
        lds_status_badge = "🔴 Critical LDS Breach Risk"
        lds_state = "error"

    # Risk Score
    bank_score = 30 if "Top 100" in bank_tier else (20 if "Rated" in bank_tier else 5)
    lc_score = 25 if "Confirmed" in lc_type else (15 if "Transferable" in lc_type else 5)

    with col2:
        st.subheader("🛡️ Trade Fraud Verification & Document Matching Checklist")
        check_sgs = st.checkbox("SGS / Cotecna Quality & Quantity Verified (+15 pts)", value=True)
        check_direct_bl = st.checkbox("Direct Clean 'Shipped on Board' B/L Issued (+10 pts)", value=True)
        check_imo = st.checkbox("Vessel IMO Verified & Active P&I Insurance (+10 pts)", value=True)
        check_sanctions = st.checkbox("Ports & Counterparties Clear OFAC/EU Sanctions (+10 pts)", value=True)

        st.markdown("**UCP 600 Document Consistency Pre-Flight Check:**")
        chk1 = st.checkbox("Invoice commodity text matches L/C Field 45A verbatim", value=True)
        chk2 = st.checkbox("Insurance Policy covers 110% of CIF value (Institute Cargo Clauses A)", value=True)
        chk3 = st.checkbox("Phytosanitary & Certificate of Origin issued by accredited authority", value=True)

        doc_score = (15 if check_sgs else 0) + (10 if check_direct_bl else 0)
        vessel_score = (10 if check_imo else 0) + (10 if check_sanctions else 0)
        total_risk_score = bank_score + lc_score + doc_score + vessel_score

        st.markdown("---")
        st.subheader("📊 Financial Exposure & Risk Results")

        if total_risk_score >= 80:
            st.success(f"Trade Risk Score: {total_risk_score} / 100 — LOW RISK (Approved for Execution)")
        elif total_risk_score >= 50:
            st.warning(f"Trade Risk Score: {total_risk_score} / 100 — MODERATE RISK (Require Confirmation)")
        else:
            st.error(f"Trade Risk Score: {total_risk_score} / 100 — HIGH RISK (Halt Transaction)")

        if lds_state == "success":
            st.success(f"Shipment Status: {lds_status_badge}")
        elif lds_state == "warning":
            st.warning(f"Shipment Status: {lds_status_badge}")
        else:
            st.error(f"Shipment Status: {lds_status_badge}")

        m1, m2 = st.columns(2)
        m1.metric("Gross Master L/C Value", f"${lc_face_value:,.2f}")
        m2.metric("Total Financing & Bank Fees", f"-${total_financing_costs:,.2f}")

        m3, m4 = st.columns(2)
        m3.metric("Net Receivable Yield", f"${net_lc_proceeds:,.2f}")
        m4.metric("Presentation Cut-Off Date", presentation_cutoff.strftime("%Y-%m-%d"))

    # Plain-English Guidance Box
    st.markdown("---")
    st.subheader("💡 Plain-English Trade Desk Guidance")
    st.info(
        f"**Desk Summary:** On this **${lc_face_value:,.2f}** transaction, bank financing and usance fees total "
        f"**${total_financing_costs:,.2f}** ({financing_cost_pct:.2f}% of cargo value). Your net payout upon presentation "
        f"will be **${net_proceeds:,.2f}**. Ensure your profit margin calculated in Module 1 exceeds **${total_financing_costs:,.2f}** "
        f"to preserve net deal profitability." if 'net_proceeds' in locals() else 
        f"**Desk Summary:** On this **${lc_face_value:,.2f}** transaction, bank financing and usance fees total "
        f"**${total_financing_costs:,.2f}** ({financing_cost_pct:.2f}% of cargo value). Your net bank payout will be **${net_lc_proceeds:,.2f}**. "
        f"Ensure your gross profit in Module 1 is greater than **${total_financing_costs:,.2f}** to stay in the green!"
    )

    # Actionable Warning & Fix Box
    st.subheader("🚨 Actionable Desk Guidance & Fixes")
    if total_risk_score < 80:
        st.warning(
            "**Action Required to Lower Risk:** Request the buyer to issue a Confirmed L/C via a Top-50 Prime Bank "
            "(e.g., HSBC, BNP Paribas, Citibank) to eliminate issuing bank credit default risk."
        )
    if days_to_lds < 7:
        st.error(
            "**Timeline Warning:** Your expected B/L date is very close to the Latest Date of Shipment (LDS). "
            "Instruct the buyer immediately to issue an official L/C Amendment (SWIFT MT707) extending the LDS by 10 days before vessel loading."
        )
    if total_risk_score >= 80 and days_to_lds >= 7:
        st.success("✅ All risk parameters and UCP 600 timeline metrics are green. Safe to proceed with document preparation.")

    # SWIFT Message Guide
    with st.expander("📖 Beginner SWIFT Message Reference Guide"):
        st.markdown("""
        * **SWIFT MT700:** Official Issue of Documentary Credit (Master L/C).
        * **SWIFT MT707:** Official L/C Amendment (used to extend LDS or change terms).
        * **SWIFT MT799:** Free Format SWIFT message used for pre-advice or Bank Comfort / Ready Willing & Able (RWA).
        * **SWIFT MT760:** Guarantee / Standby L/C / Performance Bond issuance.
        """)

    # Itemized Breakdown
    st.markdown("---")
    st.subheader("📋 Itemized L/C Financing Cost Breakdown")
    cost_breakdown_df = pd.DataFrame({
        "Fee Category": [
            "1. Usance Discounting Fee (SOFR 3.85% + Spread 2.65%)",
            "2. Advising & Processing Fee (0.125%)",
            "3. Confirmation Fee (Bank Risk Premium)",
            "4. Bank Discrepancy Reserve",
            "5. SWIFT & Courier Transmission Fee",
            "6. Total Financial Deductions",
        ],
        "Amount ($ USD)": [
            discounting_cost,
            advising_fee,
            confirmation_fee,
            discrepancy_allowance,
            courier_swift_fee,
            total_financing_costs,
        ],
    })
    st.table(cost_breakdown_df)

    # PDF Audit Report Export
    st.markdown("---")
    st.subheader("📄 Export Trade Finance Audit Report")
    finance_metrics_export = {
        "face_value": lc_face_value,
        "risk_score": total_risk_score,
        "total_fees": total_financing_costs,
        "cutoff": presentation_cutoff.strftime("%Y-%m-%d"),
        "net_proceeds": net_lc_proceeds,
        "cost_pct": financing_cost_pct,
    }

    try:
        pdf_audit_bytes = create_trade_finance_pdf(lc_number, finance_metrics_export, cost_breakdown_df)
        st.download_button(
            label="📥 Download L/C Finance & Risk Audit Report (PDF)",
            data=pdf_audit_bytes,
            file_name=f"Trade_Finance_Audit_{lc_number}_{datetime.date.today().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
        )
    except Exception as e:
        st.error(f"Error generating PDF audit report: {e}")