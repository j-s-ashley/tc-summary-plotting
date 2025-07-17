#Import standard libraries
import numpy as np
import matplotlib.pyplot as plt
import json
import argparse
from PIL import Image
#Import TC plotting scripts
import IV
import PT
import SD
import RC
import NO
import OCS
import TC
import defect_plotting
from common_functions import *
import ITkPDB_matters as db

#Parse arguments
parser = argparse.ArgumentParser(
  description="Create plots summarizing the results of module Thermal Cycling.")
parser.add_argument("-d", "--TC_directory",
  help="Directory containing all merged TC results for a single module, including ColdJigRun file and HV Stability file.")
parser.add_argument("-db", "--database",
  help="Queries ATLAS ITk Production Database, instead of local files.", action='store_true')
parser.add_argument("-t", "--tests",
  help="Test types to be plotted (IV, PT, SD, 3PG, 10PG, NO, OCS). If not specified, all will be plotted.", nargs="+", default = ["IV", "PT", "SD", "3PG", "10PG", "NO", "OCS"])
parser.add_argument("-n", "--noise_only", help="When making the 3PG/10PG plots, only make plots for the noise, not the gain or VT50", action='store_true')
parser.add_argument("-hg", "--histograms", help="Make histograms with module defect information", action='store_true')
args = parser.parse_args()

TC_directory = args.TC_directory
test_types   = args.tests
noise_only   = args.noise_only
histos       = args.histograms
query_db     = args.database


#Define file variables

if not query_db: #if using local files

    #Get files
    files = fetch_files(TC_directory)
    IV_file    = f'{TC_directory}/{files["IV"]}'
    PT_files   = [f'{TC_directory}/{PT_file}' for PT_file in files["PT"]]
    SD_files   = [f'{TC_directory}/{SD_file}' for SD_file in files["SD"]]
    TPG_files  = [f'{TC_directory}/{TPG_file}' for TPG_file in files["TPG"]]
    RC_files   = [f'{TC_directory}/{RC_file}' for RC_file in files["RC"]]
    NO_files   = [f'{TC_directory}/{NO_file}' for NO_file in files["NO"]]
    OCS_files  = [f'{TC_directory}/{OCS_file}' for OCS_file in files["OCS"]]
    TC_file    = f'{TC_directory}/{files["TC"]}'

if query_db: #if getting data from the database

    IV_file, PT_files, SD_files, TPG_files, RC_files, NO_files, OCS_files, TC_file = db.get_files()
    files = {'IV' : IV_file,
             'PT': PT_files,
             'SD': SD_files,
             '3PG': TPG_files,
             '10PG': RC_files,
             'NO': NO_files,
             'OCS': OCS_files,
             'TC': TC_file} #files sorted by type

IV_plots    = [] #initialize
PT_plots    = []
SD_plots    = []
TPG_plots   = []
RC_plots    = []
NO_plots    = []
OCS_plots   = []
TC_plots    = []
histo_plots = []

#Define TC data

TC_data = retrieve_data(TC_file)

#Make IV plots
if "IV" in test_types:
    print("\nMaking IV plots...")
    IV_data = retrieve_data(IV_file)
    IV_plots.append(IV.make_plots(IV_data, TC_data))
    print(f"\n{GREEN}IV plots complete!{RESET}")

#Make PT plots
if "PT" in test_types:
    print("\nMaking Pedestal Trim plots...")

    for PT_file in PT_files:
        PT_data = retrieve_data(PT_file)
        PT_plots.append(PT.make_plots(PT_data, TC_data))
    print(f"\n{GREEN}Pedestal Trim plots complete!{RESET}")

#Make SD plots
if "SD" in test_types:
    print("\nMaking Strobe Delay plots...")

    for SD_file in SD_files:
        SD_data = retrieve_data(SD_file)
        SD_plots.append(SD.make_plots(SD_data, TC_data))
    print(f"\n{GREEN}Strobe Delay plots complete!{RESET}")

#Make 3PG plots
if "3PG" in test_types:
    print("\nMaking 3-Point Gain plots...")

    for TPG_file in TPG_files:
        TPG_data = retrieve_data(TPG_file)
        TPG_plots.append(RC.make_plots(TPG_data, TC_data, noise_only))
    print(f"\n{GREEN}3-Point Gain plots complete!{RESET}")

#Make 10PG plots
if "10PG" in test_types:
    print("\nMaking 10-Point Gain plots...")

    for RC_file in RC_files:
        RC_data = retrieve_data(RC_file)
        RC_plots.append(RC.make_plots(RC_data, TC_data, noise_only))
    print(f"\n{GREEN}10-Point Gain plots complete!{RESET}")

#Make NO plots
if "NO" in test_types:
    print("\nMaking Noise Occupancy plots...")

    for NO_file in NO_files:
        NO_data = retrieve_data(NO_file)
        NO_plots.append(NO.make_plots(NO_data, TC_data))
    print(f"\n{GREEN}Noise Occupancy plots complete!{RESET}")

#Make OCS plots
if "OCS" in test_types:
    print("\nMaking Open Channel Search plots...")

    for OCS_file in OCS_files:
        OCS_data = retrieve_data(OCS_file)
        OCS_plots.append(OCS.make_plots(OCS_data, TC_data))
    print(f"\n{GREEN}Open Channel Search plots complete!{RESET}")

#Make defect histograms
if histos:
    print("\nMaking Defect Histograms...")
    hybrid_files = sort_files_by_hybrid(unsort_files(files), TC_directory)

    for hybrid in hybrid_files:
        if type(hybrid_files[hybrid][0]) is not dict:
            files_to_plot = [f"{TC_directory}/{file}" for file in hybrid_files[hybrid]]
        else:
            files_to_plot = hybrid_files[hybrid]
        histo_plots.append(defect_plotting.make_plots(files_to_plot, TC_data))
    print(f"\n{GREEN}Defect Histograms complete!{RESET}")
#Make TC summary plots
print("\nMaking Thermal Cycling summary plots...")

failed_tests = []

unsorted_files = unsort_files(files)

for file in unsorted_files:

    if "HV" not in file and type(file) is not dict: #if using local files
        failed_tests.append(fetch_failed_tests(f'{TC_directory}/{file}'))

    elif type(file) is dict and "HV" not in file['testType']['code']: #if querying DB
        failed_tests.append(fetch_failed_tests(file))

TC_plots.append(TC.make_plots(TC_data, failed_tests))
print(f"\n{GREEN}Thermal Cycling summary plots complete!{RESET}")

#Make single PDF from all made plots
print("\nMaking PDF...")
all_plots0 = IV_plots + PT_plots + SD_plots + make_one_list(TPG_plots) + make_one_list(RC_plots) + NO_plots + OCS_plots + make_one_list(histo_plots) + make_one_list(TC_plots) #all plots made
all_plots  = (make_one_list(all_plots0)) #reformat
component  = get_component(TC_data) #module serial number
date       = TC_data["date"][:10] #date that TC was run
run_number = TC_data["runNumber"] #ColdJig run number
make_pdf(all_plots, component, date, run_number) #put the plots into a single PDF

plt.close('all')
print(f"\n{GREEN}Plotting complete!{RESET}")



