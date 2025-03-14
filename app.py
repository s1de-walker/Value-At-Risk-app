
import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta
import plotly.express as px

# Title
st.title("Value at Risk")
st.write("")
st.write("")

st.subheader("How much could I lose over a given period, for a given probability?")


# Sidebar Instructions
st.sidebar.header("📖   How to Use Inputs")
st.sidebar.write("")
st.sidebar.write("- **Analysis Period:** If your average holding period is 5 days, you may want to analyze how prices change over 5-day intervals.")
st.sidebar.write("")
st.sidebar.write("- **Percentile:** Defines the risk threshold—e.g., the VaR 95th percentile represents a 2-sigma event and 95% of the data points are above that value.")
st.sidebar.write("")
st.sidebar.write("- **Monte Carlo Simulations:** More simulations improve accuracy but take longer to compute.")

# **Initialize Session State**
if "var_result" not in st.session_state:
    st.session_state.var_result = None
if "histogram_fig" not in st.session_state:
    st.session_state.histogram_fig = None
if "data" not in st.session_state:
    st.session_state.data = None

# User Inputs
stock = st.text_input("Enter Stock/ETF Symbol:", value="SPY")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Select Start Date:", value=datetime.today() - timedelta(days=500))
with col2:
    end_date = st.date_input("Select End Date:", value=datetime.today())

st.write("")

col1, col2, col3 = st.columns(3)
with col1:
    analysis_period = st.number_input("Select Analysis Period (Days):", min_value=1, max_value=30, value=5)
with col2:
    var_percentile = st.number_input("Select VaR Percentile:", min_value=0.01, max_value=99.99, value=95.00, format="%.2f")
with col3:
    simulations = st.number_input("Number of Monte Carlo Simulations:", min_value=100, max_value=10000, value=2000)


st.write("")

# Button to Run Calculation
if st.button("Calculate VaR"):
    # **Validation Checks**
    error_flag = False  
    
    if end_date < start_date:
        st.error("🚨 End Date cannot be earlier than Start Date. Please select a valid range.")
        error_flag = True
    
    if start_date > datetime.today().date() or end_date > datetime.today().date():
        st.error("🚨 Dates cannot be in the future. Please select a valid range.")
        error_flag = True
    
    # **Run only if there are no errors**
    if not error_flag:
        # Fetch Data
        data = yf.download(stock, start=start_date, end=end_date)["Close"]

        if not data.empty:
            returns = data.pct_change(analysis_period).dropna()
            mu, sigma = returns.mean(), returns.std()
            
            # Monte Carlo Simulation
            simulated_returns = np.random.normal(mu, sigma, simulations)
            VaR_value = np.percentile(simulated_returns, 100 - var_percentile) * 100
            # Compute CVaR (Expected Shortfall)
            CVaR_value = simulated_returns[simulated_returns < (VaR_value / 100)].mean() * 100
            
            # Create Interactive Histogram
            fig = px.histogram(x=simulated_returns, nbins=50, title="Monte Carlo Simulated Returns", labels={"x": "Returns"}, opacity=0.7, color_discrete_sequence=["#6b5d50"])
            fig.add_vline(x=VaR_value / 100, line=dict(color="red", width=2, dash="dash"))
            fig.update_layout(xaxis_title="Returns", yaxis_title="Frequency", showlegend=False)

            # Store in Session State
            st.session_state.var_result = {
                "VaR_value": VaR_value,
                "CVaR_value": CVaR_value,
                "var_percentile": var_percentile
            }

            st.session_state.histogram_fig = fig
            st.session_state.data = returns  # Store historical returns for stress testing
            
            
            
        else:
            st.error("🚨 Error fetching data. Please check the stock symbol (as per yfinance).")

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
