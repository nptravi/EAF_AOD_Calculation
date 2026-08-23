import pandas as pd
import streamlit as st

from app.database.queries import (
    get_grade_master,
    save_grade_master,
)


CHEMISTRY_COLUMNS = [
    "C", "Si", "Mn", "Cr", "Ni",
    "Cu", "Ti", "Nb", "Mo", "P", "S", "N"
]

EAF_COLUMNS = ["EAF_C", "EAF_Cr", "EAF_Ni", "EAF_Cu"]

EDITABLE_COLUMNS = ["Grade Name"] + CHEMISTRY_COLUMNS + EAF_COLUMNS

COLUMN_ORDER = ["Grade Name", "Fe"] + CHEMISTRY_COLUMNS + EAF_COLUMNS


def _calc_fe(row):
    total = 0

    for column in CHEMISTRY_COLUMNS:
        value = row[column]

        if pd.notna(value):
            total += value

    return round(100 - total, 3)


def _with_calculated_fe(df):
    df = df.copy()
    df["Fe"] = df.apply(_calc_fe, axis=1) if len(df) else 0
    return df


def _load_grade_dataframe():
    grades = get_grade_master()

    data = []

    for grade in grades:
        data.append({
            "id": grade.id,
            "Grade Name": grade.grade_name,
            "Fe": "Balance",
            "C": grade.C * 100,
            "Si": grade.Si * 100,
            "Mn": grade.Mn * 100,
            "Cr": grade.Cr * 100,
            "Ni": grade.Ni * 100,
            "Cu": grade.Cu * 100,
            "Ti": grade.Ti * 100,
            "Nb": grade.Nb * 100,
            "Mo": grade.Mo * 100,
            "P": grade.P * 100,
            "S": grade.S * 100,
            "N": grade.N * 100,
            "EAF_C": grade.EAF_C * 100,
            "EAF_Cr": grade.EAF_Cr * 100,
            "EAF_Ni": grade.EAF_Ni * 100,
            "EAF_Cu": grade.EAF_Cu * 100,
        })

    df = pd.DataFrame(
        data,
        columns=["id", "Grade Name", "Fe"] + CHEMISTRY_COLUMNS + EAF_COLUMNS
    )

    return df


def _get_original_dataframe():
    # Fixed baseline loaded once from the DB — never overwritten by
    # edits. Used for the dirty-check so it survives reruns (e.g.
    # Cancel in the navigation-protection flow).
    if "grade_original_df" not in st.session_state:
        st.session_state["grade_original_df"] = (
            _load_grade_dataframe()
        )

    return st.session_state["grade_original_df"].copy()


def _get_grade_dataframe():
    if "grade_edited_df" not in st.session_state:
        st.session_state["grade_edited_df"] = (
            _get_original_dataframe()
        )

    return st.session_state["grade_edited_df"].copy()


def grade_has_unsaved_changes():
    return st.session_state.get(
        "grade_dirty",
        False
    )


def _bump_editor_version():
    # Forces a brand-new data_editor widget instance on discard/save,
    # avoiding stale edit-delta state some Streamlit versions keep
    # tied to a widget key even after it's popped from session_state.
    st.session_state["grade_editor_version"] = (
        st.session_state.get("grade_editor_version", 0) + 1
    )


def discard_grade_changes():
    st.session_state.pop("grade_edited_df", None)
    st.session_state.pop("grade_original_df", None)
    st.session_state["grade_dirty"] = False
    _bump_editor_version()


def save_grade_changes():
    edited_df = _get_grade_dataframe().drop(columns=["Fe"])

    records = edited_df.to_dict("records")

    # Convert NaN -> None on plain dicts, not on the DataFrame column
    # (pandas silently coerces None back to NaN when assigned into a
    # numeric-dtype column, even though the lambda returns None).
    for row in records:
        row["id"] = int(row["id"]) if pd.notna(row["id"]) else None

    save_grade_master(records)

    st.session_state.pop("grade_edited_df", None)
    st.session_state.pop("grade_original_df", None)
    st.session_state["grade_dirty"] = False
    st.session_state["grade_saved"] = True
    _bump_editor_version()


def _validate(edited_df, recalculated_df):
    errors = []
    names_seen = set()

    for position, (index, row) in enumerate(edited_df.iterrows()):
        name = (
            str(row["Grade Name"]).strip()
            if pd.notna(row["Grade Name"]) else ""
        )

        if not name:
            errors.append(f"Row {position + 1}: Grade Name is blank")
        elif name in names_seen:
            errors.append(f"Row {position + 1}: duplicate grade name '{name}'")
        else:
            names_seen.add(name)

        for column in CHEMISTRY_COLUMNS + EAF_COLUMNS:
            value = row[column]

            if pd.isna(value):
                errors.append(f"Row {position + 1}: {column} is blank")
            elif value < 0 or value > 100:
                errors.append(
                    f"Row {position + 1}: {column} = {value} outside 0-100%"
                )

        fe_value = recalculated_df.iloc[position]["Fe"]

        if pd.notna(fe_value) and fe_value < 0:
            errors.append(
                f"Row {position + 1}: chemistry exceeds 100% "
                f"(Fe would be {fe_value})"
            )

    return errors


def show_grade_master():

    if st.session_state.pop("grade_saved", False):
        st.success(
            "Grade Master saved successfully."
        )

    st.subheader("Grade Master")

    original_df = _get_original_dataframe()

    chemistry_config = {}

    for column in CHEMISTRY_COLUMNS:
        chemistry_config[column] = st.column_config.NumberColumn(
            column,
            step=0.001,
            format="%.3f",
            default=0,
        )

    eaf_config = {}

    for column in EAF_COLUMNS:
        eaf_config[column] = st.column_config.NumberColumn(
            column,
            step=0.001,
            format="%.3f",
            default=0,
            help="EAF-stage target — this element only.",
        )

    column_config = {
        "Grade Name": st.column_config.TextColumn(
            "Grade Name",
            required=True,
        ),
        "Fe": st.column_config.TextColumn(
            "Fe",
            disabled=True,
            default="Balance",
            help="Fe is always the balance element — not entered or calculated here.",
        ),
        **chemistry_config,
        **eaf_config,
    }

    editor_key = (
        f"grade_editor_"
        f"{st.session_state.get('grade_editor_version', 0)}"
    )

    edited_df = st.data_editor(
        original_df,
        width="stretch",
        hide_index=True,
        num_rows="dynamic",
        column_config=column_config,
        column_order=COLUMN_ORDER,
        key=editor_key,
    )

    # Persisted purely so app.py's nav-protection Save/Discard-from-
    # elsewhere handlers (which run outside this function) can read
    # the latest edits. Never fed back into the widget's own value —
    # that previously conflicted with Streamlit's own internal
    # per-key edit tracking and corrupted typed values.
    st.session_state["grade_edited_df"] = edited_df.copy()

    is_dirty = (
        len(edited_df) != len(original_df)
        or not edited_df[EDITABLE_COLUMNS].reset_index(drop=True).equals(
            original_df[EDITABLE_COLUMNS].reset_index(drop=True)
        )
    )

    st.session_state["grade_dirty"] = is_dirty

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Save Grade Master",
            key="save_grade_master",
        ):
            recalculated_df = _with_calculated_fe(edited_df)
            errors = _validate(edited_df, recalculated_df)

            if errors:
                st.error("Please fix the following before saving:")

                for message in errors:
                    st.write(f"- {message}")
            else:
                save_grade_changes()
                st.rerun()

    with col2:
        if st.button(
            "Discard Changes",
            disabled=not is_dirty,
            key="discard_grade_master",
        ):
            discard_grade_changes()
            st.rerun()