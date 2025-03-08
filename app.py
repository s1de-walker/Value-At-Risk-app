
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
    simulations = st.number_input("Number of Monte Carlo Simulations:", min_value=100, max_value=5000, value=1000)
with col3:
    var_percentile = st.number_input("Select VaR Percentile:", min_value=0.01, max_value=99.99, value=95.00, format="%.2f")

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
            
            # Create Interactive Histogram
            fig = px.histogram(x=simulated_returns, nbins=50, title="Monte Carlo Simulated Returns", labels={"x": "Returns"}, opacity=0.7, color_discrete_sequence=["#6b5d50"])
            fig.add_vline(x=VaR_value / 100, line=dict(color="red", width=2, dash="dash"))
            fig.update_layout(xaxis_title="Returns", yaxis_title="Frequency", showlegend=False)
            
            # Display Interactive Histogram
            st.plotly_chart(fig)
            
            
            # Display VaR
            st.markdown(f"<h5>VaR {var_percentile:.1f}: <span style='font-size:32px; font-weight:bold; color:#FF5733;'>{VaR_value:.1f}%</span></h5>", unsafe_allow_html=True)
            
        else:
            st.write("Error fetching data. Please check the stock symbol.")
