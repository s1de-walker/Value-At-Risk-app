#%%writefile app.py

import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime, timedelta
import plotly.express as px

#Libraries--------------------------------------------------------------------------------------

# Title
st.title("Value at Risk")
st.write("")
st.write("")

# User Inputs
stock = st.text_input("Enter Stock/ETF Symbol:", value="SPY").upper()
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Select Start Date:", value=datetime.today() - timedelta(days=730))
with col2:
    end_date = st.date_input("Select End Date:", value=datetime.today())

date_range_days = (end_date - start_date).days  # Calculate total available days

if date_range_days < 0:
    st.error("🚨 End Date cannot be earlier than Start Date. Please select a valid range.")
    st.stop()

st.divider()

#Main inputs--------------------------------------------------------------------------------------

# Sidebar Instructions
st.sidebar.write("This Market Risk App helps users assess potential losses in a stock or ETF over a selected period for informed decision-making.")
st.sidebar.header("📖   How to Use Inputs")
st.sidebar.write("")
st.sidebar.write("- **Analysis Period:** If your average holding period is 5 days, you may want to analyze how prices change over 5-day intervals.")
st.sidebar.write("")
st.sidebar.write("- **Percentile:** Defines the risk threshold—e.g., the VaR 95th percentile represents a 2-sigma event and 95% of the data points are above that value.")
st.sidebar.write("")
st.sidebar.write("- **Monte Carlo Simulations:** More simulations improve accuracy but take longer to compute.")

# Sidebar instructions-----------------------------------------------------------------------------
if not stock:
    st.stop()

# I. SECTION: VAR
# ===============
st.subheader("How much could I lose over a given period, for a given probability?")


# **Initialize Session State**
# **Initialize Session State**
# if "var_result" not in st.session_state:
#     st.session_state.var_result = None
# if "histogram_fig" not in st.session_state:
#     st.session_state.histogram_fig = None
# if "data" not in st.session_state:
#     st.session_state.data = None

for key in ["var_result", "histogram_fig", "data"]:
    if key not in st.session_state:
        st.session_state[key] = None


st.write("")

col1, col2, col3 = st.columns(3)
with col1:
    analysis_period = st.number_input("Select Analysis Period (Days):", min_value=1, max_value=30, value=5)
with col2:
    var_percentile = st.number_input("Select VaR Percentile:", min_value=0.01, max_value=99.99, value=95.00, format="%.2f")
with col3:
    simulations = st.number_input("Number of Monte Carlo Simulations:", min_value=100, max_value=10000, value=2000)


st.write("")

#Validation of dates used repeatedly
def validate_dates(start_date, end_date):
    """Validate start and end dates. Returns True if valid, else False."""
    if end_date < start_date:
        st.error("🚨 End Date cannot be earlier than Start Date. Please select a valid range.")
        return False
    
    if start_date > datetime.today().date() or end_date > datetime.today().date():
        st.error("🚨 Dates cannot be in the future. Please select a valid range.")
        return False
    
    return True  # No need for else!




# Button to Run Calculation
if st.button("Calculate VaR"):
    if validate_dates(start_date, end_date):
        
        # Fetch Data
        data = yf.download(stock, start=start_date, end=end_date)["Close"]

        if data is not None and not data.empty:
            returns = data.pct_change(analysis_period).dropna()
            mu, sigma = returns.mean(), returns.std()
            
            # Monte Carlo Simulation
            simulated_returns = np.random.normal(mu, sigma, simulations)
            VaR_value = np.percentile(simulated_returns, 100 - var_percentile) * 100
            # Compute CVaR (Expected Shortfall)
            CVaR_value = simulated_returns[simulated_returns < (VaR_value / 100)].mean() * 100

            # Custom font color for stock name
            stock_name_colored = f"<span style='color:white'><b>{stock.upper()}</b></span>"
            
            # Create Interactive Histogram
            fig = px.histogram(x=simulated_returns, nbins=50, title=f"Monte Carlo Simulated Returns: {stock_name_colored}", labels={"x": "Returns"}, opacity=0.7, color_discrete_sequence=["#6b5d50"])
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
            st.error("🚨 Error fetching data. Please check the stock symbol (as per yfinance). Use .NS after ticker for NSE stocks")

if st.session_state.var_result:
        st.plotly_chart(st.session_state.histogram_fig)
        var_res = st.session_state.var_result
        st.markdown(f"<h5>VaR {var_res['var_percentile']:.1f}:    <span style='font-size:32px; font-weight:bold; color:#FF5733;'>{var_res['VaR_value']:.1f}%</span></h5>", unsafe_allow_html=True)
        st.write(f"**There is a {100-var_res['var_percentile']:.1f}% chance of losing more than {var_res['VaR_value']:.1f}% over the period.**")
        st.write(f"**Expected Shortfall (CVaR) in worst cases: {var_res['CVaR_value']:.2f}%**")
        st.caption("This helps to manage tail risk")

# I SECTION-----------------------------------------------------------------------------------------------------------------------

st.divider()

# II. SECTION: VAR HIGH-LOW
# =========================

# User Inputs
st.subheader("What's the range?")
st.caption("Input for High minus Low analysis")

hl_var_result = st.session_state.get("hl_var_result", None)  # Default to None

col1, col2 = st.columns(2)
with col1:
    hl_analysis_period = st.number_input("Select High-Low Analysis Period (Days):", min_value=1, max_value=30, value=5)
with col2:
    hl_var_percentile = st.number_input("Select High-Low VaR Percentile:", min_value=0.01, max_value=99.99, value=99.00, format="%.2f")

st.write("")

# Button to Run High-Low VaR Calculation
if st.button("Calculate High-Low VaR"):
    if validate_dates(start_date, end_date): 
        
        data_hl = yf.download(stock, start=start_date, end=end_date)

        if data_hl is not None and not data_hl.empty and "High" in data_hl.columns and "Low" in data_hl.columns:
            st.session_state.hl_stock_name = stock  # Store stock name
            
            hl_range = data_hl["High"] - data_hl["Low"]
            hl_range = hl_range.rolling(hl_analysis_period).sum().dropna()
            VaR_hl_value = np.percentile(hl_range, 100 - hl_var_percentile)

            st.session_state.hl_var_result = {"VaR": VaR_hl_value, "Percentile": hl_var_percentile}
            st.session_state.data_hl = data_hl  # Store data for later use
            
        else:
            st.session_state.hl_var_result = None  # Reset stored result on error
            st.error("🚨 Error fetching data. Please check the stock symbol (as per yfinance). Use .NS after ticker for NSE stocks")

# Display only if a valid result exists
if st.session_state.get("hl_var_result"):
    data_hl = st.session_state.get("data_hl")
    stock_name = st.session_state.get("hl_stock_name", stock)

    # Extract latest price and price change
    latest_price = data_hl["Close"].iloc[-1].item()
    prev_price = data_hl["Close"].iloc[-2].item()
    price_change = latest_price - prev_price
    price_change_pct = (price_change / prev_price) * 100

    # ✅ Display stock price and change
    st.metric(label="Stock Price", value=f"${latest_price:.2f}", delta=f"{price_change_pct:.2f}%")

    # ✅ Display the risk statement
    hl_var_percentile = st.session_state.hl_var_result["Percentile"]
    VaR_hl_value = st.session_state.hl_var_result["VaR"]

    st.write(f"**{100 - hl_var_percentile:.1f}% chance that <span style='color:white'><b>{stock_name}</b></span> might move a range of ${VaR_hl_value:.2f}**", unsafe_allow_html=True)



st.divider() # --------------------------------------------------------------------------------------------------------------------

st.subheader("Is it getting riskier?")
st.caption("Select rolling windows for short-term and long-term volatility.")

col1, col2 = st.columns(2)
# Check if the date difference is negative
if date_range_days < 0:
    st.write("")
else:
    # Proceed with your number input
    with col1:
        short_vol_window = st.number_input("Short-Term Window (Days):", min_value=1, max_value=date_range_days, value=10)
    with col2:
        long_vol_window = st.number_input("Long-Term Window (Days):", min_value=1, max_value=date_range_days, value=50)




st.write("")

# Button to Calculate Rolling Volatility
if st.button("Calculate Rolling Volatility"):
    if validate_dates(start_date, end_date): 

        data_rv = yf.download(stock, start=start_date, end=end_date)["Close"]
        if data_rv is not None or not data_rv.empty:
            short_vol = data_rv.pct_change().rolling(short_vol_window).std().dropna().squeeze() * np.sqrt(250) * 100
            long_vol = data_rv.pct_change().rolling(long_vol_window).std().dropna().squeeze() * np.sqrt(250) * 100
            
            # Ensure both are Series with the same index
            short_vol = short_vol.loc[short_vol.index.intersection(long_vol.index)]
            long_vol = long_vol.loc[long_vol.index.intersection(short_vol.index)]
    
            # Create a DataFrame
            vol_df = pd.DataFrame({
                "Date": short_vol.index,
                "Short Vol": short_vol.values,  # Ensure 1D
                "Long Vol": long_vol.values     # Ensure 1D
            }).dropna()
    
            # Store in session state
            st.session_state.data_rv = vol_df
            st.session_state.rv_stock_name = stock  # Store stock name after button click
    
        else:
            st.error("🚨 Error fetching data. Please check the stock symbol (as per yfinance). Use .NS after ticker for NSE stocks")

# Display Rolling Volatility Trend
if "data_rv" in st.session_state:
    vol_df = st.session_state.data_rv

    # Use the stored stock name after button click
    stock_name = st.session_state.get("rv_stock_name", stock)

    # Custom colors
    custom_colors = {"Short Vol": "red", "Long Vol": "#6b5d50"}

    # Custom font color for stock name
    stock_name_colored = f"<span style='color:white'><b>{stock_name.upper()}</b></span>"

    # Create the title with colored stock name
    plot_title = f"Rolling Volatility Trend for {stock_name_colored}"

    # Create the line plot
    fig = px.line(vol_df, x="Date", y=["Short Vol", "Long Vol"], title=plot_title,
                  labels={"value": "Volatility (%)", "Date": "Date", "variable": "Volatility Type"},
                  color_discrete_map=custom_colors)

    fig.update_traces(mode="lines", line=dict(width=2))
    fig.update_layout(showlegend=True, legend_title="Type")

    st.plotly_chart(fig, use_container_width=True)
