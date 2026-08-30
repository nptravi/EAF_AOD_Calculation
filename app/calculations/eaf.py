"""
EAF calculation engine.

This module shows how to pull the data you'll need from the DB and
shape it into plain Python values. The actual mass-balance math is
left for you to fill in.
"""
from pandas.core.arrays.datetimelike import ensure_arraylike_for_datetimelike
from sqlalchemy import case

from app.database.queries import (
    get_material_master,
    get_recovery_for_unit_code,
    get_grade_composition,
    get_element_provider,
    get_element_provider_details, get_aod_provider_master, get_material_details_by_name, get_material_details_by_id,
    get_aod_provider_master_with_materials,
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

def get_aod_recovery():
    """
    Returns {element: 0-1 fraction} for the AOD unit's recovery row.

    Example:
        recovery = get_aod_recovery()
        recovery["Mn"]   # -> 0.85 (a 0-1 fraction)
    """
    recovery_row = get_recovery_for_unit_code(3502)

    if recovery_row is None:
        raise ValueError("AOD recovery data not found in Recovery Master.")

    return {element: getattr(recovery_row, element) for element in ELEMENTS}


def calculate_eaf(params):
    """
    params: object having grade and eaf_materials as sub objects (material_name: qty

    Fill in the mass-balance calculation below.
    """
    material_rows = params["eaf_materials"]
    print(f"inside calculate_eaf: material_rows: {material_rows}")
    material_lookup = get_material_lookup()
    eaf_recovery = get_eaf_recovery()
    oxygen_qty = 0.0
    eaf_contributions = {element: 0.0 for element in ELEMENTS}
    for material_name in material_rows:
        if material_name == "Oxygen":
            oxygen_qty += material_rows[material_name]
            print("Skipping Oxygen. Calculation Code to be added after completing all other materials.")
            continue
        contrib = {element:(
                               material_lookup[material_name][element] *
                               eaf_recovery[element] *
                               material_rows[material_name]
                            )   for element in ELEMENTS}
        for element in ELEMENTS:
            eaf_contributions[element] += contrib[element]
            if element == "Si":
                print(f"{element} contrib from {material_name}: {contrib[element]}")
    print(f"Oxygen qty: {oxygen_qty}. Calculated contributions before Oxygen adjustment: {eaf_contributions} ")
    # Oxygen adjustment
    contrib = {element: 0.0 for element in ELEMENTS}
    contrib["Fe"] = - oxygen_qty * 0.1 / 1000.0
    if (0.9 * eaf_contributions["C"]) > oxygen_qty/2000.0:
        contrib["C"] = -oxygen_qty/2000.0
    else:
        contrib["C"] = -0.9 * eaf_contributions["C"]
    if (eaf_contributions["Si"]) > oxygen_qty/2000.0:
        contrib["Si"] = -oxygen_qty/2000.0
    else:
        contrib["Si"] = -eaf_contributions["Si"]
    for element in ELEMENTS:
        eaf_contributions[element] += contrib[element]
    eaf_output_weight = sum(eaf_contributions.values())
    eaf_output_chemistry = {element:eaf_contributions[element]/eaf_output_weight for element in ELEMENTS}
    print(f"Calculated contributions after Oxygen adjustment: {eaf_contributions} ")
    oxidation_rates = {"Fe": 0.02, "Cr": 0.2, "Mn": 0.4}
    # AOD Calculation
    mn_override = params["mn_override"]
    chemistry_obj = get_grade_composition(params["grade"])
    chemistry_needed = {
        "Cr": chemistry_obj.Cr
    }

    # Initialization of values / parameters
    aod_wt = eaf_output_weight
    aod_recovery = get_aod_recovery()
    aod_providers = get_aod_provider_master_with_materials()
    #print(f"aod_providers: {aod_providers}")
    material_usage = {}
    for mat in aod_providers:
        #print(f"mat: {mat} Provider name: {aod_providers[mat]["primary"].material_name}")
        material_usage[aod_providers[mat]["primary"].material_name] = 0
        if aod_providers[mat]["alternate"] is not None:
            material_usage[aod_providers[mat]["alternate"].material_name] = 0

    print(f"material_usage: {material_usage}")
    print(f"aod_recovery: {aod_recovery}")
    print(f"chemistry_needed: {chemistry_needed}")
    iter_count=0
    # elements_to_calculate = ["Cr", "Mn", "Ni", "Cu", "Nb", "Mo"]
    elements_to_calculate = ["Cr"]

    aod_materials_contributions = {
        mtrl: {
            elm:0 for elm in ELEMENTS
        }
        for mtrl in material_usage.keys()
    }
    aod_materials_contributions["eaf_metal"] =  {
            element:
                eaf_output_weight *
                eaf_output_chemistry[element] *
                aod_recovery[element]
            for element in ELEMENTS
        }




    while iter_count<1:
        iter_count+=1
        # Calculate material quantities
        for elm in elements_to_calculate:
            aod_wt = 0
            for material in aod_materials_contributions:
                print(f"material identifier 001: {aod_materials_contributions[material]}")
                for elm2 in ELEMENTS:
                    aod_wt += aod_materials_contributions[material][elm2]
            mtrl = get_element_provider(elm)
            match elm:
                case "Cr":
                    mtrl_wt = ((aod_wt * chemistry_needed[elm]) - (eaf_output_weight * eaf_output_chemistry[elm] * aod_recovery[elm])) / (aod_recovery[elm] * material_lookup[mtrl["primary"].material_name][elm])
                    material_usage[mtrl["primary"].material_name] = mtrl_wt
                case "Mn":
                    pass
                case "Ni":
                    pass
                case "Cu":
                    pass
                case "Nb":
                    pass
                case "Mo":
                    pass
            print(f"iteration: {iter_count} Material usage: {material_usage}")
        # Calculate material contributions

        # Calculate effect of Oxygen

        # Calculate Max deviation in elements chemistry

        # If max deviation < 0.002% break the loop




    return {
        "eaf_weight": eaf_output_weight,
        "eaf_chemistry": eaf_output_chemistry,
    }
