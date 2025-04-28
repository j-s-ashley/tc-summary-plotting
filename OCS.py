#import libraries
import numpy as np
import matplotlib.pyplot as plt
from common_functions import *
from matplotlib.ticker import MultipleLocator
import matplotlib


def make_plots(OCS_data, TC_data):
    '''
    Organizes the making of Open Channel Search plots, such as where the subplots go
    on the figure.

    Arguments:
    OCS_data - the contents of a pre-opened OPEN_CHANNEL_SEARCH JSON file.
    TC_data  - the contents of a pre-opened ColdJigRun JSON file.

    Returns:
    plot - Type = matplotlib figure. The plot made.
    '''

    plot = plt.figure(figsize=[15,7])

#Make plot for all OCS data from TC for the under stream
    plt.subplot(221)
    all_OCS_plot(OCS_data, TC_data, "Under")

#Make plot for all OCS data from TC for the away stream
    plt.subplot(222)
    all_OCS_plot(OCS_data, TC_data, "Away")

#Make a histogram for all OCS data from TC for the under stream
    plt.subplot(223)
    OCS_histo(OCS_data, TC_data, "Under")

#Make a histogram for all OCS data from TC for the away stream
    plt.subplot(224)
    OCS_histo(OCS_data, TC_data, "Away")

    plt.tight_layout()
    plt.close('all')

    return plot

def all_OCS_plot(OCS_data, TC_data, stream):
    '''
    Make a plot of the noise at -10V taken during the Open Channel Search, for all OCS
    tests during thermal cycling, for a given stream. Note: this function assumes all
    OCS tests are warm, as is, at the time of writing this (02/04/2025), the standard
    TC Quality Control procedure.

    Arguments:
    OCS_data - the contents of a pre-opened OPEN_CHANNEL_SEARCH JSON file.
    TC_data  - the contents of a pre-opened ColdJigRun JSON file.
    stream   - Type = string, "Under" or "Away". The stream to be plotted.
    '''

    component              = get_component(OCS_data) #hybrid serial number
    channels               = get_channels(OCS_data)
    scans                  = get_scans(OCS_data) #list of all OCS scans from TC
    warm_scans, cold_scans = sort_scan_temp(scans, TC_data) #sort scans by temp

    red_cold, red_warm, blue_cold, blue_warm, green_cold, green_warm = get_colours(warm_scans, cold_scans)

    w = -1 #warm-scan-specific counter

#For each OCS scan, sort channels and respective data into good and bad based on
#whether or not they are associated with a defect, and plot.
    for scan in scans:

        good_channels, good_data, bad_channels, bad_data = analyze_OCS(OCS_data, scan, stream)

        if scan in warm_scans:
            w = w + 1 #increment warm scan counter
            plt.scatter(good_channels, good_data, s=5, color=(red_warm, green_warm[w], blue_warm), label=f"Warm OCS {w}") #plot good data
            if w == 0: #have exactly one defect label in legend
                label = "Defect Channel"
            else:
                label = None

            plt.scatter(bad_channels, bad_data, s=50, marker="^", color=(red_warm, green_warm[w], blue_warm), label=label) #plot bad data

        else:
            print(f"{YELLOW}Scan {scan} could not be labelled warm!{RESET}")

    plt.xlabel("Channel Number")
    plt.xlim(0, len(channels))
    plt.ylim(0,)
    plt.ylabel("Noise")
    plt.title(f"{component} Noise at -10V, {stream} Stream")
    plt.grid(axis='x')
    plt.gca().xaxis.set_major_locator(MultipleLocator(128))
    if stream == 'Away':
        plt.legend(markerscale=2, bbox_to_anchor=(-0.08,1))

def OCS_histo(OCS_data, TC_data, stream):
    '''
    Makes a histogram of the number of open channels found in a given stream, for every
    Open Channel Search run during TC. Binned by chip.

    Arguments:
    OCS_data - the contents of a pre-opened OPEN_CHANNEL_SEARCH JSON file.
    TC_data  - the contents of a pre-opened ColdJigRun JSON file.
    stream   - Type = string, "Under" or "Away". The stream to be plotted.
    '''

    component = get_component(OCS_data) #hybrid serial number
    defects   = get_defects(OCS_data) #list of all OCS defects found in TC
    channels  = get_channels(OCS_data)
    scans     = get_scans(OCS_data) #list of all OCS scans from TC

    all_defect_scans = [] #initialize

#For every defect append the associated scan to all_defect_scans
    for defect in defects:
        defect_stream = defect["properties"]["chip_bank"]
        if defect["name"] == "Open channel" and stream.lower() == defect_stream:
            defect_scan = defect["properties"]["runNumber"]
            all_defect_scans.append(defect_scan)

#Create a list, defect_scans, which has all scans with defects, without duplicates
    defect_scans = [] #initialize
    for scan in all_defect_scans:
        if scan not in defect_scans:
            defect_scans.append(scan)

#Make a list of defective chips, with duplicates
    all_defect_chips = [] #initialize

    for scan in scans:
        defect_chips = []

        for defect in defects:
            defect_scan = defect["properties"]["runNumber"]
            defect_stream = defect["properties"]["chip_bank"]

            #If the defect matches desired scan and stream, append chip
            if defect_scan == scan[:-24] and defect_stream == stream.lower():
                defect_chip = defect["properties"]["chip_in_histo"]
                defect_chips.append(defect_chip)

        all_defect_chips.append(defect_chips)

    red_cold, red_warm, blue_cold, blue_warm, green_cold, green_warm = get_colours(scans, [])
    hist_range = (0, int(len(channels)/128)) #range of histogram
    bins  = (int(len(channels)/128)) #bin by chip (128 channels per ABC)
    plt.hist([chips for chips in all_defect_chips], histtype='bar', range=hist_range, bins=bins, color=[(red_warm, green_warm[w], blue_warm) for w in range(len(scans))], stacked=False, label=[f"Warm OCS {n}" for n,s in enumerate(scans)]) #plot
    plt.title(f"{component} Open Channels by Chip, {stream} Stream")
    plt.xlabel("Chip")
    plt.xlim(0, int(len(channels)/128))
    plt.grid(axis='x')
    plt.gca().xaxis.set_major_locator(MultipleLocator(1))
    plt.ylabel("Number of Open Channels")
    if stream == 'Away':
        plt.legend(bbox_to_anchor=(-0.1,1))

def analyze_OCS(OCS_data, scan, stream):
    '''
    Sort channels and their associated data by whether or not they're associated with
    a defect, for a given scan and stream.

    Arguments:
    OCS_data - the contents of a pre-opened OPEN_CHANNEL_SEARCH JSON file.
    scan     - Type = string. The name of the OCS scan to be analyzed, as it appears
               in the OPEN_CHANNEL_SEARCH JSON file.
    stream   - Type = string, "Under" or "Away". The stream to be analyzed.

    Returns:
    good_channels - Type = list of int. List of channels not associated with a defect.
    good_data     - Type = list of float. List of data associated with non-defective
                    channels.
    bad_channels  - Type = list of int. List of channels associated with a defect.
    bad_data      - Type = list of float. List of data associated with defective
                    channels.
    '''

    defects  = get_defects(OCS_data) #list of all OCS defects during TC
    channels = get_channels(OCS_data)
    scans    = get_scans(OCS_data) #list of all OCS scans from TC

#Determine the ordinal number associated with the scan of interest (0 is first, etc.)
    for n,single_scan in enumerate(scans):
        if single_scan == scan:
            scan_number = n

    data          = OCS_data["results"][f"noise_{stream.lower()}"][scan_number]
    good_channels = [] #initialize
    good_data     = []
    bad_channels  = []
    bad_data      = []

#If defect matches scan and stream of interest, append channel and data to lists.
    for defect in defects:
        defect_stream = defect["properties"]["chip_bank"]
        defect_scan   = defect["properties"]["runNumber"]
        defect_channel = defect["properties"]["channel"]

        if defect_stream == stream.lower() and defect_scan == scan[:-24]:
            bad_channels.append(defect_channel)
            bad_data.append(data[defect_channel])

    for channel in channels: #if the channel isn't bad, it's good
        if channel not in bad_channels:
            good_channels.append(channel)
            good_data.append(data[channel])

    return good_channels, good_data, bad_channels, bad_data


def get_noise(OCS_data, TC_data, stream):
    '''
    Retrieve all noise values from all Open Channel Search scans run during TC. As in
    many functions in this script, this one also assumes all Open Channel Searches are
    done warm, but could easily be adapted if current QC procedures change.

    Arguments:
    OCS_data - the contents of a pre-opened OPEN_CHANNEL_SEARCH JSON file.
    TC_data  - the contents of a pre-opened ColdJigRun JSON file.
    stream   - Type = string, "Under" or "Away". Stream for which to retrieve data.

    Returns:
    warm_noise - Type = list of list of float. Each sublist corresponds to the noise
                 results from a single Open Channel Search.
    '''

    scans                  = get_scans(OCS_data)
    warm_scans, cold_scans = sort_scan_temp(scans, TC_data)
    data                   = OCS_data["results"][f"noise_{stream.lower()}"]

    warm_noise = []

    for n,scan in enumerate(scans):

        if scan in warm_scans:
            warm_noise.append(data[n])

        else:
            print(f"{YELLOW}Scan {scan} could not be labelled as warm!{RESET}")

    return warm_noise
