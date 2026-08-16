import streamlit as st
import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
from app.database.queries import (
    get_recovery_master,
    get_units,
    save_recovery_master,
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

    if st.session_state.pop("recovery_saved", False):
        st.success("Recovery Master saved successfully.")
    if master == "Recovery Master":
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
                "Fe": row.Fe if row else 0,
                "C": row.C if row else 0,
                "Si": row.Si if row else 0,
                "Mn": row.Mn if row else 0,
                "Cr": row.Cr if row else 0,
                "Ni": row.Ni if row else 0,
                "Cu": row.Cu if row else 0,
                "Ti": row.Ti if row else 0,
                "Nb": row.Nb if row else 0,
                "Mo": row.Mo if row else 0,
                "P": 0,
                "S": 0,
                "N": 0,
            })

        df = pd.DataFrame(data)
        chemistry_columns = [
            "Fe", "C", "Si", "Mn", "Cr", "Ni",
            "Cu", "Ti", "Nb", "Mo", "P", "S", "N"
        ]

        df[chemistry_columns] = df[chemistry_columns] * 100

        chemistry_config = {}

        for column in chemistry_columns:
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
        invalid_cells = []

        for column in chemistry_columns:
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
            st.error("Invalid value entered:")
            for message in invalid_cells:
                st.write(f"- {message}")

            st.info("The invalid value has not been saved.")

        if st.button(
                "Save Recovery Master",
                disabled=bool(invalid_cells)
        ):
            save_recovery_master(
                edited_df.to_dict("records")
            )

            st.session_state["recovery_saved"] = True
            st.rerun()

elif page == "EAF & AOD Calculation":
    st.header("EAF & AOD Calculation")