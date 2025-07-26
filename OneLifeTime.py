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
        border-radius: 8px !important; /* Added rounded corners */
        padding: 10px 20px !important; /* Added padding */
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2); /* Added shadow */
        transition: all 0.3s ease; /* Smooth transition */
    }
    div.stButton > button:hover {
        background-color: #45a049 !important; /* Darker green on hover */
        box-shadow: 3px 3px 8px rgba(0,0,0,0.3); /* Larger shadow on hover */
    }
    /* Force all in-app tables to show black text and better styling */
    table {
        width: 100%;
        border-collapse: collapse;
        color: black !important;
        border-radius: 8px; /* Rounded corners for tables */
        overflow: hidden; /* Ensures rounded corners are visible */
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); /* Soft shadow for tables */
    }
    table th {
        background-color: #f2f2f2; /* Light gray header */
        padding: 12px 15px;
        text-align: left;
        font-weight: bold;
        color: black !important; /* Ensure header text is black */
    }
    table td {
        padding: 10px 15px;
        border-bottom: 1px solid #ddd; /* Light separator */
        color: black !important; /* Ensure cell text is black */
    }
    table tr:last-child td {
        border-bottom: none; /* No border on last row */
    }
    table tbody tr:hover {
        background-color: #f9f9f9; /* Subtle hover effect */
    }

    /* Style for st.metric values */
    .stMetric > div > div:nth-child(2) > div {
        font-size: 2.5em !important; /* Larger font for metric values */
        font-weight: bold !important;
        color: #1a1a1a !important; /* Darker color for emphasis */
    }
    /* Style for st.metric labels */
    .stMetric > div > div:nth-child(1) {
        font-size: 1.1em !important;
        color: #555 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("OneLifeTime")
st.write("Ever wondered how many seconds you might have left to live? OneLifeTime is a playful yet thought-provoking web app that gives you a live countdown.")

# --- Fallback life-expectancy data ---
FALLBACK = pd.DataFrame({
    "Country": ["USA","Japan","India","Brazil","Nigeria"],
    "Females Life Expectancy":[81.1,87.5,70.7,79.4,65.2],
    "Males Life Expectancy":  [76.1,81.1,68.2,72.8,62.7]
})

@st.cache_data
def load_life_expectancy():
    """
    Loads life expectancy data from an Excel file or uses fallback data.
    Renames columns to a consistent format.
    """
    try:
        df = pd.read_excel("world-lifeexpectancy.xlsx")
    except Exception as e:
        st.warning(f"Could not load 'world-lifeexpectancy.xlsx': {e}. Using fallback data.")
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
        st.warning("Excel file missing required columns. Using fallback data.")
        return FALLBACK

    return df[["Country","Females Life Expectancy","Males Life Expectancy"]]

life_df = load_life_expectancy()

# --- User Inputs ---
col1, col2 = st.columns(2)
with col1:
    country = st.selectbox("Select your country", sorted(life_df["Country"]))
    sex     = st.radio("Select your sex", ["Male","Female"], horizontal=True) # Added horizontal layout
    bdate   = st.date_input("Birth date", min_value=datetime(1900,1,1))
    btime   = st.time_input("Birth time")
    # Set default time zone to the user's local time zone if possible, otherwise UTC
    try:
        default_tz_index = pytz.common_timezones.index(str(datetime.now(pytz.utc).astimezone().tzinfo))
    except ValueError:
        default_tz_index = pytz.common_timezones.index("UTC")
    tz_name = st.selectbox("Time zone", pytz.common_timezones,
                             index=default_tz_index)

    # --- New Determinants ---
    st.markdown("---") # Separator for lifestyle factors
    st.subheader("Lifestyle Factors")
    gym         = st.radio("Do you do gym?", ["No","Yes"], horizontal=True)
    gym_since = None
    if gym == "Yes":
        gym_since = st.selectbox(
            "Gym since:",
            ["Less than a year", "Between 1 and 3 years", "More than 3 years"]
        )

    smoke         = st.radio("Do you smoke?", ["No","Yes"], horizontal=True)
    smoke_since = None
    if smoke == "Yes":
        smoke_since = st.selectbox(
            "Smoking since:",
            ["Less than a year", "Between 1 and 5 years",
             "Between 5 and 10 years", "More than 10 years"]
        )

    cancer = st.radio("Do you have cancer?", ["No","Yes"], horizontal=True)

with col2:
    row      = life_df[life_df["Country"]==country].iloc[0]
    life_exp = row["Males Life Expectancy"] if sex=="Male" else row["Females Life Expectancy"]
    st.info(f"Base life expectancy for {sex.lower()}s in {country}: **{life_exp:.1f} years**")


# --- Main Calculation ---
if st.button("Calculate My Life Time"):
    # timezone-aware birth & now
    user_tz  = pytz.timezone(tz_name)
    birth_dt = user_tz.localize(datetime.combine(bdate, btime))
    now_dt   = datetime.now(user_tz)

    # Calculate current age for display
    current_age = relativedelta.relativedelta(now_dt, birth_dt)
    st.write(f"You are currently **{current_age.years} years, {current_age.months} months, and {current_age.days} days old**.")

    # Adjust life expectancy based on lifestyle factors
    adjust = 0

    # gym adjustment
    if gym == "Yes":
        if gym_since == "Less than a year":
            adjust += 1
        elif gym_since == "Between 1 and 3 years":
            adjust += 4
        else: # More than 3 years
            adjust += 7

    # smoking adjustment
    if smoke == "Yes":
        if smoke_since == "Less than a year":
            adjust -= 1
        elif smoke_since == "Between 1 and 5 years":
            adjust -= 3
        elif smoke_since == "Between 5 and 10 years":
            adjust -= 5
        else: # More than 10 years
            adjust -= 10

    # cancer adjustment
    if cancer == "Yes":
        adjust -= 8

    effective_le = life_exp + adjust
    if effective_le < 0: # Ensure life expectancy doesn't go negative
        effective_le = 0.1 # Small positive number to avoid division by zero or negative time

    st.info(f"Adjusted life expectancy for {sex.lower()}s in {country} with your lifestyle: **{effective_le:.1f} years**")


    # Projected death datetime
    years_int = int(effective_le)
    days_frac = (effective_le - years_int) * 365.25 # Account for fractional years
    death_dt  = (
        birth_dt
        + relativedelta.relativedelta(years=years_int)
        + timedelta(days=days_frac)
    )

    sec_lived = int((now_dt - birth_dt).total_seconds())
    sec_left  = int((death_dt - now_dt).total_seconds())

    # Ensure seconds left is not negative
    if sec_left < 0:
        sec_left = 0

    # --- Display Lived vs. Left ---
    st.subheader("Your Life in Seconds")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Seconds Lived", f"{sec_lived:,}".replace(",", " "))
        st.write(f"That's approximately {sec_lived/(365.25*24*3600):.2f} years")
    with c2:
        st.metric("Seconds Left", f"{sec_left:,}".replace(",", " "))
        st.write(f"That's approximately {sec_left/(365.25*24*3600):.2f} years")

    # --- Global Live Countdown (using st.components.v1.html for persistent JS) ---
    styled_now = f"{sec_left:,}".replace(",", " ")
    countdown_html = f"""
    <div style="
      font-size:2.5em;
      color: green;
      background-color: #e6ffe6;
      padding:15px;
      border-radius:12px;
      text-align:center;
      margin-top: 20px;
      font-family: 'Inter', sans-serif; /* Use Inter font */
      box-shadow: 0 4px 10px rgba(0,0,0,0.15); /* Add shadow */
    " id="global_timer">{styled_now}</div>
    <script>
      let countG = {sec_left};
      // Clear any existing interval to prevent multiple timers on rerun
      if (window.globalCountdownInterval) {{
          clearInterval(window.globalCountdownInterval);
      }}
      window.globalCountdownInterval = setInterval(()=>{{
        countG--;
        if (countG < 0) countG = 0; // Don't go below zero
        const timerElement = document.getElementById('global_timer');
        if (timerElement) {{
            timerElement.innerText = countG.toLocaleString('fr-FR');
        }} else {{
            // If element is not found, clear interval to prevent errors
            clearInterval(window.globalCountdownInterval);
        }}
      }},1000);
    </script>
    """
    st.subheader("Your Live Countdown")
    components.html(countdown_html, height=150) # Increased height for better display

    # --- Projections for Other Countries ---
    st.subheader("What If…? You were in the EXTREME sides of the world!")
    sort_col = "Males Life Expectancy" if sex=="Male" else "Females Life Expectancy"
    top5 = life_df.sort_values(sort_col, ascending=False).head(5)
    bot5 = life_df.sort_values(sort_col, ascending=True).head(5)

    def build_projection_html(df_slice, key_prefix):
        """
        Generates HTML for a table of country projections with live countdown.
        """
        rows, js_entries = [], []
        for idx, r in df_slice.iterrows():
            le = r[sort_col] + adjust
            if le < 0: le = 0.1 # Ensure life expectancy doesn't go negative for calculations
            dt = (
                birth_dt
                + relativedelta.relativedelta(years=int(le))
                + timedelta(days=(le-int(le))*365.25)
            )
            sl = int((dt - now_dt).total_seconds())
            if sl < 0: sl = 0 # Ensure seconds left is not negative
            cell_id = f"{key_prefix}_t{idx}"
            rows.append(
                f"<tr>"
                  f"<td>{r['Country']}</td>"
                  f"<td id='{cell_id}'>{sl:,}</td>"
                  f"<td>{dt.strftime('%Y-%m-%d %H:%M:%S')}</td>"
                f"</tr>"
            )
            js_entries.append(f"{{id:'{cell_id}',cnt:{sl}}}")

        html = f"""
        <style>
          /* Specific styles for these tables to override global if needed */
          #projection-table-{{key_prefix}} table {{
              width:100%;
              border-collapse:collapse;
              color:black!important;
              font-family: 'Inter', sans-serif;
              border-radius: 8px;
              overflow: hidden;
              box-shadow: 0 2px 5px rgba(0,0,0,0.1);
          }}
          #projection-table-{{key_prefix}} thead th {{
              background:#555;
              padding:10px;
              color:white!important; /* White header text for contrast */
              text-align: left;
          }}
          #projection-table-{{key_prefix}} td {{
              padding:10px;
              border-top:1px solid #eee;
              color:black!important;
          }}
          #projection-table-{{key_prefix}} tbody tr:nth-child(even) {{
              background-color: #f8f8f8; /* Zebra striping */
          }}
          #projection-table-{{key_prefix}} tbody tr:hover {{
              background-color: #f0f0f0;
          }}
        </style>
        <div id="projection-table-{key_prefix}">
            <table>
              <thead>
                <tr><th>Country</th><th>Seconds Left</th><th>Projected Death</th></tr>
              </thead>
              <tbody>
                {''.join(rows)}
              </tbody>
            </table>
        </div>
        <script>
          let entries_{key_prefix} = [{','.join(js_entries)}];
          // Clear any existing interval for this table to prevent multiple timers on rerun
          if (window.projectionInterval_{key_prefix}) {{
              clearInterval(window.projectionInterval_{key_prefix});
          }}
          window.projectionInterval_{key_prefix} = setInterval(()=>{{
            entries_{key_prefix}.forEach(e=>{{
              e.cnt--;
              if (e.cnt < 0) e.cnt = 0; // Don't go below zero
              const element = document.getElementById(e.id);
              if (element) {{
                  element.innerText = e.cnt.toLocaleString('fr-FR');
              }} else {{
                  // If element is not found, clear interval to prevent errors
                  clearInterval(window.projectionInterval_{key_prefix});
              }}
            }});
          }},1000);
        </script>
        """
        return html

    colA, colB = st.columns(2)
    with colA:
        st.markdown("---") # Separator
        st.markdown("**Top 5 Countries**")
        components.html(build_projection_html(top5, "top"), height=350) # Adjusted height
    with colB:
        st.markdown("---") # Separator
        st.markdown("**Bottom 5 Countries**")
        components.html(build_projection_html(bot5, "bot"), height=350) # Adjusted height

# --- Separator before visitor counter ---
st.markdown("---")

# --- Visitor Counter Section ---
# This HTML component will handle Firebase initialization and visitor count logic
visitor_counter_html = f"""
<div id="visitor-count-container" style="text-align:center; padding:10px;">
    <p style="font-size:1.2em; color:black; font-family: 'Inter', sans-serif;">
        Total Visitors: <span id="visitor-count" style="font-weight:bold; color:green;">Loading...</span>
    </p>
</div>

<script type="module">
    // Import Firebase SDKs
    import {{ initializeApp }} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
    import {{ getAuth, signInAnonymously, signInWithCustomToken, onAuthStateChanged }} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
    import {{ getFirestore, doc, updateDoc, onSnapshot, increment, setDoc }} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

    // Access global variables passed from the Canvas environment
    const appId = typeof __app_id !== 'undefined' ? __app_id : 'default-app-id';
    const firebaseConfig = typeof __firebase_config !== 'undefined' ? JSON.parse(__firebase_config) : null;
    const initialAuthToken = typeof __initial_auth_token !== 'undefined' ? __initial_auth_token : null;

    const visitorCountElement = document.getElementById('visitor-count');

    if (!firebaseConfig) {{
        console.error("Firebase config not available. Cannot initialize Firebase.");
        if (visitorCountElement) visitorCountElement.innerText = 'Error: Config missing';
    }} else {{
        const app = initializeApp(firebaseConfig);
        const db = getFirestore(app);
        const auth = getAuth(app);

        async function initializeFirebaseAndCounter() {{
            try {{
                // Authenticate the user
                if (initialAuthToken) {{
                    await signInWithCustomToken(auth, initialAuthToken);
                }} else {{
                    await signInAnonymously(auth);
                }}

                // Define the Firestore document reference for the public counter
                const counterDocRef = doc(db, `artifacts/${appId}/public/data/visitor_counts/main_counter`);

                // Increment the counter on initial load.
                // Using merge: true ensures the document is created if it doesn't exist.
                await updateDoc(counterDocRef, {{
                    count: increment(1)
                }}, {{ merge: true }});

                // Set up a real-time listener for the counter
                onSnapshot(counterDocRef, (docSnap) => {{
                    if (docSnap.exists()) {{
                        const count = docSnap.data().count;
                        if (visitorCountElement) visitorCountElement.innerText = count.toLocaleString('fr-FR');
                    }} else {{
                        // If the document doesn't exist after the first attempt,
                        // it means it was just created by this instance.
                        // We can set it to 1, or handle initial state.
                        // For a robust counter, it's better to ensure it's initialized.
                        // This case should ideally not be hit if updateDoc with merge:true works.
                        if (visitorCountElement) visitorCountElement.innerText = '1'; // Default to 1 if just created
                    }}
                }}, (error) => {{
                    console.error("Error listening to visitor count:", error);
                    if (visitorCountElement) visitorCountElement.innerText = 'Error';
                }});

            }} catch (error) {{
                console.error("Firebase initialization or counter update failed:", error);
                if (visitorCountElement) visitorCountElement.innerText = 'Error';
            }}
        }}

        // Run the initialization and counter logic
        initializeFirebaseAndCounter();
    }}
</script>
"""
components.html(visitor_counter_html, height=80) # Adjust height as needed for the counter display

# --- Footer Text ---
st.markdown(
    "<p style='text-align:center; font-size:12px; color:gray; font-family: 'Inter', sans-serif;'>EmersionDesk © 2025</p>",
    unsafe_allow_html=True
)
