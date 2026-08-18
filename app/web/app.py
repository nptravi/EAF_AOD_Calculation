import streamlit as st
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.web.pages.recovery_master import show_recovery_master

st.set_page_config(
    page_title="EAF & AOD Calculation",
    page_icon="🏭",
    layout="wide"
)

st.title("EAF & AOD Calculation")

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Go to",
    [
        "Home",
        "Master Data",
        "EAF & AOD Calculation",
    ]
)

if page == "Home":
    st.write("Welcome to the EAF & AOD Calculation application.")

elif page == "Master Data":

    st.header("Master Data")

    master = st.radio(
        "Select Master",
        [
            "Recovery Master",
            "Material Group Master",
            "Material Master",
            "Grade Master",
            "AOD Provider Master",
        ],
        horizontal=True
    )

    if master == "Recovery Master":
        show_recovery_master()

    elif master == "Material Group Master":
        st.subheader("Material Group Master")

    elif master == "Material Master":
        st.subheader("Material Master")

    elif master == "Grade Master":
        st.subheader("Grade Master")

    elif master == "AOD Provider Master":
        st.subheader("AOD Provider Master")

elif page == "EAF & AOD Calculation":
    st.header("EAF & AOD Calculation")