
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Solar + BESS Financial Model v3", layout="wide")

st.title("🔋 Advanced Renewable Energy Investment Tool (Portugal)")
st.subheader("Solar + BESS Behind-the-Meter & Collective Self-Consumption (ACC)")

st.markdown("""
This application models decentralized energy infrastructure under **Decree-Law 15/2022** and **99/2024**.
It includes generation forecasting, dynamic energy destination routing, investment metrics (IRR/NPV), 
and an automated critical feasibility assessment of the storage system (BESS).
""")

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

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Inputs & Technical Setup", 
    "📊 Financial Performance (Developer)", 
    "🤝 Anchor Tenant Business Case", 
    "🧐 BESS Critical Analysis"
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

# Variables for the Anchor Fee logic
total_third_party_sales_mwh = neighbors_consumed_mwh # Energy sold to surrounding tenants
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
# The developer pays out the variable fee to the Anchor Tenant as an extra operational cost
annual_opex = (total_capex * (opex_pct / 100)) + total_anchor_variable_fee_revenue
net_annual_cashflow = total_gross_revenue - annual_opex

# Project Cashflows (15 Years)
cashflows = [-total_capex] + [net_annual_cashflow] * 15
npv_value = calculate_npv(wacc, cashflows)
irr_value = calculate_irr(cashflows)

with tab2:
    st.header("📊 Production Forecast & Energy Destination")
    
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
    
    st.subheader("💰 Investment Metrics Summary")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Project CAPEX", f"€{total_capex:,.0f}")
    k2.metric("Net Annual Cash Flow", f"€{net_annual_cashflow:,.0f}")
    if irr_value:
        k3.metric("Project IRR (TIR - 15Y)", f"{irr_value*100:.2f}%")
    else:
        k3.metric("Project IRR (TIR)", "N/A")
    k4.metric(f"Project NPV (VAL @ {wacc*100:.1f}%)", f"€{npv_value:,.0f}")

with tab3:
    st.header("🤝 Anchor Tenant Comprehensive Business Case")
    
    annual_saving_per_kwh = max(0.0, market_retail_price - ppa_anchor)
    annual_anchor_savings = (anchor_consumed_mwh * 1000 * annual_saving_per_kwh) + (bess_allocated_mwh * 1000 * annual_saving_per_kwh * 0.5)
    total_anchor_annual_benefit = annual_anchor_savings + total_anchor_variable_fee_revenue
    
    col_a1, col_a2 = st.columns(2)
    col_a1.metric("Year 1 Direct Energy Savings", f"€{annual_anchor_savings:,.0f}")
    col_a2.metric("Year 1 Variable Roof Fee Earned", f"€{total_anchor_variable_fee_revenue:,.0f}")
    
    st.subheader("📈 15-Year Cumulative Savings & Fee Income for Anchor Tenant")
    anchor_years = list(range(1, 16))
    cum_benefits = []
    current_benefit = 0
    for y in anchor_years:
        # Assuming a 2% energy grid tariff inflation for realism
        current_benefit += (annual_anchor_savings * (1.02 ** (y - 1))) + total_anchor_variable_fee_revenue
        cum_benefits.append(current_benefit)
        
    st.area_chart(pd.DataFrame({"Year": anchor_years, "Cumulative Financial Benefit (€)": cum_benefits}).set_index("Year"))

with tab4:
    st.header("🧐 Critical Analysis: Does BESS Make Financial Sense?")
    
    # Simple mathematical comparison: BESS Cost vs Arbitrage Value
    bess_capex_cost = capex_bess
    bess_added_annual_revenue = rev_bess - (bess_allocated_mwh * 1000 * market_spill) # revenue minus what it would make if just spilled directly
    bess_simple_payback = bess_capex_cost / (bess_added_annual_revenue + 0.1) if bess_energy > 0 else 0
    
    st.subheader("📊 Battery Storage Financial Breakdown")
    c1, c2, c3 = st.columns(3)
    c1.metric("Specific BESS CAPEX Allocation", f"€{bess_capex_cost:,.0f}")
    c2.metric("Additional Annual Revenue from BESS", f"€{bess_added_annual_revenue:,.0f}")
    if bess_energy > 0:
        c3.metric("Isolated BESS Payback", f"{bess_simple_payback:.1f} Years")
    else:
        c3.metric("Isolated BESS Payback", "No BESS deployed")
        
    st.markdown("""
    ### 📝 Qualitative & Regulatory Critical Assessment
    
    #### 🟢 When BESS Makes Perfect Sense:
    1. **High Spread/Volatility in PPAs:** If the difference between the daytime solar capture price and evening peak consumption (ACC or Grid) is greater than **€0.08/kWh**, the arbitrage margin justifies the investment.
    2. **Grid Injection Constraints:** In Portugal, if E-REDES denies high grid injection capacity, a BESS acts as a 'buffer'. It stores the solar energy that would otherwise be forcedly clipped or wasted, allowing it to be dispatched legally during off-peak solar hours via the ACC framework.
    3. **Operational Upsell to Anchor:** The battery can be monetized implicitly by offering 'uninterruptible power' (UPS) or *Peak Shaving* services to the Anchor Tenant, boosting contract stickiness.
    
    #### 🔴 When BESS is a Financial Drag:
    1. **High Unitary Cost (>€450/kWh):** If the procurement cost of the storage system is high, the stand-alone payback of the battery stretches past 10-12 years, destroying overall project IRR.
    2. **High Direct ACC Absorption:** If your surrounding tenants (within 2-4km) consume **100% of the solar surplus in real-time** during the day, the battery is redundant. It is always more profitable to sell a solar kWh directly via an ACC PPA instantly than to store it (due to roundtrip efficiency losses of ~15%).
    
    #### ⚖️ Conclusion for this specific Configuration:
    """)
    
    if bess_energy == 0:
        st.info("De-congested profile: No battery is currently being simulated.")
    elif bess_simple_payback > 9.5:
        st.error(f"⚠️ **Red Light:** The standalone battery payback is **{bess_simple_payback:.1f} years**. Under current pricing assumptions, the BESS acts as a financial drag on the developer's IRR. Consider down-sizing the battery or negotiating lower equipment pricing.")
    else:
        st.success(f"💚 **Green Light:** The battery payback is **{bess_simple_payback:.1f} years**, which aligns well with a 15-year infrastructure project lifecycle. The BESS enhances project flexibility and locks in evening peak premium revenues.")
