import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px

DATA_URL = "Motor_Vehicle_Collisions_-_Crashes.csv"


st.title("Motor Vehicle Collisions in New York City")
st.markdown("This application is a Streamlit dashboard that can be used "
            "to analyze motor vehicle collisions in NYC")

@st.cache(persist=True)
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows, parse_dates=[['CRASH DATE', 'CRASH TIME']],
                    dtype={
                        "BOROUGH":str,
                        "ON STREET NAME": str,
                        "CROSS STREET NAME": str,
                        "OFF STREET NAME": str
                        })
    data = data[(data['LONGITUDE'].between(-75, -73)) & (data['LATITUDE'].between(40, 41))]
    data.dropna(subset=['LATITUDE', 'LONGITUDE'], inplace=True)
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis='columns', inplace=True)
    data.rename(columns={'crash date_crash time': 'date/time'}, inplace=True)
    return data

data = load_data(10000)
original_data = data

st.header("Where are the most people injured in NYC?")
injured_people = st.slider("Number of persons injured in vehicle collisions", 0, 19)
st.map(data.query('`number of persons injured` >= @injured_people')[["latitude", "longitude"]].dropna(how="any"))

st.header("How many collisions occur during a given time of day?")
#hour = st.selectbox("Hour to look at", range(0, 24), 1)
#hour = st.sidebar.slider("Hour to look at", 0, 23)
hour = st.slider("Hour to look at", 0, 23)
data = data[data['date/time'].dt.hour == hour]

st.markdown("Vehicle collisions between %i:00 and %i:00" % (hour, hour + 1 % 24))
midpoint = (np.mean(data['latitude']), np.mean(data['longitude']))

st.write(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state={
        "latitude": midpoint[0],
        "longitude": midpoint[1],
        "zoom": 10,
        "pitch": 50,
    },
    layers=[
        pdk.Layer(
        "HexagonLayer",
        data=data[['date/time', 'latitude', 'longitude']],
        get_position=['longitude', 'latitude'],
        radius=100,
        extruded=True,
        pickable=True,
        elevation_scale=4,
        elevation_range=[0,1000],
        ),
    ],
))

st.subheader("Breakdown by minute between %i:00 and %i:00" % (hour, hour + 1 % 24))
filtered = data[
    (data['date/time'].dt.hour >= hour) & (data['date/time'].dt.hour < (hour+1))
]
hist = np.histogram(filtered['date/time'].dt.minute, bins=60, range=(0,60))[0]
chart_data = pd.DataFrame({'minute': range(60),
                            'crashes': hist})
fig = px.bar(chart_data, x='minute', y='crashes', hover_data=['minute', 'crashes'], height=400)
st.write(fig)

if st.checkbox("Show Raw Data Reflecting Your Filters Above", False):
    st.subheader('Raw Data')
    st.write(data)

st.header("Top 5 dangerous streets by affected type")
select = st.selectbox('Choose an affected type of people below:', ['Pedestrians', 'Cyclists', 'Motorists'])

if select == 'Pedestrians':
    st.write(original_data.query('`number of pedestrians injured` >= 1')[['on street name', 'number of pedestrians injured']].sort_values(by=['number of pedestrians injured'],ascending=False).dropna(how='any')[:5])

elif select == 'Cyclists':
    st.write(original_data.query('`number of cyclist injured` >= 1')[['on street name', 'number of cyclist injured']].sort_values(by=['number of cyclist injured'],ascending=False).dropna(how='any')[:5])

else:
    st.write(original_data.query('`number of motorist injured` >= 1')[['on street name', 'number of motorist injured']].sort_values(by=['number of motorist injured'],ascending=False).dropna(how='any')[:5])
