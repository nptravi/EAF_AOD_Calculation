import pandas as pd
import streamlit as st

from app.database.queries import (
    get_recovery_master,
    get_units,
    save_recovery_master,
)


CHEMISTRY_COLUMNS = [
    "Fe", "C", "Si", "Mn", "Cr", "Ni",
    "Cu", "Ti", "Nb", "Mo", "P", "S", "N"
]


def _load_recovery_dataframe():
    units = get_units()
    rows = get_recovery_master()

    recovery_by_unit = {
        row.unit_code: row
        for row in rows
    }

    data = []

    for unit in units:
        row = recovery_by_unit.get(unit.unit_code)

        data.append({
            "Unit": unit.unit_name,
            "Unit Code": unit.unit_code,
            "Fe": row.Fe * 100 if row else 0,
            "C": row.C * 100 if row else 0,
            "Si": row.Si * 100 if row else 0,
            "Mn": row.Mn * 100 if row else 0,
            "Cr": row.Cr * 100 if row else 0,
            "Ni": row.Ni * 100 if row else 0,
            "Cu": row.Cu * 100 if row else 0,
            "Ti": row.Ti * 100 if row else 0,
            "Nb": row.Nb * 100 if row else 0,
            "Mo": row.Mo * 100 if row else 0,
            "P": row.P * 100 if row else 0,
            "S": row.S * 100 if row else 0,
            "N": row.N * 100 if row else 0,
        })

    return pd.DataFrame(data)


def _get_original_dataframe():
    # Loaded once from the DB and never overwritten by edits.
    # This is the fixed baseline used for the dirty-check, so it
    # must NOT be replaced by the edited df on rerun.
    if "recovery_original_df" not in st.session_state:
        st.session_state["recovery_original_df"] = (
            _load_recovery_dataframe()
        )

    return st.session_state["recovery_original_df"].copy()


def _get_recovery_dataframe():
    if "recovery_edited_df" not in st.session_state:
        st.session_state["recovery_edited_df"] = (
            _get_original_dataframe()
        )

    return st.session_state["recovery_edited_df"].copy()


def recovery_has_unsaved_changes():
    return st.session_state.get(
        "recovery_dirty",
        False
    )


def _bump_editor_version():
    # st.data_editor can retain stale edit-delta state tied to its key
    # even after that key is popped from session_state. Bumping a
    # version suffix forces Streamlit to instantiate a brand-new
    # widget, guaranteeing a clean reset.
    st.session_state["recovery_editor_version"] = (
        st.session_state.get("recovery_editor_version", 0) + 1
    )


def discard_recovery_changes():
    st.session_state.pop("recovery_edited_df", None)
    st.session_state.pop("recovery_original_df", None)
    st.session_state["recovery_dirty"] = False
    _bump_editor_version()


def save_recovery_changes():
    edited_df = _get_recovery_dataframe()

    save_recovery_master(
        edited_df.to_dict("records")
    )

    st.session_state.pop("recovery_edited_df", None)
    st.session_state.pop("recovery_original_df", None)
    st.session_state["recovery_dirty"] = False
    st.session_state["recovery_saved"] = True
    _bump_editor_version()


def show_recovery_master():

    if st.session_state.pop("recovery_saved", False):
        st.success(
            "Recovery Master saved successfully."
        )

    st.subheader("Recovery Master")

    original_df = _get_original_dataframe()
    df = _get_recovery_dataframe()

    chemistry_config = {}

    for column in CHEMISTRY_COLUMNS:
        chemistry_config[column] = (
            st.column_config.NumberColumn(
                column,
                step=0.001,
                format="%.3f",
            )
        )

    edited_df = st.data_editor(
        df,
        width="stretch",
        hide_index=True,
        disabled=["Unit", "Unit Code"],
        num_rows="fixed",
        column_config=chemistry_config,
        key=f"recovery_editor_{st.session_state.get('recovery_editor_version', 0)}",
    )

    st.session_state["recovery_edited_df"] = (
        edited_df.copy()
    )

    is_dirty = not edited_df.equals(original_df)

    st.session_state["recovery_dirty"] = is_dirty

    invalid_cells = []

    for column in CHEMISTRY_COLUMNS:

        for index, value in edited_df[column].items():

            if pd.isna(value):
                invalid_cells.append(
                    f"{column} in row {index + 1} is blank"
                )

            elif value < 0 or value > 100:
                invalid_cells.append(
                    f"{column} in row {index + 1}: "
                    f"{value} is outside 0–100%"
                )

    if invalid_cells:

        st.error("Invalid value entered.")

        for message in invalid_cells:
            st.write(f"- {message}")

        st.info(
            "The invalid value has not been saved."
        )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Save Recovery Master",
            disabled=bool(invalid_cells),
            key="save_recovery_master",
        ):

            save_recovery_changes()

            st.rerun()

    with col2:

        if st.button(
            "Discard Changes",
            disabled=not is_dirty,
            key="discard_recovery_master",
        ):

            discard_recovery_changes()

            st.rerun()