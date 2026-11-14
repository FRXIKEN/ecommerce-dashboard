# E-Commerce Public Dataset Analysis Dashboard ✨

Proyek analisis data transaksi marketplace Brasil (Olist) periode **Januari 2017 - Agustus 2018** (order berstatus `delivered`).
Analisis menjawab empat pertanyaan bisnis (SMART):

1. Kategori produk apa saja yang menjadi 10 penyumbang revenue terbesar dan 5 terendah, dan berapa persen kontribusinya?
2. Bagaimana tren order dan revenue bulanan (pertumbuhan MoM) dan kapan puncaknya?
3. State mana yang menyumbang revenue terbesar, dan berapa % order terlambat serta rata-rata review score di tiap state?
4. Bagaimana segmentasi pelanggan berdasarkan RFM (per 30 Agustus 2018)?

## Struktur Direktori

```
submission
├── dashboard
│   ├── main_data.csv      # data per item order (sudah bersih)
│   └── dashboard.py       # aplikasi Streamlit
├── data
│   └── *.csv              # data mentah (9 berkas)
├── notebook.ipynb         # proses analisis lengkap
├── README.md
├── requirements.txt
└── url.txt                # tautan dashboard di Streamlit Cloud
```

## Setup Environment

Disarankan menggunakan Python 3.9 atau lebih baru.

**Shell / Terminal (venv)**
```
cd submission
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Anaconda**
```
conda create --name ecommerce-ds python=3.11
conda activate ecommerce-ds
pip install -r requirements.txt
```

## Menjalankan Dashboard

```
cd submission
streamlit run dashboard/dashboard.py
```

Dashboard akan terbuka di `http://localhost:8501`. Fitur: filter periode dan state, KPI ringkas, dan empat tab
(Kategori Produk, Tren Bulanan, Wilayah & Pengiriman termasuk peta dan binning keterlambatan, Segmentasi RFM).

## Menjalankan Notebook

Jalankan dari folder `submission` agar path `data/` terbaca. Instal Jupyter terlebih dahulu (`pip install jupyter`), lalu buka
`notebook.ipynb` dengan Jupyter/VS Code/Colab dan jalankan seluruh sel dari atas ke bawah.
Sel pada tahap *Cleaning Data* akan membuat ulang `dashboard/main_data.csv`. (Di Colab, unggah folder `data/` terlebih dahulu.)

## Deploy ke Streamlit Community Cloud

1. Unggah folder `submission` ke repositori GitHub.
2. Di https://share.streamlit.io pilih *New app*, lalu atur **Main file path** ke `dashboard/dashboard.py`.
3. Salin URL aplikasi ke `url.txt`.

## Sumber Data

Brazilian E-Commerce Public Dataset by Olist (Kaggle), versi yang disediakan Dicoding.
