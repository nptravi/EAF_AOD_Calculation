import pandas as pd
import streamlit as st

from app.database.queries import (
    get_grade_master,
    get_material_master,
    get_recovery_for_unit_code,
    get_element_provider_details,
    get_element_provider,
)

from app.calculations.calculation import (
    calculate_eaf_aod,
)

ELEMENTS = [
    "Fe", "C", "Si", "Mn", "Cr", "Ni",
    "Cu", "Ti", "Nb", "Mo", "P", "S", "N"
]
DISPLAY_ELEMENTS = ["C", "Si", "Mn", "Cr", "Ni", "Cu", "Nb", "Mo"]

BUCKET_DEFAULT_ROWS = 5
FAFA_DEFAULT_ROWS = 2


def _blank_material_df(num_rows):
    return pd.DataFrame({
        "material": [None] * num_rows,
        "qty": [0] * num_rows,
    })


def show_eaf_aod_calculation():
    st.subheader("FeMn / SiMn override to be implemented")
    # --- Grade selection -----------------------------------------------
    grades = get_grade_master()
    grade_names = [g.grade_name for g in grades]
    Si_provider = get_element_provider_details("Si").material_name

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

    # ["C", "Si", "Mn", "Cr", "Ni", "Cu", "Nb", "Mo"]
    grade_chemistry = {
        "C": sg.C*100,
        "Si": sg.Si*100,
        "Mn": sg.Mn*100,
        "Cr": sg.Cr*100,
        "Ni": sg.Ni*100,
        "Cu": sg.Cu*100,
        "Nb": sg.Nb*100,
        "Mo": sg.Mo*100
    }
    grade_display_chemistry = {
        element: [f"{grade_chemistry[element]:.3f}"]
        for element in DISPLAY_ELEMENTS
    }

    materials = get_material_master()
    material_by_name = {m.material_name: m for m in materials}
    st.subheader("EAF Input Materials:")
    col3, col4, col5 = st.columns([1,1,2])

    eaf_output_chemistry = {}
    aod_output_chemistry = {}
    aod_additions = {}
    result = {}
    # --- Bucket and FAFA combined----------------------------------------------------------
    with col3:
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

        special_materials = [Si_provider, "Oxygen"]
        special_config = {
            "material": st.column_config.TextColumn(
                "Material",
                disabled=True,
                width=200,
            ),
            "qty": st.column_config.NumberColumn(
                "Qty (T) / Nm3",
                step=0.01,
                format="%.2f",
                width=75,
            ),
        }

        if "special_baseline" not in st.session_state:
            st.session_state["special_baseline"] = pd.DataFrame(
                {
                    "material": [Si_provider, "Oxygen"],
                    "qty": [0.3, 400],
                }
            )

        special_edited = st.data_editor(
            st.session_state["special_baseline"],
            num_rows="fixed",
            column_config=special_config,
            hide_index=True,
            key="special_editor",
        )

        # --- Calculate ---------------------------------------------------------
        #st.markdown("""
         #   <style>
          #  .stButton > button {
           #     width: 200px;
            #    height: 60px;
             #   font-size: 28px;
            #}
            #</style>
            #""", unsafe_allow_html=True)
        #if st.button("Calculate"):
        recovery_row = get_recovery_for_unit_code(3501)
        eaf_regular_materials = 0
        eaf_materials = {}
        for _, row in bucket_edited.iterrows():
            if row.material is not None:
                eaf_regular_materials+=row.qty
                if row.material not in eaf_materials:
                    eaf_materials[row.material] = row.qty
                else:
                    eaf_materials[row.material] += row.qty
        for _, row in special_edited.iterrows():
            if row.material is not None:
                if row.material not in eaf_materials:
                    eaf_materials[row.material] = row.qty
                else:
                    eaf_materials[row.material] += row.qty
        mn_provider = get_element_provider("Mn")
        mn_override = {"material": mn_provider["alternate"].material_name, "qty": 0.0}

        params = {
            "grade": selected_grade_name,
            "eaf_materials": eaf_materials,
            "mn_override": mn_override,
        }
        #print(f"params: {params}")
        if eaf_regular_materials > 0:
            result = calculate_eaf_aod(params)
        else:
            result ={}


    with col4:
        if "eaf_weight" in result:
            st.subheader(f"EAF Charge wt: {result['eaf_charge_weight']:.1f} T")
            st.subheader(f"EAF Output wt: {result['eaf_weight']:.1f} T")
            st.subheader(f"AOD Output wt: {result['aod_weight']:.1f} T")
            eaf_output_chemistry = {
                element: [f"{result['eaf_chemistry'][element] * 100:.3f}"]
                for element in DISPLAY_ELEMENTS
            }
            aod_output_chemistry = {
                element: [f"{result['aod_chemistry'][element] * 100:.3f}"]
                for element in DISPLAY_ELEMENTS
            }
            aod_additions = result['aod_additions']
            st.subheader("AOD Material Additions")
            st.table(aod_additions)


    with col5:
        if "eaf_weight" in result:
            st.subheader("Grade Chemistry")
            st.table(grade_display_chemistry)
            st.subheader("EAF Chemistry (%)")
            st.table(eaf_output_chemistry)
            st.subheader("AOD Chemistry (%)")
            st.table(aod_output_chemistry)


