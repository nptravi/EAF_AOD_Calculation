import streamlit as st
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.web.pages.recovery_master import (
    show_recovery_master,
    recovery_has_unsaved_changes,
    save_recovery_changes,
    discard_recovery_changes,
)
from app.web.pages.material_master import (
    show_material_master,
    material_has_unsaved_changes,
    save_material_changes,
    discard_material_changes,
)
from app.web.pages.grade_master import (
    show_grade_master,
    grade_has_unsaved_changes,
    save_grade_changes,
    discard_grade_changes,
)
from app.web.pages.aod_provider_master import (
    show_aod_provider_master,
    aod_provider_has_unsaved_changes,
    save_aod_provider_changes,
    discard_aod_provider_changes,
)

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

MASTER_OPTIONS = [
    "Recovery Master",
    "Material Master",
    "Grade Master",
    "AOD Provider Master",
]


def _has_unsaved_changes(master_name):
    if master_name == "Recovery Master":
        return recovery_has_unsaved_changes()
    if master_name == "Material Master":
        return material_has_unsaved_changes()
    if master_name == "Grade Master":
        return grade_has_unsaved_changes()
    if master_name == "AOD Provider Master":
        return aod_provider_has_unsaved_changes()
    return False


def _save_changes(master_name):
    if master_name == "Recovery Master":
        save_recovery_changes()
    elif master_name == "Material Master":
        save_material_changes()
    elif master_name == "Grade Master":
        save_grade_changes()
    elif master_name == "AOD Provider Master":
        save_aod_provider_changes()


def _discard_changes(master_name):
    if master_name == "Recovery Master":
        discard_recovery_changes()
    elif master_name == "Material Master":
        discard_material_changes()
    elif master_name == "Grade Master":
        discard_grade_changes()
    elif master_name == "AOD Provider Master":
        discard_aod_provider_changes()


def _on_master_change():
    new_selection = st.session_state["selected_master"]
    active = st.session_state["active_master"]

    if new_selection == active:
        return

    if _has_unsaved_changes(active):
        # Block the switch, keep radio showing the active page,
        # and ask the user how to proceed.
        st.session_state["pending_master"] = new_selection
        st.session_state["selected_master"] = active
    else:
        st.session_state["active_master"] = new_selection


if page == "Home":
    st.write("Welcome to the EAF & AOD Calculation application.")

elif page == "Master Data":

    st.header("Master Data")

    if "active_master" not in st.session_state:
        st.session_state["active_master"] = MASTER_OPTIONS[0]

    if "selected_master" not in st.session_state:
        st.session_state["selected_master"] = st.session_state["active_master"]

    st.radio(
        "Select Master",
        MASTER_OPTIONS,
        horizontal=True,
        key="selected_master",
        on_change=_on_master_change,
    )

    pending = st.session_state.get("pending_master")

    if pending:
        active = st.session_state["active_master"]

        st.warning(
            f"You have unsaved changes in **{active}**. "
            f"Switch to **{pending}**?"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Save & Continue", key="nav_save"):
                _save_changes(active)
                st.session_state["active_master"] = pending
                # Don't set selected_master directly here — the radio
                # widget was already instantiated this run. Pop it so
                # the bootstrap line re-seeds it from active_master
                # on the next rerun instead.
                st.session_state.pop("selected_master", None)
                st.session_state.pop("pending_master", None)
                st.rerun()

        with col2:
            if st.button("Discard & Continue", key="nav_discard"):
                _discard_changes(active)
                st.session_state["active_master"] = pending
                st.session_state.pop("selected_master", None)
                st.session_state.pop("pending_master", None)
                st.rerun()

        with col3:
            if st.button("Cancel", key="nav_cancel"):
                st.session_state.pop("pending_master", None)
                st.rerun()

    else:
        active = st.session_state["active_master"]

        if active == "Recovery Master":
            show_recovery_master()

        elif active == "Material Master":
            show_material_master()

        elif active == "Grade Master":
            show_grade_master()

        elif active == "AOD Provider Master":
            show_aod_provider_master()

elif page == "EAF & AOD Calculation":
    st.header("EAF & AOD Calculation")