import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dateutil import relativedelta
import pytz
import streamlit.components.v1 as components

# --- Constants for calculations ---
SECONDS_IN_MINUTE = 60
MINUTES_IN_HOUR = 60
HOURS_IN_DAY = 24
DAYS_IN_YEAR_AVG = 365.25 # Accounts for leap years on average
SECONDS_IN_YEAR = SECONDS_IN_MINUTE * MINUTES_IN_HOUR * HOURS_IN_DAY * DAYS_IN_YEAR_AVG

# --- Page configuration ---
st.set_page_config(page_title="OneLifeTime", layout="wide")

# --- Global CSS for Button & Table Text Colors and general styling ---
st.markdown("""
<style>
    /* Apply Inter font globally where possible for consistency */
    body {
        font-family: 'Inter', sans-serif;
    }

    /* Primary button styling */
    div.stButton > button {
        background-color: #4CAF50 !important; /* Green background */
        color: black !important; /* Black text for contrast */
        border: none !important;
        border-radius: 8px !important; /* Rounded corners */
        padding: 10px 20px !important; /* Ample padding */
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2); /* Soft shadow */
        transition: all 0.3s ease; /* Smooth hover effect */
        font-weight: bold; /* Make button text bold */
    }
    div.stButton > button:hover {
        background-color: #45a049 !important; /* Darker green on hover */
        box-shadow: 3px 33px 8px rgba(0,0,0,0.3); /* Larger shadow on hover */
        transform: translateY(-2px); /* Slight lift effect */
    }

    /* Table styling for all Streamlit dataframes and custom tables */
    table {
        width: 100%;
        border-collapse: collapse;
        color: black !important; /* Ensure table text is black */
        border-radius: 8px; /* Rounded corners for tables */
        overflow: hidden; /* Ensures rounded corners are visible */
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); /* Soft shadow for tables */
        font-family: 'Inter', sans-serif;
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

    /* Styling for st.metric values (large numbers) */
    .stMetric > div > div:nth-child(2) > div {
        font-size: 2.5em !important; /* Larger font for metric values */
        font-weight: bold !important;
        color: #1a1a1a !important; /* Darker color for emphasis */
        font-family: 'Inter', sans-serif;
    }
    /* Styling for st.metric labels (descriptions) */
    .stMetric > div > div:nth-child(1) {
        font-size: 1.1em !important;
        color: #555 !important;
        font-family: 'Inter', sans-serif;
    }

    /* General text styling for consistency */
    p, label, .stMarkdown, .stText {
        font-family: 'Inter', sans-serif;
        color: #333; /* Darker grey for general text */
    }

    /* Info boxes */
    .stAlert {
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.title("OneLifeTime")
st.write("Ever wondered how many seconds you might have left to live? OneLifeTime is a playful yet thought-provoking web app that gives you a live countdown.")

# --- Fallback life-expectancy data in case Excel file is missing or malformed ---
FALLBACK_LIFE_EXPECTANCY_DATA = pd.DataFrame({
    "Country": ["USA", "Japan", "India", "Brazil", "Nigeria"],
    "Females Life Expectancy": [81.1, 87.5, 70.7, 79.4, 65.2],
    "Males Life Expectancy": [76.1, 81.1, 68.2, 72.8, 62.7]
})

@st.cache_data
def load_life_expectancy_data():
    """
    Loads life expectancy data from 'world-lifeexpectancy.xlsx'.
    Provides robust column mapping and falls back to default data on error or missing columns.
    """
    try:
        df = pd.read_excel("world-lifeexpectancy.xlsx")
    except Exception as e:
        st.warning(f"Error loading 'world-lifeexpectancy.xlsx': {e}. Using fallback data.")
        return FALLBACK_LIFE_EXPECTANCY_DATA

    # Attempt to map column names flexibly
    column_mapping = {}
    for col in df.columns:
        lower_col = col.strip().lower()
        if "country" in lower_col:
            column_mapping[col] = "Country"
        elif "female" in lower_col and "expectancy" in lower_col:
            column_mapping[col] = "Females Life Expectancy"
        elif "male" in lower_col and "expectancy" in lower_col:
            column_mapping[col] = "Males Life Expectancy"

    df = df.rename(columns=column_mapping)

    # Check if all required columns are present after mapping
    required_cols = {"Country", "Females Life Expectancy", "Males Life Expectancy"}
    if not required_cols.issubset(df.columns):
        st.warning(f"Excel file missing one or more required columns ({required_cols}). Using fallback data.")
        return FALLBACK_LIFE_EXPECTANCY_DATA

    return df[list(required_cols)] # Return only the required columns

life_expectancy_df = load_life_expectancy_data()

# --- User Inputs Section ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Your Personal Details")
    country = st.selectbox("Select your country", sorted(life_expectancy_df["Country"].unique()))
    sex = st.radio("Select your sex", ["Male", "Female"], horizontal=True)
    birth_date = st.date_input("Birth date", min_value=datetime(1900, 1, 1))
    birth_time = st.time_input("Birth time")

    # Attempt to set default timezone to user's local timezone
    try:
        default_tz_name = str(datetime.now(pytz.utc).astimezone().tzinfo)
        default_tz_index = pytz.common_timezones.index(default_tz_name)
    except (ValueError, AttributeError):
        default_tz_index = pytz.common_timezones.index("UTC") # Fallback to UTC

    timezone_name = st.selectbox("Time zone", pytz.common_timezones, index=default_tz_index)

    st.markdown("---") # Separator for lifestyle factors
    st.subheader("Lifestyle Factors")
    
    # Gym input
    gym_choice = st.radio("Do you do gym?", ["No", "Yes"], horizontal=True)
    gym_since = None
    if gym_choice == "Yes":
        gym_since = st.selectbox(
            "Gym since:",
            ["Less than a year", "Between 1 and 3 years", "More than 3 years"]
        )

    # Smoking input
    smoke_choice = st.radio("Do you smoke?", ["No", "Yes"], horizontal=True)
    smoke_since = None
    if smoke_choice == "Yes":
        smoke_since = st.selectbox(
            "Smoking since:",
            ["Less than a year", "Between 1 and 5 years",
             "Between 5 and 10 years", "More than 10 years"]
        )

    # Cancer input
    cancer_choice = st.radio("Do you have cancer?", ["No", "Yes"], horizontal=True)

with col2:
    # Display base life expectancy for selected country and sex
    country_data_row = life_expectancy_df[life_expectancy_df["Country"] == country].iloc[0]
    base_life_expectancy = country_data_row["Males Life Expectancy"] if sex == "Male" else country_data_row["Females Life Expectancy"]
    st.info(f"Base life expectancy for **{sex.lower()}s** in **{country}**: **{base_life_expectancy:.1f} years**")

# --- Main Calculation and Display Section ---
if st.button("Calculate My Life Time"):
    # Create timezone-aware datetime objects for birth and current time
    user_timezone = pytz.timezone(timezone_name)
    birth_datetime_aware = user_timezone.localize(datetime.combine(birth_date, birth_time))
    current_datetime_aware = datetime.now(user_timezone)

    # Calculate current age for display purposes
    current_age_delta = relativedelta.relativedelta(current_datetime_aware, birth_datetime_aware)
    st.write(f"You are currently **{current_age_delta.years} years, {current_age_delta.months} months, and {current_age_delta.days} days old**.")

    # Calculate life expectancy adjustment based on lifestyle factors
    life_expectancy_adjustment = 0

    # Gym adjustment
    if gym_choice == "Yes":
        if gym_since == "Less than a year":
            life_expectancy_adjustment += 1
        elif gym_since == "Between 1 and 3 years":
            life_expectancy_adjustment += 4
        else: # More than 3 years
            life_expectancy_adjustment += 7

    # Smoking adjustment
    if smoke_choice == "Yes":
        if smoke_since == "Less than a year":
            life_expectancy_adjustment -= 1
        elif smoke_since == "Between 1 and 5 years":
            life_expectancy_adjustment -= 3
        elif smoke_since == "Between 5 and 10 years":
            life_expectancy_adjustment -= 5
        else: # More than 10 years
            life_expectancy_adjustment -= 10

    # Cancer adjustment
    if cancer_choice == "Yes":
        life_expectancy_adjustment -= 8

    effective_life_expectancy = base_life_expectancy + life_expectancy_adjustment
    # Ensure effective life expectancy does not go below a reasonable minimum
    if effective_life_expectancy < 0.1:
        effective_life_expectancy = 0.1

    st.info(f"Adjusted life expectancy for **{sex.lower()}s** in **{country}** with your lifestyle: **{effective_life_expectancy:.1f} years**")

    # Project the estimated death datetime
    years_component = int(effective_life_expectancy)
    days_component = (effective_life_expectancy - years_component) * DAYS_IN_YEAR_AVG
    projected_death_datetime = (
        birth_datetime_aware
        + relativedelta.relativedelta(years=years_component)
        + timedelta(days=days_component)
    )

    # Calculate total seconds lived and remaining
    seconds_lived = int((current_datetime_aware - birth_datetime_aware).total_seconds())
    seconds_left = int((projected_death_datetime - current_datetime_aware).total_seconds())

    # Ensure seconds left is not negative (if projected death is in the past)
    if seconds_left < 0:
        seconds_left = 0

    # --- Display Seconds Lived vs. Seconds Left ---
    st.subheader("Your Life in Seconds")
    col_lived, col_left = st.columns(2)
    with col_lived:
        st.metric("Seconds Lived", f"{seconds_lived:,}".replace(",", " "))
        st.write(f"That's approximately {seconds_lived / SECONDS_IN_YEAR:.2f} years")
    with col_left:
        st.metric("Seconds Left", f"{seconds_left:,}".replace(",", " "))
        st.write(f"That's approximately {seconds_left / SECONDS_IN_YEAR:.2f} years")

    # --- Global Live Countdown (using st.components.v1.html for persistent JavaScript) ---
    formatted_seconds_left = f"{seconds_left:,}".replace(",", " ")
    global_countdown_html = f"""
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
    " id="global_timer">{formatted_seconds_left}</div>
    <script>
      let countG = {seconds_left};
      // Clear any existing interval to prevent multiple timers on rerun
      if (window.globalCountdownInterval) {{
          clearInterval(window.globalCountdownInterval);
      }}
      window.globalCountdownInterval = setInterval(()=>{{
        countG--;
        if (countG < 0) countG = 0; // Ensure count doesn't go below zero
        const timerElement = document.getElementById('global_timer');
        if (timerElement) {{
            timerElement.innerText = countG.toLocaleString('fr-FR'); // Format with French locale
        }} else {{
            // If element is not found (e.g., page reloaded), clear interval
            clearInterval(window.globalCountdownInterval);
        }}
      }},1000); // Update every 1 second
    </script>
    """
    st.subheader("Your Live Countdown")
    components.html(global_countdown_html, height=150) # Adjusted height for better display

    # --- Projections for Other Countries Section ---
    st.subheader("What If…? You were in the EXTREME sides of the world!")
    
    # Determine the correct column for sorting based on selected sex
    sort_column = "Males Life Expectancy" if sex == "Male" else "Females Life Expectancy"
    
    # Get top 5 and bottom 5 countries based on life expectancy
    top_5_countries = life_expectancy_df.sort_values(sort_column, ascending=False).head(5)
    bottom_5_countries = life_expectancy_df.sort_values(sort_column, ascending=True).head(5)

    def generate_projection_table_html(df_slice, prefix_key):
        """
        Generates HTML for a table of country projections with live countdowns for each row.
        """
        table_rows = []
        js_entries_for_interval = []

        for idx, row_data in df_slice.iterrows():
            # Calculate adjusted life expectancy for this specific country
            current_le = row_data[sort_column] + life_expectancy_adjustment
            if current_le < 0.1: current_le = 0.1 # Minimum life expectancy

            # Project death datetime for this country
            years_part = int(current_le)
            days_part = (current_le - years_part) * DAYS_IN_YEAR_AVG
            projected_dt_country = (
                birth_datetime_aware
                + relativedelta.relativedelta(years=years_part)
                + timedelta(days=days_part)
            )
            
            # Calculate seconds left for this country
            seconds_left_country = int((projected_dt_country - current_datetime_aware).total_seconds())
            if seconds_left_country < 0: seconds_left_country = 0 # Ensure not negative

            cell_unique_id = f"{prefix_key}_cell_{idx}"
            table_rows.append(
                f"<tr>"
                  f"<td>{row_data['Country']}</td>"
                  f"<td id='{cell_unique_id}'>{seconds_left_country:,}</td>"
                  f"<td>{projected_dt_country.strftime('%Y-%m-%d %H:%M:%S')}</td>"
                f"</tr>"
            )
            js_entries_for_interval.append(f"{{id:'{cell_unique_id}',cnt:{seconds_left_country}}}")

        # Construct the full HTML string for the table and its embedded JavaScript
        html_output = f"""
        <style>
          /* Specific styles for these projection tables */
          #projection-table-{prefix_key} table {{
              width:100%;
              border-collapse:collapse;
              color:black!important;
              font-family: 'Inter', sans-serif;
              border-radius: 8px;
              overflow: hidden;
              box-shadow: 0 2px 5px rgba(0,0,0,0.1);
          }}
          #projection-table-{prefix_key} thead th {{
              background:#555;
              padding:10px;
              color:white!important; /* White header text for contrast */
              text-align: left;
          }}
          #projection-table-{prefix_key} td {{
              padding:10px;
              border-top:1px solid #eee;
              color:black!important;
          }}
          #projection-table-{prefix_key} tbody tr:nth-child(even) {{
              background-color: #f8f8f8; /* Zebra striping */
          }}
          #projection-table-{prefix_key} tbody tr:hover {{
              background-color: #f0f0f0;
          }}
        </style>
        <div id="projection-table-{prefix_key}">
            <table>
              <thead>
                <tr><th>Country</th><th>Seconds Left</th><th>Projected Death</th></tr>
              </thead>
              <tbody>
                {''.join(table_rows)}
              </tbody>
            </table>
        </div>
        <script>
          let entries_{prefix_key} = [{','.join(js_entries_for_interval)}];
          // Clear any existing interval for this specific table to prevent multiple timers
          if (window.projectionInterval_{prefix_key}) {{
              clearInterval(window.projectionInterval_{prefix_key});
          }}
          window.projectionInterval_{prefix_key} = setInterval(()=>{{
            entries_{prefix_key}.forEach(e=>{{
              e.cnt--;
              if (e.cnt < 0) e.cnt = 0; // Ensure count doesn't go below zero
              const element = document.getElementById(e.id);
              if (element) {{
                  element.innerText = e.cnt.toLocaleString('fr-FR'); // Format with French locale
              }} else {{
                  // If element is not found, clear interval to prevent errors
                  clearInterval(window.projectionInterval_{prefix_key});
              }}
            }});
          }},1000); // Update every 1 second
        </script>
        """
        return html_output

    col_top, col_bottom = st.columns(2)
    with col_top:
        st.markdown("---") # Separator
        st.markdown("**Top 5 Countries**")
        components.html(generate_projection_table_html(top_5_countries, "top_countries"), height=350)
    with col_bottom:
        st.markdown("---") # Separator
        st.markdown("**Bottom 5 Countries**")
        components.html(generate_projection_table_html(bottom_5_countries, "bottom_countries"), height=350)

# --- Separator before visitor counter ---
st.markdown("---")

# --- Visitor Counter Section (Firestore Integration) ---
# This HTML component handles Firebase initialization and real-time visitor count logic.
# It uses global variables (__app_id, __firebase_config, __initial_auth_token)
# provided by the Canvas environment for Firebase setup.
visitor_counter_html_content = f"""
<div id="visitor-count-container" style="text-align:center; padding:10px; border-radius:8px; background-color:#f0f0f0; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
    <p style="font-size:1.2em; color:black; font-family: 'Inter', sans-serif; margin:0;">
        Total Visitors: <span id="visitor-count" style="font-weight:bold; color:#007bff;">Loading...</span>
    </p>
</div>

<script type="module">
    // Import Firebase SDKs from CDN
    import {{ initializeApp }} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
    import {{ getAuth, signInAnonymously, signInWithCustomToken }} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
    import {{ getFirestore, doc, updateDoc, onSnapshot, increment }} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

    // Access global variables provided by the Canvas environment
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

        async function setupVisitorCounter() {{
            try {{
                // Authenticate the user. Use custom token if available, otherwise sign in anonymously.
                if (initialAuthToken) {{
                    await signInWithCustomToken(auth, initialAuthToken);
                }} else {{
                    await signInAnonymously(auth);
                }}

                // Define the Firestore document reference for the public visitor counter.
                // This path ensures it's stored as public data within the app's artifacts.
                const counterDocRef = doc(db, `artifacts/${appId}/public/data/visitor_counts/main_counter`);

                // Increment the counter on initial load for each unique visit/session.
                // Using merge: true ensures the document is created if it doesn't exist on the first visit.
                await updateDoc(counterDocRef, {{
                    count: increment(1)
                }}, {{ merge: true }});

                // Set up a real-time listener (onSnapshot) to display the current count.
                // This will update the count automatically if other users visit the app.
                onSnapshot(counterDocRef, (docSnap) => {{
                    if (docSnap.exists()) {{
                        const currentCount = docSnap.data().count;
                        if (visitorCountElement) {{
                            visitorCountElement.innerText = currentCount.toLocaleString('fr-FR');
                        }}
                    }} else {{
                        // If the document doesn't exist (e.g., first ever visit), initialize it to 1.
                        // This case should ideally be rare after the initial updateDoc.
                        if (visitorCountElement) {{
                            visitorCountElement.innerText = '1';
                        }}
                    }}
                }}, (error) => {{
                    console.error("Error listening to visitor count:", error);
                    if (visitorCountElement) {{
                        visitorCountElement.innerText = 'Error loading count';
                    }}
                }});

            }} catch (error) {{
                console.error("Firebase initialization or counter setup failed:", error);
                if (visitorCountElement) {{
                    visitorCountElement.innerText = 'Error initializing counter';
                }}
            }}
        }}

        // Execute the visitor counter setup function when the script runs
        setupVisitorCounter();
    }}
</script>
"""
components.html(visitor_counter_html_content, height=80) # Adjust height as needed for the counter display

# --- Footer Text ---
st.markdown(
    "<p style='text-align:center; font-size:12px; color:gray; font-family: 'Inter', sans-serif;'>EmersionDesk © 2025</p>",
    unsafe_allow_html=True
)
