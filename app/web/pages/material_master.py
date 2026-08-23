import math

import pandas as pd
import streamlit as st

from app.database.queries import (
    get_material_master,
    save_material_master,
)


def _to_optional_int(value):
    if value is None:
        return None

    if isinstance(value, str) and value.strip() == "":
        return None

    try:
        if isinstance(value, float) and math.isnan(value):
            return None
    except TypeError:
        pass

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_optional_float(value):
    if value is None:
        return None

    if isinstance(value, str) and value.strip() == "":
        return None

    try:
        if isinstance(value, float) and math.isnan(value):
            return None
    except TypeError:
        pass

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


CHEMISTRY_COLUMNS = [
    "C", "Si", "Mn", "Cr", "Ni",
    "Cu", "Ti", "Nb", "Mo", "P", "S", "N"
]

EDITABLE_COLUMNS = ["Material Name", "Bucket Only", "LPP"] + CHEMISTRY_COLUMNS

COLUMN_ORDER = ["Material Name", "Bucket Only", "LPP", "Fe"] + CHEMISTRY_COLUMNS


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


def _load_material_dataframe():
    materials = get_material_master()

    data = []

    for material in materials:
        data.append({
            "id": material.id,
            "Material Name": material.material_name,
            "Bucket Only": material.bucket_only,
            "LPP": material.lpp,
            "Fe": "Balance",
            "C": material.C * 100,
            "Si": material.Si * 100,
            "Mn": material.Mn * 100,
            "Cr": material.Cr * 100,
            "Ni": material.Ni * 100,
            "Cu": material.Cu * 100,
            "Ti": material.Ti * 100,
            "Nb": material.Nb * 100,
            "Mo": material.Mo * 100,
            "P": material.P * 100,
            "S": material.S * 100,
            "N": material.N * 100,
        })

    df = pd.DataFrame(
        data,
        columns=["id", "Material Name", "Bucket Only", "LPP", "Fe"] + CHEMISTRY_COLUMNS
    )

    return df


def _get_original_dataframe():
    # Fixed baseline loaded once from the DB — never overwritten by
    # edits. Used for the dirty-check so it survives reruns (e.g.
    # Cancel in the navigation-protection flow).
    if "material_original_df" not in st.session_state:
        st.session_state["material_original_df"] = (
            _load_material_dataframe()
        )

    return st.session_state["material_original_df"].copy()


def _get_material_dataframe():
    if "material_edited_df" not in st.session_state:
        st.session_state["material_edited_df"] = (
            _get_original_dataframe()
        )

    return st.session_state["material_edited_df"].copy()


def material_has_unsaved_changes():
    return st.session_state.get(
        "material_dirty",
        False
    )


def _bump_editor_version():
    # Forces a brand-new data_editor widget instance on discard/save,
    # avoiding stale edit-delta state some Streamlit versions keep
    # tied to a widget key even after it's popped from session_state.
    st.session_state["material_editor_version"] = (
        st.session_state.get("material_editor_version", 0) + 1
    )


def discard_material_changes():
    st.session_state.pop("material_edited_df", None)
    st.session_state.pop("material_original_df", None)
    st.session_state["material_dirty"] = False
    _bump_editor_version()


def save_material_changes():
    edited_df = _get_material_dataframe().drop(columns=["Fe"])

    records = edited_df.to_dict("records")

    # Convert NaN -> None here, on plain dicts. Doing this on the
    # DataFrame column instead (e.g. via .apply) doesn't work reliably:
    # pandas silently coerces None back to NaN to keep a numeric-dtype
    # column homogeneous, even though the lambda returns None.
    for row in records:
        row["id"] = int(row["id"]) if pd.notna(row["id"]) else None
        row["LPP"] = float(row["LPP"]) if pd.notna(row["LPP"]) else None

    save_material_master(records)

    st.session_state.pop("material_edited_df", None)
    st.session_state.pop("material_original_df", None)
    st.session_state["material_dirty"] = False
    st.session_state["material_saved"] = True
    _bump_editor_version()


def _validate(edited_df, recalculated_df):
    errors = []
    names_seen = set()

    for position, (index, row) in enumerate(edited_df.iterrows()):
        name = (
            str(row["Material Name"]).strip()
            if pd.notna(row["Material Name"]) else ""
        )

        if not name:
            errors.append(f"Row {position + 1}: Material Name is blank")
        elif name in names_seen:
            errors.append(f"Row {position + 1}: duplicate material name '{name}'")
        else:
            names_seen.add(name)

        for column in CHEMISTRY_COLUMNS:
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


def show_material_master():

    if st.session_state.pop("material_saved", False):
        st.success(
            "Material Master saved successfully."
        )

    st.subheader("Material Master")

    original_df = _get_original_dataframe()

    chemistry_config = {}

    for column in CHEMISTRY_COLUMNS:
        chemistry_config[column] = st.column_config.NumberColumn(
            column,
            step=0.001,
            format="%.3f",
            default=0,
        )

    column_config = {
        "Material Name": st.column_config.TextColumn(
            "Material Name",
            required=True,
        ),
        "Bucket Only": st.column_config.CheckboxColumn(
            "Bucket Only",
            default=False,
        ),
        "LPP": st.column_config.NumberColumn(
            "LPP",
            step=0.01,
            format="%.2f",
        ),
        "Fe": st.column_config.TextColumn(
            "Fe",
            disabled=True,
            default="Balance",
            help="Fe is always the balance element — not entered or calculated here.",
        ),
        **chemistry_config,
    }

    editor_key = (
        f"material_editor_"
        f"{st.session_state.get('material_editor_version', 0)}"
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
    # doing so previously conflicted with Streamlit's own internal
    # per-key edit tracking and was corrupting typed values.
    st.session_state["material_edited_df"] = edited_df.copy()

    is_dirty = (
        len(edited_df) != len(original_df)
        or not edited_df[EDITABLE_COLUMNS].reset_index(drop=True).equals(
            original_df[EDITABLE_COLUMNS].reset_index(drop=True)
        )
    )

    st.session_state["material_dirty"] = is_dirty

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Save Material Master",
            key="save_material_master",
        ):
            recalculated_df = _with_calculated_fe(edited_df)
            errors = _validate(edited_df, recalculated_df)

            if errors:
                st.error("Please fix the following before saving:")

                for message in errors:
                    st.write(f"- {message}")
            else:
                save_material_changes()
                st.rerun()

    with col2:
        if st.button(
            "Discard Changes",
            disabled=not is_dirty,
            key="discard_material_master",
        ):
            discard_material_changes()
            st.rerun()