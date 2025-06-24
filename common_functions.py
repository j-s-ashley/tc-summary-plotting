#import libraries
import numpy as np
import os
import json
from matplotlib.backends.backend_pdf import PdfPages
import pprint

def get_component(data):
    '''
    Retrieve component serial number.

    Arguments:
    data - the contents of a pre-opened JSON file.

    Returns:
    component - Type = string. Component serial number.
    '''

    component = data["component"] #sufficient for most module types

#If it's an R2 hybrid, the logical hybrid serial number can be found in the file
    if "H4" in component:
        component = data["properties"]["det_info"]["name"][2:]

    return component

def get_scans(data):
    '''
    Get a list of all scans associated with the data given.

    Arguments:
    data - the contents of a pre-opened JSON file.

    Returns:
    scans - Type = list of string. All scans associated with the given data.
    '''

    scans = data["properties"]["itsdaq_test_info"]["all_tests"]

    return scans

def sort_scan_temp(scans, TC_data):
    '''
    Given a list of scans, sort them based on the temperature at which they were
    taken.

    Arguments:
    scans - Type = list of string. List of scans to be sorted.
    TC_data - the contents of a pre-opened ColdJigRun JSON file.

    Returns:
    warm_scans - Type = list of string. List of warm scans.
    cold_scans - Type = list of string. List of cold scans.
    '''

    tests = TC_data["properties"]["ColdJig_History"] #all test sections
    warm_scans = [] #initialize
    cold_scans = []

#For each test section, get a list of all scans performed. Iterate through the scans,
#and for each scan, see if it matches an item in the list of scans passed to the
#function. If it does and is associated with a cold section, append it to cold_scans.
    for test in tests:

        try:
            all_scans = tests[test]["itsdaq_test_info"]["all_tests"]

        except:
            all_scans = []

        for scan in all_scans:

            if scan in scans and test_is_cold(test, tests):
                cold_scans.append(scan)

#If the scan isn't cold, it must be warm
    for scan in scans:

        if scan not in cold_scans:
            warm_scans.append(scan)

    return warm_scans, cold_scans

def test_is_cold(test, tests):
    '''
    Determine if a testing section was performed cold.

    Arguments:
    test  - Type = string. The name of the testing section of interest.
    tests - Type = list of string. All testing sections from thermal cycling.

    Returns:
    boolean - Whether or not the testing section was performed cold.
    '''

    if "WARM" in test or "PRE_TC" in test or "POST_TC" in test or "TC_END" in test or "ROOM_TEMPERATURE" in test or "TC_START" in test:
        return False #test was warm

    elif "COLD" in test or "COOLDOWN" in test or last_cold_test(test, tests):
        return True #test was cold


    else:
        print(f"{YELLOW}Test {test} could not be flagged as warm or cold!{RESET}")

def fetch_files(directory):
    '''
    Retrieve all relevent files for make_TC_plots.py from a given directory, and sort
    them by associated test type.

    Arguments:
    directory - Type = string. The path to the directory in which relevent files are
                stored.

    Returns:
    sorted_files - Type = dict. All files of interest, sorted by test type.
    '''

    files = os.listdir(directory) #all files in the directory

    valid_files = [] #initialize
#Filter out any files that are not relevent to make_TC_plots.py
    for file in files:
        if ("TC" in file or "ColdJigRun" in file or "HVSTABILITY" in file) and file[-4:] == "json":
            valid_files.append(file) #relevent files

        else:
            print(f"{YELLOW}Found invalid file {file}, discarding.{RESET}")

    sorted_files = {} #initialize

    PTs  = [] #initialize
    SDs  = []
    TPGs = []
    RCs  = []
    NOs  = []
    OCSs = []

#Sort files by test type. Add to sorted_files immediately for test types with only
#one associated file. Otherwise, append to list of files of that test type, and add
#that list to sorted_files.
    for valid_file in valid_files:

        if "MODULE_IV_AMAC_TC" in valid_file:
            sorted_files["IV"] = valid_file
        elif "PEDESTAL_TRIM_TC" in valid_file:
            PTs.append(valid_file)
        elif "STROBE_DELAY_TC" in valid_file:
            SDs.append(valid_file)
        elif "3PG_TC" in valid_file:
            TPGs.append(valid_file)
        elif "RESPONSE_CURVE_TC" in valid_file:
            RCs.append(valid_file)
        elif "NO_TC" in valid_file:
            NOs.append(valid_file)
        elif "OPEN_CHANNEL_SEARCH_TC" in valid_file:
            OCSs.append(valid_file)
        elif "HVSTABILITY" in valid_file:
            sorted_files["HVS"] = valid_file
        elif "ColdJigRun" in valid_file or "MODULE_TC" in valid_file:
            sorted_files["TC"] = valid_file

        sorted_files["PT"] = PTs
        sorted_files["SD"] = SDs
        sorted_files["TPG"] = TPGs
        sorted_files["RC"] = RCs
        sorted_files["NO"] = NOs
        sorted_files["OCS"] = OCSs

    return sorted_files

def last_cold_test(test, tests):
    '''
    Because the name of the last cold IV doesn't have a name that is easily
    identifiable as cold, this function compares the end time of the final cool down
    with the start time of the IV. If it is less than 100 seconds, it assumes the IV
    is cold.

    Arguments:
    test  - Type = string. Testing section of interest.
    tests - Type = list of string. List of all testing sections from thermal cycling.

    Returns:
    boolean - Whether or not the given test is the last cold IV.
    '''

    test_start = tests[test]["start_time"] #start time of the given test section

#Get the name of the last cooldown
    for test_name in tests:
        if "COOLDOWN" in test_name:
            last_cooldown_name = test_name

    cooldown_end = tests[last_cooldown_name]["stop_time"] #end time of last cooldown
#If the test of interest starts within 100 seconds of the end of the last cooldown,
#assume this is the last cold IV.

    if abs(test_start - cooldown_end) < 100:
        return True

    else:
        return False

def fetch_failed_tests(file):
    '''
    Retrieve a list of all failed tests in a given file.

    Arguments:
    file - Type = string. The name of the JSON file to retrieve failed tests for.

    Returns:
    failed_tests - Type = list of string. A list of all failed tests in that file.
    '''

    if type(file) is dict: #if the file is already opened
        data = file

    else:
        with open(file, 'r') as f: #open the file
            data = json.load(f)

    try:
        failed_tests = data["properties"]["itsdaq_test_info"]["failed_tests"]

    except:
        failed_tests = []

    return failed_tests

def get_channels(data):
    '''
    Create a list of channel numbers for the hybrid associated with the given data.

    Arguments:
    data - the contents of a pre-opened JSON file.

    Returns:
    channels - Type = list of int. List of channel numbers.
    '''

    results   = data["results"]
    test_type = get_test_type(data) #different case for RCs due to file formatting

#Get the name of the first data field
    if test_type != "3PG" and test_type != "10PG": #not an RC

        for n,field in enumerate(results):
            if n == 0:
                first_field = field #first list of results for that test type

    elif test_type == "3PG" or test_type == "10PG": #RC
        first_field = "gain_away"

    data_set = make_one_list(results[first_field][0]) #reformat first test's data
    channels = [n for n in range(len(data_set))] #one channel per data point

    return channels

def get_defects(data):
    '''
    Retrieve a list of defects associated with the given data.

    Arguments:
    data - the contents of a pre-opened JSON file.

    Returns:
    defects - Type = list of dict. The defects found in the file.
    '''

    defects = data["defects"]

    return defects

def get_test_type(data):
    '''
    At the moment, only used to distinguish between 3-Point Gain and 10-Point Gain
    tests. If the data passed to the function is associated with neither, it returns
    None. Otherwise, it returns the type of Response Curve associated with the data.

    Arguments:
    data - the contents of a pre-opened JSON file.

    Returns:
    test_type - Type = string, "3PG" or "10PG", or none. The type of Response Curve.
    '''
    try:
        ft_code = data["properties"]["fit_type_code"] #see if there is a fit_type_code
    except:
        ft_code = None #if it doesn't exist, make it None

    if ft_code == 4: #fit_type_code for 3PG
        test_type = "3PG"
    elif ft_code == 3: #fit_type_code for 10PG
        test_type = "10PG"

    elif "trim_away" in list(data["results"].keys()):
        test_type = "PT"
    elif "StrobeDelay_away" in list(data["results"].keys()):
        test_type = "SD"
    elif "enc_est_away" in list(data["results"].keys()):
        test_type = "NO"
    elif "noise_away" in list(data["results"].keys()):
        test_type = "OCS"

    return test_type

def make_one_list(data_list):
    '''
    Given a list of lists, reformat it so it is one list.

    Arguments:
    data_list - Type = list of list. The list to be reformatted.

    Returns:
    flattened_list - Type = list. Reformatted list.
    '''

    flattened_list = [] #initialize

    try:
        for sublist in data_list: #iterate through each sublist
            for point in sublist: #iterate through the points in the sublist
                flattened_list.append(point) #append each point individually
    except: #if the list is already flattened
        flattened_list = data_list #do nothing to the list

    return flattened_list

def unsort_files(files):
    '''
    Given a dictionary of files sorted by type, unsort them to yield simply a list of
    files.

    Arguments:
    files - Type = dict. A dictionary of files, sorted by type.

    Returns:
    unsorted_files - Type = list of string. Unsorted list of files.
    '''

    unsorted_files = [] #initialize

    for file_type in files:
        file_list = files[file_type] #get all files of a type

        if type(file_list) is list: #if there are multiple files
            unsorted_files.append(file_list) #append the list

        else:
            unsorted_files.append([file_list]) #make it a list, and append it

    unsorted_files = make_one_list(unsorted_files) #flatten the list

    return unsorted_files

def make_pdf(plots, component, date, run_number):
    '''
    Given all plots made by the make_TC_plots.py scripts, put them into a single PDF.

    Arguments:
    plots      - Type = list of matplotlib figures. A list of all plots made.
    component  - Type = string. The module serial number.
    date       - Type = string. The date that TC began.
    run_number - Type = int. The ColdJig runNumber.
    '''

    with PdfPages(f'{component}_{date}_{run_number}_TC_plots.pdf') as pdf:
        for plot in plots:
            pdf.savefig(plot, bbox_inches='tight')

def sort_files_by_hybrid(files, TC_directory):
    '''
    Sort files by associated hybrid serial number.

    Arguments:
    files        - Type = list of string. The list of files to be sorted.
    TC_directory - Type = string. The path to the directory wher the files are stored.

    Returns:
    sorted_files - Type = dict. A dictionary with keys corresponding to unique hybrid
                   serial numbers, where the contents associated with each key are
                   the files associated with that hybrid serial number.
    '''

    sorted_files = {} #initialize

    for file in files:

        data = retrieve_data(file)
        file_SN = get_component(data) #get the SN from inside the file

        if file_SN in sorted_files.keys(): #if SN is already in the dictionary
            sorted_files[file_SN].append(file) #just append the file to that key list

        elif "20USEH" in file_SN or "20USBH" in file_SN: #otherwise, create a new key
            sorted_files[file_SN] = [file]

    return sorted_files

def get_colours(warm_scans, cold_scans):
    '''
    Assign temperature-related colours for plotting, based on the number of cold and
    warm scans being plotted.

    Arguments:
    warm_scans - Type = list of string. The list of warm tests being plotted (one scan
                 per data set).
    cold_scans - Type = list of string. The list of cold tests being plotted (one scan
                 per daya set).

    Returns:
    red_cold   - Type = int. The red RGB value for cold test plotting.
    red_warm   - Type = int. The red RGB value for warm test plotting.
    blue_cold  - Type = int. The blue RGB value for cold test plotting.
    blue_warm  - Type = int. The blue RGB value for warm test plotting.
    green_cold - Type = list of float. The green RGB values for each cold test.
    green_warm - Type = list of float. The green RGB values for each warm test.
    '''

    red_cold = 0 #no red in cold plots
    red_warm = 1 #strong red in warm plots
    blue_cold = 1 #strong blue in cold plots
    blue_warm = 0 #no blue in warm plots.

## To differentiate individual tests, decrease the amount of green for each scan.
## For warm plots, reds get redder, and for cold plots, blues get bluer as TC goes.

    green_cold = [1 - i * (1 / len(cold_scans)) for i, scan in enumerate(cold_scans)]
    green_warm = [1 - j * (1 / len(warm_scans)) for j, scan in enumerate(warm_scans)]

    return red_cold, red_warm, blue_cold, blue_warm, green_cold, green_warm

def get_index(item, items):
    '''
    Determine the index in a list of items which corresponds to the item of interest.

    Arguments:
    item - Type = any. The item of interest.
    items - Type = list. The list which contains the item of interest.
    '''

    for n,element in enumerate(items):
        if element == item:
            index = n

    return index


def retrieve_data(data_file):
    '''
    Retrieve data from a data file, using a different method for real local files,
    and "files" (data dictionaries) pulled from the ATLAS ITk Production Database.

    Arguments:
    data_file - type = string or dict. Either a path to a local JSON,
                or a data dictionary from the database.

    Returns:
    data - type = dict. The data dictionary.
    '''
    if type(data_file) is dict: #if the data_file was pulled from DB
        data = data_file #do nothing

    else: #if it's a path to a local file
        with open(data_file, 'r') as f: #open the JSON
            data = json.load(f)

    return data

'''
Sets global variables for colour terminal printout.
'''
global RED, GREEN, YELLOW, BLUE, RESET

RED    = '\033[31m'
GREEN  = '\033[32m'
YELLOW = '\033[33m'
BLUE   = '\033[94m'
RESET  = '\033[0m'
