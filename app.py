import streamlit as st
import time
from datetime import datetime
import base64
from io import BytesIO
import os
from pathlib import Path
from PIL import Image
from streamlit_js_eval import get_geolocation
import requests
from database import init_db, save_visit

# --- Initialization ---
# Create tables if they don't exist
init_db()

# --- Helper Functions ---
def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}"

def get_ip_location():
    try:
        response = requests.get("https://ipinfo.io/json", timeout=3)
        data = response.json()
        if 'loc' in data:
            lat, lon = data['loc'].split(',')
            return float(lat), float(lon)
    except Exception:
        return None, None
    return None, None

# --- Session State ---
if 'loc_lat' not in st.session_state: st.session_state.loc_lat = None
if 'loc_lon' not in st.session_state: st.session_state.loc_lon = None

# --- UI ---
st.set_page_config(page_title="Daily Store Reports", page_icon="📝", layout="centered")
st.title("DAILY REPORT")
st.subheader("DAILY STORE VISIT REPORTS")

# --- Main Form Container ---
with st.container():
    sr_name = st.selectbox("SR NAME *", ["SHUBRAM KAR", "RAJU DAS"], key="sr_name")
    store_name_person = st.text_input("STORE NAME AND CONTACT PERSON *", key="store_name")
    visit_type = st.radio("STORE VISIT TYPE *", ["NEW VISIT", "RE VISIT"], horizontal=True, key="visit_type")
    store_category = st.radio("STORE CATEGORY *", ["MT", "HoReCa"], horizontal=True, key="category")
    phone = st.text_input("PHONE NUMBER *", key="phone")
    lead_type = st.radio("LEAD TYPE *", ["HOT", "WARM", "COLD", "DEAD"], horizontal=True, key="lead_type")
    follow_up_date = st.date_input("FOLLOW UP DATE", key="follow_up_date")
    
    st.write("TOBACCO PRODUCTS INTERESTED IN / THEY DEAL IN *")
    c1, c2, c3 = st.columns(3)
    p1 = c1.checkbox("CIGARETTE", key="p1")
    p2 = c2.checkbox("ROLLING PAPERS", key="p2")
    p3 = c3.checkbox("CIGARS", key="p3")
    p4 = c1.checkbox("HOOKAH", key="p4")
    p5 = c2.checkbox("ZIPPO LIGHTERS", key="p5")
    p6 = c3.checkbox("NONE", key="p6")

    order_details = st.text_area("ORDER DETAILS IF CONVERTED (Optional)", key="order_details")
    
    st.markdown("### 📸 PHOTOGRAPH *")
    cam_val = st.camera_input("Take Photo", key="camera")
    upl_val = st.file_uploader("Or Upload", type=['jpg','png','jpeg'], key="upload")
    final_photo = cam_val if cam_val else upl_val

    st.markdown("---")
    st.markdown("### 📍 LOCATION CAPTURE")
    
    # --- Location Logic ---
    loc_trigger = st.checkbox("Record Location (Click to Enable GPS)", key="loc_trigger")
    
    # 1. Provide Reset Button always
    if st.button("Reset Location"):
        st.session_state.loc_lat = None
        st.session_state.loc_lon = None
        st.rerun()

    current_lat = st.session_state.loc_lat
    current_lon = st.session_state.loc_lon

    # 2. Try Fetching if needed
    if loc_trigger and current_lat is None:
        try:
            # Try Browser First
            loc_data = get_geolocation()
            
            if loc_data:
                # Success Logic
                if 'coords' in loc_data:
                    st.session_state.loc_lat = loc_data['coords']['latitude']
                    st.session_state.loc_lon = loc_data['coords']['longitude']
                    st.rerun()
                
                # Failure Logic -> Fallback
                elif 'error' in loc_data:
                    with st.spinner("Switching to Network Location..."):
                        lat, lon = get_ip_location()
                        if lat:
                            st.session_state.loc_lat = lat
                            st.session_state.loc_lon = lon
                            st.rerun()
                        else:
                            st.error("❌ Network Location Failed.")
            
            else:
                st.info("📡 Fetching GPS... (This depends on your device)")
                # Escape hatch for slow devices
                if st.button("Taking too long? Use Network Location"):
                     with st.spinner("Fetching Network Location..."):
                        lat, lon = get_ip_location()
                        if lat:
                            st.session_state.loc_lat = lat
                            st.session_state.loc_lon = lon
                            st.rerun()
                        else:
                            st.error("❌ Network Location Failed.")
        except Exception as e:
            # Fallback on Crash
            lat, lon = get_ip_location()
            if lat:
                st.session_state.loc_lat = lat
                st.session_state.loc_lon = lon
                st.rerun()

    # 3. Display Result (If Found)
    if st.session_state.loc_lat:
        lat_disp = st.session_state.loc_lat
        lon_disp = st.session_state.loc_lon
        map_link = f"https://www.google.com/maps?q={lat_disp},{lon_disp}"
        st.success("✅ Location Captured!")
        st.write(f"**Coordinates:** {lat_disp}, {lon_disp}")
        st.markdown(f"**Link:** [{map_link}]({map_link})")
    
    location_recorded_answer = st.radio("DID YOU RECORD THE LOCATION? *", ["YES", "NO"], horizontal=True, key="loc_recorded")

# --- SUBMIT BUTTON (OUTSIDE CONTAINER) ---
st.markdown("---")
# Use full width container for button area to separate it visually
with st.container():
    submitted = st.button("SUBMIT REPORT", type="primary", use_container_width=True)

if submitted:
    # Validation
    errors = []
    if not store_name_person: errors.append("Store Name is required.")
    if not phone: errors.append("Phone Number is required.")
    if not final_photo: errors.append("Photograph is required.")
    
    products = []
    if p1: products.append("CIGARETTE")
    if p2: products.append("ROLLING PAPERS")
    if p3: products.append("CIGARS")
    if p4: products.append("HOOKAH")
    if p5: products.append("ZIPPO LIGHTERS")
    if p6: products.append("NONE")
    if not products: errors.append("Select at least one Product.")
    
    final_lat = ""
    final_lon = ""
    if location_recorded_answer == "YES":
        if st.session_state.loc_lat is None:
             errors.append("You said YES to location, but none is recorded. Please check 'Record Location'.")
        else:
             final_lat = str(st.session_state.loc_lat)
             final_lon = str(st.session_state.loc_lon)

    if errors:
        for e in errors:
            st.error(f"❌ {e}")
    else:
        try:
            img = Image.open(final_photo)
            img.thumbnail((800,800))
            b64_img = image_to_base64(img)
            prod_str = ", ".join(products)
            maps_url = ""
            if final_lat and final_lon:
                maps_url = f"https://www.google.com/maps?q={final_lat},{final_lon}"
                
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M:%S")
            
            # Prepare Dictionary for Database
            visit_data = {
                "date": current_date,
                "time": current_time,
                "sr_name": sr_name,
                "store_name": store_name_person,
                "visit_type": visit_type,
                "store_category": store_category,
                "phone": phone,
                "lead_type": lead_type,
                "follow_up_date": str(follow_up_date),
                "products": prod_str,
                "order_details": order_details,
                "latitude": final_lat,
                "longitude": final_lon,
                "maps_url": maps_url,
                "location_recorded_answer": location_recorded_answer,
                "image_data": b64_img
            }
            
            with st.spinner("Saving to Secure Database..."):
                ok, msg = save_visit(visit_data)
                if ok:
                    st.success("✅ Report Saved Successfully to Database!")
                    st.balloons()
                    # Optional: reset fields
                else:
                    st.error(f"❌ Database Error: {msg}")
        except Exception as e:
            st.error(f"❌ Processing Error: {e}")
