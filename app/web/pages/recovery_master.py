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


def show_recovery_master():

    st.subheader("Recovery Master")
    if st.session_state.get("recovery_saved", False):
        st.success("Recovery Master saved successfully.")
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

    df = pd.DataFrame(data)

    chemistry_config = {}

    for column in CHEMISTRY_COLUMNS:
        chemistry_config[column] = st.column_config.NumberColumn(
            column,
            step=0.001,
            format="%.3f",
        )

    edited_df = st.data_editor(
        df,
        width="stretch",
        hide_index=True,
        disabled=["Unit", "Unit Code"],
        num_rows="fixed",
        column_config=chemistry_config,
        key="recovery_editor",
    )
    original_df = df.copy()

    is_dirty = not edited_df.equals(original_df)

    if is_dirty:
        st.warning(
            "You have unsaved changes in Recovery Master."
        )

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

        st.info("The invalid value has not been saved.")

    if st.button(
        "Save Recovery Master",
        disabled=bool(invalid_cells),
        key="save_recovery_master",
    ):

        save_recovery_master(
            edited_df.to_dict("records")
        )

        st.session_state["recovery_saved"] = True

        st.rerun()