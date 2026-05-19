# Let's rewrite the Streamlit app code to include:
# 1. An input field for the "Project Name" (Nome do Projeto).
# 2. A script-based print feature or standard layout that allows exporting/printing the most important data easily.
# Streamlit doesn't have a native "direct to local printer" button due to browser sandbox security, 
# but we can implement a clean layout inside a standard button function or a layout optimized for printing (e.g., using a text/markdown area or a st.download_button for a clean text report, or st.button with js for windows.print()).
# Let's use a standard web printing trick: st.button linked to an HTML/JS print mechanism or a clean st.download_button for a textual report that can be saved/printed instantly. Even better, let's offer a clean text summary inside the app that users can copy/print, or a file download. Let's make a beautiful "Generate Report" download button or view.

app_code_v4 = """
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Solar + BESS Financial Model v4", layout="wide")

st.title("🔋 Advanced Renewable Energy Investment Tool (Portugal)")
st.subheader("Solar + BESS Behind-the-Meter & Collective Self-Consumption (ACC)")

st.markdown(\"\"\"
This application models decentralized energy infrastructure under **Decree-Law 15/2022** and **99/2024**.
Includes generation forecasting, investment metrics (IRR/NPV), and an automated report generator.
\"\"\")

# Helper financial functions
def calculate_npv(wacc, cashflows):
    return sum(cf / (1 + wacc)**t for t, cf in enumerate(cashflows))

def calculate_irr(cashflows, max_iter=1000):
    r = 0.1
    for _ in range(max_iter):
        npv = calculate_npv(r, cashflows)
        if abs(npv) < 1e-2:
            return r
        deriv = sum(-t * cf / (1 + r)**(t+1) for t, cf in enumerate(cashflows))
        if deriv == 0:
            break
        r_new = r - npv / deriv
        if abs(r_new - r) < 1e-5:
            return r_new
        r = r_new
    return None

# --- TOP LEVEL PROJECT IDENTIFICATION ---
st.header("📋 Project Identification")
project_name = st.text_input("Project Name / Nome do Projeto", value="Project Solar + BESS Alcoutim")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Inputs & Technical Setup", 
    "📊 Financial Performance", 
    "🤝 Anchor Tenant Business Case", 
    "🧐 BESS Critical Analysis",
    "🖨️ Export & Print Report"
])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🏢 Technical Parameters")
        roof_size = st.number_input("Available Roof Space (m²)", min_value=100, max_value=100000, value=6000, step=500)
        voltage_level = st.selectbox("Grid Connection Level", ["Low Voltage (BT) <= 2km share limit", "Medium Voltage (MT) <= 4km share limit"])
        
        max_pv_estimated = int(roof_size / 7)
        st.caption(f"Estimated max physical PV capacity for this roof area: ~{max_pv_estimated} kWp")
        
        pv_capacity = st.number_input("Proposed Solar PV Capacity (kWp)", min_value=10, max_value=5000, value=min(max_pv_estimated, 1000), step=50)
        bess_power = st.number_input("BESS Power Capacity (kW)", min_value=0, max_value=2000, value=500, step=50)
        bess_energy = st.number_input("BESS Storage Capacity (kWh)", min_value=0, max_value=4000, value=1000, step=100)

    with col2:
        st.header("💰 Financial Assumptions")
        unit_capex_pv = st.number_input("Solar PV CAPEX (€/kWp)", min_value=500, max_value=1500, value=750, step=50)
        unit_capex_bess = st.number_input("BESS CAPEX (€/kWh)", min_value=300, max_value=1000, value=450, step=50)
        wacc = st.slider("Investor WACC / Discount Rate (%)", 4.0, 15.0, 7.5, 0.5) / 100.0
        
        st.subheader("Commercial Tariffs (€/kWh)")
        ppa_anchor = st.slider("Anchor Tenant PPA Price", 0.05, 0.25, 0.09, 0.01)
        market_retail_price = st.slider("Anchor Current Retail Price (Grid)", 0.12, 0.30, 0.16, 0.01)
        ppa_neighbors = st.slider("Neighbors (ACC) PPA Price", 0.05, 0.25, 0.11, 0.01)
        market_spill = st.slider("Grid Spill Price (OMIE Spot)", 0.02, 0.15, 0.05, 0.01)
        
        anchor_roof_fee = st.slider("Anchor Variable Fee for Third Party Sales (€/kWh sold)", 0.00, 0.05, 0.01, 0.005)
        opex_pct = st.slider("Annual OPEX (% of total CAPEX)", 1.0, 5.0, 2.0, 0.5)

    st.header("📈 Consumption Profiling")
    col3, col4, col5 = st.columns(3)
    with col3:
        anchor_demand = st.number_input("Anchor Tenant Annual Demand (MWh)", min_value=50, value=1500, step=50)
    with col4:
        neighbors_demand = st.number_input("Neighbors (ACC) Total Demand (MWh)", min_value=50, value=2500, step=50)
    with col5:
        solar_yield = st.number_input("Specific Yield (kWh/kWp/year)", min_value=1000, max_value=2000, value=1500, step=50)

# Calculations Engine
annual_production_mwh = (pv_capacity * solar_yield) / 1000

# Distribution heuristics
anchor_direct_pct = min(0.55, (anchor_demand / (annual_production_mwh + 0.1)))
anchor_consumed_mwh = min(annual_production_mwh * anchor_direct_pct, anchor_demand)

bess_annual_throughput_mwh = (bess_energy * 300 * 0.85) / 1000 if bess_energy > 0 else 0
bess_allocated_mwh = min(bess_annual_throughput_mwh, annual_production_mwh - anchor_consumed_mwh)

remaining_for_neighbors = max(0.0, annual_production_mwh - anchor_consumed_mwh - bess_allocated_mwh)
neighbors_consumed_mwh = min(remaining_for_neighbors, neighbors_demand)
spill_mwh = max(0.0, remaining_for_neighbors - neighbors_consumed_mwh)

total_third_party_sales_mwh = neighbors_consumed_mwh
total_anchor_variable_fee_revenue = total_third_party_sales_mwh * 1000 * anchor_roof_fee

# Developer Revenues
capex_pv = pv_capacity * unit_capex_pv
capex_bess = bess_energy * unit_capex_bess
total_capex = capex_pv + capex_bess

rev_anchor = anchor_consumed_mwh * 1000 * ppa_anchor
rev_bess = bess_allocated_mwh * 1000 * max(ppa_anchor * 1.25, ppa_neighbors * 1.15)
rev_neighbors = neighbors_consumed_mwh * 1000 * ppa_neighbors
rev_spill = spill_mwh * 1000 * market_spill

total_gross_revenue = rev_anchor + rev_bess + rev_neighbors + rev_spill
annual_opex = (total_capex * (opex_pct / 100)) + total_anchor_variable_fee_revenue
net_annual_cashflow = total_gross_revenue - annual_opex

cashflows = [-total_capex] + [net_annual_cashflow] * 15
npv_value = calculate_npv(wacc, cashflows)
irr_value = calculate_irr(cashflows)
payback = total_capex / (net_annual_cashflow + 0.1)

# Savings Calculation
annual_saving_per_kwh = max(0.0, market_retail_price - ppa_anchor)
annual_anchor_savings = (anchor_consumed_mwh * 1000 * annual_saving_per_kwh) + (bess_allocated_mwh * 1000 * annual_saving_per_kwh * 0.5)
total_anchor_annual_benefit = annual_anchor_savings + total_anchor_variable_fee_revenue

with tab2:
    st.header("📊 Developer Financial Performance")
    m1, m2, m3 = st.columns(3)
    m1.metric("Predicted Annual PV Production", f"{annual_production_mwh:,.1f} MWh")
    m2.metric("Total Shared with Neighbors (ACC)", f"{neighbors_consumed_mwh:,.1f} MWh")
    m3.metric("Annual Roof Fee Paid to Anchor", f"€{total_anchor_variable_fee_revenue:,.0f}")
    
    st.subheader("📈 Energy Flow Destination Chart")
    flow_data = pd.DataFrame({
        "Energy Destination": ["Anchor Tenant (Direct)", "Stored in BESS", "Sleeved to Neighbors (ACC)", "Spilled to Grid (Spot)"],
        "MWh per Year": [anchor_consumed_mwh, bess_allocated_mwh, neighbors_consumed_mwh, spill_mwh]
    }).set_index("Energy Destination")
    st.bar_chart(flow_data)

with tab3:
    st.header("🤝 Anchor Tenant Comprehensive Business Case")
    col_a1, col_a2 = st.columns(2)
    col_a1.metric("Year 1 Direct Energy Savings", f"€{annual_anchor_savings:,.0f}")
    col_a2.metric("Year 1 Variable Roof Fee Earned", f"€{total_anchor_variable_fee_revenue:,.0f}")

with tab4:
    st.header("🧐 Critical Analysis: Does BESS Make Financial Sense?")
    bess_capex_cost = capex_bess
    bess_added_annual_revenue = rev_bess - (bess_allocated_mwh * 1000 * market_spill)
    bess_simple_payback = bess_capex_cost / (bess_added_annual_revenue + 0.1) if bess_energy > 0 else 0
    st.metric("Isolated BESS Payback", f"{bess_simple_payback:.1f} Years" if bess_energy > 0 else "No BESS")

# --- NEW TAB: PRINT / EXPORT REPORT ---
with tab5:
    st.header("🖨️ Project Summary Report")
    st.write("Review the compiled report below. You can save it as a text file or print this web page directly.")
    
    # Constructing a clean text report layout
    report_text = f\"\"\"==================================================
INVESTMENT & VIABILITY REPORT: {project_name.upper()}
==================================================

[1] PROJECT SUMMARY & IDENTIFICATION
--------------------------------------------------
* Project Name: {project_name}
* Grid Connection Level: {voltage_level}
* Roof Space Evaluated: {roof_size:,} m²

[2] TECHNICAL CONFIGURATION
--------------------------------------------------
* Proposed Solar PV: {pv_capacity:,} kWp
* Expected Annual PV Generation: {annual_production_mwh:,.1f} MWh
* BESS Power Capacity: {bess_power:,} kW
* BESS Storage Capacity: {bess_energy:,} kWh

[3] DEVELOPER FINANCIAL METRICS (15-YEAR HORIZON)
--------------------------------------------------
* Total Estimated Project CAPEX: €{total_capex:,.0f}
* Net Annual Cash Flow: €{net_annual_cashflow:,.0f}
* Project IRR (TIR): {f'{irr_value*100:.2f}%' if irr_value else 'N/A'}
* Project NPV (VAL @ {wacc*100:.1f}%): €{npv_value:,.0f}
* Simple Payback Period: {payback:.1f} Years

[4] COMMERCIAL ENERGY ROUTING & REVENUES
--------------------------------------------------
* Anchor Tenant Direct Consumption: {anchor_consumed_mwh:,.1f} MWh/yr (Revenue: €{rev_anchor:,.0f}/yr)
* BESS Optimization Allocation: {bess_allocated_mwh:,.1f} MWh/yr (Revenue: €{rev_bess:,.0f}/yr)
* Shared with Neighbors (ACC Framework): {neighbors_consumed_mwh:,.1f} MWh/yr (Revenue: €{rev_neighbors:,.0f}/yr)
* Grid Spill Excess (Spot Market): {spill_mwh:,.1f} MWh/yr (Revenue: €{rev_spill:,.0f}/yr)

[5] ANCHOR TENANT BENEFIT PACKAGE (YEAR 1)
--------------------------------------------------
* Direct Energy Bill Savings: €{annual_anchor_savings:,.0f}/yr
* Variable Roof Fee Revenue (€{anchor_roof_fee}/kWh): €{total_anchor_variable_fee_revenue:,.0f}/yr
* Total Annual Anchor Financial Benefit: €{total_anchor_annual_benefit:,.0f}/yr
* Cumulative 15-Year Benefit Potential: €{total_anchor_annual_benefit * 15:,.0f}

[6] STORAGE (BESS) AUDIT VERDICT
--------------------------------------------------
* Standalone BESS CAPEX: €{bess_capex_cost:,.0f}
* BESS Incremental Revenue: €{bess_added_annual_revenue:,.0f}/yr
* Isolated Battery Payback: {f'{bess_simple_payback:.1f} Years' if bess_energy > 0 else 'N/A'}

Report compiled automatically by the Solar+BESS ACC Decentrailzed Utility Engine.
==================================================
\"\"\"
    
    st.text_area("Report Preview", value=report_text, height=450)
    
    # Download button for the text report
    st.download_button(
        label="💾 Download Clean Report (.txt)",
        data=report_text,
        file_name=f"Report_{project_name.replace(' ', '_')}.txt",
        mime="text/plain"
    )
    
    st.markdown(\"\"\"
    💡 **Tip to Print to PDF:** To print a fully styled report layout, you can simply press **Ctrl + P** (Windows) or **Cmd + P** (Mac) right now in your browser to save this web tab directly to a PDF or physical printer!
    \"\"\")
"""

with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_code_v4)

print("App code v4 written successfully with project naming and download/print features.")
