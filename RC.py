#import libraries
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.ticker import MultipleLocator
from common_functions import *

def make_plots(RC_data, noise_only):
    '''
    Organizes the making of plots, such as where each subplot goes on the figures.
    Used for both 3-Point Gain and 10-Point Gain scans.

    Arguments:
    RC_data - the contents of a pre-opened RESPONSE_CURVE JSON file.
    noise_only - Boolean. If True, only make noise plots, not gain or VT50.
    Returns:
    plots - Type = list of matplotlib figures. The plots made.
    '''
    matplotlib.rcParams['font.size'] = 5
    plots = [] #initialize

#Make a figure for noise plots
    noise_plot = plt.figure(figsize=[8,4], dpi=50)

#Make a plot of all under stream noise during HBI
    plt.subplot(221)
    all_RC_plots(RC_data, "Under", "innse")

#Make a plot of all away stream noise during HBI
    plt.subplot(222)
    all_RC_plots(RC_data, "Away", "innse")

#Make a plot of the average under stream noise
    plt.subplot(223)
    average_RC_plots(RC_data, "Under", "innse")

#Make a plot of the average away stream noise
    plt.subplot(224)
    average_RC_plots(RC_data, "Away", "innse")

    plt.tight_layout()
    plots.append(noise_plot)
    if not noise_only:
    #Make a figure for gain plots
        gain_plot = plt.figure(figsize=[8,4], dpi=50)

    #Make a plot of all under stream gain during HBI
        plt.subplot(221)
        all_RC_plots(RC_data, "Under", "gain")

    #Make a plot of all away stream gain during HBI
        plt.subplot(222)
        all_RC_plots(RC_data, "Away", "gain")

    #Make a plot of the average under stream gain
        plt.subplot(223)
        average_RC_plots(RC_data, "Under", "gain")

    #Make a plot of the average away stream gain
        plt.subplot(224)
        average_RC_plots(RC_data, "Away", "gain")

        plt.tight_layout()
        plots.append(gain_plot)
    #Make a figure for VT50 plots
        vt50_plot = plt.figure(figsize=[8,4], dpi=50)

    #Make a plot of all under stream VT50s during HBI
        plt.subplot(221)
        all_RC_plots(RC_data, "Under", "vt50")

    #Make a plot of all away stream VT50s during HBI
        plt.subplot(222)
        all_RC_plots(RC_data, "Away", "vt50")

    #Make a plot of the average under stream VT50s
        plt.subplot(223)
        average_RC_plots(RC_data, "Under", "vt50")

    #Make a plot of the average away stream VT50s
        plt.subplot(224)
        average_RC_plots(RC_data, "Away", "vt50")

        plt.tight_layout()
        plots.append(vt50_plot)

    plt.close('all')

    return plots

def all_RC_plots(RC_data, stream, field):
    '''
    Makes a plot of all test results for a given stream and given field (noise, gain,
    or VT50), colour-coded by test temperature.

    Arguments:
    RC_data - the contents of a pre-opened RESPONSE_CURVE JSON file.
    stream  - Type = string, "Under" or "Away". Stream to be plotted.
    field   - Type = string, "innse", "gain", or "vt50". Field to be plotted.
    '''

    component                 = get_component(RC_data) #hybrid serial number
    test_type                 = get_test_type(RC_data) #3PG or 10PG?
    channels                  = get_channels(RC_data)
    expected_noise, noise_max = get_noise_info(component, stream) #based on hybrid
    scans                     = get_scans(RC_data) #list of all RC scans
#Get results for given field and stream, for all scans
    data                      = get_data(RC_data, stream, field)

    red_cold, red_warm, blue_cold, blue_warm, green_cold, green_warm = get_colours(warm_scans, cold_scans)

    if field == "innse": #Plot expected noise and maximum noise for that hybrid
        plt.plot(channels, [expected_noise for channel in channels], color='k', linestyle='dashed', label=f"Expected Noise")
        plt.plot(channels, [noise_max for channel in channels], color='g', linestyle='dashed', label=f"Allowed Max")
        title = "Noise" #label it a noise plot

    elif field == "gain":
        title = "Gain" #label it a gain plot

    elif field == "vt50":
        title = "VT50" #label it a VT50 plot

    else:
        print(f"{YELLOW}Invalid field type {field}!{RESET}")

    w = -1 #initialize temperature-specfic counters
    c = -1

#For each scan, determine which channels are defective and sort data accordingly.
#Then, plot it based on temperature.
    for n,scan in enumerate(scans):

        good_channels, bad_channels, good_data, bad_data = analyze_RC(RC_data, stream, scan, field) #sorted channels and data for scan, based on defectiveness

        if scan in warm_scans:
            w = w + 1 #increment warm scan counter
            plt.scatter(good_channels, good_data, s=0.05, color=(red_warm, green_warm[w], blue_warm), label=f"Warm Test {w}") #plot non-defective warm data
            if w == 0:
                label = "Defect Channel" #have exactly one entry in legend for defects
            else:
                label = None
            plt.scatter(bad_channels, bad_data, s=5, color=(red_warm, green_warm[w], blue_warm), marker="^", label=label) #plot defective warm data

        elif scan in cold_scans:
            c = c + 1 #increment cold scan counter
            plt.scatter(good_channels, good_data, s=0.05, color=(red_cold, green_cold[c], blue_cold), label=f"Cold Test {c}") #plot non-defective cold data
            plt.scatter(bad_channels, bad_data, s=5, color=(red_cold, green_cold[c], blue_cold), marker="^") #plot defective cold data

        else:
            print(f"{YELLOW}Scan {scan} could not be labelled as warm or cold!{RESET}")

    plt.xlabel("Channel Number")
    plt.ylabel(f"{title}")
    plt.xlim(0,len(channels))
    plt.title(f"{component} {title}, {stream} Stream, {test_type}")
    if stream == 'Away':
        legend = plt.legend(ncol=2, markerscale=10, fontsize=5, bbox_to_anchor=(-0.17, 1))
        if field == "innse":
            legend.legend_handles[3]._sizes = [50]
        else:
            legend.legend_handles[1]._sizes = [50]
        legend
    plt.grid(axis='x')
    plt.gca().xaxis.set_major_locator(MultipleLocator(128))


def average_RC_plots(RC_data, stream, field):
    '''
    Makes a plot of the mean value for a given field (noise, gain, or VT50) for each
    channel in a given stream, for each temperature extreme. Uses the standard
    deviation for the channel as an error bar.

    Arguments:
    RC_data - the contents of a pre-opened RESPONSE_CURVE JSON file.
    stream  - Type = string, "Under" or "Away". Stream to be plotted.
    field   - Type = string, "innse", "gain", or "vt50". Field to be plotted.
    '''

    scans                     = get_scans(RC_data) #get all RC scans
#Get all data for stream and field from HBI
    data                      = get_data(RC_data, stream, field)
    channels                  = get_channels(RC_data)
    component                 = get_component(RC_data) #hybrid serial number
    warm_data = [] #initialize
    cold_data = []

#If plotting noise, also plot the expected and maximum noise for the hybrid type and
#stream.
    if field == "innse":
        expected_noise, noise_max             = get_noise_info(component, stream)
        expected_noise_under, noise_max_under = get_noise_info(component, "Under")
        expected_noise_away, noise_max_away   = get_noise_info(component, "Away")

        plt.plot(channels, [expected_noise for channel in channels], color='k', linestyle='dashed', label=f"Under Expected Warm Noise = {expected_noise_under} ENC\nAway Expected Warm Noise = {expected_noise_away} ENC") #plot expected noise
        plt.plot(channels, [noise_max for channel in channels], color='g', linestyle='dashed', label=f"Under Maximum Allowed Noise = {noise_max_under} ENC\nAway Maximum Allowed Noise = {noise_max_away} ENC") #plot maximum noise
        title = "Noise" #label it a noise plot

    elif field == "gain":
        title = "Gain" #label it a gain plot

    elif field == "vt50":
        title = "VT50" #label it a vt50 plot

    else:
        print(f"{YELLOW}Invalid field type {field}{RESET}!")

#If a scan is warm, append it's corresponding data to warm_data. Same for cold.
    for n, scan in enumerate(scans):

        if scan in warm_scans:
            warm_data.append(make_one_list(data[n]))

        elif scan in cold_scans:
            cold_data.append(make_one_list(data[n]))

        else:
            print(f"{YELLOW}Scan {scan} could not be labelled as warm or cold!{RESET}")

#Reformat so each list corresponds to all warm or cold data for a single channel
    warm_data_by_channel = np.swapaxes(warm_data, 0, 1)
    cold_data_by_channel = np.swapaxes(cold_data, 0, 1)
#Calculate mean and standard deviation per channel by temperature
    warm_means            = [np.mean(channel) for channel in warm_data_by_channel]
    cold_means            = [np.mean(channel) for channel in cold_data_by_channel]
    warm_stds             = [np.std(channel) for channel in warm_data_by_channel]
    cold_stds             = [np.std(channel) for channel in cold_data_by_channel]

    plt.errorbar(channels, warm_means, yerr=warm_stds, ms=0.7, elinewidth=0.3, color='r', fmt='o', label=f"Mean Warm {title}") #plot warm data
    plt.errorbar(channels, cold_means, yerr=cold_stds, ms=0.7, elinewidth=0.3, color='b', fmt='o', label=f"Mean Cold {title}") #plot cold data
    plt.xlabel("Channel Number")
    plt.ylabel(f"{title}")
    plt.title(f"{component} Mean {title}, {stream} Stream")
    plt.xlim(0, len(channels))
    if stream == 'Away' and field == 'innse':
        plt.legend(markerscale=4, bbox_to_anchor=(-0.18,1))
    elif stream == 'Away':
        plt.legend(markerscale=4, bbox_to_anchor=(-0.33, 1))
    plt.grid(axis='x')
    plt.gca().xaxis.set_major_locator(MultipleLocator(128))

def get_noise_info(component, stream):
    '''
    Retrieve the expected and maximum acceptable noise at 20C for the given hybrid
    type and stream.

    Arguments:
    component - Type = string. The hybrid serial number.
    stream    - Type = string, "Under" or "Away". The stream to retrieve values for.

    Returns:
    expected_noise - Type = int. Expected noise for given hybrid type and stream.
    noise_max      - Type = int. Maximum acceptable noise for give hybrid type and
                     stream.
    '''

#R0
    if "H0" in component and stream == "Under" and "H4" not in component:
        expected_noise = 589
        noise_max      = 798
    elif "H0" in component and stream == "Away" and "H4" not in component:
        expected_noise = 527
        noise_max      = 785

    elif "H1" in component and stream == "Under" and "H4" not in component:
        expected_noise = 625
        noise_max      = 815
    elif "H1" in component and stream == "Away" and "H4" not in component:
        expected_noise = 598
        noise_max      = 876

#R1
    elif "H2" in component and stream == "Under":
        expected_noise = 613
        noise_max      = 916
    elif "H2" in component and stream == "Away":
        expected_noise = 524
        noise_max      = 908

    elif "H3" in component and stream == "Under":
        expected_noise = 595
        noise_max      = 963
    elif "H3" in component and stream == "Away":
        expected_noise = 510
        noise_max      = 996

#R2
    elif "H4" in component and stream == "Under":
        expected_noise = 650
        noise_max      = 999
    elif "H4" in component and stream == "Away":
        expected_noise = 595
        noise_max      = 1035

#R3
    elif "H5" in component and stream == "Under":
        expected_noise = 672
        noise_max      = 1075
    elif "H5" in component and stream == "Away":
        expected_noise = 571
        noise_max      = 1057

    elif "H6" in component and stream == "Under":
        expected_noise = 608
        noise_max      = 1075
    elif "H6" in component and stream == "Away":
        expected_noise = 571
        noise_max      = 1057

    elif "H7" in component and stream == "Under":
        expected_noise = 669
        noise_max      = 1092
    elif "H7" in component and stream == "Away":
        expected_noise = 564
        noise_max      = 1043

    elif "H8" in component and stream == "Under":
        expected_noise = 605
        noise_max      = 1092
    elif "H8" in component and stream == "Away":
        expected_noise = 564
        noise_max      = 1147

#R4
    elif "H9" in component and stream == "Under":
        expected_noise = 862
        noise_max      = 1154
    elif "H9" in component and stream == "Away":
        expected_noise = 792
        noise_max      = 1172

    elif "HA" in component and stream == "Under":
        expected_noise = 842
        noise_max      = 1154
    elif "HA" in component and stream == "Away":
        expected_noise = 792
        noise_max      = 1172

#R5
    elif "HB" in component and stream == "Under":
        expected_noise = 917
        noise_max      = 1229
    elif "HB" in component and stream == "Away":
        expected_noise = 668
        noise_max      = 1233

    elif "HC" in component and stream == "Under":
        expected_noise = 896
        noise_max      = 1229
    elif "HC" in component and stream == "Away":
        expected_noise = 668
        noise_max      = 1233

#LS
    elif "HX2" in component and stream == "Under":
        expected_noise = 824
        noise_max      = 1243
    elif "HX2" in component and stream == "Away":
        expected_noise = 779
        noise_max      = 1243

#SS
    elif "HX" in component and stream == "Under":
        expected_noise = 610
        noise_max      = 918
    elif "HX" in component and stream == "Away":
        expected_noise = 577
        noise_max      = 918

    elif "HY" in component and stream == "Under":
        expected_noise = 610
        noise_max      = 918
    elif "HY" in component and stream == "Away":
        expected_noise = 577
        noise_max      = 918

    return expected_noise, noise_max

def get_data(RC_data, stream, field):
    '''
    Retrieve all data for a given field (noise, gain, or VT50) and stream.

    Arguments:
    RC_data - the contents of a pre-opened RESPONSE_CURVE JSON file.
    stream  - Type = string, "Under" or "Away". Stream to get data for.
    field   - Type = string, "innse", "gain", or "vt50". Field to get data for.

    Returns:
    data - Type = list of list of float. Each sublist corresponds to the results from
           a single test.
    '''

    data = RC_data["results"][f"{field}_{stream.lower()}"] #get the data

    return data

def analyze_RC(RC_data, stream, scan, field):
    '''
    Determines which channels are defective in a given RC test, and their associated
    field value (noise, gain, or VT50). Then sorts channels and associated values into
    good_channels/good_data and bad_channels/bad_data depending on whether or not the
    channel is defective.

    Arguments:
    RC_data - the contents of a pre-opened RESPONSE_CURVE JSON file.
    stream  - Type = string, "Under" or "Away". The stream to be analyzed.
    scan    - Type = string. The name of the specific test to be analyzed, as it
              appears in the RESPONSE_CURVE JSON file.
    field   - Type = string, "innse", "gain", or "vt50". The field to be analyzed.

    Returns:
    good_channels - Type = list of int. A list of channels not associated with a
                    defect.
    bad_channels  - Type = list of int. A list of channels associated with a defect.
    good_data     - Type = list of float. A list of data not associated with defective
                    channels.
    bad_data      - Type = list of float. A list of data associated with defective
                    channels.
    '''

    defects       = get_defects(RC_data)
    data          = get_data(RC_data, stream, field)
    channels      = get_channels(RC_data)
    bad_channels  = [] #initialize
    good_channels = []
    good_data     = []
    bad_data      = []
    scans         = get_scans(RC_data) #list of all RC scans during HBI

#Determine the ordinal number associated with the scan of interest (0 is first, etc.)
    for n,single_scan in enumerate(scans):
        if single_scan == scan:
            scan_number = n

    scan_data = make_one_list(data[scan_number]) #minor reformatting

#Figure out which channels are defective, and their assiociated data values
    for defect in defects:

        if defect["properties"]["chip_bank"] == stream.lower() and defect["properties"]["runNumber"] == scan[:-19]: #does the defect match stream and scan of interest?

            try: #append bad channels and associated data to respective list
                #this won't work if >1 channel is affected by the defect
                channel = defect["properties"]["channel"]
                bad_channels.append(channel)
                bad_data.append(scan_data[channel])
            except:
                pass
            try: #for when >1 channel is affected by the defect
                first_channel = defect["properties"]["channel_from"]
                last_channel  = defect["properties"]["channel_to"]
                defect_channels = np.linspace(first_channel, last_channel, last_channel - first_channel + 1) #make a list of affected by the defect
                for channel in defect_channels:
                    channel = int(channel) #np.linspace produces floats
                    bad_channels.append(channel)
                    bad_data.append(scan_data[channel])
            except:
                 if "channel_from" not in defect["properties"] and "channel" not in defect["properties"]:
                    defect_chip = defect["properties"]["chip_in_histo"]
                    first_channel = defect_chip * 128
                    last_channel = (defect_chip + 1) * 128 - 1
                    defect_channels = np.linspace(first_channel, last_channel, last_channel - first_channel + 1)
                    for channel in defect_channels:
                        channel = int(channel)
                        bad_channels.append(channel)
                        bad_data.append(scan_data[channel])

    for channel in channels: #if it isn't a bad channel, call it a good channel
        if channel not in bad_channels:
            good_channels.append(channel)
            good_data.append(scan_data[channel])

    return good_channels, bad_channels, good_data, bad_data
