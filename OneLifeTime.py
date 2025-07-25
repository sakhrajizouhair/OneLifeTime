import pandas as pd
from datetime import datetime, timedelta
from dateutil import relativedelta
import streamlit as st
import streamlit.components.v1 as components

# 1. Load and preprocess life‐expectancy data
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.dropna(subset=['Life expectancy'])
    df = df.rename(columns={'Life expectancy': 'life_expectancy'})
    return df

df = load_data('life_expectancy_by_country.csv')

# 2. Build HTML + JS snippet for any slice of countries
def build_projection_html(
    df_slice: pd.DataFrame,
    now_dt: datetime,
    birth_dt: datetime,
    sort_col: str,
    key_prefix: str
) -> str:
    rows = []
    js_entries = []

    for idx, r in df_slice.iterrows():
        le = r[sort_col]
        # exact death datetime = birth + integer years + fractional days
        dt = (
            birth_dt
            + relativedelta.relativedelta(years=int(le))
            + timedelta(days=(le - int(le)) * 365.25)
        )
        sl = int((dt - now_dt).total_seconds())
        cell_id = f"{key_prefix}_t{idx}"

        rows.append(f"""
<tr>
  <td>{r['Country']}</td>
  <td id="{cell_id}">{sl}</td>
  <td>{dt.strftime('%Y-%m-%d %H:%M:%S')}</td>
</tr>
""")

        js_entries.append(f"{{id:'{cell_id}',cnt:{sl}}}")

    # inline <style> forces all text to white
    table_html = f"""
<style>
  table {{
    width: 100%;
    border-collapse: collapse;
    color: white;
  }}
  thead th {{
    background: #444;
    color: white;
    padding: 8px;
  }}
  td {{
    color: white;
    padding: 8px;
    border-top: 1px solid rgba(255,255,255,0.2);
  }}
</style>
<table>
  <thead>
    <tr>
      <th>Country</th>
      <th>Seconds Left</th>
      <th>Projected Death</th>
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
  setInterval(() => {{
    entries.forEach(e => {{
      e.cnt--;
      document.getElementById(e.id)
              .innerText = e.cnt.toLocaleString('fr-FR');
    }});
  }}, 1000);
</script>
"""

    return table_html + script

# 3. Streamlit app layout
st.title("What If...? Your Deadline in Other Countries")

# 3a. Ask user for birth date & time
birth_date = st.date_input("Enter your date of birth", datetime(1990, 1, 1).date())
birth_time = st.time_input("Enter your time of birth", datetime.now().time())
birth_dt = datetime.combine(birth_date, birth_time)

now_dt = datetime.now()

# 3b. Prepare top 5 & bottom 5 slices
sort_col = 'life_expectancy'
df_top5 = df.sort_values(sort_col, ascending=False).head(5)
df_bottom5 = df.sort_values(sort_col, ascending=True).head(5)

# 4. Render Top 5
st.header("Top 5 Countries by Life Expectancy")
html_top = build_projection_html(df_top5, now_dt, birth_dt, sort_col, "top5")
components.html(html_top, height=350)

# 5. Render Bottom 5
st.header("Bottom 5 Countries by Life Expectancy")
html_bottom = build_projection_html(df_bottom5, now_dt, birth_dt, sort_col, "bottom5")
components.html(html_bottom, height=350)

