# warehouse_zone_optimizer.py

import streamlit as st
import googlemaps
from datetime import datetime
from geopy.distance import geodesic
import os

# ===============================
# CONFIG
# ===============================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
WAREHOUSE_ADDRESS = "198 Morris Rd, Schenectady, NY"
MAX_DRIVERS = 11
MAX_DELIVERY_HOURS = 2  # 2 hours

gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

# ===============================
# SESSION STATE
# ===============================
if "orders" not in st.session_state:
    st.session_state.orders = []

if "delivered_orders" not in st.session_state:
    st.session_state.delivered_orders = {f"DRIVER {i+1}": [] for i in range(MAX_DRIVERS)}

# ===============================
# HELPER FUNCTIONS
# ===============================
def get_travel_time(origin, destination):
    try:
        directions = gmaps.directions(
            origin,
            destination,
            mode="driving",
            departure_time=datetime.now()
        )
        if directions:
            return directions[0]["legs"][0]["duration"]["value"] / 60
    except Exception as e:
        st.warning(f"Google Maps error: {e}")
    return None


def get_coordinates(address):
    result = gmaps.geocode(address)
    if result:
        loc = result[0]["geometry"]["location"]
        return (loc["lat"], loc["lng"])
    return None


def assign_drivers(orders):
    drivers = {f"DRIVER {i+1}": [] for i in range(MAX_DRIVERS)}
    warehouse_coord = get_coordinates(WAREHOUSE_ADDRESS)

    sorted_orders = sorted(orders, key=lambda x: x["timestamp"])

    for order in sorted_orders:
        order_coord = get_coordinates(order["address"])
        if not order_coord:
            continue

        travel_minutes = get_travel_time(WAREHOUSE_ADDRESS, order["address"])
        if not travel_minutes or travel_minutes > MAX_DELIVERY_HOURS * 60:
            continue

        best_driver = None
        min_distance = float("inf")

        for driver, driver_orders in drivers.items():
            if not driver_orders:
                avg_dis_
