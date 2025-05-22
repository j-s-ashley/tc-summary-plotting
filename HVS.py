#import libraries
import numpy as np
import matplotlib.pyplot as plt
from common_functions import *
import matplotlib

def make_plots(HVS_data):
    '''
    Plots High Voltage Stability current by reading number. Only in its own script for
    consistency's sake.

    Arguments:
    HVS_data - the contents of a pre-opened HVSTABILITY JSON file.

    Returns:
    plot - Type = matplotlib figure. The plot made.
    '''

    component = get_component(HVS_data)
    plot = plt.figure(figsize=[9,4], dpi=50)

    currents = HVS_data["results"]["CURRENT"] #current readings
    readings = range(len(currents)) #list of int corresponding to each reading

    plt.plot(readings, currents, marker="o", color='firebrick', markersize=2, linewidth=0.5) #plot
    plt.title(f"{component} Current During HV Stability Test")
    plt.xlabel("Reading Number")
    plt.ylabel("Current (A)")

    plt.close('all')

    return plot
