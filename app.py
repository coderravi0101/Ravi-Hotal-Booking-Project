import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Hotel Booking Analytics",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_PATH = Path(__file__).parent / "Hotel Bookings.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    # Dataset-specific cleaning
    if "children" in df.columns:
        df["children"] = df["children"].fillna(0)
    if "country" in df.columns:
        df["country"] = df["country"].fillna("Unknown")
    if "agent" in df.columns:
        df["agent"] = df["agent"].fillna(0)
    if "company" in df.columns:
        df["company"] = df["company"].fillna(0)

    if "reservation_status_date" in df.columns:
        df["reservation_status_date"] = pd.to_datetime(
            df["reservation_status_date"], errors="coerce"
        )

    if "arrival_date_month" in df.columns:
        month_order = [
            "January","February","March","April","May","June",
            "July","August","September","October","November","December"
        ]
        df["arrival_date_month"] = pd.Categorical(
            df["arrival_date_month"], categories=month_order, ordered=True
        )

    df["total_nights"] = (
        df.get("stays_in_weekend_nights", 0).fillna(0)
        + df.get("stays_in_week_nights", 0).fillna(0)
    )
    df["total_guests"] = (
        df.get("adults", 0).fillna(0)
        + df.get("children", 0).fillna(0)
        + df.get("babies", 0).fillna(0)
    )
    df["estimated_revenue"] = df["adr"].fillna(0) * df["total_nights"]
    return df

df = load_data()

# ---------------- Sidebar ----------------
st.sidebar.title("🏨 Hotel Analytics")
st.sidebar.caption("Interactive hotel booking dashboard")

hotel_options = ["All"] + sorted(df["hotel"].dropna().unique().tolist())
hotel_filter = st.sidebar.selectbox("Hotel", hotel_options)

year_options = ["All"] + sorted(df["arrival_date_year"].dropna().unique().tolist())
year_filter = st.sidebar.selectbox("Arrival year", year_options)

segment_options = ["All"] + sorted(df["market_segment"].dropna().astype(str).unique().tolist())
segment_filter = st.sidebar.selectbox("Market segment", segment_options)

customer_options = ["All"] + sorted(df["customer_type"].dropna().astype(str).unique().tolist())
customer_filter = st.sidebar.selectbox("Customer type", customer_options)

cancel_options = ["All", "Not Cancelled", "Cancelled"]
cancel_filter = st.sidebar.selectbox("Booking status", cancel_options)

filtered = df.copy()

if hotel_filter != "All":
    filtered = filtered[filtered["hotel"] == hotel_filter]
if year_filter != "All":
    filtered = filtered[filtered["arrival_date_year"] == year_filter]
if segment_filter != "All":
    filtered = filtered[filtered["market_segment"].astype(str) == segment_filter]
if customer_filter != "All":
    filtered = filtered[filtered["customer_type"].astype(str) == customer_filter]
if cancel_filter == "Cancelled":
    filtered = filtered[filtered["is_canceled"] == 1]
elif cancel_filter == "Not Cancelled":
    filtered = filtered[filtered["is_canceled"] == 0]

# ---------------- Header ----------------
st.title("🏨 Hotel Booking Analytics Dashboard")
st.markdown(
    "Explore booking demand, cancellations, pricing, customer behavior, "
    "market segments and operational patterns."
)

st.caption(
    f"Showing {len(filtered):,} bookings out of {len(df):,} total records."
)

# ---------------- KPIs ----------------
total_bookings = len(filtered)
cancel_rate = filtered["is_canceled"].mean() * 100 if total_bookings else 0
avg_adr = filtered["adr"].mean() if total_bookings else 0
avg_stay = filtered["total_nights"].mean() if total_bookings else 0
repeat_rate = (
    (filtered["is_repeated_guest"] == 1).mean() * 100 if total_bookings else 0
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Bookings", f"{total_bookings:,}")
c2.metric("Cancellation Rate", f"{cancel_rate:.1f}%")
c3.metric("Average ADR", f"${avg_adr:,.2f}")
c4.metric("Avg. Stay", f"{avg_stay:.2f} nights")
c5.metric("Repeat Guests", f"{repeat_rate:.1f}%")

st.divider()

# ---------------- Tabs ----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview", "❌ Cancellations", "👥 Customers", "💰 Revenue & Stay", "🔎 Data Explorer"]
)

with tab1:
    st.subheader("Booking Overview")

    col1, col2 = st.columns(2)

    with col1:
        if len(filtered):
            yearly = (
                filtered.groupby("arrival_date_year", as_index=False)
                .size()
                .rename(columns={"size": "bookings"})
            )
            fig = px.bar(
                yearly,
                x="arrival_date_year",
                y="bookings",
                title="Bookings by Arrival Year",
                labels={"arrival_date_year": "Year", "bookings": "Bookings"},
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        monthly = (
            filtered.groupby("arrival_date_month", observed=False)
            .size()
            .reset_index(name="bookings")
        )
        fig = px.line(
            monthly,
            x="arrival_date_month",
            y="bookings",
            markers=True,
            title="Bookings by Arrival Month",
            labels={"arrival_date_month": "Month", "bookings": "Bookings"},
        )
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        hotel_counts = filtered["hotel"].value_counts().reset_index()
        hotel_counts.columns = ["hotel", "bookings"]
        fig = px.pie(
            hotel_counts,
            names="hotel",
            values="bookings",
            hole=0.45,
            title="Bookings by Hotel",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        market = filtered["market_segment"].value_counts().reset_index()
        market.columns = ["market_segment", "bookings"]
        fig = px.bar(
            market.sort_values("bookings"),
            x="bookings",
            y="market_segment",
            orientation="h",
            title="Bookings by Market Segment",
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Cancellation Analysis")

    col1, col2 = st.columns(2)

    with col1:
        cancellation = (
            filtered.groupby("hotel")["is_canceled"]
            .mean()
            .mul(100)
            .reset_index(name="cancellation_rate")
        )
        fig = px.bar(
            cancellation,
            x="hotel",
            y="cancellation_rate",
            title="Cancellation Rate by Hotel",
            labels={"cancellation_rate": "Cancellation Rate (%)"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        segment_cancel = (
            filtered.groupby("market_segment")["is_canceled"]
            .mean()
            .mul(100)
            .reset_index(name="cancellation_rate")
            .sort_values("cancellation_rate")
        )
        fig = px.bar(
            segment_cancel,
            x="cancellation_rate",
            y="market_segment",
            orientation="h",
            title="Cancellation Rate by Market Segment",
            labels={"cancellation_rate": "Cancellation Rate (%)"},
        )
        st.plotly_chart(fig, use_container_width=True)

    if len(filtered):
        fig = px.histogram(
            filtered,
            x="lead_time",
            color="is_canceled",
            nbins=40,
            barmode="overlay",
            title="Lead Time vs Booking Cancellation",
            labels={"lead_time": "Lead Time (days)", "is_canceled": "Cancelled"},
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Customer & Booking Behavior")

    col1, col2 = st.columns(2)

    with col1:
        customer = filtered["customer_type"].value_counts().reset_index()
        customer.columns = ["customer_type", "bookings"]
        fig = px.pie(
            customer,
            names="customer_type",
            values="bookings",
            hole=0.45,
            title="Bookings by Customer Type",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        repeat = filtered["is_repeated_guest"].value_counts().reset_index()
        repeat.columns = ["is_repeated_guest", "bookings"]
        repeat["guest_type"] = repeat["is_repeated_guest"].map(
            {0: "New Guest", 1: "Repeated Guest"}
        )
        fig = px.bar(
            repeat,
            x="guest_type",
            y="bookings",
            title="New vs Repeated Guests",
        )
        st.plotly_chart(fig, use_container_width=True)

    top_countries = (
        filtered["country"]
        .fillna("Unknown")
        .astype(str)
        .value_counts()
        .head(15)
        .sort_values()
        .reset_index()
    )
    top_countries.columns = ["country", "bookings"]
    fig = px.bar(
        top_countries,
        x="bookings",
        y="country",
        orientation="h",
        title="Top 15 Booking Countries",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Revenue, Pricing & Length of Stay")

    col1, col2 = st.columns(2)

    with col1:
        adr_by_month = (
            filtered.groupby("arrival_date_month", observed=False)["adr"]
            .mean()
            .reset_index()
        )
        fig = px.line(
            adr_by_month,
            x="arrival_date_month",
            y="adr",
            markers=True,
            title="Average Daily Rate by Month",
            labels={"adr": "Average Daily Rate"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        stay_counts = filtered["total_nights"].value_counts().sort_index().head(20)
        stay_df = stay_counts.reset_index()
        stay_df.columns = ["total_nights", "bookings"]
        fig = px.bar(
            stay_df,
            x="total_nights",
            y="bookings",
            title="Length of Stay Distribution",
            labels={"total_nights": "Total Nights"},
        )
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        meal = filtered["meal"].value_counts().reset_index()
        meal.columns = ["meal", "bookings"]
        fig = px.pie(
            meal,
            names="meal",
            values="bookings",
            title="Meal Type Distribution",
            hole=0.4,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        parking = filtered["required_car_parking_spaces"].value_counts().sort_index()
        parking_df = parking.reset_index()
        parking_df.columns = ["parking_spaces", "bookings"]
        fig = px.bar(
            parking_df,
            x="parking_spaces",
            y="bookings",
            title="Required Car Parking Spaces",
        )
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("Interactive Data Explorer")
    st.write("Use the sidebar filters to narrow the records, then download the filtered dataset.")

    display_cols = [
        c for c in [
            "hotel", "is_canceled", "lead_time", "arrival_date_year",
            "arrival_date_month", "arrival_date_week_number",
            "stays_in_weekend_nights", "stays_in_week_nights",
            "adults", "children", "babies", "meal", "country",
            "market_segment", "customer_type", "adr", "total_nights",
            "total_guests", "total_of_special_requests"
        ] if c in filtered.columns
    ]

    st.dataframe(
        filtered[display_cols],
        use_container_width=True,
        height=500,
    )

    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Filtered CSV",
        data=csv,
        file_name="filtered_hotel_bookings.csv",
        mime="text/csv",
    )

st.divider()

st.markdown(
    "<div style='text-align:center; color:gray;'>"
    "Hotel Booking Analytics • Streamlit Portfolio Project"
    "</div>",
    unsafe_allow_html=True,
)
