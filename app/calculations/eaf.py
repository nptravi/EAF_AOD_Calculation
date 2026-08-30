"""
EAF calculation engine.

This module shows how to pull the data you'll need from the DB and
shape it into plain Python values. The actual mass-balance math is
left for you to fill in.
"""
from pandas.core.arrays.datetimelike import ensure_arraylike_for_datetimelike
from sqlalchemy import case
from sqlalchemy.testing import force_drop_names

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
        "C": chemistry_obj.C,
        "Si": chemistry_obj.Si,
        "Mn": chemistry_obj.Mn,
        "Cr": chemistry_obj.Cr,
        "Ni": chemistry_obj.Ni,
        "Cu": chemistry_obj.Cu,
        "Nb": chemistry_obj.Nb,
        "Mo": chemistry_obj.Mo
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
    elements_to_calculate = ["Cr", "Mn", "Ni", "Cu", "Nb", "Mo","Si"]


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

    materials_having_si = [
        mtrl for mtrl in material_lookup
        if material_lookup[mtrl]["Si"] > 0.1
    ]



    while iter_count<50:
        iter_count+=1
        # Calculate material quantities
        for elm in elements_to_calculate:
            aod_wt = 0
            for material in aod_materials_contributions:
                #print(f"material identifier 001: {aod_materials_contributions[material]}")
                for elm2 in ELEMENTS:
                    aod_wt += aod_materials_contributions[material][elm2]
            mtrl = get_element_provider(elm)
            primary_material_name = mtrl["primary"].material_name
            if mtrl["alternate"] is None:
                alternate_material_name = None
            else:
                alternate_material_name = mtrl["alternate"].material_name

            calculated_material_name = primary_material_name
            calculated_material_weight = 0
            forced_material_name = None
            forced_qty = 0

            if elm == "Mn":
                if alternate_material_name is not None:
                    forced_material_name = params["mn_override"]["material"]
                    forced_qty = params["mn_override"]["qty"]
            if elm == "Si":
                # Other Material Contribution Calculation
                forced_material_contribution = {elm2: 0 for elm2 in ELEMENTS}
                other_materials_Si_contribution = sum(
                    aod_materials_contributions[mat][elm]
                    for mat in aod_materials_contributions.keys()
                    if mat != primary_material_name
                )
                # FeSi Contribution Calculation
                if calculated_material_name is not None:
                    calculated_material_weight = (
                            (
                                    (aod_wt * chemistry_needed[elm]) -
                                    other_materials_Si_contribution
                            ) /
                            (
                                    aod_recovery[elm] *
                                    material_lookup[calculated_material_name][elm]
                            )
                    )
                    if calculated_material_weight < 0:
                        calculated_material_weight = 0
                    calculated_material_contribution = {
                        elm2:
                            calculated_material_weight *
                            aod_recovery[elm2] *
                            material_lookup[calculated_material_name][elm2]
                        for elm2 in ELEMENTS
                    }
                    aod_materials_contributions[calculated_material_name] = calculated_material_contribution.copy()
                    material_usage[calculated_material_name] = calculated_material_weight
                else:
                    print(f"No provider material for {elm}")
            else:
                # Calculation for elements other than Si
                # Forced Material Calculation
                forced_material_contribution = {elm2:0 for elm2 in ELEMENTS}
                if forced_material_name is not None:
                    forced_material_contribution = {
                        elm2:
                            forced_qty *
                            aod_recovery[elm2] *
                            material_lookup[forced_material_name][elm]
                        for elm2 in ELEMENTS
                    }
                    material_usage[forced_material_name] = forced_qty
                    aod_materials_contributions[forced_material_name] = forced_material_contribution.copy()
                # Other Material Calculation
                if calculated_material_name is not None:
                    calculated_material_weight = (
                                (
                                    (aod_wt * chemistry_needed[elm]) -
                                    (eaf_output_weight * eaf_output_chemistry[elm] * aod_recovery[elm]) -
                                    (forced_material_contribution[elm])
                                ) /
                                (
                                   aod_recovery[elm] *
                                   material_lookup[calculated_material_name][elm]
                                )
                    )
                    calculated_material_contribution = {
                        elm2:
                            calculated_material_weight *
                            aod_recovery[elm2] *
                            material_lookup[calculated_material_name][elm2]
                        for elm2 in ELEMENTS
                    }
                    aod_materials_contributions[calculated_material_name] = calculated_material_contribution.copy()
                    material_usage[calculated_material_name] = calculated_material_weight
                else:
                    print(f"No provider material for {elm}")

        print(f"iteration: {iter_count} Material usage: {material_usage}")
        #print(f"aod materials contributions: {aod_materials_contributions}")

        # TODO Calculate effect of Oxygen
        oxidation_loss = {}
        oxidation_fe =oxidation_rates["Fe"] * sum(mat.get("Fe") for mat in aod_materials_contributions.values())
        oxidation_c = ((aod_wt * chemistry_needed["C"]) -
                               sum(
                                   mat.get("C")
                                        for mat in aod_materials_contributions.values()
                                        if mat !="Oxygen"
                               )
                       )
        oxidation_cr = sum(mat.get("Cr") for mat in aod_materials_contributions.values()) * oxidation_rates["Cr"]
        oxidation_mn = (
                        sum(
                            mat.get("Mn")
                                for mat in aod_materials_contributions.values()
                                if mat not in materials_having_si
                            ) *
                        oxidation_rates["Mn"]
        )
        # Real losses due to oxidation of elements already accounted through recovery. Hence oxidation of Cr and Mn is
        # assumed to be recovered with Si
        # Calculation below calculation is based on chemical reaction for reducing Oxides of Cr and Mn with Si
        oxidation_si = (oxidation_cr * 84.0 / 208.0) + (oxidation_mn * 28.0 / 110.0)
        aod_materials_contributions["Oxygen"]={elm2:0 for elm2 in ELEMENTS}
        aod_materials_contributions["Oxygen"]["Fe"] = -oxidation_fe
        aod_materials_contributions["Oxygen"]["C"] =  oxidation_c
        aod_materials_contributions["Oxygen"]["Si"] = -oxidation_si

        # Calculate Max deviation in elements chemistry
        combined_aod_contributions = {
            elm2: sum(mat.get(elm2) for mat in aod_materials_contributions.values())
            for elm2 in ELEMENTS
        }
        #print(f"Combined aod contributions: {combined_aod_contributions}")
        aod_output_weight = sum(combined_aod_contributions.values())
        aod_output_chemistry = {
            elm2: combined_aod_contributions[elm2]/aod_output_weight
            for elm2 in ELEMENTS
        }
        #print(f"aod output chemistry: {aod_output_chemistry}")
        chemistry_deviation = {
            elm2: abs(chemistry_needed[elm2] - aod_output_chemistry[elm2])
            for elm2 in chemistry_needed.keys()
        }
        print(f"chemistry deviation: {chemistry_deviation} Max Deviation: {max(chemistry_deviation.values())}")
        if max(chemistry_deviation.values()) < 0.00001:
            break
    print(f"AOD output weight: {aod_output_weight}")
    print(f"AOD chemistry: {aod_output_chemistry}")

        # If max deviation < 0.002% break the loop




    return {
        "eaf_weight": eaf_output_weight,
        "eaf_chemistry": eaf_output_chemistry,
    }
