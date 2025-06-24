import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import json
from common_functions import *
import TC
import SD

def make_plots(files, TC_data):
    '''
    Governs the making of defect histograms and bar plots.

    Arguments:
    files - Type = list of string. The paths to the merged files.

    Returns:
    defects_plot - Type = matplotlib plot. The finished histograms/bar plots. 
    '''

    matplotlib.rcParams['font.size'] = 5
    for file in files:

        data = retrieve_data(file)
        test_type = get_test_type(data)

        if test_type == "PT": #sort by test type
            PT_data = data
        elif test_type == "SD":
            SD_data = data
        elif test_type == "3PG":
            TPG_data = data
        elif test_type == "10PG":
            RC_data = data
        elif test_type == "NO":
            NO_data = data
        elif test_type == "OCS":
            OCS_data = data

    SD_defects    = get_defects(SD_data) #get all the defects for each test type
    PT_defects    = get_defects(PT_data)
    TPG_defects   = get_defects(TPG_data)
    RC_defects    = get_defects(RC_data)
    NO_defects    = get_defects(NO_data)
    OCS_defects   = get_defects(OCS_data)

    defects_plot = plt.figure(figsize=[8,4], dpi=50) #make the figure
    chips        = SD.get_chips(SD_data) #get the chips (using the SD)
    component    = get_component(PT_data) #hybrid serial number

    plt.subplot(221)
    defects_by_chip(PT_defects, SD_defects, TPG_defects, RC_defects, NO_defects, OCS_defects, "Under", chips, component)

    plt.subplot(222)
    defects_by_chip(PT_defects, SD_defects, TPG_defects, RC_defects, NO_defects, OCS_defects, "Away", chips, component)

    plt.subplot(223)
    defects_by_type(PT_defects, SD_defects, TPG_defects, RC_defects, NO_defects, OCS_defects, "Under", component)

    plt.subplot(224)
    defects_by_type(PT_defects, SD_defects, TPG_defects, RC_defects, NO_defects, OCS_defects, "Away", component)

    plt.tight_layout()

    defect_progression_plot = plt.figure(figsize=[8,4], dpi=50)
    defects_by_test(TC_data, PT_defects, SD_defects, TPG_defects, RC_defects, NO_defects, component)

    return defects_plot, defect_progression_plot

def defects_by_chip(PT_defects, SD_defects, TPG_defects, RC_defects, NO_defects, OCS_defects, stream, chips, component):
    '''
    Makes a histogram of the number of defects by chip, colour-coded by the test type
    in which the defect occured.

    Arguments:
    PT_defects  - Type = list of dict. A list of all defects that occured during the
                  Pedestal Trim.
    SD_defects  - As above, for the Strobe Delay.
    TPG_defects - As above, for the Three-Point Gain.
    RC_defects  - As above, for the Ten-Point Gain.
    NO_defects  - As above, for the Noise Occupancy.
    OCS_defects - As above, for the Open Channel Search.
    stream      - Type = string, "Under" or "Away". The stream to be plotted.
    chips       - Type = list of int. The chip numbers to be plotted.
    component   - Type = string. The hybrid serial number.
    '''

    PT_defects_by_chip   = get_defect_chips(PT_defects, stream) #list of defects' chips
    SD_defects_by_chip   = get_defect_chips(SD_defects, stream)
    TPG_defects_by_chip  = get_defect_chips(TPG_defects, stream)
    RC_defects_by_chip = get_defect_chips(RC_defects, stream)
    NO_defects_by_chip   = get_defect_chips(NO_defects, stream)
    OCS_defects_by_chip  = get_defect_chips(OCS_defects, stream)

    hist_range = (0, len(chips)) #set the range for the histogram
    bins = len(chips) #one bin per chip
    plt.hist([PT_defects_by_chip, SD_defects_by_chip, TPG_defects_by_chip, RC_defects_by_chip, NO_defects_by_chip, OCS_defects_by_chip], histtype='bar', range=hist_range, bins=bins, color=['red', 'orange', 'yellow', 'green', 'blue', 'purple'], stacked="true", label=['Pedestal Trim', 'Strobe Delay', '3-Point Gain', '10-Point Gain', 'Noise Occupancy', 'Open Channel Search'])
    plt.title(f"{component} Defects by Chip, {stream} Stream")
    plt.xlabel("Chip")
    plt.ylabel("Number of Defects")
    plt.xlim(0, len(chips))
    if stream == 'Away':
        plt.legend(bbox_to_anchor=(-0.15,1))

def defects_by_type(PT_defects, SD_defects, TPG_defects, RC_defects, NO_defects, OCS_defects, stream, component):
    '''
    Makes a bar plot of the number of defects per defect type, that occured during
    thermal cycling.

    Arguments:
    PT_defects  - Type = list of dict. A list of all defects that occured during the
                  Pedestal Trim.
    SD_defects  - As above, for the Strobe Delay.
    TPG_defects - As above, for the Three-Point Gain.
    RC_defects  - As above, for the Ten-Point Gain.
    NO_defects  - As above, for the Noise Occupancy.
    OCS_defects - As above, for the Open Channel Search.
    stream      - Type = string, "Under" or "Away". The stream to be plotted.
    component   - Type = string. The hybrid serial number.
    '''

    total_defects = make_one_list([PT_defects, SD_defects, TPG_defects, RC_defects, NO_defects, OCS_defects]) #all the defects from TC
    defect_types   = [] #initialize
    unique_defects = []

    for defect in total_defects:
        defect_stream = defect["properties"]["chip_bank"] #under or away
        if defect_stream == stream.lower(): #does it match the stream being plotted?
            defect_types.append(defect["name"])

        if defect_stream == stream.lower() and defect["name"] not in unique_defects:
            unique_defects.append(defect["name"]) #make a list without repeats

    unique_defect_lengths = [] #initialize
    for unique_defect in unique_defects:
        matching_defects = [defect for defect in defect_types if defect == unique_defect] #list of all defects matching the unique defect
        unique_defect_lengths.append(len(matching_defects)) #the number of times that
                                                            #defect occurs

    plt.bar(unique_defects, unique_defect_lengths, color='c')
    plt.title(f"{component} Defects by Type, {stream} Stream")
    plt.xlabel("Defect Type")
    plt.ylabel("Number of Defects")
    plt.xticks(rotation=80)

def defects_by_test(TC_data, PT_defects, SD_defects, TPG_defects, RC_defects, NO_defects, component):
    '''
    Makes a bar plot for the number of defects per test. One subplot covers warm
    tests, and the other cold tests. The bars are seperated by test type.

    Arguments:
    TC_data     - the contents of a pre-opened ColdJigRun JSON file.
    PT_defects  - Type = list of dict. A list of all defects that occured during the
                 Pedestal Trim.
    SD_defects  - As above, for the Strobe Delay.
    TPG_defects - As above, for the Three-Point Gain.
    RC_defects  - As above, for the Ten-Point Gain.
    NO_defects  - As above, for the Noise Occupancy.
    OCS_defects - As above, for the Open Channel Search.
    component   - Type = string. The hybrid serial number.
    '''

    test_sections = TC_data["properties"]["ColdJig_History"] #ie 4_TC_COLD_TEST_0
    ## Filter out sections related to warm-up or cool-down, IVs, and OCS
    valid_sections = [section for section in test_sections if TC.test_is_valid(section)and "IV" not in section and "HV" not in section and "OPEN" not in section]
    warm_sections, cold_sections = TC.sort_sect_temp(test_sections) #sort 'em by temp

    ## Get defective tests for each test type
    PT_defect_tests = [defect["properties"]["runNumber"] for defect in PT_defects]
    SD_defect_tests = [defect["properties"]["runNumber"] for defect in SD_defects]
    TPG_defect_tests = [defect["properties"]["runNumber"] for defect in TPG_defects]
    RC_defect_tests = [defect["properties"]["runNumber"] for defect in RC_defects]
    NO_defect_tests = [defect["properties"]["runNumber"] for defect in NO_defects]

    warm_bar_heights = [] #initialize
    cold_bar_heights = []
    warm_tests = []
    cold_tests = []

    for section in valid_sections:
        try:
            tests = TC_data["properties"]["ColdJig_History"][section]["itsdaq_test_info"]["all_tests"] #get the tests taken in that section

        except: #if there aren't any tests in that section
            tests = [] #leave it blank
            print(f"{YELLOW}Tests for {section} could not be found! Discarding.{RESET}")
        PT_occurances  = 0 #initialize number of times a PT test is in a defect
        SD_occurances  = 0
        TPG_occurances = 0
        RC_occurances  = 0
        NO_occurances  = 0
        for test in tests: #for each of the tests taken in a testing section

            test = ''.join(i for i in test if i.isdigit() or i == '-') #reformat
    ## Add one to PT_occurances for every time the test occurs in the list of PT
    ## defect tests. In other words, add the number of defects in that test.
            PT_occurances += PT_defect_tests.count(test)
            SD_occurances += SD_defect_tests.count(test)
            TPG_occurances += TPG_defect_tests.count(test)
            RC_occurances += RC_defect_tests.count(test)
            NO_occurances += NO_defect_tests.count(test)

        if section in warm_sections: #if this happened warm, use it for the warm plot
           warm_bar_heights.append([PT_occurances, SD_occurances, TPG_occurances, RC_occurances, NO_occurances])
           warm_tests.append([test for test in tests if "IV" not in test])

        elif section in cold_sections: #if it happened cold, use it for the cold plot
            cold_bar_heights.append([PT_occurances, SD_occurances, TPG_occurances, RC_occurances, NO_occurances])
            cold_tests.append([test for test in tests if "IV" not in test])

    plt.subplot(211)
    warm_labels = [] #initialize
    for n,test in enumerate(make_one_list(warm_tests)): #define x labels for warm plot
    ## Every five tests, have a tick label incrementing by one. Five "tests"
    ## corresponds to one Full Test (PT, SD, 3PG, 10PG, NO).
        if n % 5 == 0:
            warm_labels.append(int(n/5))
        else:
            warm_labels.append('')

    plt.bar(make_one_list(warm_tests), make_one_list(warm_bar_heights), align='edge', color=['red','orange','yellow','green','blue'], label=["Pedestal Trim","Strobe Delay","3-Point Gain","10-Point Gain","Noise Occupancy"] * int(len(make_one_list(warm_tests))/5))
    plt.xticks(ticks=make_one_list(warm_tests),labels=warm_labels)
    plt.title(f"{component} Warm Defects Throughout TC")
    plt.xlabel("Warm Test Number")
    plt.ylabel("Number of Defects")
    handles,labels = plt.gca().get_legend_handles_labels()
    plt.legend(handles[:5], labels[:5], ncols=5, bbox_to_anchor=(0.795, -0.19))

    plt.subplot(212)
    cold_labels = [] #initialize
    for n,test in enumerate(make_one_list(cold_tests)): #define x labels for cold plot
        if n % 5 == 0:
            cold_labels.append(int(n/5))
        else:
            cold_labels.append('')
    plt.bar(make_one_list(cold_tests), make_one_list(cold_bar_heights), align='edge', color=['red','orange','yellow','green','blue'])
    plt.xticks(ticks=make_one_list(cold_tests), labels=cold_labels)
    plt.title(f"{component} Cold Defects Throughout TC")
    plt.xlabel("Cold Test Number")
    plt.ylabel("Number of Defects")
    plt.tight_layout()

def get_defect_chips(defects, stream):
    '''
    Make a list of the chips corresponding to the defects (with repeats).

    Arguments:
    defects - Type = list of dict. All the defects of interest.
    stream  - Type = string, "Under" or "Away". The stream of interest.

    Returns:
    defects_by_chip - Type = list of int. The chips corresponding to each defect.
    '''
    defects_by_chip = [] #initialize
    for defect in defects:
    ## If defect belongs to stream of interest, append the chip to returned list.
        if defect["properties"]["chip_bank"] == stream.lower():
            defects_by_chip.append(defect["properties"]["chip_in_histo"])

    return defects_by_chip


