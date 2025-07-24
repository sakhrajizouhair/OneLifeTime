import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dateutil import tz, relativedelta
import pytz
import time
import os
import streamlit.components.v1 as components

# Page configuration
st.set_page_config(page_title="OneLifeTime", layout="wide")

# Title and description
st.title("OneLifeTime")
st.write("Calculate how many seconds you have left based on your birth data and life expectancy.")

# Load life expectancy data (with caching)
@st.cache_data
def load_life_expectancy():
    try:
        df = pd.read_excel("world-lifeexpectancy.xlsx")
        # Normalize column names
        if 'Country' not in df.columns:
            country_col = next((c for c in df.columns if 'country' in c.lower()), None)
            if country_col:
                df = df.rename(columns={country_col: 'Country'})
        female_col = next((c for c in df.columns if 'female' in c.lower()), None)
        male_col = next((c for c in df.columns if 'male' in c.lower()), None)
        if female_col:
            df = df.rename(columns={female_col: 'Females Life Expectancy'})
        if male_col:
            df = df.rename(columns={male_col: 'Males Life Expectancy'})
        return df[['Country', 'Females Life Expectancy', 'Males Life Expectancy']]
    except Exception:
        # Fallback data
        data = {
            "Country": ["USA", "Japan", "India", "Brazil", "Nigeria"],
            "Females Life Expectancy": [81.1, 87.5, 70.7, 79.4, 65.2],
            "Males Life Expectancy": [76.1, 81.1, 68.2, 72.8, 62.7]
        }
        return pd.DataFrame(data)

life_df = load_life_expectancy()

# Inputs
col1, col2 = st.columns(2)
with col1:
    country = st.selectbox("Select your country", sorted(life_df["Country"].unique()))
    sex = st.radio("Select your sex", ["Male", "Female"])
    birth_date = st.date_input("Birth date", min_value=datetime(1900, 1, 1))
    birth_time = st.time_input("Birth time")
    tz_name = st.selectbox("Select your time zone", pytz.common_timezones, index= pytz.common_timezones.index("UTC") )
    include_js = st.checkbox("Use JavaScript live countdown", value=True)

with col2:
    row = life_df[life_df["Country"] == country].iloc[0]
    if sex == "Male":
        le = row["Males Life Expectancy"]
    else:
        le = row["Females Life Expectancy"]
    st.info(f"Life expectancy for {sex.lower()}s in {country}: {le:.1f} years")

# Calculate on button press
if st.button("Calculate Life Deadline"):
    # Build timezone-aware datetimes
    user_tz = pytz.timezone(tz_name)
    birth_dt = datetime.combine(birth_date, birth_time)
    birth_dt = user_tz.localize(birth_dt)
    now_dt = datetime.now(user_tz)

    # Compute expected death datetime with leap-year handling
    years_int = int(le)
    days_frac = (le - years_int) * 365.25
    death_dt = birth_dt + relativedelta.relativedelta(years=years_int)
    death_dt += timedelta(days=days_frac)

    # Seconds lived and left
    seconds_lived = (now_dt - birth_dt).total_seconds()
    seconds_left = (death_dt - now_dt).total_seconds()

    # Display summary metrics
    st.subheader("Your Life in Seconds")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Seconds Lived", f"{int(seconds_lived):,}")
        st.write(f"~ {seconds_lived/ (365.25*24*3600):.2f} years")
    with c2:
        st.metric("Seconds Left", f"{int(seconds_left):,}")
        st.write(f"~ {seconds_left/ (365.25*24*3600):.2f} years")

    # Live countdown
    st.subheader("Live Countdown")
    if include_js:
        # JavaScript-powered countdown
        html = f"""
        <div style="font-size:2.5em; text-align:center;" id="timer">{int(seconds_left):,}</div>
        <script>
        let count = {int(seconds_left)};
        setInterval(()=>{
            count--;
            document.getElementById('timer').innerText = count.toLocaleString();
        }, 1000);
        </script>
        """
        components.html(html, height=120)
    else:
        # Python demo for 10 seconds
        placeholder = st.empty()
        for _ in range(10):
            seconds_left -= 1
            placeholder.metric("Seconds Left (Live Demo)", f"{int(seconds_left):,}")
            time.sleep(1)

    # Life expectancy comparison tables
    st.subheader("Life Expectancy Comparison")
    left, right = st.columns(2)
    with left:
        st.write("Top 10 Countries")
        sort_col = "Males Life Expectancy" if sex=="Male" else "Females Life Expectancy"
        st.dataframe(life_df.sort_values(sort_col, ascending=False).head(10), use_container_width=True)
    with right:
        st.write("Bottom 10 Countries")
        st.dataframe(life_df.sort_values(sort_col).head(10), use_container_width=True)
