import pandas as pd
import streamlit as st

from app.database.queries import (
    get_grade_master,
    get_material_master,
    get_recovery_for_unit_code,
)

from app.calculations.eaf import (
    calculate_eaf,
)

ELEMENTS = [
    "Fe", "C", "Si", "Mn", "Cr", "Ni",
    "Cu", "Ti", "Nb", "Mo", "P", "S", "N"
]
DISPLAY_ELEMENTS = ["C", "Si", "Mn", "Cr", "Ni", "Cu", "Nb", "Mo", "P", "S", "N"]

BUCKET_DEFAULT_ROWS = 5
FAFA_DEFAULT_ROWS = 2


def _blank_material_df(num_rows):
    return pd.DataFrame({
        "material": [None] * num_rows,
        "qty": [0] * num_rows,
    })


def show_eaf_aod_calculation():

    # --- Grade selection -----------------------------------------------
    grades = get_grade_master()
    grade_names = [g.grade_name for g in grades]

    col1, col2 = st.columns([0.2,3])
    with col1:
        st.subheader("Grades")
        #st.markdown(
         #   '<p style="font-size:20px; font-weight:700; margin-top:8px;">Grade</p>',
         #   unsafe_allow_html=True
       # )
    with col2:
        st.markdown("""
        <style>
            input[role="combobox"] {
                font-size: 28px !important;
            }
        </style>
        """, unsafe_allow_html=True)
        selected_grade_name = st.selectbox("Grade", grade_names, width=200, label_visibility="collapsed")
        sg = next(g for g in grades if g.grade_name == selected_grade_name)
    # TODO: show EAF_C / EAF_Cr / EAF_Ni / EAF_Cu as reference info only
    st.subheader("EAF Chemistry Needed")
    eaf_chemistry = {
        "C": [sg.C*100],
        "Cr": [sg.Cr*100],
        "Ni": [sg.Ni*100],
        "Cu": [sg.Cu*100]
    }
    st.table(eaf_chemistry)
    materials = get_material_master()
    material_by_name = {m.material_name: m for m in materials}
    st.subheader("EAF Input Materials:")
    col3, col4 = st.columns([1,3])
    # --- Bucket ----------------------------------------------------------
    with col3:
        st.text("Bucket")

        bucket_config = {
            "material": st.column_config.SelectboxColumn(
                "Material",
                options=sorted(m.material_name for m in materials),
                width=200,
            ),
            "qty": st.column_config.NumberColumn("Qty (T)", step=0.01, format="%.2f", width=75),
        }

        if "bucket_baseline" not in st.session_state:
            st.session_state["bucket_baseline"] = _blank_material_df(BUCKET_DEFAULT_ROWS)

        bucket_edited = st.data_editor(
            st.session_state["bucket_baseline"],
            num_rows="dynamic",
            column_config=bucket_config,
            hide_index=True,
            key="bucket_editor",
        )

        # --- FAFA --------------------------------------------------------------
        st.text("FAFA")

        fafa_config = {
            "material": st.column_config.SelectboxColumn(
                "Material",
                options=sorted(m.material_name for m in materials if not m.bucket_only),
                width=200,
            ),
            "qty": st.column_config.NumberColumn("Qty (T)", step=0.01, format="%.2f",width=75),
        }

        if "fafa_baseline" not in st.session_state:
            st.session_state["fafa_baseline"] = _blank_material_df(FAFA_DEFAULT_ROWS)

        fafa_edited = st.data_editor(
            st.session_state["fafa_baseline"],
            num_rows="dynamic",
            column_config=fafa_config,
            hide_index=True,
            key="fafa_editor",
        )
    with col4:
        st.subheader("EAF Calculation Result will be shown here")

    # --- Calculate ---------------------------------------------------------
    if st.button("Calculate EAF"):
        recovery_row = get_recovery_for_unit_code(3501)
        eaf_materials = {}
        for _,row in bucket_edited.iterrows():
            if row.material is not None:
                if row.material not in eaf_materials:
                    eaf_materials[row.material] = row.qty
                else:
                    eaf_materials[row.material] += row.qty
        for _,row in fafa_edited.iterrows():
            if row.material is not None:
                if row.material not in eaf_materials:
                    eaf_materials[row.material] = row.qty
                else:
                    eaf_materials[row.material] += row.qty
        params = {
            "grade": selected_grade_name,
            "eaf_materials": eaf_materials,
        }
        result = calculate_eaf(params)
        st.subheader(f"EAF output: {result['eaf_weight']:.1f} T")
        eaf_output_chemistry = {
            element: [f"{result['eaf_chemistry'][element] * 100:.3f}"]
            for element in DISPLAY_ELEMENTS
        }
        st.subheader("EAF Chemistry (%)")
        st.table(eaf_output_chemistry)

        # TODO: loop bucket_edited + fafa_edited rows
        # TODO: for each row -> material_by_name[row["Material"]], qty = row["Qty (T)"]
        # TODO: per element: contribution += qty * material.<element> * getattr(recovery_row, element)
        #       (Fe isn't stored on MaterialMaster — it's 1 - sum(other 12))
        # TODO: output_weight = sum(contributions.values())
        # TODO: output_chemistry[el] = contributions[el] / output_weight * 100

        pass

    # --- Output --------------------------------------------------------------
    # TODO: display output_weight + output_chemistry table
