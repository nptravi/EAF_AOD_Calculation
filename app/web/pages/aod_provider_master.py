import pandas as pd
import streamlit as st

from app.database.queries import (
    get_material_master,
    get_eligible_provider_materials,
    get_aod_provider_master,
    save_aod_provider_master,
)


ELEMENTS = ["Si", "Mn", "Cr", "Ni", "Cu", "Nb", "Mo"]

EDITABLE_COLUMNS = ["Primary Material", "Alternate Material"]

COLUMN_ORDER = ["Element", "Primary Material", "Alternate Material"]


def _load_provider_dataframe():
    # Use ALL materials to resolve currently-saved selections (so a
    # material later flagged Bucket Only still displays correctly
    # instead of showing blank/broken), but restrict the dropdown's
    # selectable OPTIONS to eligible (non-Bucket-Only) materials only.
    all_materials = get_material_master()
    id_to_name = {m.id: m.material_name for m in all_materials}

    existing = {
        provider.element: provider
        for provider in get_aod_provider_master()
    }

    data = []

    for element in ELEMENTS:
        provider = existing.get(element)

        data.append({
            "Element": element,
            "Primary Material": (
                id_to_name.get(provider.primary_material_id)
                if provider and provider.primary_material_id
                else None
            ),
            "Alternate Material": (
                id_to_name.get(provider.alternate_material_id)
                if provider and provider.alternate_material_id
                else None
            ),
        })

    return pd.DataFrame(data, columns=COLUMN_ORDER)


def _get_material_options():
    eligible = get_eligible_provider_materials()
    return sorted(m.material_name for m in eligible)


def _get_original_dataframe():
    # Fixed baseline loaded once from the DB — never overwritten by
    # edits. Used for the dirty-check so it survives reruns (e.g.
    # Cancel in the navigation-protection flow).
    if "aod_original_df" not in st.session_state:
        st.session_state["aod_original_df"] = (
            _load_provider_dataframe()
        )

    return st.session_state["aod_original_df"].copy()


def aod_provider_has_unsaved_changes():
    return st.session_state.get(
        "aod_provider_dirty",
        False
    )


def _bump_editor_version():
    st.session_state["aod_provider_editor_version"] = (
        st.session_state.get("aod_provider_editor_version", 0) + 1
    )


def discard_aod_provider_changes():
    st.session_state.pop("aod_provider_edited_df", None)
    st.session_state.pop("aod_original_df", None)
    st.session_state["aod_provider_dirty"] = False
    _bump_editor_version()


def save_aod_provider_changes():
    edited_df = st.session_state.get("aod_provider_edited_df")

    if edited_df is None:
        edited_df = _get_original_dataframe()

    save_aod_provider_master(edited_df.to_dict("records"))

    st.session_state.pop("aod_provider_edited_df", None)
    st.session_state.pop("aod_original_df", None)
    st.session_state["aod_provider_dirty"] = False
    st.session_state["aod_provider_saved"] = True
    _bump_editor_version()


def show_aod_provider_master():

    if st.session_state.pop("aod_provider_saved", False):
        st.success(
            "AOD Provider Master saved successfully."
        )

    st.subheader("AOD Provider Master")

    st.caption(
        "Bucket Only materials are hidden from these dropdowns. "
        "Primary Material may be left blank for now — it must be "
        "set before running the EAF & AOD calculation."
    )

    original_df = _get_original_dataframe()
    material_options = _get_material_options()

    column_config = {
        "Element": st.column_config.TextColumn(
            "Element",
            disabled=True,
        ),
        "Primary Material": st.column_config.SelectboxColumn(
            "Primary Material",
            options=material_options,
            required=False,
        ),
        "Alternate Material": st.column_config.SelectboxColumn(
            "Alternate Material",
            options=material_options,
            required=False,
        ),
    }

    editor_key = (
        f"aod_provider_editor_"
        f"{st.session_state.get('aod_provider_editor_version', 0)}"
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

    # Persisted purely so app.py's nav-protection Save/Discard-from-
    # elsewhere handlers (which run outside this function) can read
    # the latest edits. Never fed back into the widget's own value.
    st.session_state["aod_provider_edited_df"] = edited_df.copy()

    is_dirty = not edited_df[EDITABLE_COLUMNS].reset_index(drop=True).equals(
        original_df[EDITABLE_COLUMNS].reset_index(drop=True)
    )

    st.session_state["aod_provider_dirty"] = is_dirty

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "Save AOD Provider Master",
            key="save_aod_provider_master",
        ):
            save_aod_provider_changes()
            st.rerun()

    with col2:
        if st.button(
            "Discard Changes",
            disabled=not is_dirty,
            key="discard_aod_provider_master",
        ):
            discard_aod_provider_changes()
            st.rerun()