# Thermal Cycling Plotting
Running `python3 make_TC_plots.py -d [DIRECTORY_PATH]` will produce a series of plots displaying the results of module thermal cycling, provided the following:
- The directory contains all the merged files from TC for a single module, including the enviromental summary file (refered to in the code as a ColdJigRun JSON), and the HVSTABILITY JSON.
- These merged files were produced by Cole Helling's merging script, found in the ch_SimplerMerging branch of ITSDAQ, in `contrib/itsdaq-merger`.

Plots produced include:
- All IV results throughout TC, and all breakdown voltages flagged by ITSDAQ.
- All Pedestal Trim values throughout TC, and mean Pedestal Trim values.
- All Strobe Delay results throughout TC, and mean Strobe Delay values. 
- All input noise, VT50, and gain values throughout TC, and mean input noise, VT50, and gain values for the 3-Point Gain and 10-Point Gain (Respose Curve).
- All Noise Occupancy values throughout TC, and mean Noise Occupancy values.
- All Open Channel Search values throughout TC, and a histogram of the number of open channels (as flagged by ITSDAQ) in each Open Channel Search.
- The High Voltage Stability current as a function of reading number.
- The dew point and humidity throughout TC.
- A results summary table, indicating which individual tests passed and failed, and whether they were taken warm or cold.

All plots are subsequently assembled into a single PDF. 

All plots which display all the results for a test throughout TC (except the IV plots) flag defect channels/chips with a triangle.

Additionally, terminal printout is produced which gives an overview of enviromental data (maximum and minimum temperature and humidity, etc.) and the cycling itself (number of tests, duration, run numbers, etc.), as well a summary of results (what percent of warm and cold tests failed for each test type), and a list of all failed tests. 

However, a user may only be interested in the results for some of the tests. If this is the case, they can use the `-t` argument, with the test acronyms they are interested in as a space-seperated list. Options are: IV, SD, PT, 3PG, 10PG, NO, OCS, HVS, and TC. TC produces the results summary and enviromental summary plots, as well as the aforementioned terminal printout. Not specifying this argument will cause all plots to be produced.

Additionally, the `-n` argument can be used if the user only wants the noise plots created for the 3- and/or 10-Point Gain, and not the gain or VT50 plots.

Finally, the `-hg` argument produces two histograms per stream, depicting the number of defects throughout all of thermal cycling per chip (colour-coded by associated test type), and the number of defects by defect type, respectively.

# Notes
- `make_TC_plots.py` is the main script. `IV.py`, `SD.py`, `PT.py`, `RC.py`, `NO.py`, `OCS.py`, `HVS.py`, `TC.py`, and `common_functions.py` contain function definitions for plotting their corresponding tests (except `common_functions.py`, which contains functions used in the plotting of multiple tests, or in `make_TC_plots.py` directly).
-  The TC results summary table will flag a test as failed if it failed for any hybrid on the module.

## Future Work
- Removing unnecessary duplication, and general code tidy-up.
- Aesthetic matters, particularly for the TC results summary table.
- A `--colour-blind` flag or similar that changes the colour scheme of certain plots to be more friendly to the red/green colour-blind. 
- Some histograms that display number of defects by defect type, particularly for the 10-Point Gain.

## Contact
For any questions, comments, or concerns, please email Madison Levagood at madisonlevagood@gmail.com, or reach out via Mattermost at @mlevagoo. You're welcome to contact me at any time convenient for you, however, I'm in the PST (GMT-8) timezone, and inquiries recieved during the night, or when I am in class, may recieve delayed responses. Apologies for the inconvenience. 
