import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dateutil import relativedelta
import pytz
import streamlit.components.v1 as components

# Page configuration
st.set_page_config(page_title="OneLifeTime", layout="wide")

# --- Global CSS for Button & Table Text Colors ---
st.markdown("""
<style>
  /* Make the primary button green with black text */
  div.stButton > button {
    background-color: #4CAF50 !important;
    color: black !important;
    border: none !important;
  }
  /* Force all in‐app tables to show white text */
  table, table th, table td {
    color: white !important;
  }
</style>
""", unsafe_allow_html=True)

st.title("OneLifeTime")
st.write("Ever wondered how many seconds you might have left to live? OneLifeTime is a playful yet thought-provoking web app that gives you a live countdown.")

# --- Fallback life‐expectancy data ---
FALLBACK = pd.DataFrame({
    "Country": ["USA","Japan","India","Brazil","Nigeria"],
    "Females Life Expectancy":[81.1,87.5,70.7,79.4,65.2],
    "Males Life Expectancy":  [76.1,81.1,68.2,72.8,62.7]
})

@st.cache_data
def load_life_expectancy():
    try:
        df = pd.read_excel("world-lifeexpectancy.xlsx")
    except:
        return FALLBACK

    col_map = {}
    for col in df.columns:
        lower = col.strip().lower()
        if "country" in lower:
            col_map[col] = "Country"
        elif "female" in lower and "expectancy" in lower:
            col_map[col] = "Females Life Expectancy"
        elif "male" in lower and "expectancy" in lower:
            col_map[col] = "Males Life Expectancy"

    df = df.rename(columns=col_map)
    req = {"Country","Females Life Expectancy","Males Life Expectancy"}
    if not req.issubset(df.columns):
        return FALLBACK

    return df[["Country","Females Life Expectancy","Males Life Expectancy"]]

life_df = load_life_expectancy()

# --- User Inputs ---
col1, col2 = st.columns(2)
with col1:
    country = st.selectbox("Select your country", sorted(life_df["Country"]))
    sex     = st.radio("Select your sex", ["Male","Female"])
    bdate   = st.date_input("Birth date", min_value=datetime(1900,1,1))
    btime   = st.time_input("Birth time")
    tz_name = st.selectbox("Time zone", pytz.common_timezones,
                           index=pytz.common_timezones.index("UTC"))

with col2:
    row      = life_df[life_df["Country"]==country].iloc[0]
    life_exp = row["Males Life Expectancy"] if sex=="Male" else row["Females Life Expectancy"]

# --- Main Calculation ---
if st.button("Calculate My Life Time"):
    user_tz  = pytz.timezone(tz_name)
    birth_dt = user_tz.localize(datetime.combine(bdate, btime))
    now_dt   = datetime.now(user_tz)

    # Projected death datetime
    years_int = int(life_exp)
    days_frac = (life_exp - years_int) * 365.25
    death_dt  = (birth_dt
                 + relativedelta.relativedelta(years=years_int)
                 + timedelta(days=days_frac))

    sec_lived = int((now_dt - birth_dt).total_seconds())
    sec_left  = int((death_dt - now_dt).total_seconds())

    # --- Display Lived vs. Left ---
    st.subheader("Your Life in Seconds") 
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Seconds Lived", f"{sec_lived:,}".replace(",", " "))
        st.write(f"~{sec_lived/(365.25*24*3600):.2f} years")
    with c2:
        st.metric("Seconds Left", f"{sec_left:,}".replace(",", " "))
        st.write(f"~{sec_left/(365.25*24*3600):.2f} years")

    # --- Global Live Countdown ---
    styled_now = f"{sec_left:,}".replace(",", " ")
    countdown_html = f"""
    <div style="
      font-size:2.5em;
      color: green;
      background-color: #e6ffe6;
      padding:10px;
      border-radius:8px;
      text-align:center;
    " id="global_timer">{styled_now}</div>
    <script>
      let countG = {sec_left};
      setInterval(()=>{{  
        countG--;
        document.getElementById('global_timer')
                .innerText = countG.toLocaleString('fr-FR');
      }},1000);
    </script>
    """
    st.subheader("Live Countdown")
    components.html(countdown_html, height=120)

    # --- Projections for Other Countries ---
    st.subheader("What If…? You were in the EXTREME of the world!")
    sort_col = "Males Life Expectancy" if sex=="Male" else "Females Life Expectancy"
    top5 = life_df.sort_values(sort_col, ascending=False).head(5)
    bot5 = life_df.sort_values(sort_col, ascending=True).head(5)

    def build_projection_html(df_slice, key_prefix):
        rows = []
        js_entries = []
        for idx, r in df_slice.iterrows():
            le = r[sort_col]
            dt = (birth_dt
                  + relativedelta.relativedelta(years=int(le))
                  + timedelta(days=(le-int(le))*365.25))
            sl = int((dt - now_dt).total_seconds())
            cell_id = f"{key_prefix}_t{idx}"
            rows.append(
                f"<tr>"
                  f"<td>{r['Country']}</td>"
                  f"<td id='{cell_id}'>{str(sl).replace(',', ' ')}</td>"
                  f"<td>{dt.strftime('%Y-%m-%d %H:%M:%S')}</td>"
                f"</tr>"
            )
            js_entries.append(f"{{id:'{cell_id}',cnt:{sl}}}")

        # Inline style to force white text in this mini‐HTML
        table_html = f"""
        <style>
          table {{
            width: 100%;
            border-collapse: collapse;
            color: white !important;
          }}
          thead th {{
            background: #444;
            color: white !important;
            padding: 8px;
          }}
          td {{
            color: white !important;
            padding: 8px;
            border-top: 1px solid rgba(255,255,255,0.2);
          }}
        </style>
        <table>
          <thead>
            <tr>
              <th>Country</th><th>Seconds Center</th><th>Projected Death</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
        """
        js_array = "[" + ",".join(js_entries) + "]"
        script = f"""
        <script>
          let entries = {js_array};
          setInterval(()=>{{  
            entries.forEach(e=>{{  
              e.cnt--;
              document.getElementById(e.id)
                      .innerText = e.cnt.toLocaleString('fr-FR');
            }});
          }},1000);
        </script>
        """
        return table_html + script

    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Top 5 Countries**")
        components.html(build_projection_html(top5, "top"), height=300)
    with colB:
        st.markdown("**Bottom 5 Countries**")
        components.html(build_projection_html(bot5, "bot"), height=300)
