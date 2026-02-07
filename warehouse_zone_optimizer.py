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
                avg_distance = geodesic(warehouse_coord, order_coord).miles
            else:
                distances = [
                    geodesic(get_coordinates(o["address"]), order_coord).miles
                    for o in driver_orders
                ]
                avg_distance = sum(distances) / len(distances)

            if avg_distance < min_distance:
                min_distance = avg_distance
                best_driver = driver

        if best_driver:
            drivers[best_driver].append(order)

    for driver in drivers:
        drivers[driver].sort(key=lambda x: x["timestamp"])

    return drivers


def clear_orders(delivered_orders):
    st.session_state.orders = [
        o for o in st.session_state.orders if o not in delivered_orders
    ]

# ===============================
# STREAMLIT UI
# ===============================
st.title("Order Classification")

st.subheader("Add New Order")
new_address = st.text_input("Enter Customer Address")

if st.button("Add Order"):
    if new_address:
        st.session_state.orders.append(
            {"address": new_address, "timestamp": datetime.now()}
        )
        st.success(f"Added: {new_address}")

drivers = assign_drivers(st.session_state.orders)

st.subheader("Driver Assignments")

for driver_name, driver_orders in drivers.items():
    st.markdown(f"### 🚚 {driver_name}")

    if driver_orders:
        for i, order in enumerate(driver_orders, 1):
            st.write(
                f"{i}. {order['address']} "
                f"(Added: {order['timestamp'].strftime('%H:%M:%S')})"
            )
    else:
        st.info("No orders assigned")

    if driver_orders and st.button(f"DONE - {driver_name}", key=driver_name):
        clear_orders(driver_orders)
        st.success(f"{driver_name} completed deliveries")
        st.experimental_rerun()


