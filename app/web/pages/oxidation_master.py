import pandas as pd
import streamlit as st

from app.database.queries import (
    get_oxidation_master,
    save_oxidation_master,
)


ELEMENTS = ["Fe", "Mn", "Cr"]

EDITABLE_COLUMNS = ["Oxidation Rate"]

COLUMN_ORDER = ["Element", "Oxidation Rate"]


def _load_oxidation_dataframe():
    existing = {
        oxidation.element: oxidation
        for oxidation in get_oxidation_master()
    }

    data = []

    for element in ELEMENTS:
        oxidation = existing.get(element)

        data.append({
            "Element": element,
            "Oxidation Rate": (
                oxidation.oxidation_rate * 100.0
                if oxidation
                else 0.0
            ),
        })

    return pd.DataFrame(data, columns=COLUMN_ORDER)


def _get_original_dataframe():
    # Fixed baseline loaded once from the DB — never overwritten by
    # edits. Used for the dirty-check so it survives reruns.
    if "oxidation_original_df" not in st.session_state:
        st.session_state["oxidation_original_df"] = (
            _load_oxidation_dataframe()
        )

    return st.session_state["oxidation_original_df"].copy()


def oxidation_has_unsaved_changes():
    return st.session_state.get(
        "oxidation_dirty",
        False
    )


def _bump_editor_version():
    st.session_state["oxidation_editor_version"] = (
        st.session_state.get("oxidation_editor_version", 0) + 1
    )


def discard_oxidation_changes():
    st.session_state.pop("oxidation_edited_df", None)
    st.session_state.pop("oxidation_original_df", None)
    st.session_state["oxidation_dirty"] = False
    _bump_editor_version()


def save_oxidation_changes():
    edited_df = st.session_state.get("oxidation_edited_df")

    if edited_df is None:
        edited_df = _get_original_dataframe()

    save_oxidation_master(
        edited_df.to_dict("records")
    )

    st.session_state.pop("oxidation_edited_df", None)
    st.session_state.pop("oxidation_original_df", None)
    st.session_state["oxidation_dirty"] = False
    st.session_state["oxidation_saved"] = True
    _bump_editor_version()


def show_oxidation_master():

    if st.session_state.pop("oxidation_saved", False):
        st.success(
            "Oxidation Master saved successfully."
        )

    st.subheader("Oxidation Master")

    st.caption(
        "Set the oxidation rate for each element."
    )

    original_df = _get_original_dataframe()

    column_config = {
        "Element": st.column_config.TextColumn(
            "Element",
            disabled=True,
        ),
        "Oxidation Rate": st.column_config.NumberColumn(
            "Oxidation Rate",
            min_value=0.0,
            step=0.01,
            format="%.1f",
            required=True,
        ),
    }

    editor_key = (
        f"oxidation_editor_"
        f"{st.session_state.get('oxidation_editor_version', 0)}"
    )

    edited_df = st.data_editor(
        original_df,
        width="stretch",
        hide_index=True,
        num_rows="fixed",
        disabled=["Element"],
        column_config=column_config,
        column_order=COLUMN_ORDER,
        key=editor_key,
    )

    # Persisted so app.py's nav-protection Save/Discard-from-
    # elsewhere handlers can read the latest edits.
    st.session_state["oxidation_edited_df"] = edited_df.copy()

    is_dirty = not edited_df[EDITABLE_COLUMNS].reset_index(
        drop=True
    ).equals(
        original_df[EDITABLE_COLUMNS].reset_index(
            drop=True
        )
    )

    st.session_state["oxidation_dirty"] = is_dirty

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Save Oxidation Master",
            key="save_oxidation_master",
        ):
            save_oxidation_changes()
            st.rerun()

    with col2:
        if st.button(
            "Discard Changes",
            disabled=not is_dirty,
            key="discard_oxidation_master",
        ):
            discard_oxidation_changes()
            st.rerun()
