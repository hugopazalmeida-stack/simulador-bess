# simulador-bess
🔋 Solar + BESS Investment &amp; Viability Tool for the Portuguese Energy Market (&lt;1MW). Models Anchor Tenant PPAs, Collective Self-Consumption (ACC) energy flows, and storage arbitrage under DL 15/2022.
# 🔋 Solar + BESS ACC Financial Viability Tool (Portugal)

An advanced investment evaluation and decision-making application tailored for decentralized energy projects in Portugal under **Decree-Law 15/2022** and **Decree-Law 99/2024**. 

This tool is designed for energy consultants and infrastructure investors (HNWIs) to screen decentralized solar and storage opportunities up to 1MW behind-the-meter.

## 🚀 Features

* **PV Generation Forecast:** Estimates annual MWh output based on roof availability and regional specific yields.
* **Dynamic Energy Routing:** Models the exact destination flow of generated electrons (Anchor Tenant direct consumption, BESS storage, ACC neighbor sharing, or Grid spill).
* **Advanced Financial Metrics:** Computes Project IRR (TIR), NPV (VAL) based on custom WACC/Discount rates, and simple Payback periods.
* **BESS Critical Audit:** Features an automated "smart traffic-light" evaluation system that isolates battery costs vs. arbitrage margins to verify if storage makes financial sense.
* **Anchor Tenant Business Case:** Generates a 15-year cumulative savings and variable fee income projection to act as a data-driven sales pitch for asset owners (€0.01/kWh third-party fee routing included).

## 🛠️ Tech Stack & Setup

Built with **Python** and **Streamlit**. 

To run this application locally, ensure you have Python installed and run the following commands in your terminal:

```bash
# 1. Install dependencies
pip install streamlit pandas numpy

# 2. Run the application
streamlit run app.py
