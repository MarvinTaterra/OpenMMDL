# This script was generated by OpenMM-MDL Setup on 2022-11-27.


#       ,-----.    .-------.     .-''-.  ,---.   .--.,---.    ,---.,---.    ,---. ______       .---.
#     .'  .-,  '.  \  _(`)_ \  .'_ _   \ |    \  |  ||    \  /    ||    \  /    ||    _ `''.   | ,_|
#    / ,-.|  \ _ \ | (_ o._)| / ( ` )   '|  ,  \ |  ||  ,  \/  ,  ||  ,  \/  ,  || _ | ) _  \,-./  )
#   ;  \  '_ /  | :|  (_,_) /. (_ o _)  ||  |\_ \|  ||  |\_   /|  ||  |\_   /|  ||( ''_'  ) |\  '_ '`)
#   |  _`,/ \ _/  ||   '-.-' |  (_,_)___||  _( )_\  ||  _( )_/ |  ||  _( )_/ |  || . (_) `. | > (_)  )
#   : (  '\_/ \   ;|   |     '  \   .---.| (_ o _)  || (_ o _) |  || (_ o _) |  ||(_    ._) '(  .  .-'
#    \ `"/  \  ) / |   |      \  `-'    /|  (_,_)\  ||  (_,_)  |  ||  (_,_)  |  ||  (_.\.' /  `-'`-'|___
#     '. \_/``".'  /   )       \       / |  |    |  ||  |      |  ||  |      |  ||       .'    |        \
#       '-----'    `---'        `'-..-'  '--'    '--''--'      '--''--'      '--''-----'`      `--------`


from scripts.forcefield_water import (
    ff_selection,
    water_forecfield_selection,
    water_model_selection,
    generate_forcefield,
    generate_transitional_forcefield,
)
from scripts.protein_ligand_prep import (
    protein_choice,
    prepare_ligand,
    rdkit_to_openmm,
    merge_protein_and_ligand,
    water_padding_solvent_builder,
    water_absolute_solvent_builder,
    membrane_builder,
    water_conversion,
)
from scripts.post_md_conversions import (
    mdtraj_conversion,
    MDanalysis_conversion,
    rmsd_for_atomgroups,
    RMSD_dist_frames,
    atomic_distance,
)
from scripts.cleaning_procedures import cleanup, post_md_file_movement

import simtk.openmm.app as app
from simtk.openmm.app import (
    PDBFile,
    Modeller,
    PDBReporter,
    StateDataReporter,
    DCDReporter,
    CheckpointReporter,
)
from simtk.openmm import (
    unit,
    Platform,
    Platform_getPlatformByName,
    MonteCarloBarostat,
    LangevinMiddleIntegrator,
)
from simtk.openmm import Vec3
import simtk.openmm as mm
import sys
import os
import shutil

# Input Files
############# Ligand and Protein Data ###################
########   Add the Ligand SDf File and Protein PDB File in the Folder with the Script  #########

ligand_select = "yes"
ligand_name = "UNK"
ligand_sdf = "6b73_lig.sdf"

minimize = False
protein = "6b73-moe-processed_openMMDL.pdb"

############# Ligand and Protein Preparation ###################

protein_prepared = "Yes"

############# Forcefield, Water and Membrane Model Selection ###################

ff = "AMBER14"
water = "TIP3P-FB"

############# Membrane Settings ###################

add_membrane = True
membrane_lipid_type = "POPC"
membrane_padding = 1.0
membrane_ionicstrength = 0.15
membrane_positive_ion = "Na+"
membrane_negative_ion = "Cl-"

############# Post MD Processing ###################

MDAnalysis_Postprocessing = True
MDTraj_Cleanup = True

# System Configuration

nonbondedMethod = app.PME
nonbondedCutoff = 1.0 * unit.nanometers
ewaldErrorTolerance = 0.0005
constraints = app.HBonds
rigidWater = True
constraintTolerance = 0.000001
hydrogenMass = 1.5 * unit.amu

# Integration Options

dt = 0.004 * unit.picoseconds
temperature = 300 * unit.kelvin
friction = 1.0 / unit.picosecond
pressure = 1.0 * unit.atmospheres
barostatInterval = 25

# Simulation Options

steps = 1250000
equilibrationSteps = 1000
platform = Platform.getPlatformByName("CUDA")
platformProperties = {"Precision": "single"}
dcdReporter = DCDReporter("trajectory.dcd", 12500)
dataReporter = StateDataReporter(
    "log.txt",
    1000,
    totalSteps=steps,
    step=True,
    speed=True,
    progress=True,
    potentialEnergy=True,
    temperature=True,
    separator="\t",
)
checkpointReporter = CheckpointReporter("checkpoint.chk", 10000)
checkpointReporter10 = CheckpointReporter("10x_checkpoint.chk", 100000)
checkpointReporter100 = CheckpointReporter("100x_checkpoint.chk", 1000000)

if ligand_select == "yes":

    print("Preparing MD Simulation with ligand")

    ligand_prepared = prepare_ligand(ligand_sdf, minimize_molecule=minimize)

    omm_ligand = rdkit_to_openmm(ligand_prepared, ligand_name)

protein_pdb = protein_choice(protein_is_prepared=protein_prepared, protein=protein)
forcefield_selected = ff_selection(ff)
water_selected = water_forecfield_selection(
    water=water, forcefield_selection=ff_selection(ff)
)
model_water = water_model_selection(water=water, forcefield_selection=ff_selection(ff))
print("Forcefield and Water Model Selected")

if ligand_select == "yes":

    if add_membrane == True:
        transitional_forcefield = generate_transitional_forcefield(
            protein_ff=forcefield_selected,
            solvent_ff=water_selected,
            add_membrane=add_membrane,
            rdkit_mol=ligand_prepared,
        )

    forcefield = generate_forcefield(
        protein_ff=forcefield_selected,
        solvent_ff=water_selected,
        add_membrane=add_membrane,
        rdkit_mol=ligand_prepared,
    )

    complex_topology, complex_positions = merge_protein_and_ligand(
        protein_pdb, omm_ligand
    )

    print("Complex topology has", complex_topology.getNumAtoms(), "atoms.")

modeller = app.Modeller(complex_topology, complex_positions)

if add_membrane == True:
    membrane_builder(
        ff,
        model_water,
        forcefield,
        transitional_forcefield,
        protein_pdb,
        modeller,
        membrane_lipid_type,
        membrane_padding,
        membrane_positive_ion,
        membrane_negative_ion,
        membrane_ionicstrength,
        protein,
    )

elif add_membrane == False:
    if Water_Box == "Buffer":
        water_padding_solvent_builder(
            model_water,
            forcefield,
            water_padding_distance,
            protein_pdb,
            modeller,
            water_positive_ion,
            water_negative_ion,
            water_ionicstrength,
            protein,
        )
    elif Water_Box == "Absolute":
        water_absolute_solvent_builder(
            model_water,
            forcefield,
            water_box_x,
            water_box_y,
            water_box_z,
            protein_pdb,
            modeller,
            water_positive_ion,
            water_negative_ion,
            water_ionicstrength,
            protein,
        )

if add_membrane == True:
    if model_water == "tip4pew" or model_water == "tip5p":
        water_conversion(model_water, modeller, protein)

topology = modeller.topology

positions = modeller.positions


# Prepare the Simulation

print("Building system...")
system = forcefield.createSystem(
    topology,
    nonbondedMethod=nonbondedMethod,
    nonbondedCutoff=nonbondedCutoff,
    constraints=constraints,
    rigidWater=rigidWater,
    ewaldErrorTolerance=ewaldErrorTolerance,
    hydrogenMass=hydrogenMass,
)
system.addForce(MonteCarloBarostat(pressure, temperature, barostatInterval))
integrator = LangevinMiddleIntegrator(temperature, friction, dt)
integrator.setConstraintTolerance(constraintTolerance)
simulation = app.Simulation(topology, system, integrator, platform, platformProperties)
simulation.context.setPositions(positions)

# Minimize and Equilibrate

print("Performing energy minimization...")
simulation.minimizeEnergy()

with open(f"Energyminimization_{protein}", "w") as outfile:
    PDBFile.writeFile(modeller.topology, modeller.positions, outfile)

print("Equilibrating...")
simulation.context.setVelocitiesToTemperature(temperature)
simulation.step(equilibrationSteps)

with open(f"Equilibration_{protein}", "w") as outfile:
    PDBFile.writeFile(modeller.topology, modeller.positions, outfile)


# Simulate

print("Simulating...")
simulation.reporters.append(PDBReporter(f"output_{protein}", 1250000))
simulation.reporters.append(dcdReporter)
simulation.reporters.append(dataReporter)
simulation.reporters.append(checkpointReporter)
simulation.reporters.append(checkpointReporter10)
simulation.reporters.append(checkpointReporter100)
simulation.reporters.append(
    StateDataReporter(
        sys.stdout, 1000, step=True, potentialEnergy=True, temperature=True
    )
)
simulation.currentStep = 0
simulation.step(steps)
mdtraj_conversion(f"Equilibration_{protein}")
MDanalysis_conversion(
    f"centered_old_coordinates.pdb", f"centered_old_coordinates.dcd", ligand_name="UNK"
)
rmsd_for_atomgroups(
    f"prot_lig_top.pdb",
    f"prot_lig_traj.dcd",
    selection1="backbone",
    selection2=["protein", "resname UNK"],
)
RMSD_dist_frames(f"prot_lig_top.pdb", f"prot_lig_traj.dcd", lig="UNK")
post_md_file_movement(protein, ligand_sdf)
