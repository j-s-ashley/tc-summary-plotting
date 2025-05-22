#import libraries
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from common_functions import *
from matplotlib.ticker import MultipleLocator


def make_plots(TC_data, failed_tests):
    '''
    Organizes the making of plots, and terminal outputs.

    Arguments:
    TC_data      - the contents of a pre-opened ColdJigRun JSON file.
    failed_tests - Type = list of string. A list of all tests, of any type, that
                   failed during thermal cycling.

    Returns:
    plots - Type = list of matplotlib figures. The plots made.
    '''

    matplotlib.rcParams['font.size'] = 7 #set plot fontsize globally
    failed_tests = make_one_list(failed_tests) #reformat
    env_plot = plt.figure(figsize=[7,5], dpi=50)

#Make a plot of the environmental data during TC
    environmental_plot(TC_data)

#Make a table of all TC tests, indicating which passed, and which failed
    results_plot = plt.figure(figsize=[8,6], dpi=10)
    results_table(TC_data, failed_tests)

    environmental_summary(TC_data) #terminal output about environmental data
    results_summary(TC_data, failed_tests) #terminal output about test pass/fails

    plots = [env_plot, results_plot]
    plt.close('all')
    return plots

def environmental_plot(TC_data):
    '''
    Makes a plot of chuck temperature and dew point throughout thermal cycling.

    Arguments:
    TC_data - the contents of a pre-opened ColdJigRun JSON file.
    '''

    environmental_data = TC_data["results"]["environmental_data"]
    timestamps         = TC_data["results"]["environmental_data"]["timestamps"]
    #reformat time so it's in hours, starting from 0
    times = [(timestamp - timestamps[0]) / 3600 for timestamp in timestamps]

    DP_fields   = [] #initialize
    temp_fields = []

#Get the correct dew point and chuck temp fields for the chuck the module was on
    for field in environmental_data.keys():
        if field[0:2] == "DP":
            DP_fields.append(field)
        elif field[0:11] == "thermometer":
            temp_fields.append(field)

    colors = ['green', 'yellow', 'blue', 'orange', 'red'] #for plotting

#Plot dew points
    for d,field in enumerate(DP_fields):
        data = TC_data["results"]["environmental_data"][field]
        plt.plot(times, data, color=colors[d], linestyle="dashed", label=f"Chuck {field[-1]} Dew Point") #plot

#Plot chuck temperature
    for t,field in enumerate(temp_fields):
        data = TC_data["results"]["environmental_data"][field]
        plt.plot(times, data, color=colors[t], label=f"Chuck {field[-1]} Temperature") #plot

    plt.title("Chuck Temperature and Dew Point Throughout TC")
    plt.xlabel("Time (hr)")
    plt.ylabel("Temperature (C)")
    plt.legend()

def results_table(TC_data, failed_tests):
    '''
    Makes a table of all tests taken during TC, and fills the squares pertaining to
    passed tests green, and failed tests red.

    Arguments:
    TC_data      - the contents of a pre-opened ColdJigRun JSON file.
    failed_tests - Type = list of string. A list of all failed tests during TC.
    '''

    all_tests      = [] #initialize
#Make a list of all TC test sections (such as 41_TC_WARM_TEST_4)
    test_sections  = TC_data["properties"]["ColdJig_History"]
    valid_sections = [] #initialize

#get a list of all tests
    for test_section in test_sections:
        if test_is_valid(test_section): #is the section relevant?
            try:
                tests = TC_data["properties"]["ColdJig_History"][test_section]["itsdaq_test_info"]["all_tests"] #get tests for that section, if they exist

            except:
                print(f"{YELLOW}Tests for {test_section} not found! Discarding.{RESET}")
                tests = [] #no tests found
            all_tests.append(tests) #list of list of tests
            valid_sections.append(test_section) #append if section is testing section

    formatted_tests = format_tests(all_tests) #formatting

    colors = [] #initialize
#If a test passed, append green for that test, if it failed, append red, if there is
#no test, append white
    for test_list in formatted_tests:
       row_colors = [] #inititalize colours for this row on the table

       for n,test in enumerate(test_list):

           if test in failed_tests:
               row_colors.append((1, 0, 0.1)) #red

           elif test == "":
               row_colors.append('grey')
           else:
               row_colors.append((0, 0.7, 0)) #green
           test_list[n] = test.translate({ord(c): None for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ_'}) #Just the test number, since test type is the table column

       colors.append(row_colors) #append list of colours to master list

#If test section is cold, make the corresponding label blue, red otherwise
    row_label_colors = [] #initialize
    for test in valid_sections:
        if test_is_cold(test, test_sections):
            row_label_colors.append('dodgerblue') #make it blue
        else:
            row_label_colors.append((0.7, 0.1, 0)) #make it red

    plt.rcParams['axes.spines.left'] = False #get rid of default plot box
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.bottom'] = False

    results_table = plt.table(formatted_tests, colors, 'center', bbox=[0.05,-0.13,1.05,1.22], rowLabels=valid_sections, rowLoc = 'center', colLabels=["IV", "Pedestal Trim", "Strobe Delay", "3-Point Gain", "10-Point Gain", "NO", "OCS", "HV Stability"], rowColours=row_label_colors) #make the table

#get rid of axis ticks and labels
    plt.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    results_table.auto_set_font_size(False) #override automatic fontsize setting
    results_table.set_fontsize(6) #set fontsize for the table
    results_table #create the table

def environmental_summary(TC_data):
    '''
    Prints out enviromental summary data to the terminal, including information on
    maximum and minimum chuck temperatures and humidity, the number of cold, warm, and
    cold shunted tests performed, the duration of the cycling, and the ColdJig and
    ITSDAQ run numbers.

    Arguments:
    TC_data - the contents of a pre-opened ColdJigRun JSON file.
    '''

    TC_summary         = TC_data["results"]["summary"] #Where this info is stored
    max_temp           = TC_summary["max_temperature"] #max chuck temperature
    min_temp           = TC_summary["min_temperature"] #min chuck temperature
    max_hum            = TC_summary["max_humidity"] #max chuck humidity
    min_hum            = TC_summary["min_humidity"] #min chuck humidity
    n_cold             = TC_summary["cold_tests"] #number of cold tests
    n_warm             = TC_summary["warm_tests"] #number of warm tests
    n_shunted          = TC_summary["cold_shunted_tests"] #number of cold shunted
    duration           = TC_summary["duration_hours"] #TC duration
    cj_run_numbers     = TC_summary["coldjig_runNumbers"] #ColdJig run numbers
    itsdaq_run_numbers = TC_summary["itsdaq_runNumbers"] #ITSDAQ run numbers

    text = f"{BLUE}The maximum chuck temperature was {max_temp:.3}C.\nThe minimum chuck temperature was {min_temp:.3}C.\nThe maximum humidity was {max_hum:.3}%.\nThe minimum humidty was {min_hum:.3}%.\nThere were {n_cold} cold tests, {n_shunted} of them shunted.\nThere were {n_warm} warm tests.\nTC took {duration} hours, with ColdJig run number(s) {cj_run_numbers}, and ITSDAQ run number(s) {itsdaq_run_numbers}.{RESET}" #text to print

    print(f"\nTC Overview:\n{text}\n") #print to terminal


def results_summary(TC_data, failed_tests):
    '''
    Prints out the rate of failure to the terminal (failed tests / total tests * 100%)
    for each test type, and a list of all failed tests.

    Arguments:
    TC_data      - the contents of a pre-opened ColdJigRun JSON file.
    failed_tests - Type = list of string. List of all failed tests from cycling.
    '''

    test_sections                = TC_data["properties"]["ColdJig_History"]
    warm_sections, cold_sections = sort_sect_temp(test_sections) #sort by temp
    warm_failed, cold_failed     = sort_scan_temp(failed_tests, TC_data) #sort failed
    #relevant sections
    valid_sections = [section for section in test_sections if test_is_valid(section)]
    warm_tests = [] #initialize
    cold_tests = []

#Get a list of tests from each test section. Append tests to either warm_tests or
#cold_tests, as appropriate
    for section in valid_sections:
        try:
            tests = TC_data["properties"]["ColdJig_History"][section]["itsdaq_test_info"]["all_tests"] #get tests for section, if they exist
        except:
            tests = []
            print(f"{YELLOW}Tests for {section} could not be found! Discarding.{RESET}")

        if section in warm_sections:
            for test in tests: #append each warm test individually
                warm_tests.append(test)

        elif section in cold_sections:
            for test in tests: #append each cold test individually
                cold_tests.append(test)
        else:
            print(f"{YELLOW}Testing section {section} could not be labelled warm or cold!{RESET}")

    warm_IVs  = [] #initialize
    warm_PTs  = []
    warm_SDs  = []
    warm_RCs  = []
    warm_NOs  = []
    warm_OCSs = []
    warm_HVSs = []

#Sort warm tests by test type
    for test in warm_tests:
        if "MODULE_IV_AMAC" in test:
            warm_IVs.append(test)
        elif "PEDESTAL_TRIM" in test:
            warm_PTs.append(test)
        elif "STROBE_DELAY" in test:
            warm_SDs.append(test)
        elif "RESPONSE_CURVE" in test:
            warm_RCs.append(test)
        elif "_NO" in test:
            warm_NOs.append(test)
        elif "OPEN_CHANNEL_SEARCH" in test:
            warm_OCSs.append(test)
        elif "HVSTABILITY" in test:
            warm_HVSs.append(test)
        else:
            print(f"{YELLOW}Could not identify test type for {test}!{RESET}")

    cold_IVs  = [] #initialize
    cold_PTs  = []
    cold_SDs  = []
    cold_RCs  = []
    cold_NOs  = []

#Sort cold tests by test type
    for test in cold_tests:
        if "MODULE_IV_AMAC" in test:
            cold_IVs.append(test)
        elif "PEDESTAL_TRIM" in test:
            cold_PTs.append(test)
        elif "STROBE_DELAY" in test:
            cold_SDs.append(test)
        elif "RESPONSE_CURVE" in test:
            cold_RCs.append(test)
        elif "_NO" in test:
            cold_NOs.append(test)
        else:
            print(f"{YELLOW}Could not identify test type for {test}!{RESET}")

#Make a list of failed tests by temperature and test type
    failed_warm_IVs  = [IV for IV in warm_IVs if IV in failed_tests]
    failed_warm_PTs  = [PT for PT in warm_PTs if PT in failed_tests]
    failed_warm_SDs  = [SD for SD in warm_SDs if SD in failed_tests]
    failed_warm_RCs  = [RC for RC in warm_RCs if RC in failed_tests]
    failed_warm_NOs  = [NO for NO in warm_NOs if NO in failed_tests]
    failed_warm_OCSs = [OCS for OCS in warm_OCSs if OCS in failed_tests]

    failed_cold_IVs = [IV for IV in cold_IVs if IV in failed_tests]
    failed_cold_PTs = [PT for PT in cold_PTs if PT in failed_tests]
    failed_cold_SDs = [SD for SD in cold_SDs if SD in failed_tests]
    failed_cold_RCs = [RC for RC in cold_RCs if RC in failed_tests]
    failed_cold_NOs = [NO for NO in cold_NOs if NO in failed_tests]

#Define statements for each test type

    IV_text = f"{printout_color(failed_warm_IVs)}Out of {len(warm_IVs)} warm IVs, {len(failed_warm_IVs)} failed ({len(failed_warm_IVs) / len(warm_IVs) * 100 :.3}%).{printout_color(failed_cold_IVs)}\nOut of {len(cold_IVs)} cold IVs, {len(failed_cold_IVs)} failed ({len(failed_cold_IVs) / len(cold_IVs) * 100 :.3}%).{RESET}\n"

    PT_text = f"{printout_color(failed_warm_PTs)}Out of {len(warm_PTs)} warm Pedestal Trims, {len(failed_warm_PTs)} failed ({len(failed_warm_PTs) / len(warm_PTs) * 100 :.3}%).{printout_color(failed_cold_PTs)}\nOut of {len(cold_PTs)} cold Pedestal Trims, {len(failed_cold_PTs)} failed ({len(failed_cold_PTs) / len(cold_PTs) * 100 :.3}%).{RESET}\n"

    SD_text = f"{printout_color(failed_warm_SDs)}Out of {len(warm_SDs)} warm Strobe Delays, {len(failed_warm_SDs)} failed ({len(failed_warm_SDs) / len(warm_SDs) * 100 :.3}%).\n{printout_color(failed_cold_SDs)}Out of {len(cold_SDs)} cold Strobe Delays, {len(failed_cold_SDs)} failed ({len(failed_cold_SDs) / len(cold_SDs) * 100 :.3}%).{RESET}\n"

    RC_text = f"{printout_color(failed_warm_RCs)}Out of {len(warm_RCs)} warm Response Curves (10PG and 3PG), {len(failed_warm_RCs)} failed ({len(failed_warm_RCs) / len(warm_RCs) * 100 :.3}%).\n{printout_color(failed_cold_RCs)}Out of {len(cold_RCs)} cold Response Curves, {len(failed_cold_RCs)} failed ({len(failed_cold_RCs) / len(cold_RCs) * 100 :.3}%).\n{RESET}"

    NO_text = f"{printout_color(failed_warm_NOs)}Out of {len(warm_NOs)} warm Noise Occupancy tests, {len(failed_warm_NOs)} failed ({len(failed_warm_NOs) / len(warm_NOs) * 100 :.3}%).\n{printout_color(failed_cold_NOs)}Out of {len(cold_NOs)} cold Noise Occupancy tests, {len(failed_cold_NOs)} failed ({len(failed_cold_NOs) / len(cold_NOs) * 100 :.3}%).{RESET}\n"

    OCS_text = f"{printout_color(failed_warm_OCSs)}Out of {len(warm_OCSs)} Open Channel Searches (all warm), {len(failed_warm_OCSs)} failed ({len(failed_warm_OCSs) / len(warm_OCSs) * 100 :.3}%).{RESET}"

    total_text = IV_text + PT_text + SD_text + RC_text + NO_text + OCS_text

    print(f"\nResults Summary:\n{total_text}\n") #print to terminal
#Print out every failed test during TC
    if failed_tests != []:
        print(f"\n{RED}Failed Tests:{RESET}\n\n")
        for test in failed_tests:
            print(f"{RED}{test}{RESET}\n")
    else:
        print(f"{GREEN}All tests passed!{RESET}")

def sort_sect_temp(test_sections):
    '''
    Take a list of test sections, sort them by temperature, and filter out the
    irrelevant sections.

    Arguments:
    test_sections - Type = list of string. Every testing section (ie.
                    41_TC_WARM_TEST_4) from TC.

    Returns:
    valid_warm_sections - Type = list of string. All relevent warm testing sections.
    valid_cold_sections - Type = list of string. All relevent cold testing sections.
    '''

    valid_sections = [] #initialize
    warm_sections  = []
    cold_sections  = []

#Sort sections by temperature
    for section in test_sections:
        if test_is_cold(section, test_sections):
            cold_sections.append(section)
        else:
            warm_sections.append(section)

#Filter out irrelevent sections
    valid_cold_sections = [section for section in cold_sections if test_is_valid(section)]
    valid_warm_sections = [section for section in warm_sections if test_is_valid(section)]

    return valid_warm_sections, valid_cold_sections

def test_is_valid(section):
    '''
    For the purposes of this script, we only care about sections associated with
    tests.Sections associated with temperature changes, initialization, or turning on
    the module do not correspond to any tests, and are therefore "not valid" in the
    context of this script.

    Arguments:
    section - Type = string. Name of a single testing section, as it appears in the
              ColdJigRun JSON file (such as 41_TC_WARm_TEST_4).

    Returns:
    Type = boolean. Whether or not the section is valid.
    '''

    if "TEST" in section or "IV" in section or "HV" in section or "OPEN" in section:
        return True #section is associated with electrical tests

    elif "COOLDOWN" in section or "WARMUP" in section or "TC_START" in section or "ROOM_TEMPERATURE" in section or "TURN_ON" in section or "TC_END" in section:

        return False #section is not associated with electrical tests

    else:
        print(f"{YELLOW}Unrecognized test section: {section}. Discarding.{RESET}")
        return False #section is not recognized

def format_tests(all_tests):
    '''
    Given all tests conducted during thermal cycling, reformat them into a list
    of list, where each sublist contains an IV, Pedestal Trim, Strobe Delay, 3-Point
    Gain, 10-Point Gain, Noise Occupancy, Open Channel Search, and HV-Stability test
    for a test section. Where a section does not contain a particular test type, keep
    that test in the list as an empty string.

    Arguments:
    all_tests - Type = list of list of string. Each sublist corresponds to the names
                of all tests run in a single testing section.

    Returns:
    formatted_tests - Type = list of list of string. Each sublist corresponds to the
                      names of all tests run in a single testing section, with empty
                      strings where there are no tests of a type.
    '''

    formatted_tests = [] #initialize

    for test_list in all_tests: #iterate through the sections

        IV   = "" #initialize
        PT   = ""
        SD   = ""
        RC3  = ""
        RC10 = ""
        NO   = ""
        OCS  = ""
        HVS  = ""
        is_10PG = False #first RC will be a 3PG, second a 10PG

        for test in test_list: #iterate through tests associated with a single section
            #Label the test by test type

            if "IV" in test:
                IV = test
            elif "PEDESTAL_TRIM" in test:
                PT = test
            elif "STROBE_DELAY" in test:
                SD = test
            elif "RESPONSE_CURVE" in test and not is_10PG:
                RC3 = test
                is_10PG = True #next RC will be a 10PG
            elif "RESPONSE_CURVE" in test and is_10PG:
                RC10 = test
            elif "_NO" in test:
                NO = test
            elif "OPEN_CHANNEL_SEARCH" in test:
                OCS = test
            elif "HVSTABILITY" in test:
                HVS = test

        formatted_list = [IV, PT, SD, RC3, RC10, NO, OCS, HVS] #all test types
        formatted_tests.append(formatted_list) #append all test types

    return formatted_tests

def printout_color(failed_test_list):
    '''
    Determine the colour of the terminal printout for the line in results summary
    pertaining to the given failed_test_list.

    Arguments:
    failed_test_list - Type = list of string. A list of failed test names.

    Returns:
    print_color - Type = string. Either RED (if some tests fail), or GREEN (if all
                  tests pass). These correspond to global variables assosciated with
                  colour terminal printout, declared in common_functions.py.
    '''

    if len(failed_test_list) > 0: #if some tests fail
        print_color = RED
    else: #if all tests pass
        print_color = GREEN

    return print_color
