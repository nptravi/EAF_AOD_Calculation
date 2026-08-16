import streamlit as st


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

    st.subheader(master)

elif page == "EAF & AOD Calculation":
    st.header("EAF & AOD Calculation")