#import standard and custom libraries

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.ticker import MultipleLocator
from common_functions import *

def make_plots(IV_data, TC_data):
    '''
    Function which governs the making of IV plots.

    Arguments:
    IV_data - the contents of a pre-opened IV JSON file
    TC_data - the contents of a pre-opened ColdJigRun JSON file

    Returns:
    plot - Type = matplotlib figure. The plot made.
    '''

    matplotlib.rcParams['font.size'] = 6
    plot = plt.figure(figsize=[8, 4], dpi=50)

#Make overview plot
    plt.subplot(121)
    make_overview_plot(IV_data, TC_data)

#Make breakdown voltage plot
    plt.subplot(122)
    make_breakdown_plot(IV_data, TC_data)

    plt.tight_layout()
    plt.close('all')

    return plot

def make_overview_plot(IV_data, TC_data):
    '''
    Plots all IVs throughout thermal cycling, using a blue colour scheme
    for cold IVs and a red colour scheme for warm IVs.

    Arguments:
    IV_data - the contents of a pre-opened IV JSON file
    TC_data - the contents of a pre-opened ColdJigRun JSON file
    '''

    voltages               = get_voltages(IV_data)
    currents               = get_currents(IV_data)
    scans                  = get_scans(IV_data) #names of specific IVs
    warm_scans, cold_scans = sort_scan_temp(scans, TC_data) #scans sorted by temp
    component = get_component(IV_data) #module serial number

    red_cold, red_warm, blue_cold, blue_warm, green_cold, green_warm = get_colours(warm_scans, cold_scans)

    w = -1 #initialize warm scan counter
    c = -1 #initialize cold scan counter

#Plot IVs based on temperature
    for n, scan in enumerate(scans):
        if scan in warm_scans:
            w = w + 1
            plt.plot(voltages[n], currents[n], color=(red_warm, green_warm[w], blue_warm), label=f"Warm IV {w}", marker='.', markersize=3, linewidth=0.9) #plot warm scan

        elif scan in cold_scans:
            c = c + 1
            plt.plot(voltages[n], currents[n], color=(red_cold, green_cold[c], blue_cold), label=f"Cold IV {c}", marker='.', markersize=3, linewidth=0.9) #plot cold scan

        else:
            print(f"{YELLOW}Scan {scan} not flagged as warm or cold!{RESET}") #scan won't be plotted

    plt.xlabel("Voltage (V)")
    plt.ylabel("Current (nA)")
    plt.title(f"{component} IV Results Throughout TC")
    plt.legend(ncol=2, fontsize=5, framealpha=0.6, bbox_to_anchor=(1,1))

def make_breakdown_plot(IV_data, TC_data):
    '''
    Makes a plot showing all breakdown voltages registered by
    ITSDAQ where |Vbd| <= 550V.

    Arguments:
    IV_data - the contents of a pre-opened IV JSON file
    TC_data - the contents of a pre-opened ColdJigRun JSON file
    '''
    VBDs                    = get_VBDs(IV_data) #retrieve all breakdown voltages
    scans                   = get_scans(IV_data)
    warm_scans, cold_scans  = sort_scan_temp(scans, TC_data)

    component  = get_component(IV_data)
    warm_tests = []
    cold_tests = []

    for n, scan in enumerate(scans): #Sort IV number by temperature
        if scan in warm_scans:
            warm_tests.append(n)
        elif scan in cold_scans:
            cold_tests.append(n)
        else:
            print(f"{YELLOW}Scan {scan} not flagged as warm or cold!{RESET}")

#Plot
    plt.scatter(warm_tests, [VBDs[w] for w in warm_tests], color='r',
                label="Warm Breakdown", s=7)
    plt.scatter(cold_tests, [VBDs[c] for c in cold_tests], color='b',
                label="Cold Breakdown", s=7)
    plt.plot(range(len(scans)), [500 for scan in scans], color='g',
            linestyle='dashed', label="Pass Criteria")
    plt.plot(range(len(scans)), [350 for scan in scans], color='k',
            linestyle='dashed', label="Nominal Bias Voltage")
    plt.xlabel("Test Number")
    plt.ylabel("Breakdown Voltage (V)")
    plt.ylim(0, 600)
    plt.title(f"{component} Breakdown Voltage Throughout TC")
    plt.grid(axis='x')
    plt.gca().xaxis.set_major_locator(MultipleLocator(2))
    plt.legend(ncol=2)

def get_voltages(IV_data):
    '''
    Retrieve the voltage values for all IVs performed during TC.

    Arguments:
    IV_data - the contents of a pre-opened IV JSON file

    Returns:
    voltages - Type = list of list. Each sublist is the voltages for a single test.
    '''

    voltages = IV_data["results"]["VOLTAGE"]

    return voltages

def get_currents(IV_data):
    '''
    Retrieve the current values for all IVs performed during TC.

    Arguments:
    IV_data - the contents of a pre-opened IV JSON file

    Returns:
    currents - Type = list of list. Each sublist is the currents for a single test.
    '''

    currents = IV_data["results"]["CURRENT"]

    return currents

def get_VBDs(IV_data):
    '''
    Retrieve all breakdown voltages throughout TC. If the breakdown voltage is above
    550V (outside scope of IV), replace it with nan.

    Arguments:
    IV_data - the contents of a pre-opened IV JSON file.

    Returns:
    VBDs - Type = list of float. A list of the breakdown voltages, one per IV.
    '''

    VBDs = IV_data["results"]["VBD"]

    for n in range(len(VBDs)):
        if VBDs[n] > 550:    #replace VBD with nan if VBD > 550V
            VBDs[n] = np.nan

    return VBDs
























