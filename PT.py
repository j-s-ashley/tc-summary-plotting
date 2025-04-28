#import libraries

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.ticker import MultipleLocator
from common_functions import *

def make_plots(PT_data, TC_data):
    '''
    Responsible for organization of plotting (which plot goes where on the figure).

    Arguments:
    PT_data - the contents of a pre-opened PEDESTAL_TRIM JSON file.
    TC_data - the contents of a pre-opened ColdJigRun JSON file.

    Returns:
    plot - Type = matplotlib figure. The plot made.
    '''

    plot = plt.figure(figsize=[15,7])
    plt.subplot(221)
    all_scans_plot(PT_data, TC_data, "Under") #make plot of all PTs for away stream

    plt.subplot(222)
    all_scans_plot(PT_data, TC_data, "Away") #make plot of all PTs for under stream

    plt.subplot(223)
    average_trim_plot(PT_data, TC_data, "Under") #make plot of average PTs for away stream

    plt.subplot(224)
    average_trim_plot(PT_data, TC_data, "Away") #make plot of average PTs for under stream

    plt.tight_layout()
    plt.close('all')

    return plot

def all_scans_plot(PT_data, TC_data, stream):
    '''
    Makes a plot of all pedestal trim values, colour-coded by test temperature, for
    a given stream.

    Arguments:
    PT_data - the contents of a pre-opened PEDESTAL_TRIM JSON file.
    TC_data - the contents of a pre-opened ColdJigRun JSON file.
    stream  - Type = string, "Under" or "Away". The stream to be plotted.
    '''

    component = get_component(PT_data)
    scans = get_scans(PT_data)
    warm_scans, cold_scans = sort_scan_temp(scans, TC_data) #sort scan number by temp
    channels = get_channels(PT_data) #get a list of channel numbers
    red_cold, red_warm, blue_cold, blue_warm, green_cold, green_warm = get_colours(warm_scans, cold_scans)
#Plot

    w = -1 #initialize
    c = -1
    for scan in scans:
        good_trims, good_channels, bad_trims, bad_channels = analyze_trims(PT_data, TC_data, scan, stream) #sort trims and their channels by whether or not they are marked defective for a given scan.

        if scan in warm_scans:
            w = w + 1 #increment number of warm scans
            plt.scatter(good_channels, good_trims, color=(red_warm, green_warm[w], blue_warm), label=f"Warm PT {w}", s=2) #plot good warm channels

            if w == 0:
                name = "Bad Trim" #put exactly one 'Bad Trim' indicator in legend
            else:
                name = None

            plt.scatter(bad_channels, bad_trims, color=(red_warm, green_warm[w], blue_warm), label=name, s=20, marker='^') #plot defective warm channels


        elif scan in cold_scans:
            c = c + 1 #increment number of cold scans
            plt.scatter(good_channels, good_trims, color=(red_cold, green_cold[c], blue_cold), label=f"Cold PT {c}", s=2) #plot good cold channels
            plt.scatter(bad_channels, bad_trims, color=(red_cold, green_cold[c], blue_cold), s=20, marker="^") #plot defective cold channels

        else:
        #If the scan isn't being flagged by temperature correctly, inform user and
        #continue. This should not happen, but may if file structure is changed.
            print(f"{YELLOW}PT Scan {scan} could not be flagged as warm or cold!{RESET}")



    plt.xlabel("Channel Number")
    plt.ylabel("Trim Value")
    plt.title(f"{component} Pedestal Trim Results Throughout TC, {stream} Stream")
    plt.xlim(0, len(channels))
    plt.grid(axis='x')
    if stream == 'Away':
        plt.legend(ncol=2, markerscale=3, fontsize=10, framealpha=0.6, bbox_to_anchor=(-0.1, 1))
    plt.gca().xaxis.set_major_locator(MultipleLocator(128))

def average_trim_plot(PT_data, TC_data, stream):
    '''
    Makes a plot displaying the mean pedestal trim value for each temperature extrema
    of each channel, for the specified stream. Also includes the standard deviation as
    error bars.

    Arguments:
    PT_data - the contents of a pre-opened PEDESTAL_TRIM JSON file.
    TC_data - the contents of a pre-opened ColdJigRun JSON file.
    stream  - Type = string, "Under" or "Away". The stream to be plotted.
    '''

    warm_trims, cold_trims = get_trims(PT_data, TC_data, stream) #sort trims by temp
    channels               = get_channels(PT_data)

#Reformat trims so each sublist corresponds to all warm PTs in TC for a single channel
    warm_trims_by_channel = np.swapaxes(warm_trims, 0, 1)

#Calculate mean and standard deviation per channel
    warm_means = [np.mean(channel) for channel in warm_trims_by_channel]
    warm_stds  = [np.std(channel) for channel in warm_trims_by_channel]

#Reformat trims so each sublist corresponds to all cold PTs in TC for a single channel
    cold_trims_by_channel = np.swapaxes(cold_trims, 0, 1)

#Calculate mean and standard deviation per channel
    cold_means = [np.mean(channel) for channel in cold_trims_by_channel]
    cold_stds  = [np.std(channel) for channel in cold_trims_by_channel]

#Plot
    plt.errorbar(channels, warm_means, yerr=warm_stds, color='r', ms=2, elinewidth=0.5, fmt="o", label="Mean Warm Trims")
    plt.errorbar(channels, cold_means, yerr=cold_stds, color='b', ms=2, elinewidth=0.5, fmt="o", label="Mean Cold Trims")

    plt.xlabel("Channel Number")
    plt.ylabel("Trim Value")
    plt.title(f"Mean Trim Value Throughout TC, {stream} Stream")
    plt.xlim(0, len(channels))
    plt.grid(axis='x')
    plt.gca().xaxis.set_major_locator(MultipleLocator(128))
    if stream == 'Away':
        plt.legend(markerscale=3, bbox_to_anchor=(-0.2, 1))


def analyze_trims(PT_data, TC_data, scan, stream):
    '''
    For a given PT test and stream, sorts the channels and their respective trim values
    into "good" (not a defective channel) and "bad" (defective channel).

    Arguments:
    PT_data - the contents of a pre-opened PEDESTAL_TRIM JSON file.
    TC_data - the contents of a pre-opened ColdJigRun JSON file.
    scan    - Type = string. The name of the test as it appears in the PEDESTAL_TRIM
              JSON.
    stream  - Type = string, "Under" or "Away". The stream to analyze trims for.

    Returns:
    good_trims    - Type = list of int. Trims not associated with defective channels.
    good_channels - Type = list of int. Channels not associated with a defect.
    bad_trims     - Type = list of int. Trims associated with defective channels.
    bad_channels  - Type = list of int. Channels associated with a defect.
    '''

#Retrieve desired data based on stream
    if stream == "Away":
        results = PT_data["results"]["trim_away"]

    elif stream == "Under":
        results = PT_data["results"]["trim_under"]

    else:
        print(f"{YELLOW}Invalid stream type {stream} given! Must be 'Away' or 'Under'.{RESET}")

    scans = get_scans(PT_data) #get all PT scans
    index = get_index(scan, scans) #get the scans index corresponding to scan

#results is list of list, where index corresponds to test number.
    trims    = results[index] #get results for specific scan
    defects  = get_defects(PT_data) #get a list of all PT defects during TC
    channels = get_channels(PT_data)

    good_channels = [] #initialize
    bad_channels  = []
    good_trims    = []
    bad_trims     = []

#Determine which defects were for this specific stream and scan
    for defect in defects:

        defect_stream  = defect["properties"]["chip_bank"]
        defect_scan    = defect["properties"]["runNumber"]
        defect_channel = defect["properties"]["channel"]

#If defect is for given stream and scan, append the defect channel and corresponding
#trim value to bad_channels and bad_trims, respectively.
        if defect_stream == stream.lower() and defect_scan == scan[:-18]:
            bad_channels.append(defect_channel)
            bad_trims.append(trims[defect_channel])

#If a channel isn't a bad channel, it must be a good channel.
    for channel in channels:
        if channel not in bad_channels:
            good_channels.append(channel)
            good_trims.append(trims[channel])

    return good_trims, good_channels, bad_trims, bad_channels



def get_trims(PT_data, TC_data, stream):
    '''
    For a given stream, retrieve all trims throughout TC, sorted by test temperature.

    Arguments:
    PT_data - the contents of a pre-opened PEDESTAL_TRIM JSON file
    TC_data - the contents of a pre-opened ColdJigRun file
    stream  - Type = string, "Under" or "Away". The stream to get trims for.

    Returns:
    warm_trims - Type = list of list of int. Each sublist corresponds to the trims of
                 a single warm test, for the given stream.
    cold_trims - Type = list of list of int. Each sublist corresponds to the trims of
                 a single cold test, for the given stream.
    '''

#Get data based on stream
    if stream == "Away":
        results = PT_data["results"]["trim_away"]

    elif stream == "Under":
        results = PT_data["results"]["trim_under"]

    else:
        print(f"{YELLOW}Invalid stream type {stream} given! Must be 'Away' or 'Under'.{RESET}")

    scans                  = get_scans(PT_data) #retrieve all PT scans
    warm_scans, cold_scans = sort_scan_temp(scans, TC_data) #sort scans by temp

    warm_trims = [] #initialize
    cold_trims = []

#If a scan is done warm, append the corresponding list of trims to warm_trims.
#Do the same for cold.
    for n,scan in enumerate(scans):
        if scan in warm_scans:
            warm_trims.append(results[n])
        elif scan in cold_scans:
            cold_trims.append(results[n])
        else:
            print(f"{YELLOW}Scan {scan} could not be identified as warm or cold!{RESET}")

    return warm_trims, cold_trims
