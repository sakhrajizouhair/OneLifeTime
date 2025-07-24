import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dateutil import relativedelta
import pytz
import time
import streamlit.components.v1 as components

# Page config
st.set_page_config(page_title="OneLifeTime", layout="wide")

st.title("OneLifeTime")
st.write("Calculate how many seconds you have left based on your birth data.")

@st.cache_data
def load_life_expectancy(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
    else:
        try:
            df = pd.read_excel("world-lifeexpectancy.xlsx")
        except FileNotFoundError:
            # fallback sample
            data = {
                "Country": ["USA", "Japan", "India", "Brazil", "Nigeria"],
                "Females Life Expectancy": [81.1, 87.5, 70.7, 79.4, 65.2],
                "Males Life Expectancy": [76.1, 81.1, 68.2, 72.8, 62.7]
            }
            return pd.DataFrame(data)

    # normalize column names
    if 'Country' not in df.columns:
        country_col = next((c for c in df.columns if 'country' in c.lower()), None)
        if country_col:
            df = df.rename(columns={country_col: 'Country'})
    female_col = next((c for c in df.columns if 'female' in c.lower()), None)
    male_col   = next((c for c in df.columns if 'male'   in c.lower()), None)
    if female_col:
        df = df.rename(columns={female_col: 'Females Life Expectancy'})
    if male_col:
        df = df.rename(columns={male_col:   'Males Life Expectancy'})
    return df[['Country', 'Females Life Expectancy', 'Males Life Expectancy']]

# allow uploading the real dataset if not checked into your repo
upload = st.file_uploader("Upload world-lifeexpectancy.xlsx", type=["xlsx"])
life_df = load_life_expectancy(upload)

# --- USER INPUTS ---
col1, col2 = st.columns(2)
with col1:
    country = st.selectbox("Select your country", sorted(life_df["Country"].unique()))
    sex     = st.radio("Select your sex", ["Male", "Female"])
    bdate   = st.date_input("Birth date", min_value=datetime(1900,1,1))
    btime   = st.time_input("Birth time")
    tz_name = st.selectbox("Time zone", pytz.common_timezones, index=pytz.common_timezones.index("UTC"))
    use_js  = st.checkbox("Use JavaScript live countdown", value=True)

# grab expectancy internally
row = life_df[life_df["Country"]==country].iloc[0]
life_expectancy = row["Males Life Expectancy"] if sex=="Male" else row["Females Life Expectancy"]

# --- CALCULATION & DISPLAY ---
if st.button("Calculate Life Deadline"):
    user_tz  = pytz.timezone(tz_name)
    birth_dt = user_tz.localize(datetime.combine(bdate, btime))
    now_dt   = datetime.now(user_tz)

    # compute death datetime
    years_int = int(life_expectancy)
    days_frac = (life_expectancy - years_int) * 365.25
    death_dt  = (birth_dt 
                 + relativedelta.relativedelta(years=years_int) 
                 + timedelta(days=days_frac))

    seconds_lived = (now_dt - birth_dt).total_seconds()
    seconds_left  = (death_dt - now_dt).total_seconds()

    # metrics
    st.subheader("Your Life in Seconds")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Seconds Lived", f"{int(seconds_lived):,}")
        st.write(f"~{seconds_lived/(365.25*24*3600):.2f} years")
    with c2:
        st.metric("Seconds Left", f"{int(seconds_left):,}")
        st.write(f"~{seconds_left/(365.25*24*3600):.2f} years")

    # live countdown
    st.subheader("Live Countdown")
    if use_js:
        html = f"""
        <div style="font-size:2.5em; text-align:center;" id="timer">{int(seconds_left):,}</div>
        <script>
        let count = {int(seconds_left)};
        setInterval(()=>{{  
            count--;
            document.getElementById('timer').innerText = count.toLocaleString();
        }}, 1000);
        </script>
        """
        components.html(html, height=120)
    else:
        placeholder = st.empty()
        for _ in range(10):
            seconds_left -= 1
            placeholder.metric("Seconds Left (Live Demo)", f"{int(seconds_left):,}")
            time.sleep(1)

    # comparison tables
    st.subheader("Life Expectancy Comparison")
    left, right = st.columns(2)
    sort_col = "Males Life Expectancy" if sex=="Male" else "Females Life Expectancy"
    with left:
        st.write("Top 10 Countries")
        st.dataframe(life_df.sort_values(sort_col, ascending=False).head(10), use_container_width=True)
    with right:
        st.write("Bottom 10 Countries")
        st.dataframe(life_df.sort_values(sort_col).head(10), use_container_width=True)
