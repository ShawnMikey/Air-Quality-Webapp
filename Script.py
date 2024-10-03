# Melakukan import libraries
import folium
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Threshold air quality
thresh_co = 630
thresh_o3 = 78.5
thresh_no2 = 56.5
thresh_so2 = 78.6
thresh_pm25 = 35
thresh_pm10 = 150

# Threshold kondisi cuaca
thresh_temp_down = 35
thresh_temp_up = 15
thresh_wspm = 10
thresh_dewp_down = 10
thresh_dewp_up = 15
thresh_press_down = 1000
thresh_press_up = 1020

######################################################################################################################
# Beberapa helper functions

# Fungsi untuk membuat report per satu feature
def create_reports(df, feature, param, timewindow):
  dicts = {feature:param}
  report = df.groupby(["station", timewindow]).agg(dicts).reset_index()
  return report

# Fungsi untuk membuat report untuk semua feature
def create_report(df, features, params, timeframe):
  dicts = {}
  for feature in features:
      dicts[feature] = params
  dicts["is_rain"] = "sum"
  report = df.groupby(["station", timeframe]).agg(dicts).reset_index()
  return report

# Fungsi untuk melakukan scoring
def create_scoring(df):
  # Membuat copy dataframe
  dummy = df.copy()

  # Iterate terhadap semua station
  scores = {}
  for station in stations:
    # Membuat report station
    df = dummy[dummy["station"] == station].copy()

    # Membuat scoring untuk konten udara
    df["CO_POINT"] = df["CO"] < thresh_co
    df["O3_POINT"] = df["O3"] < thresh_o3
    df["NO2_POINT"] = df["NO2"] < thresh_no2
    df["SO2_POINT"] = df["SO2"] < thresh_so2
    df["PM25_POINT"] = df["PM2.5"] < thresh_pm25
    df["PM10_POINT"] = df["PM10"] < thresh_pm10

    # Membuat scoring untuk kondisi cuaca
    df["TEMP_POINT"] = (df["TEMP"] > thresh_temp_down) & (df["TEMP"] < thresh_temp_up)
    df["DEW_POINT"] = (df["DEWP"] > thresh_dewp_down) & (df["DEWP"] < thresh_dewp_up)
    df["PRESS_POINT"] = (df["PRES"] > thresh_press_down) & (df["PRES"] < thresh_press_up)
    df["WSPM_POINT"] = df["WSPM"] < thresh_wspm

    # Menghitung score akhir rata-rata semua feature
    score = (df["CO_POINT"].mean() + df["O3_POINT"].mean() + df["NO2_POINT"].mean() + 
             df["SO2_POINT"].mean() + df["PM25_POINT"].mean() + df["PM10_POINT"].mean() + 
             df["TEMP_POINT"].mean() + df["DEW_POINT"].mean() + df["PRESS_POINT"].mean() + 
             df["WSPM_POINT"].mean()) / 10
    scores[station] = score

  return scores

######################################################################################################################

# Meload data csv hasil pengolahan di colab
df = pd.read_csv("air_quality_clean.csv")
datetime_features = ["year", "month", "day", "hour"]
df["date"] = pd.to_datetime(df[datetime_features])

# Membuat title dashboard
st.title('Air Quality Dashboard :fog:')

# Membuat sidebar untuk memilih range tanggal yang dianalisis
with st.sidebar:
    # Menambahkan logo perusahaan
    st.image("soundwave.webp")

    # Menambahkan quotes
    st.write("'Autobots Inferior, Soundwave Superior'")
    st.write("-- Soundwave")
  
    # Mengambil start date dan end date
    start_date, end_date = st.date_input(
        label = "Rentang Waktu",
        min_value = df["date"].min(),
        max_value = df["date"].max(),
        value = [df["date"].min(), df["date"].max()]
    )

# Mengambil dataframe dengan rentang date pada input
dummy = df[(df["date"] >= str(start_date)) & (df["date"] <= str(end_date))]

# Memasukkan feature lintang dan bujur setiap lokasi stasiun dari google maps
# Kemudian melakukan merging dengan dataframe sebelumnya
stasiun = ["Aotizhongxin", "Changping", "Dingling", "Gucheng", "Tiantan", 
           "Dongsi", "Huairou", "Wanliu", "Wanshouxigong", "Nongzhanguan", 
           "Shunyi", "Guanyuan"]
lintang = [39.9936, 40.2181, 40.2915, 39.9129, 39.8821, 39.9333, 
           40.3160, 39.9614, 39.8831, 39.9347, 40.1281, 39.9249]
bujur = [116.4072, 116.2330, 116.2350, 116.2072, 116.4121, 116.4175, 
         116.6315, 116.3050, 116.3665, 116.4633, 116.6543, 116.3415]
results = pd.DataFrame()
results["station"] = stasiun
results["LAT"] = lintang
results["LON"] = bujur
dummy = dummy.merge(results, on = "station", how = "left")

######################################################################################################################

# Membuat subheader #1
st.subheader("Perubahan Kualitas Udara dan Kondisi Cuaca")

# Mengambil kota-kota yang ingin di visualisasi
stations = st.multiselect(
   label = "Pilih Lokasi",
   options = ('Aotizhongxin', 'Changping', 'Dingling', 'Gucheng', 
              'Tiantan', 'Dongsi', 'Huairou', 'Wanliu', 'Wanshouxigong', 
              'Nongzhanguan', 'Shunyi', 'Guanyuan')
)

# Mengambil input hourly, daily, monthly, dan yearly yang ingin di visualisasi
timewindow = st.selectbox(
   label = "Pilih Interval Waktu", 
   options = ('hour', 'day', 'month', 'year')
)

# Mengambil input features yang ingin di visualisasi
feature1 = st.selectbox(
   label = "Pilih Feature Pertama",
   options = ('PM2.5', 'PM10', 'SO2', 'NO2', 
              'CO', 'O3', 'TEMP', 'PRES', 'DEWP', 
              'WSPM', 'RAIN', 'is_rain')
)

# Mengambil input features yang ingin di visualisasi
feature2 = st.selectbox(
   label = "Pilih Feature Kedua",
   options = ('PM2.5', 'PM10', 'SO2', 'NO2', 
              'CO', 'O3', 'TEMP', 'PRES', 'DEWP', 
              'WSPM', 'RAIN', 'is_rain')
)

# Membuat chart placeholder
report_1 = create_reports(dummy, feature1, "mean", timewindow)
report_2 = create_reports(dummy, feature2, "mean", timewindow)

# Looping untuk membuat plot
fig, ax = plt.subplots(2, 1, figsize=(16, 16), sharex = True)
ax = ax.flatten()

for station in stations:
   report_dummy = report_1[report_1["station"] == station]
   ax[0].set_title(report_dummy.columns[2], fontsize = 20)
   sns.lineplot(x = report_dummy.columns[1], y = report_dummy.columns[2], 
                data = report_dummy, label = station, 
                ax = ax[0], palette = "rocket", markers = True)
   ax[0].set_ylabel(" ")

for station in stations:
   report_dummy = report_2[report_2["station"] == station]
   ax[1].set_title(report_dummy.columns[2], fontsize = 20)
   sns.lineplot(x = report_dummy.columns[1], y = report_dummy.columns[2], 
                data = report_dummy, label = station, 
                ax = ax[1], palette = "rocket", markers = True)
   ax[1].set_xlabel(report_dummy.columns[1].upper(), fontsize = 20)
   ax[1].set_ylabel(" ")
   
plt.legend()

st.pyplot(fig)

######################################################################################################################

# Membuat subheader #2
st.subheader("Best Score Kualitas Udara dan Kondisi Cuaca")

# Beberapa list penting
stations = ['Aotizhongxin', 'Changping', 'Dingling', 'Gucheng', 
            'Tiantan', 'Dongsi', 'Huairou', 'Wanliu', 'Wanshouxigong', 
            'Nongzhanguan', 'Shunyi', 'Guanyuan']
numerik = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3',
           'TEMP', 'PRES', 'DEWP', 'RAIN', 'WSPM', 'is_rain']

# Membuat report
hourly = create_report(dummy, numerik, "mean", "hour")
daily = create_report(dummy, numerik, "mean", "day")
monthly = create_report(dummy, numerik, "mean", "month")
yearly = create_report(dummy, numerik, "mean", "year")

# Mendapatkan semua score time window
hourly_score = create_scoring(hourly).values()
daily_score = create_scoring(daily).values()
monthly_score = create_scoring(monthly).values()
yearly_score = create_scoring(yearly).values()

# Membuat dataframe ringkasan
result = pd.DataFrame({"Hourly":hourly_score, "Daily":daily_score, "Monthly":monthly_score, "Yearly":yearly_score})
result.index = stations
result["Mean"] = result.mean(axis = 1)

# Membuat barplot
fig, ax = plt.subplots(figsize=(12, 8))
colors = ["#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4", "#D3D3D3", "#D3D3D3", 
          "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
sns.barplot(x = result["Mean"].sort_values(ascending = False), 
            y = result["Mean"].sort_values(ascending = False).index, 
            palette = colors, ax = ax)
plt.xlabel(" ")
plt.ylabel(" ")
st.pyplot(fig)

######################################################################################################################

# Membuat subheader #3
st.subheader("Peta Lokasi Stasiun Pemantau Udara")

# Membuat map starting location
m = folium.Map(location = (results["LAT"].mean(), results["LON"].mean()), zoom_start = 10)

# Membuat marker
for i in range(12):
  folium.Marker(
      location = [results.iloc[i, 1], results.iloc[i, 2]],
      tooltip = "Click me!",
      popup = results.iloc[i, 0],
      icon = folium.Icon(color = "green"),
  ).add_to(m)

# Meload map
map_html = m._repr_html_()
components.html(map_html, height = 500)

# Penjelasan map
with st.expander("Lihat penjelasan"):
    st.write(
        """Lokasi stasiun pemantau udara mayoritas mengumpul di daerah perkotaan padat/besar 
        yaitu Aotizhongxin, Wanliu, Gucheng, Guanyuan, Dongsi, Nongzhanguan, Wanshouxigong, dan Tiantan. 
        Kota besar ini sebenarnya adalah kota Beijing yang merupakan ibukota China. Sedangkan stasiun 
        udara lain seperti Changping, Dingling, Huairou, dan Shunyi terpisah dan cukup jauh perkotaan 
        padat/besar atau kota Beijing. Hal ini mengakibatkan kualitas udara untuk stasiun pemantau udara 
        dekat Kota Beijing lebih buruk dibandingkan yang bukan.
        """
    )
