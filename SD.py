#import libraries
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.ticker import MultipleLocator
from common_functions import *

def make_plots(SD_data):
    '''
    Organizes the plot-making (which plots go where on the figure and such).

    Arguments:
    SD_data - the contents of a pre-opened STROBE_DELAY JSON file.

    Returns:
    plot - Type = matplotlib figure. The plot made.
    '''
    matplotlib.rcParams['font.size'] = 5
    plot = plt.figure(figsize=[8,4], dpi=50)

#Make a plot of all SD results throughout HBI for under stream
    plt.subplot(221)
    all_strobes_plot(SD_data, "Under")

#Make a plot of all SD results throughout HBI for away stream
    plt.subplot(222)
    all_strobes_plot(SD_data, "Away")

#Make a plot of average SD for under stream
    plt.subplot(223)
    average_strobes_plot(SD_data, "Under")

#Make a plot of average SD for away stream
    plt.subplot(224)
    average_strobes_plot(SD_data, "Away")

    plt.tight_layout()
    plt.close('all')

    return plot

def all_strobes_plot(SD_data, stream):
    '''
    Makes a plot of all Strobe Delay taken during thermal cycling, colour-coded by
    test temperature, for a given stream.

    Arguments:
    SD_data - the contents of a pre-opened STROBE_DELAY JSON file.
    stream  - Type = string, "Under" or "Away". The stream to be plotted.
    '''

    scans                  = get_scans(SD_data) #get a list of all SD scans
    component              = get_component(SD_data) #hybrid serial number
    chips                  = get_chips(SD_data) #list of chip number

    red_cold, red_warm, blue_cold, blue_warm, green_cold, green_warm = get_colours(warm_scans, cold_scans) #define plotting colours

    w = -1 #initialize temp-specific counters
    c = -1

#For each SD scan, sort chips by whether or not they're defective, and plot based on
#test temperature.
    for scan in scans:

#For this scan, sort  chips and their respective strobe delays based on whether
#or not that chip is labelled defective.
        strobe_info = analyze_strobes(SD_data, scan, stream)
        good_strobes, bad_strobes, good_chips, bad_chips = strobe_info

        if scan in warm_scans:
            w = w + 1 #increment warm scan counter
            plt.scatter(good_chips, good_strobes, color=(red_warm, green_warm[w], blue_warm), label=f"Warm SD {w}", s=6) #plot
            if w == 0:
#Ensure there is exactly one item in the legend displaying a bad strobe marker.
                label = "Bad Strobe"
            else:
                label = None

            plt.scatter(bad_chips, bad_strobes, color=(red_warm, green_warm[w], blue_warm), marker='^', label=label, s=20)

        elif scan in cold_scans:
            c = c + 1 #increment cold scan counter
            plt.scatter(good_chips, good_strobes, color=(red_cold, green_cold[c], blue_cold), label=f"Cold SD {c}", s=6) #plot
            plt.scatter(bad_chips, bad_strobes, color=(red_cold, green_cold[c], blue_cold), marker='^', s=20)

        else:
            print(f"{YELLOW}Scan {scan} can not be labelled as warm or cold!{RESET}")

    plt.xlabel("Chip Number")
    plt.ylabel("Strobe Delay")
    plt.title(f"{component} Strobe Delay, {stream} Stream")
    plt.xlim(-0.5, len(chips) - 0.5)
    plt.grid(axis='x')
    if stream == 'Away':
        plt.legend(ncol=2, fontsize=5, bbox_to_anchor=(-0.1, 1))

def average_strobes_plot(SD_data, stream):
    '''
    Makes a plot of the mean strobe delay value for each channel of a given stream, for
    each temperature extreme. Use the standard deviation as error bars.

    Arguments:
    SD_data - the contents of a pre-opened STROBE_DELAY JSON file.
    stream  - Type = string, "Under" or "Away". The stream to be plotted.
    '''

    chips = get_chips(SD_data) #get a list of chip numbers
    scans = get_scans(SD_data) #get a list of all SD scans
#Sort strobe delay values by temp for a given stream

#Reformat so each list corresponds to all SDs at a temperature for a single chip
    warm_strobes_by_chip = np.swapaxes(warm_strobes, 0, 1)
    cold_strobes_by_chip = np.swapaxes(cold_strobes, 0, 1)

#Get mean and standard deviation at each temperature extreme, by chip
    warm_means = [np.mean(chip) for chip in warm_strobes_by_chip]
    warm_stds  = [np.std(chip) for chip in warm_strobes_by_chip]

    cold_means = [np.mean(chip) for chip in cold_strobes_by_chip]
    cold_stds  = [np.std(chip) for chip in cold_strobes_by_chip]

    plt.errorbar(chips, warm_means, yerr=warm_stds, color='r', fmt='o', label="Mean Warm Strobe Delay", ms=3) #plot warm mean SD values
    plt.errorbar(chips, cold_means, yerr=cold_stds, color='b', fmt='o', label="Mean Cold Strobe Delay", ms=3) #plot cold mean SD values

    plt.xlabel("Chip Number")
    plt.ylabel("Strobe Delay")
    plt.title(f"Mean Strobe Delay, {stream} Stream")
    plt.xlim(-0.5, len(chips) - 0.5)
    plt.grid(axis='x')
    if stream == 'Away':
        plt.legend(bbox_to_anchor=(-0.15, 1))

def analyze_strobes(SD_data, scan, stream):
    '''
    For a given stream, sort chips and their corresponding strobe delay values based on
    whether or not the channel is labelled defective in a given scan.

    Arguments:
    SD_data - the contents of a pre-opened STROBE_DELAY JSON file.
    scan    - Type = string. The name of the scan to analyze, as it appears in the
              STROBE_DELAY JSON file.
    stream  - Type = string, "Under" or "Away". The stream to be analyzed.

    Returns:
    good_strobes - Type = list of int. List of strobe delay values not associated with
                   a defective chip.
    bad_strobes  - Type = list of int. List of strobe delay values associated with a
                   defective chip.
    good_chips   - Type = list of int. List of chips that are not associated with a
                   defect.
    bad_chips    - Type = list of int. List of chips that are associated with a defect
    '''

    defects      = SD_data["defects"] #get a list of all SD defects
    good_strobes = [] #intialize
    bad_strobes  = []
    good_chips   = []
    bad_chips    = []
    scans        = get_scans(SD_data) #get a list of all scans
    chips        = get_chips(SD_data) #get a list of chip numbers
    index        = get_index(scan, scans) #get the index of scans associated with scan

#For each defect, if it is associated with the given scan and stream, append the chip
#and corresponding SD value to bad_chips and bad_strobes.
    for defect in defects:
        defect_stream = defect["properties"]["chip_bank"]
        defect_chip   = defect["properties"]["chip_in_histo"]
        defect_scan   = defect["properties"]["runNumber"]

        if defect_stream == stream.lower() and defect_scan == scan[:-17]:
            bad_chips.append(defect_chip)
            bad_strobe = SD_data["results"][f"StrobeDelay_{stream.lower()}"][index][defect_chip]
            bad_strobes.append(bad_strobe)

#If the chip isn't bad, it must be good
    for chip in chips:
        if chip not in bad_chips:
            good_chips.append(chip)
            good_strobe = SD_data["results"][f"StrobeDelay_{stream.lower()}"][index][chip]
            good_strobes.append(good_strobe)

    return good_strobes, bad_strobes, good_chips, bad_chips


def get_strobes(SD_data, stream):
    '''
    Retrieve all strobe delay values for a given stream during thermal cycling, sorted
    by test temperature.

    Arguments:
    SD_data - the contents of a pre-opened STROBE_DELAY JSON file.
    stream  - Type = string, "Under" or "Away". The stream for which to retrieve data.

    Returns:
    warm_strobes - Type = list of list of int. Each sublist corresponds to a list of
                   strobe delay values for a single warm test.
    cold_strobes - Type = list of list of int. Each sublist corresponds to a list of
                   strobe delay values for a single cold test.
    '''

    scans                  = get_scans(SD_data) #get a list of all SD scans

    warm_strobes = [] #initialize
    cold_strobes = []

#For each scan, append results to temperature-appropriate list
    for scan_number,scan in enumerate(scans):

#Get strobe results for a scan, and reformat (file gives -1 for unused chip numbers).
        strobes0 = SD_data["results"][f"StrobeDelay_{stream.lower()}"][scan_number]
        strobes = [strobe for strobe in strobes0 if strobe != -1]

#Append results to warm_strobes or cold_strobes, depending on scan temperature.
        if scan in warm_scans:
            warm_strobes.append(strobes)

        elif scan in cold_scans:
            cold_strobes.append(strobes)

        else:
            print(f"{YELLOW}Scan {scan} could not be labelled as warm or cold!{RESET}")

    return warm_strobes, cold_strobes

def get_chips(SD_data):
    '''
    Makes a list of numbers, starting at 0 and incrementing by 1, where each number
    corresponds to a chip on the hybrid. The STROBE_DELAY JSON lists aa value for more
    chips than there are on the physical hybrid; for entries not associated with an
    actual chip, the value is just -1. To get a list of chips, therefore, get_chips()
    takes the length of a single test list for a single stream, without the -1s.

    Arguments:
    SD_data - the contents of a pre-opened STROBE_DELAY JSON file.

    Returns:
    chips - Type = list of int. List of chip numbers.
    '''

    strobes0 = SD_data["results"]["StrobeDelay_away"][0]
    strobes = [strobe for strobe in strobes0 if strobe != -1]
    chips = list(range(len(strobes)))

    return chips
