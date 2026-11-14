import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib.ticker import FuncFormatter

st.set_page_config(page_title="E-Commerce Dashboard", page_icon="🛒", layout="wide")
sns.set_theme(style="whitegrid")

HIGHLIGHT, MUTED, ALERT = "#1f77b4", "#bdbdbd", "#d62728"
SEGMENT_COLORS = {
    "Loyal Customers": "#2ca02c",
    "Big Spenders (Baru)": HIGHLIGHT,
    "Recent Customers": "#9ecae1",
    "Needs Attention": MUTED,
    "At Risk (Bernilai Tinggi)": "#ff7f0e",
    "Lost / Hibernating": ALERT,
}


def currency_fmt(x, _=None):
    return f"R$ {x / 1e6:.1f} jt" if x >= 1e6 else f"R$ {x / 1e3:.0f} rb"


@st.cache_data
def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main_data.csv")
    df = pd.read_csv(path, parse_dates=["order_purchase_timestamp"])
    df["is_late"] = df["is_late"].astype(bool)
    return df


def build_rfm(df):
    ref_date = df["order_purchase_timestamp"].max().normalize() + pd.Timedelta(days=1)
    rfm = (
        df.groupby("customer_unique_id")
        .agg(last_purchase=("order_purchase_timestamp", "max"),
             frequency=("order_id", "nunique"),
             monetary=("price", "sum"))
        .reset_index()
    )
    rfm["recency"] = (ref_date - rfm["last_purchase"]).dt.days
    n_bins = min(5, len(rfm))
    labels = list(range(1, n_bins + 1))
    rfm["r_score"] = pd.qcut(rfm["recency"].rank(method="first", ascending=False), n_bins, labels=labels).astype(int)
    rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), n_bins, labels=labels).astype(int)

    conditions = [
        rfm["frequency"] >= 2,
        (rfm["r_score"] >= 4) & (rfm["m_score"] >= 4),
        rfm["r_score"] >= 4,
        (rfm["r_score"] <= 2) & (rfm["m_score"] >= 4),
        rfm["r_score"] <= 2,
    ]
    names = ["Loyal Customers", "Big Spenders (Baru)", "Recent Customers",
             "At Risk (Bernilai Tinggi)", "Lost / Hibernating"]
    rfm["segment"] = np.select(conditions, names, default="Needs Attention")
    return rfm, ref_date


# ---------------------------------------------------------------- data & filter
data = load_data()

st.title("🛒 E-Commerce Public Dataset Dashboard")
st.caption("Order berstatus *delivered*, Januari 2017 - Agustus 2018. Revenue = jumlah harga item (tanpa ongkos kirim).")

months = sorted(data["order_month"].unique())
states = sorted(data["customer_state"].dropna().unique())

with st.sidebar:
    st.header("Filter")
    start_m, end_m = st.select_slider("Periode (bulan)", options=months, value=(months[0], months[-1]))
    selected_states = st.multiselect("State pelanggan", options=states, default=[],
                                     placeholder="Semua state")
    st.markdown("---")
    st.caption("Kosongkan filter state untuk menampilkan seluruh wilayah.")

mask = (data["order_month"] >= start_m) & (data["order_month"] <= end_m)
if selected_states:
    mask &= data["customer_state"].isin(selected_states)
df = data[mask]

if df.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

# ---------------------------------------------------------------- KPI
order_level = (
    df.groupby("order_id")
    .agg(customer_unique_id=("customer_unique_id", "first"), customer_state=("customer_state", "first"),
         revenue=("price", "sum"), is_late=("is_late", "first"), delay_days=("delay_days", "first"),
         review_score=("review_score", "first"))
    .reset_index()
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Revenue", f"R$ {df['price'].sum():,.0f}")
c2.metric("Jumlah Order", f"{order_level.shape[0]:,}")
c3.metric("Pelanggan Unik", f"{df['customer_unique_id'].nunique():,}")
c4.metric("% Order Terlambat", f"{order_level['is_late'].mean() * 100:.1f}%")
c5.metric("Rata-rata Review", f"{order_level['review_score'].mean():.2f}")

tab1, tab2, tab3, tab4 = st.tabs(["Kategori Produk", "Tren Bulanan", "Wilayah & Pengiriman", "Segmentasi RFM"])

# ---------------------------------------------------------------- Tab 1
with tab1:
    st.subheader("Kategori produk dengan revenue tertinggi dan terendah")
    cat = (df.groupby("category").agg(revenue=("price", "sum"), orders=("order_id", "nunique"))
           .sort_values("revenue", ascending=False))
    cat["pct_revenue"] = cat["revenue"] / cat["revenue"].sum() * 100

    n_top = st.slider("Jumlah kategori teratas", 5, 20, 10)
    top = cat.head(n_top).sort_values("revenue")
    bottom = cat.tail(5).sort_values("revenue", ascending=False)

    col_a, col_b = st.columns([1.5, 1])
    with col_a:
        fig, ax = plt.subplots(figsize=(9, 6))
        colors = [HIGHLIGHT if i >= len(top) - 3 else MUTED for i in range(len(top))]
        ax.barh(top.index, top["revenue"], color=colors)
        for y, (rev, pct) in enumerate(zip(top["revenue"], top["pct_revenue"])):
            ax.text(rev, y, f"  {rev / 1e6:.2f} jt ({pct:.1f}%)", va="center", fontsize=8)
        ax.set_xlim(0, top["revenue"].max() * 1.3)
        ax.xaxis.set_major_formatter(FuncFormatter(currency_fmt))
        ax.set_title(f"{n_top} Kategori dengan Revenue Tertinggi", loc="left", fontweight="bold")
        ax.set_xlabel("Total revenue (R$)"); ax.set_ylabel("")
        sns.despine(); plt.tight_layout()
        st.pyplot(fig); plt.close(fig)
    with col_b:
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.barh(bottom.index, bottom["revenue"], color=ALERT)
        for y, rev in enumerate(bottom["revenue"]):
            ax.text(rev, y, f"  R$ {rev:,.0f}", va="center", fontsize=8)
        ax.set_xlim(0, bottom["revenue"].max() * 1.35)
        ax.set_title("5 Kategori dengan Revenue Terendah", loc="left", fontweight="bold")
        ax.set_xlabel("Total revenue (R$)"); ax.set_ylabel("")
        sns.despine(); plt.tight_layout()
        st.pyplot(fig); plt.close(fig)
    st.info(f"{n_top} kategori teratas menyumbang **{cat.head(n_top)['pct_revenue'].sum():.1f}%** dari total revenue pada filter ini.")

# ---------------------------------------------------------------- Tab 2
with tab2:
    st.subheader("Tren order dan revenue bulanan")
    monthly = (df.groupby("order_month").agg(revenue=("price", "sum"), orders=("order_id", "nunique")))
    monthly["MoM revenue (%)"] = monthly["revenue"].pct_change() * 100

    fig, ax1 = plt.subplots(figsize=(13, 5))
    x = np.arange(len(monthly))
    ax1.bar(x, monthly["revenue"], color=MUTED, label="Revenue (R$)")
    ax1.yaxis.set_major_formatter(FuncFormatter(currency_fmt))
    ax1.set_xticks(x); ax1.set_xticklabels(monthly.index, rotation=45, ha="right")
    ax1.set_ylabel("Revenue (R$)")
    ax2 = ax1.twinx()
    ax2.plot(x, monthly["orders"], color=HIGHLIGHT, marker="o", linewidth=2.5, label="Jumlah order")
    ax2.set_ylabel("Jumlah order"); ax2.grid(False)
    peak = monthly["revenue"].idxmax()
    ax1.set_title(f"Puncak revenue: {peak} (R$ {monthly.loc[peak, 'revenue'] / 1e6:.2f} jt)",
                  loc="left", fontweight="bold")
    h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", frameon=False)
    sns.despine(right=False); plt.tight_layout()
    st.pyplot(fig); plt.close(fig)

    st.dataframe(
        monthly.rename(columns={"revenue": "Revenue (R$)", "orders": "Order"})
        .style.format({"Revenue (R$)": "{:,.0f}", "Order": "{:,.0f}", "MoM revenue (%)": "{:+.1f}"}, na_rep="-"),
        use_container_width=True,
    )

# ---------------------------------------------------------------- Tab 3
with tab3:
    st.subheader("Revenue, keterlambatan, dan kepuasan per state")
    state_perf = (
        order_level.groupby("customer_state")
        .agg(customers=("customer_unique_id", "nunique"), orders=("order_id", "count"),
             revenue=("revenue", "sum"), late_pct=("is_late", lambda s: s.mean() * 100),
             avg_review=("review_score", "mean"))
        .sort_values("revenue", ascending=False)
    )
    overall_late = order_level["is_late"].mean() * 100
    top_states = state_perf.head(10).sort_values("revenue")

    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    axes[0].barh(top_states.index, top_states["revenue"], color=HIGHLIGHT)
    axes[0].xaxis.set_major_formatter(FuncFormatter(currency_fmt))
    axes[0].set_title("Revenue (R$)", loc="left", fontweight="bold")
    axes[1].barh(top_states.index, top_states["late_pct"],
                 color=[ALERT if v > overall_late else MUTED for v in top_states["late_pct"]])
    axes[1].axvline(overall_late, color="black", linestyle="--", linewidth=1)
    axes[1].set_title(f"% Order terlambat (rata-rata {overall_late:.1f}%)", loc="left", fontweight="bold")
    axes[2].barh(top_states.index, top_states["avg_review"], color=MUTED)
    axes[2].set_xlim(0, 5)
    axes[2].set_title("Rata-rata review score", loc="left", fontweight="bold")
    sns.despine(); plt.tight_layout()
    st.pyplot(fig); plt.close(fig)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Peta sebaran order (per kode pos pelanggan)**")
        geo = (df.dropna(subset=["lat", "lng"]).groupby(["lat", "lng"], as_index=False)
               .agg(orders=("order_id", "nunique")))
        geo["size"] = np.clip(geo["orders"] * 300, 300, 8000)
        st.map(geo, latitude="lat", longitude="lng", size="size")
    with col_b:
        st.markdown("**Keterlambatan vs review score (binning)**")
        og = order_level.dropna(subset=["review_score"]).copy()
        og["delay_group"] = pd.cut(og["delay_days"], bins=[-999, 0, 3, 7, 999],
                                   labels=["Tepat waktu", "Telat 1-3 hari", "Telat 4-7 hari", "Telat >7 hari"])
        dr = og.groupby("delay_group", observed=True).agg(orders=("order_id", "count"),
                                                           avg_review=("review_score", "mean"))
        fig, ax = plt.subplots(figsize=(6, 4.2))
        bars = ax.bar(dr.index.astype(str), dr["avg_review"], color=["#2ca02c", "#f0c419", "#ff7f0e", ALERT][:len(dr)])
        for b, v, n in zip(bars, dr["avg_review"], dr["orders"]):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.05, f"{v:.2f}\n({n:,})", ha="center", fontsize=9)
        ax.set_ylim(0, 5.3); ax.set_ylabel("Rata-rata review score")
        plt.xticks(rotation=10); sns.despine(); plt.tight_layout()
        st.pyplot(fig); plt.close(fig)

    st.dataframe(state_perf.round(2), use_container_width=True)

# ---------------------------------------------------------------- Tab 4
with tab4:
    st.subheader("Segmentasi pelanggan (RFM)")
    if df["customer_unique_id"].nunique() < 5:
        st.warning("Jumlah pelanggan terlalu sedikit untuk segmentasi RFM. Perluas filter.")
    else:
        rfm, ref_date = build_rfm(df)
        st.caption(f"Tanggal acuan recency: {ref_date.date()} (1 hari setelah transaksi terakhir pada filter). "
                   "Frequency dikelompokkan manual (1 vs >= 2 order); skor Recency dan Monetary memakai kuintil.")

        seg = (rfm.groupby("segment")
               .agg(customers=("customer_unique_id", "count"), avg_recency=("recency", "mean"),
                    avg_frequency=("frequency", "mean"), avg_monetary=("monetary", "mean"), revenue=("monetary", "sum"))
               .sort_values("customers"))
        seg["pct_customers"] = seg["customers"] / seg["customers"].sum() * 100
        seg["pct_revenue"] = seg["revenue"] / seg["revenue"].sum() * 100
        colors = [SEGMENT_COLORS[s] for s in seg.index]

        fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
        for ax, col, title in zip(axes, ["pct_customers", "pct_revenue"], ["% Pelanggan", "% Revenue"]):
            ax.barh(seg.index, seg[col], color=colors)
            for y, v in enumerate(seg[col]):
                ax.text(v, y, f" {v:.1f}%", va="center", fontsize=9)
            ax.set_xlim(0, seg[col].max() * 1.2)
            ax.set_title(title, loc="left", fontweight="bold")
        sns.despine(); plt.tight_layout()
        st.pyplot(fig); plt.close(fig)

        st.dataframe(
            seg.sort_values("customers", ascending=False)[
                ["customers", "pct_customers", "avg_recency", "avg_frequency", "avg_monetary", "revenue", "pct_revenue"]
            ].round(2),
            use_container_width=True,
        )

        st.markdown("**Top 10 pelanggan berdasarkan monetary**")
        st.dataframe(rfm.sort_values("monetary", ascending=False).head(10)
                     [["customer_unique_id", "recency", "frequency", "monetary", "segment"]].round(2),
                     use_container_width=True, hide_index=True)

st.caption("Proyek Analisis Data - E-Commerce Public Dataset")
