import streamlit as st
import pandas as pd
from datetime import datetime
import time
import os

# Page configuration
st.set_page_config(page_title="OneLifeTime", layout="wide")

# Title and description
st.title("OneLifeTime")
st.write("Calculate how many seconds you have left.")
st.checkbox("Show live countdown for 10 seconds")

# Load life expectancy data
@st.cache_data
def load_data():
    try:
        file_path = "world-lifeexpectancy.xlsx"
        df = pd.read_excel(file_path)
        # Assuming the columns are named as you mentioned
        # Rename if necessary to match your actual column names
        if 'Country' not in df.columns:
            # Try to identify the country column
            country_col = [col for col in df.columns if 'country' in col.lower()]
            if country_col:
                df = df.rename(columns={country_col[0]: 'Country'})
        
        # Similarly for life expectancy columns
        female_col = [col for col in df.columns if 'female' in col.lower()]
        male_col = [col for col in df.columns if 'male' in col.lower()]
        
        if female_col:
            df = df.rename(columns={female_col[0]: 'Females Life Expectancy'})
        if male_col:
            df = df.rename(columns={male_col[0]: 'Males Life Expectancy'})
            
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        # Provide fallback data in case the file can't be loaded
        data = {
            "Country": ["USA", "Japan", "India", "Brazil", "Nigeria"],
            "Females Life Expectancy": [81.1, 87.5, 70.7, 79.4, 65.2],
            "Males Life Expectancy": [76.1, 81.1, 68.2, 72.8, 62.7]
        }
        return pd.DataFrame(data)

life_expectancy_df = load_data()

# User inputs
col1, col2 = st.columns(2)

with col1:
    # Country selection
    countries = sorted(life_expectancy_df["Country"].unique())
    selected_country = st.selectbox("Select your country", countries)
    
    # Sex selection
    sex = st.radio("Select your sex", ["Male", "Female"])
    
    # Birth date and time
    birth_date = st.date_input("Birth date", min_value=datetime(1900, 1, 1))
    birth_time = st.time_input("Birth time")

with col2:
    # Display life expectancy for selected country
    country_data = life_expectancy_df[life_expectancy_df["Country"] == selected_country].iloc[0]
    
    if sex == "Male":
        life_expectancy = country_data["Males Life Expectancy"]
        st.info(f"Life expectancy for males in {selected_country}: {life_expectancy} years")
    else:
        life_expectancy = country_data["Females Life Expectancy"]
        st.info(f"Life expectancy for females in {selected_country}: {life_expectancy} years")

# Calculate when button is pressed
if st.button("Calculate Life Deadline"):
    # Combine birth date and time
    birth_datetime = datetime.combine(birth_date, birth_time)
    current_datetime = datetime.now()
    
    # Calculate seconds lived
    seconds_lived = (current_datetime - birth_datetime).total_seconds()
    
    # Calculate seconds left
    seconds_in_year = 365.25 * 24 * 60 * 60
    total_seconds = life_expectancy * seconds_in_year
    seconds_left = total_seconds - seconds_lived
    
    # Display results
    st.subheader("Your Life in Seconds")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Seconds Lived", f"{seconds_lived:,.0f}")
        years_lived = seconds_lived / seconds_in_year
        st.write(f"That's approximately {years_lived:.2f} years")
        
    with col2:
        st.metric("Seconds Left", f"{seconds_left:,.0f}")
        years_left = seconds_left / seconds_in_year
        st.write(f"That's approximately {years_left:.2f} years")
    
    # Create a countdown
    st.subheader("Your Life Countdown")
    countdown_placeholder = st.empty()
    
    # Display top and bottom 10 countries
    st.subheader("Life Expectancy Comparison")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Top 10 Countries by Life Expectancy")
        if sex == "Male":
            top_countries = life_expectancy_df.sort_values("Males Life Expectancy", ascending=False).head(10)
            st.dataframe(top_countries[["Country", "Males Life Expectancy"]])
        else:
            top_countries = life_expectancy_df.sort_values("Females Life Expectancy", ascending=False).head(10)
            st.dataframe(top_countries[["Country", "Females Life Expectancy"]])
    
    with col2:
        st.write("Bottom 10 Countries by Life Expectancy")
        if sex == "Male":
            bottom_countries = life_expectancy_df.sort_values("Males Life Expectancy").head(10)
            st.dataframe(bottom_countries[["Country", "Males Life Expectancy"]])
        else:
            bottom_countries = life_expectancy_df.sort_values("Females Life Expectancy").head(10)
            st.dataframe(bottom_countries[["Country", "Females Life Expectancy"]])
            
    # Live countdown (will update for a few seconds as demo)
    for i in range(10):
        seconds_left -= 1
        countdown_placeholder.metric("Seconds Left (Live)", f"{seconds_left:,.0f}")
        time.sleep(1)
