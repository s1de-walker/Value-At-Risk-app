import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime, timedelta

# Title
st.title("Value at Risk")
st.subheader("How much could I lose over a given period, for a given probability?")

# Sidebar Instructions
st.sidebar.header("📖   How to Use Inputs")
st.sidebar.write("- **Analysis Period:** Defines the period for computing price changes.")
st.sidebar.write("- **Percentile:** Defines the risk threshold for VaR.")
st.sidebar.write("- **Monte Carlo Simulations:** More simulations improve accuracy but increase computation time.")

# Initialize Session State
if "var_result" not in st.session_state:
    st.session_state.var_result = None
if "hl_var_result" not in st.session_state:
    st.session_state.hl_var_result = None

# User Inputs
stock = st.text_input("Enter Stock/ETF Symbol:", value="SPY")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Select Start Date:", value=datetime.today() - timedelta(days=500))
with col2:
    end_date = st.date_input("Select End Date:", value=datetime.today())

col1, col2, col3 = st.columns(3)
with col1:
    analysis_period = st.number_input("Select Analysis Period (Days):", min_value=1, max_value=30, value=5)
with col2:
    var_percentile = st.number_input("Select VaR Percentile:", min_value=0.01, max_value=99.99, value=95.00, format="%.2f")
with col3:
    simulations = st.number_input("Number of Monte Carlo Simulations:", min_value=100, max_value=10000, value=2000)

# Button to Run VaR Calculation
if st.button("Calculate VaR"):
    data = yf.download(stock, start=start_date, end=end_date)["Close"]
    if not data.empty:
        returns = data.pct_change(analysis_period).dropna()
        mu, sigma = returns.mean(), returns.std()
        simulated_returns = np.random.normal(mu, sigma, simulations)
        VaR_value = np.percentile(simulated_returns, 100 - var_percentile) * 100
        CVaR_value = simulated_returns[simulated_returns < (VaR_value / 100)].mean() * 100
        st.session_state.var_result = {"VaR": VaR_value, "CVaR": CVaR_value, "Percentile": var_percentile}
    else:
        st.error("Error fetching data. Please check the stock symbol.")

# Button to Run High-Low VaR Calculation
if st.button("Calculate High-Low VaR"):
    data_hl = yf.download(stock, start=start_date, end=end_date)
    if not data_hl.empty and "High" in data_hl.columns and "Low" in data_hl.columns:
        hl_returns = (data_hl["High"] - data_hl["Low"]) / data_hl["Low"]
        hl_returns = hl_returns.rolling(analysis_period).sum().dropna()
        mu_hl, sigma_hl = hl_returns.mean(), hl_returns.std()
        simulated_hl_returns = np.random.normal(mu_hl, sigma_hl, simulations)
        VaR_hl_value = np.percentile(simulated_hl_returns, 100 - var_percentile) * 100
        CVaR_hl_value = simulated_hl_returns[simulated_hl_returns < (VaR_hl_value / 100)].mean() * 100
        st.session_state.hl_var_result = {"VaR": VaR_hl_value, "CVaR": CVaR_hl_value, "Percentile": var_percentile}
    else:
        st.error("Error fetching high-low data. Please check the stock symbol.")

# Display Results
if st.session_state.var_result:
    st.write(f"**VaR ({st.session_state.var_result['Percentile']}%): {st.session_state.var_result['VaR']:.2f}%**")
    st.write(f"**Expected Shortfall (CVaR): {st.session_state.var_result['CVaR']:.2f}%**")
if st.session_state.hl_var_result:
    st.write(f"**High-Low VaR ({st.session_state.hl_var_result['Percentile']}%): {st.session_state.hl_var_result['VaR']:.2f}%**")
    st.write(f"**High-Low Expected Shortfall (CVaR): {st.session_state.hl_var_result['CVaR']:.2f}%**")
