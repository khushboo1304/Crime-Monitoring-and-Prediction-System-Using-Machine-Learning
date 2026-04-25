import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
import seaborn as sns
from folium.plugins import HeatMap
import joblib 

model = joblib.load("crime_model.pkl")

# ---------------- PAGE SETTINGS ----------------
st.set_page_config(page_title="Police Crime Dashboard", layout="wide")

# ---------------- LOGIN SYSTEM ----------------
def load_users():
    with open("users.json") as f:
        return json.load(f)

users = load_users()

def login():
    st.title("🚔 Police Secure Login")
    st.subheader("Authorized Personnel Only")

    username = st.text_input("👮 Username")
    password = st.text_input("🔑 Password", type="password")

    if st.button("Login"):
        if username in users and users[username] == password:
            st.session_state['logged_in'] = True
        else:
            st.error("❌ Invalid Credentials")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login()
    st.stop()

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    return pd.read_csv("combined_crime_data.csv")

df = load_data()

# ---------------- TITLE ----------------
st.title("🚔 Crime Monitoring Dashboard")
st.markdown("### Real-Time Crime Analysis System for Police")

# ---------------- SIDEBAR FILTER ----------------
st.sidebar.header("🔍 Filter Options")

city = st.sidebar.selectbox("Select City", df['City'].unique())

crime = st.sidebar.multiselect(
    "Select Crime Type",
    df[df['City'] == city]['Crime_Type'].unique()
)

if len(crime) > 0:
    filtered_df = df[
        (df['City'] == city) &
        (df['Crime_Type'].isin(crime))
    ]
else:
    filtered_df = df[df['City'] == city]
# ---------------- METRICS ----------------
st.subheader("📊 Overview")

col1, col2, col3 = st.columns(3)

col1.metric("Total Crimes", len(filtered_df))
col2.metric("Crime Types", filtered_df['Crime_Type'].nunique())
col3.metric("Cities", df['City'].nunique())

high_risk_count = len(filtered_df[filtered_df['Risk_Level'] == 'High Risk'])

if high_risk_count > 50:
    st.error("🚨 ALERT: High Crime Area Detected!")
elif high_risk_count > 20:
    st.warning("⚠️ Medium Risk Area")
else:
    st.success("✅ Area is relatively safe")

# ---------------- DATA TABLE ----------------
st.subheader("📄 Crime Records")
st.dataframe(filtered_df.head(50))

# ---------------- CHART ----------------
st.subheader("📊 Crime Distribution")

fig, ax = plt.subplots()
sns.countplot(
    y='Crime_Type',
    data=filtered_df,
    order=filtered_df['Crime_Type'].value_counts().index[:10],
    ax=ax
)
st.pyplot(fig)

# ---------------- MAP ----------------
st.subheader("🌍 Crime Map")

from folium.plugins import HeatMap  # make sure this is at top also

if len(filtered_df) > 0:
    m = folium.Map(
        location=[filtered_df['Latitude'].mean(), filtered_df['Longitude'].mean()],
        zoom_start=10
    )

    # 🔥 HEATMAP (ADD HERE)
    heat_data = filtered_df[['Latitude', 'Longitude']].values.tolist()
    HeatMap(heat_data).add_to(m)

    # 🎯 RISK LEVEL MARKERS (FIXED INDENTATION)
    for _, row in filtered_df.sample(min(500, len(filtered_df))).iterrows():

        if row['Risk_Level'] == 'High Risk':
            color = 'red'
        elif row['Risk_Level'] == 'Medium Risk':
            color = 'orange'
        else:
            color = 'green'

        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=6,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=row['Risk_Level']
        ).add_to(m)

    folium_static(m)

else:
    st.warning("No data available")

# ---------------- ALERT SYSTEM ----------------
st.subheader("⚠️ Area Safety Check")

lat = st.number_input("Enter Latitude(Safety Check)", key="lat1")
lon = st.number_input("Enter Longitud(Safety Check)", key="lon1")

def check_alert(lat, lon):
    for _, row in df.iterrows():
        if abs(lat - row['Latitude']) < 0.01 and abs(lon - row['Longitude']) < 0.01:
            return "🔴 HIGH CRIME AREA!"
    return "🟢 SAFE AREA"

if st.button("Check Safety"):
    result = check_alert(lat, lon)
    if "HIGH" in result:
        st.error(result)
    else:
        st.success(result)

 # 🤖 CRIME PREDICTION
st.subheader("🤖 Crime Prediction")

lat2 = st.number_input("Enter Latitude (Prediction)", key="lat2")
lon2 = st.number_input("Enter Longitude (Prediction)", key="lon2")
month = st.slider("Select Month", 1, 12)

if st.button("Predict Crime"):
    try:
        prediction = model.predict([[lat2, lon2, month]])
        st.success(f"Predicted Crime Type: {prediction[0]}")
    except:
        st.error("Prediction failed. Check model or input.")

# ---------------- DOWNLOAD ----------------
st.subheader("⬇️ Download Report")

csv = filtered_df.to_csv(index=False)
st.download_button("Download CSV", csv, "crime_report.csv")

# ---------------- LOGOUT ----------------
if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.experimental_rerun()

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("🚀 Developed for Police Crime Analysis System")