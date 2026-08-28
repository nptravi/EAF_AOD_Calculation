"""
EAF calculation engine.

This module shows how to pull the data you'll need from the DB and
shape it into plain Python values. The actual mass-balance math is
left for you to fill in.
"""

from app.database.queries import (
    get_material_master,
    get_recovery_for_unit_code,
    get_grade_composition,
)

ELEMENTS = [
    "Fe", "C", "Si", "Mn", "Cr", "Ni",
    "Cu", "Ti", "Nb", "Mo", "P", "S", "N"
]


def material_chemistry_fraction(material):
    """
    material: a MaterialMaster row (e.g. from get_material_master()).

    MaterialMaster stores C, Si, Mn, Cr, Ni, Cu, Ti, Nb, Mo, P, S, N
    as 0-1 fractions. Fe is NOT a column — it's always the balance.

    Returns a dict of all 13 elements -> 0-1 fraction.
    """
    chemistry = {
        "C": material.C,
        "Si": material.Si,
        "Mn": material.Mn,
        "Cr": material.Cr,
        "Ni": material.Ni,
        "Cu": material.Cu,
        "Ti": material.Ti,
        "Nb": material.Nb,
        "Mo": material.Mo,
        "P": material.P,
        "S": material.S,
        "N": material.N,
    }
    chemistry["Fe"] = 1 - sum(chemistry.values())
    return chemistry


def get_material_lookup():
    """
    Returns {material_name: chemistry_dict} for every material in
    Material Master. chemistry_dict is the 13-element 0-1 fraction
    dict from material_chemistry_fraction().

    Example:
        lookup = get_material_lookup()
        lookup["FeSi"]["Si"]   # -> 0.75 (a 0-1 fraction)
    """
    materials = get_material_master()
    return {
        material.material_name: material_chemistry_fraction(material)
        for material in materials
    }


def get_eaf_recovery():
    """
    Returns {element: 0-1 fraction} for the EAF unit's recovery row.

    Example:
        recovery = get_eaf_recovery()
        recovery["Mn"]   # -> 0.85 (a 0-1 fraction)
    """
    recovery_row = get_recovery_for_unit_code(3501)

    if recovery_row is None:
        raise ValueError("EAF recovery data not found in Recovery Master.")

    return {element: getattr(recovery_row, element) for element in ELEMENTS}


def calculate_eaf(params):
    """
    params: object having grade and eaf_materials as sub objects (material_name: qty

    Fill in the mass-balance calculation below.
    """
    material_rows = params["eaf_materials"]
    print(f"inside calculate_eaf: material_rows: {material_rows}")
    material_lookup = get_material_lookup()
    recovery = get_eaf_recovery()
    oxygen_qty = 0.0
    contributions = {element: 0.0 for element in ELEMENTS}
    for material_name in material_rows:
        if material_name == "Oxygen":
            oxygen_qty += material_rows[material_name]
            print("Skipping Oxygen. Calculation Code to be added after completing all other materials.")
            continue
        contrib = {element:(
                               material_lookup[material_name][element] *
                               recovery[element] *
                               material_rows[material_name]
                            )   for element in ELEMENTS}
        for element in ELEMENTS:
            contributions[element] += contrib[element]
            if element == "Si":
                print(f"{element} contrib from {material_name}: {contrib[element]}")
    print(f"Oxygen qty: {oxygen_qty}. Calculated contributions before Oxygen adjustment: {contributions} ")
    # Oxygen adjustment
    contrib = {element: 0.0 for element in ELEMENTS}
    contrib["Fe"] = - oxygen_qty * 0.1 / 1000.0
    if (0.9 * contributions["C"]) > oxygen_qty/2000.0:
        contrib["C"] = -oxygen_qty/2000.0
    else:
        contrib["C"] = -0.9 * contributions["C"]
    if (contributions["Si"]) > oxygen_qty/2000.0:
        contrib["Si"] = -oxygen_qty/2000.0
    else:
        contrib["Si"] = -contributions["Si"]
    for element in ELEMENTS:
        contributions[element] += contrib[element]
    output_weight = sum(contributions.values())
    output_chemistry = {element:contributions[element]/output_weight for element in ELEMENTS}
    print(f"Calculated contributions after Oxygen adjustment: {contributions} ")

    return {
        "eaf_weight": output_weight,
        "eaf_chemistry": output_chemistry,
    }
