import itkdb
import pprint
import numpy as np
import getpass as gp
from common_functions import *

def establish_db_client():
    '''
    Establishes client to permit access to the ATLAS ITk Production Database.

    Returns:
    client - type = class. Allows DB access.
    '''
    print(f"{BLUE}\nPlease provide your ATLAS ITk Production Database Access Codes.{RESET}")
    access_code1 = gp.getpass("Access Code 1:")
    access_code2 = gp.getpass("Access Code 2:")

    user = itkdb.core.User(access_code1, access_code2)
    client = itkdb.Client(user=user)

    return client

def get_files():
    '''
    Creates "files" -- data dictionaries in a similar format to the merged data files,
    for use in the pre-existing plotting software.

    Returns:
    IV_file, HVS_file, TC_file - type = dict. A dictionary containing all the
                                 requisite information from the database, formatted.

    PT_file, SD_file, TPG_file, RC_file, NO_file OCS_file - type = list of dict.
                                 A list of data dictionaries, one per hybrid.
    '''
    client = establish_db_client() #get DB access
    module_sn = input("Module Serial Number (ie. 20USEM40000080):")

    module = get_db_module(client, module_sn) #get module object from DB
    hybrids = get_db_hybrids(client, module) #get hybrid objects from DB
    test_IDs = get_test_IDs(client, module, hybrids)
    test_runs = client.get("getTestRunBulk", json={"testRun": test_IDs})
    IV_file, PT_file, SD_file, TPG_file, RC_file, NO_file, OCS_file, HVS_file, TC_file = make_data_dicts(test_runs) #assemble the data into dictionaries

    return IV_file, PT_file, SD_file, TPG_file, RC_file, NO_file, OCS_file, HVS_file, TC_file

def get_db_module(client, module_sn):
    '''
    Retrieves the module object from the database.

    Arguments:
    client - type = class. Enables database access.
    module_sn - type = string. The module serial number.

    Returns:
    module - type = dict. The module object.
    '''
    try:
        module = client.get("getComponent", json={"component": f'{module_sn}'})
        print(f"{GREEN}\nFound module {module['serialNumber']}!{RESET}")
        return module
    except:
        print(f"{RED}\nCould not find module {module_sn} in database!{RESET}")


def get_db_hybrids(client, module):
    '''
    Retrieves the hybrid objects associated with the module of interest.

    Arguments:
    client - type = class. Enables database access.
    module - type = dict. Module object from database.
    '''

    hybrids = [] #initialize
    children = module['children'] #all module children

    if 'M4' in module['serialNumber'] or 'M5' in module['serialNumber']: #if it's a split module, children are half-modules

        for child in children:
            half_module_sn = child['component']['serialNumber']
            half_module = client.get("getComponent", json={"component": f'{half_module_sn}'}) #retrieve half-module object
            grandchildren = half_module['children'] #children of the half-module

            for grandchild in grandchildren:
                if grandchild['component'] is None: #this happens sometimes
                    continue
 
                #if the module grandchild is a hybrid
                elif '20USEH' in grandchild['component']['serialNumber']:

                    hybrid_sn = grandchild['component']['serialNumber']
                    hybrid = client.get("getComponent", json={"component": f'{hybrid_sn}'})
                    print(f"{GREEN}\nFound hybrid {hybrid_sn}!{RESET}")
                    hybrids.append(hybrid)


    elif 'M0' in module['serialNumber'] or 'M1' in module['serialNumber'] or 'M2' in module['serialNumber'] or '3L' in module['serialNumber'] or '3R' in module['serialNumber'] or 'MS' in module['serialNumber'] or 'ML' in module['serialNumber']: #if it isn't a split-module, hybrids will be children

        for child in children:
            if child['component'] is None:
                continue

            elif '20USEH' in child['component']['serialNumber'] or '20USBH' in child['component']['serialNumber']: #if the child is a hybrid
                hybrid_sn = child['component']['serialNumber']
                hybrid = client.get("getComponent", json={"component": f'{hybrid_sn}'})
                print(f"{GREEN}\nFound hybrid {hybrid_sn}!{RESET}")
                hybrids.append(hybrid)

    return hybrids

def get_test_IDs(client, module, hybrids):
    '''
    Get the test ID (unique identifying string for a given test) for the relevant TC
    tests.

    Arguments:
    client - type = class. Enables DB access.
    module - type = dict. Module object from DB.
    hybrids - type = list of dict. List of hybrid objects from DB.

    Returns:
    test_IDs - type = list of string. The relevant test IDs.
    '''
    components        = [hybrid for hybrid in hybrids] #create a components list, with the hybrids in it.
    components.append(module) #add the module to the components list.
    TC_overview_tests = [] #initialize
    test_runs         = []

    for component in components: #for every hybrid and module

        all_tests = component['tests'] #all tests uploaded to that component

        TC_tests = [test for test in all_tests if "TC" in test['code'] or 'HVSTABILITY' in test['code']] #all tests associated with Thermal Cycling

        for TC_test in TC_tests: #for every test from TC

            test_runs.append(TC_test['testRuns']) #individual test runs

            if "MODULE_TC" in TC_test["code"]: #refers to test used in TC.py
                TC_overview_tests.append(TC_test['testRuns'])

    if len(make_one_list(test_runs)) > (3 + len(hybrids) * 6) and "M2" not in module['serialNumber']:
        valid_runs = get_valid_tests(make_one_list(test_runs))
    elif len(make_one_list(test_runs)) > (3 + (2 * 6)) and "M2" in module['serialNumber']:
        valid_runs = get_valid_tests(make_one_list(test_runs))

    else:
        valid_runs = make_one_list(test_runs)
    test_IDs = [run['id'] for run in valid_runs] #get the test IDs
    overview_ID = get_correct_overview(client, make_one_list(TC_overview_tests), valid_runs) #MODULE_TC tests get uploaded with ColdJig runNumber
    test_IDs.append(overview_ID)

    return test_IDs


def get_correct_overview(client, TC_overview_tests, all_runs):
    '''
    All electrical tests during TC are uploaded to the DB with the ITSDAQ runNumber in
    the runNumber field, except for MODULE_TC test, which contains a summary of TC.
    This is uploaded with the ColdJig runNumber. To find the correct MODULE_TC test,
    this function compares the dates electrical tests were done with the MODULE_TC
    test date. If it finds more than one valid option, it asks the user for the
    ColdJig runNumber directly.

    Arguments:
    client - type = class. Enables DB access.
    TC_overview_tests - type = list of dict. All MODULE_TC tests uploaded to that
                        module in the DB.
    all_runs - type = list of dict. All relevant electrical tests.

    Returns:
    overview_ID - type = string. The test ID for the MODULE_TC test.
    '''
    overview_dates      = [test['date'][:10] for test in TC_overview_tests]
    overview_institutes = [test['institution']['code'] for test in TC_overview_tests]
    overview_uploads    = [test['cts'][:10] for test in TC_overview_tests]
    example_dates       = [run['date'][:10] for run in all_runs]
    example_institutes  = [run['institution']['code'] for run in all_runs]
    example_uploads     = [run['cts'][:10] for run in all_runs]
    potential_tests     = [] #initialize

    for n,test in enumerate(TC_overview_tests):
        #if the date macthes electrical test and is at the correct institute
        if (overview_dates[n] in example_dates or overview_uploads[n] in example_uploads) and overview_institutes[n] in example_institutes:
            potential_tests.append(test) #it might be the correct one

    if len(potential_tests) == 1: #if there's only one option, it is the correct one
        overview_ID = potential_tests[0]['id']

    elif len(potential_tests) > 1: #if there's multiple options, get ColdJig runNumber
        print(f"{YELLOW}Sorry, multiple MODULE_TC tests found on the same dates from the same institute. Please provide the ColdJig runNumber.{RESET}")
        coldjig_rn = input("ColdJig runNumber:")

        for potential_test in potential_tests:

            if potential_test['runNumber'] == coldjig_rn:
                overview_ID = potential_test['id']
                break

    return overview_ID



def make_data_dicts(test_runs):
    '''
    Make data dictionaries for the different test types, from database information.

    Arguments:
    test_runs - type = list of dict. All relevant test runs.

    Returns:
    IV_files, HVS_files, TC_files - type = dict. A dictionary of TC test data.
    PT_files, SD_files, TPG_files, RC_files, NO_files, OCS_files - type = list of
    dict. A list of data dictionaries, one per hybrid.
    '''
    IV_runs     = [] #initialize
    PT_runs     = []
    SD_runs     = []
    TPG_runs    = []
    RC_runs     = []
    NO_runs     = []
    OCS_runs    = []
    HVS_runs    = []
    TC_runs     = []
    all_RC_runs = []

    for run in test_runs: #sort test runs by test type
        test_type = run['testType']['code']
        if test_type == 'MODULE_IV_AMAC_TC':
            IV_runs.append(run)
        elif test_type == 'PEDESTAL_TRIM_TC':
            PT_runs.append(run)
        elif test_type == 'STROBE_DELAY_TC':
            SD_runs.append(run)
        elif test_type == 'RESPONSE_CURVE_TC':
            all_RC_runs.append(run)
        elif test_type == 'NO_TC':
            NO_runs.append(run)
        elif test_type == 'OPEN_CHANNEL_SEARCH_TC':
            OCS_runs.append(run)
        elif test_type == 'HVSTABILITY':
            HVS_runs.append(run)
        elif test_type == 'MODULE_TC':
            TC_runs.append(run)

    TPG_runs, RC_runs = sort_RCs(all_RC_runs) #sort by 3PG and 10PG
    IV_files          = format_data(IV_runs, 'IV')[0]
    PT_files          = format_data(PT_runs, 'PT')
    SD_files          = format_data(SD_runs, 'SD')
    TPG_files         = format_data(TPG_runs, '3PG')
    RC_files          = format_data(RC_runs, '10PG')
    NO_files          = format_data(NO_runs, 'NO')
    OCS_files         = format_data(OCS_runs, 'OCS')
    HVS_files         = format_data(HVS_runs, 'HVS')[0]
    TC_files          = format_data(TC_runs, 'TC')[0]

    return IV_files, PT_files, SD_files, TPG_files, RC_files, NO_files, OCS_files, HVS_files, TC_files


def sort_RCs(all_RC_runs):
    '''
    Sort a list of Response Curve test runs into 3-Point Gain and 10-Point Gain runs.

    Arguments:
    all_RC_runs - type = list of dict. A list of all Response Curve runs.

    Returns:
    TPG_runs - type = list of dict. A list of all 3-Point Gain runs.
    RC_runs - type = list of dict. A list of all 10-Point Gain runs.
    '''

    times_by_hybrid = {} #initialize
    TPG_runs        = []
    RC_runs         = []
    all_times       = []

    for run in all_RC_runs:
        hybrid = [run["components"][n]["serialNumber"] for n in range(len(run["components"])) if "20USEH" in run["components"][n]["serialNumber"] or "20USBH" in run["components"][n]["serialNumber"]][0] #get hybrid run is uploaded to
        if 'H4' in hybrid: #if the hybrid belongs to an R2
            hybrid = fix_R2_hybrid_sn(run) #H0 or H1 logical hybrid
        time = run["date"] #get the run date and time
        all_times.append(time)

        #if run happened before other RC associated with hybrid, it's a 3PG
        if hybrid in times_by_hybrid.keys() and times_by_hybrid[hybrid][0] > time:
            TPG_runs.append(run)
            RC_runs.append(times_by_hybrid[hybrid][1])

        #if run happened after other RC associated with hybrid, it's a 10PG
        elif hybrid in times_by_hybrid.keys() and times_by_hybrid[hybrid][0] < time:
            RC_runs.append(run)
            TPG_runs.append(times_by_hybrid[hybrid][1])

        else: #if no other test is associated with the hybrid, add it to the dict
            times_by_hybrid[hybrid] = [time, run]

    return TPG_runs, RC_runs


def format_data(runs, test_type):
    '''
    Format a test run into a similar format as the merged JSONs, for use in the
    pre-existing plotting script.

    Arguments:
    runs - type = list of dict. The test runs to be formatted.
    test_type - type = string. The type of test (IV, PT, etc.).
    '''
    formatted_runs = [] #initialize

    for run in runs:
        #if it's a module-level test
        if test_type == 'IV' or test_type == 'TC' or test_type == 'HVS':

            component_sn = [run["components"][n]["serialNumber"] for n in range(len(run["components"])) if "20USEM" in run["components"][n]["serialNumber"] or "20USBM" in run["components"][n]["serialNumber"] or "20USE3" in run["components"][n]["serialNumber"]][0] #module serial number
        else: #if it's a hybrid-level test
            component_sn = [run["components"][n]["serialNumber"] for n in range(len(run["components"])) if "20USEH" in run["components"][n]["serialNumber"] or "20USBH" in run["components"][n]["serialNumber"]][0] #hybrid serial number

        run["component"] = component_sn #put component serial number in run dict
        results          = {} #initialize

        for result_category in run["results"]:

            data_name          = result_category['code'] #name of the data category
            data               = result_category['value'] #data in that category
            results[data_name] = data #add it to a results dict


        run["results"] = results #add reformattd results to run dict

        itsdaq_info  = {} #initialize
        coldjig_info = {}
        ft_code      = None
        det_info     = {}

        for property_category in run["properties"]:
            #if test has itsdaq_test_info property
            if property_category["code"] == "itsdaq_test_info":
                itsdaq_info = property_category['value']
            #if test has ColdJig_History property
            elif property_category['code'] == 'ColdJig_History':
                coldjig_info = property_category['value']
            #if test has fit_type_code property
            elif property_category['code'] == 'fit_type_code':
                ft_code = property_category['value']
            #if test has det_info property
            elif property_category['code'] == 'det_info':
                det_info = property_category['value']

        run['properties']                     = {} #clear out the properties, reformat
        run['properties']['itsdaq_test_info'] = itsdaq_info
        run['properties']['ColdJig_History']  = coldjig_info
        run['properties']['fit_type_code']    = ft_code
        run['properties']['det_info']         = det_info
        formatted_runs.append(run)

    return formatted_runs

def fix_R2_hybrid_sn(test_run):
    '''
    The EndCap is... complicated. R2s have one physical hybrid, and therefore one
    hybrid in the database (20USEH4...). However, they have two HCCs, and therefore
    two logical hybrids (20USEH4..._H0 and 20USEH4..._H1). This function takes a test
    run and returns the logical hybrid associated with the test run, instead of the
    physical hybrid it's attached to in the DB.

    Arguments:
    test_run - type = dict. A database test run.

    Returns:
    hybrid_sn - type = string. The logical hybrid the test is associated with.
    '''
    for property in test_run["properties"]: #iterate through the test properties
        if property['code'] == 'det_info': #find the det_info property
            hybrid_sn = property['value']['name'] #get the logical hybrid SN

    return hybrid_sn


def get_valid_tests(test_runs):

    print(f"{BLUE}\nMultiple TC rounds found. Please provide some more information.{RESET}")
    institute = input("Institute code tests were run at (ie. UBC):")
    itsdaq_rn = input("ITSDAQ runNumber(s):")
    valid_runs = [run for run in test_runs if run['institution']['code'] == institute and itsdaq_rn in run['runNumber']] #filter out irrelevant tests

    return valid_runs
