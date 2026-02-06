# warehouse_zone_optimizer.py

import streamlit as st
import googlemaps
from datetime import datetime, timedelta
import pandas as pd
from geopy.distance import geodesic

# ===============================
# CONFIG
# ===============================
import os
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
WAREHOUSE_ADDRESS = "198 Morris Rd, Schenectady, NY"
MAX_ZONES = 10
MAX_DELIVERY_HOURS = 2  # 2 hours

# Initialize Google Maps client
gmaps = googlemaps.Client(key=GOOGLE_API_KEY)

# Initialize session state
if "orders" not in st.session_state:
    st.session_state.orders = []  # List of dicts: {address, timestamp}

# ===============================
# Helper Functions
# ===============================

def get_travel_time(origin, destination):
    """Return travel time in minutes using Google Maps Directions API"""
    try:
        directions = gmaps.directions(origin, destination, mode="driving", departure_time=datetime.now())
        if directions:
            duration_sec = directions[0]['legs'][0]['duration']['value']
            return duration_sec / 60  # minutes
    except Exception as e:
        st.warning(f"Error fetching travel time: {e}")
    return None

def get_coordinates(address):
    """Return (lat, lng) tuple for an address"""
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        location = geocode_result[0]['geometry']['location']
        return (location['lat'], location['lng'])
    return None

def assign_zones(orders):
    """Assign orders into ZONE 1-10 based on distance clustering and delivery time"""
    zones = {f"ZONE {i+1}": [] for i in range(MAX_ZONES)}
    warehouse_coord = get_coordinates(WAREHOUSE_ADDRESS)

    # Sort orders by timestamp (first come first serve)
    sorted_orders = sorted(orders, key=lambda x: x['timestamp'])

    for order in sorted_orders:
        order_coord = get_coordinates(order['address'])
        if not order_coord:
            continue

        # Check if delivery within 2 hours from now
        travel_minutes = get_travel_time(WAREHOUSE_ADDRESS, order['address'])
        if travel_minutes is None or travel_minutes > MAX_DELIVERY_HOURS * 60:
            continue  # Skip orders that exceed 2 hours

        # Assign to best ZONE
        best_zone = None
        min_avg_distance = float("inf")
        for zone_name, zone_orders in zones.items():
            if len(zone_orders) == 0:
                avg_distance = geodesic(warehouse_coord, order_coord).miles
            else:
                distances = [geodesic(get_coordinates(o['address']), order_coord).miles for o in zone_orders]
                avg_distance = sum(distances)/len(distances)
            if avg_distance < min_avg_distance:
                min_avg_distance = avg_distance
                best_zone = zone_name
        
        if best_zone:
            zones[best_zone].append(order)

    # Sort orders inside each zone based on delivery priority (earliest first)
    for zone_name, zone_orders in zones.items():
        zone_orders.sort(key=lambda x: x['timestamp'])
    return zones

def clear_delivered_orders(delivered_orders):
    st.session_state.orders = [o for o in st.session_state.orders if o not in delivered_orders]

# ===============================
# Streamlit App UI
# ===============================
st.title("TYPE IT IN GENE")

# Input new order
st.subheader("Add New Order")
new_address = st.text_input("Enter Customer Address:")
if st.button("Add Order"):
    if new_address:
        st.session_state.orders.append({"address": new_address, "timestamp": datetime.now()})
        st.success(f"Order added: {new_address}")

# Assign zones
zones = assign_zones(st.session_state.orders)

# Display zones
st.subheader("Delivery Zones")
for zone_name, zone_orders in zones.items():
    if zone_orders:
        st.markdown(f"**{zone_name}**")
        for idx, order in enumerate(zone_orders):
            st.write(f"{idx+1}. {order['address']} (Added: {order['timestamp'].strftime('%H:%M:%S')})")

# DONE button
if st.button("DONE"):
    delivered_orders = []
    for zone_orders in zones.values():
        delivered_orders.extend(zone_orders)
    clear_delivered_orders(delivered_orders)
    st.success("Delivered orders cleared.")

# Auto-refresh on new order
