#import libraries
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from common_functions import *

def make_plots(NO_data):
    '''
    Organizes the making of the plots, such as where the subplots go on the figure.

    Arguments:
    NO_data - the contents of a pre-opened NO JSON file.

    Returns:
    plot - Type = matplotlib figure. The plot made.
    '''
    matplotlib.rcParams['font.size'] = 5
    plot = plt.figure(figsize=[8,4], dpi=50)

#Make plot of all NO data throughout HBI for the under stream
    plt.subplot(221)
    all_occupancy_plots(NO_data, "Under")

#Make plot of all NO data throughout HBI for the away stream
    plt.subplot(222)
    all_occupancy_plots(NO_data, "Away")

#Make plot of mean NO data for the under stream
    plt.subplot(223)
    average_occupancy_plots(NO_data, "Under")

#Make a plot of mean NO data for the away stream
    plt.subplot(224)
    average_occupancy_plots(NO_data, "Away")

    plt.tight_layout()
    plt.close('all')

    return plot

def all_occupancy_plots(NO_data, stream):
    '''
    Makes a plot of all Noise Occupancy data from all of thermal cycling, colour-coded
    by test temperature, for a given stream.

    Arguments:
    NO_data - the contents of a pre-opened NO JSON file.
    stream  - Type = string, "Under" or "Away". The stream to be plotted.
    '''

    component              = get_component(NO_data) #hybrid serial number
    scans                  = get_scans(NO_data) #list of all NO scans during HBI
    chips                  = get_channels(NO_data)

    red_cold, red_warm, blue_cold, blue_warm, green_cold, green_warm = get_colours(warm_scans, cold_scans) #get colours for plotting

    w = -1 #initialize temp-specific counters
    c = -1

#Plot each scan, colour-coded by temperature, and mark defective chips
    for scan in scans:
        #sort chips and data by whether or not they're associated with a defect
        good_chips, good_data, bad_chips, bad_data = analyze_NO(NO_data, stream, scan)

        if scan in warm_scans:
            w = w + 1 #increment warm scan counter
            plt.scatter(good_chips, good_data, color=(red_warm, green_warm[w], blue_warm), label=f"Warm NO {w}", s=6) #plot good warm data

            if w == 0: #have exactly one defect label in legend
                label = "Defect Chip"
            else:
                label = None

            plt.scatter(bad_chips, bad_data, color=(red_warm, green_warm[w], blue_warm), s=20, marker="^", label=label) #plot bad warm data

        elif scan in cold_scans:
            c = c + 1 #increment cold scan counter
            plt.scatter(good_chips, good_data, color=(red_cold, green_cold[c], blue_cold), label=f"Cold NO {c}", s=6) #plot good cold data
            plt.scatter(bad_chips, bad_data, color=(red_cold, green_cold[c], blue_cold), s=20, marker="^") #plot bad cold data

        else:
            print(f"{YELLOW}Scan {scan} could not be labelled warm or cold!{RESET}")

    plt.xlabel("Chip Number")
    plt.ylabel("Occupancy")
    plt.xlim(-0.5, len(chips) - 0.5)
    plt.title(f"{component} Occupancy Throughout HBI, {stream} Stream")
    plt.grid(axis='x')
    if stream == 'Away':
        plt.legend(ncol=2, fontsize=5, bbox_to_anchor=(-0.1,1))

def average_occupancy_plots(NO_data, stream):
    '''
    Makes a plot of the mean noise occupancy throughout HBI for each chip and
    temperature extreme for a given stream, with the standard deviation as error bars.

    Arguments:
    NO_data - the contents of a pre-opened NO JSON file.
    stream  - Type = string, "Under" or "Away". The stream to be plotted.
    '''

    component            = get_component(NO_data) #hybrid serial number
    chips                = get_channels(NO_data)

    #Reformat data so each sublist corresponds to all data values for a given chip, at
    #the indicated temperature
    warm_data_by_chip = np.swapaxes(warm_data, 0, 1)
    cold_data_by_chip = np.swapaxes(cold_data, 0, 1)

    #Get mean and standard deviation per chip
    warm_means = [np.mean(chip) for chip in warm_data_by_chip]
    cold_means = [np.mean(chip) for chip in cold_data_by_chip]

    warm_stds = [np.std(chip) for chip in warm_data_by_chip]
    cold_stds = [np.std(chip) for chip in cold_data_by_chip]

    plt.errorbar(chips, warm_means, yerr=warm_stds, color='r', fmt='o', label="Mean Warm Occupancy", ms=3) #plot warm data
    plt.errorbar(chips, cold_means, yerr=cold_stds, color='b', fmt='o', label="Mean Cold Occupancy", ms=3) #plot cold data

    plt.xlabel("Chip Number")
    plt.ylabel("Occupancy")
    plt.xlim(-0.5, len(chips) - 0.5)
    plt.title(f"{component} Mean Occupancy, {stream} Stream")
    plt.grid(axis='x')
    if stream == 'Away':
        plt.legend(bbox_to_anchor=(-0.2, 1))

def analyze_NO(NO_data, stream, scan):
    '''
    Sort chips and their associated noise occupancy by whether or not the chip is
    assocaited with a defect for a given stream and scan.

    Arguments:
    NO_data - the contents of a pre-opened NO JSON file.
    stream  - Type = string, "Under" or "Away". Stream to be analyzed.
    scan    - Type = string. Name of specific NO test to be analyzed, as it appears in
              the NO JSON file.

    Returns:
    good_chips - Type = list of int. List of chips not associated with a defect.
    good_data  - Type = list of float. List of data associated with non-defective
                 chips.
    bad_chips  - Type = list of int. List of chips associated with a defect.
    bad_data   - Type = list of float. List of data associated with defective chips.
    '''

    defects = get_defects(NO_data) #list of all NO defects from HBI
    chips   = get_channels(NO_data)
    scans   = get_scans(NO_data) #list of all NO scans from HBI
    scan_number = get_index(scan, scans) #get scans index associated with scan

    data = NO_data["results"][f"occupancy_mean_{stream.lower()}"][scan_number]

    good_chips = [] #initialize
    good_data  = []
    bad_chips  = []
    bad_data   = []

#If a defect matches the stream and scan given, append the associated chip to
#bad_chips, and append that chip's data to bad_data
    for defect in defects:
        defect_stream = defect["properties"]["chip_bank"]
        defect_scan   = defect["properties"]["runNumber"]
        defect_chip   = defect["properties"]["chip_in_histo"]

        if defect_stream == stream.lower() and defect_scan == scan[:-7]:
            bad_chips.append(defect["properties"]["chip_in_histo"])
            bad_data.append(data[defect_chip])

    for chip in chips: #If the chip isn't bad, it's good
        if chip not in bad_chips:
            good_chips.append(chip)
            good_data.append(data[chip])

    return good_chips, good_data, bad_chips, bad_data

def get_data(NO_data, stream):
    '''
    For a given stream, retrieve all Noise Occupancy data taken throughout HBI, and
    sort it by temperature extreme.

    Arguments:
    NO_data - the contents of a pre-opened NO JSON file.
    stream  - Type = string, "Under" or "Away". The stream for which to retrieve data.

    Returns:
    warm_data - Type = list of list of float. Each sublist corresponds to the NO
                results from a single warm test.
    cold_data - Type = list of list of float. Each sublist corresponds to the NO
                results from a single cold test.
    '''

    scans                  = get_scans(NO_data) #list of all NO scans during HBI

    data = NO_data["results"][f"occupancy_mean_{stream.lower()}"] #data for stream

    warm_data = [] #initialize
    cold_data = []

#If a scan is warm, append its data to warm_data, if it's cold, append its data
#to cold_data
    for n,scan in enumerate(scans):

        if scan in warm_scans:
            warm_data.append(data[n])

        elif scan in cold_scans:
            cold_data.append(data[n])

        else:
            print(f"{YELLOW}Scan {scan} could not be labelled warm or cold!{RESET}")

    return warm_data, cold_data
