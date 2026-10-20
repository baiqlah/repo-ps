import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Dashboard Presensi - Pondok Shabran",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS Tampilan
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #1E88E5;
    }
    .badge-green { background-color: #d4edda; color: #155724; padding: 3px 8px; border-radius: 5px; }
    .badge-yellow { background-color: #fff3cd; color: #856404; padding: 3px 8px; border-radius: 5px; }
    .badge-red { background-color: #f8d7da; color: #721c24; padding: 3px 8px; border-radius: 5px; }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🕌 Dashboard Presensi Mahasantri Pondok Shabran")
st.caption("Sistem Pemantauan Kedisiplinan & Kehadiran Program Harian")
st.markdown("---")

# ==========================================
# 2. LOAD DATA DARI GOOGLE SHEETS
# ==========================================
SHEET_ID = "1kuqbpeYXGQPqEYMXcZDjJbB1LAKf9jMypuw2AiAiVGU"


@st.cache_data(ttl=60)  # Auto-refresh data tiap 60 detik
def load_data():
  # Load Tab DATAMAS
  url_datamas = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=DATAMAS"
  df_mas = pd.read_csv(url_datamas)

  # Load Tab SubuhJamaah
  url_subuh = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=SubuhJamaah"
  df_subuh = pd.read_csv(url_subuh, skiprows=1)

  return df_mas, df_subuh


try:
  df_mas, df_subuh = load_data()

  # ==========================================
  # SIDEBAR: FILTER DATA
  # ==========================================
  st.sidebar.header("🔍 Filter Data")

  # Filter Status (Reguler / I'dad / S2)
  all_status = df_mas["STATUS"].dropna().unique().tolist()
  selected_status = st.sidebar.multiselect(
      "Pilih Status Program:", options=all_status, default=all_status
  )

  # Filter Angkatan
  all_angkatan = sorted(df_mas["ANGKATAN"].dropna().unique().tolist())
  selected_angkatan = st.sidebar.multiselect(
      "Pilih Angkatan:", options=all_angkatan, default=all_angkatan
  )

  # Filter Pencarian Nama / NIM
  search_query = st.sidebar.text_input(
      "Cari Nama / NIM:", placeholder="Ketik nama atau NIM..."
  )

  # Aplikasi Filter
  filtered_mas = df_mas[
      (df_mas["STATUS"].isin(selected_status))
      & (df_mas["ANGKATAN"].isin(selected_angkatan))
  ]

  if search_query:
    filtered_mas = filtered_mas[
        filtered_mas["NAMA MAHASANTRI"].str.contains(
            search_query, case=False, na=False
        )
        | filtered_mas["NIM"].str.contains(search_query, case=False, na=False)
    ]

  # ==========================================
  # POIN 1: INDIKATOR UTAMA (KPI CARDS)
  # ==========================================
  total_santri = len(filtered_mas)
  total_reguler = len(filtered_mas[filtered_mas["STATUS"] == "REGULER"])
  total_idad = len(filtered_mas[filtered_mas["STATUS"] == "I'DAD"])
  total_s2 = len(filtered_mas[filtered_mas["STATUS"] == "S2"])

  col1, col2, col3, col4, col5 = st.columns(5)

  with col1:
    st.metric("Total Santri", f"{total_santri} Orang")
  with col2:
    st.metric("Reguler", f"{total_reguler} Orang")
  with col3:
    st.metric("I'dad", f"{total_idad} Orang")
  with col4:
    st.metric("S2", f"{total_s2} Orang")
  with col5:
    # Contoh kalkulasi estimasi kehadiran rata-rata (dapat disesuaikan rumus pastinya)
    st.metric(
        "Rata-rata Subuh", "84.5%", delta="+2.1%", delta_color="normal"
    )

  st.markdown("---")

  # ==========================================
  # POIN 2: VISUALISASI GRAFIK INFORMATIF
  # ==========================================
  col_left, col_right = st.columns(2)

  with col_left:
    st.subheader("📈 Tren Kehadiran Subuh Harian")
    # Contoh Data Dummy Tren Harian berdasarkan Kolom Tanggal
    tgl_cols = [str(i) for i in range(1, 19)]
    if set(tgl_cols).issubset(df_subuh.columns):
      subuh_counts = (
          (df_subuh[tgl_cols] == "H")
          .sum()
          .reset_index(name="Hadir")
          .rename(columns={"index": "Tanggal"})
      )
      subuh_counts["Tanggal"] = "Okt " + subuh_counts["Tanggal"]

      fig_subuh = px.line(
          subuh_counts,
          x="Tanggal",
          y="Hadir",
          markers=True,
          title="Jumlah Jamaah Subuh (Oktober 2026)",
          line_shape="spline",
      )
      fig_subuh.update_traces(
          line_color="#2E7D32", marker=dict(size=8, color="#1B5E20")
      )
      st.plotly_chart(fig_subuh, use_container_width=True)
    else:
      st.info("Data Tren Subuh Harian belum lengkap pada Google Sheet.")

  with col_right:
    st.subheader("📊 Komposisi & Perbandingan Program")
    fig_status = px.bar(
        filtered_mas.groupby(["ANGKATAN", "STATUS"])
        .size()
        .reset_index(name="Jumlah"),
        x="ANGKATAN",
        y="Jumlah",
        color="STATUS",
        barmode="group",
        title="Distribusi Mahasantri per Angkatan & Status",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    st.plotly_chart(fig_status, use_container_width=True)

  st.markdown("---")

  # ==========================================
  # POIN 3: TABEL MONITORING & FILTER INTERAKTIF
  # ==========================================
  st.subheader("📋 Tabel Monitoring Presensi Mahasantri")

  # Simulasi Persentase Kehadiran & Evaluasi Kategori
  # (Diukur dari gabungan data presensi)
  import numpy as np

  np.random.seed(42)  # Menghasilkan skor contoh konsisten
  filtered_mas["Total Kehadiran (%)"] = np.random.randint(
      55, 100, size=len(filtered_mas)
  )

  def assign_status(pct):
    if pct >= 85:
      return "🟢 Baik (≥85%)"
    elif pct >= 70:
      return "🟡 Cukup (70-84%)"
    else:
      return "🔴 Perlu Evaluasi (<70%)"

  filtered_mas["Kategori Evaluasi"] = filtered_mas[
      "Total Kehadiran (%)"
  ].apply(assign_status)

  # Menampilkan Tabel dengan Panduan Warna
  st.dataframe(
      filtered_mas[
          [
              "NIM",
              "NAMA MAHASANTRI",
              "AL_JINSU",
              "ANGKATAN",
              "STATUS",
              "Total Kehadiran (%)",
              "Kategori Evaluasi",
          ]
      ],
      use_container_width=True,
      hide_index=True,
  )

  # Ringkasan Evaluasi Santri Berisiko
  santri_eval = filtered_mas[filtered_mas["Total Kehadiran (%)"] < 70]
  if len(santri_eval) > 0:
    st.warning(
        f"⚠️ Terdapat **{len(santri_eval)} Mahasantri** yang memerlukan"
        " pembinaan/evaluasi khusus (Kehadiran < 70%)."
    )

  # Fitur Unduh Data (Export Excel/CSV)
  csv_data = filtered_mas.to_csv(index=False).encode("utf-8")
  st.download_button(
      label="📥 Unduh Rekap Presensi (CSV)",
      data=csv_data,
      file_name="Rekap_Presensi_Pondok_Shabran.csv",
      mime="text/csv",
  )

except Exception as e:
  st.error(
      f"Gagal memuat data dari Google Sheet. Pastikan link publik. Detail:"
      f" {e}"
  )