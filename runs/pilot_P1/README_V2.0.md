Description of ISU-ILCC Battery Aging Dataset

1.  General Information

1.1. Data title: ISU-ILCC Battery Aging Dataset

1.2. Authors

?  Tingkai Li

Iowa State University (Present Affiliation: University of Connecticut)

ORCID: 0000-0003-1934-1000

Emails: tkl@iastate.edu; tingkai.li@uconn.edu

?  Jinqiang Liu

Iowa State University

ORCID: 0000-0002-1106-6473

Email: jinqiang@iastate.edu

?  Adam Thelen

Iowa State University

ORCID: 0000-0001-5443-3678

Email: acthelen@iastate.edu

?  Chad Tischer

Iowa Lakes Community College

Email: ctischer@iowalakes.edu

?  Chao Hu (Corresponding author)

Iowa State University (Present Affiliation: University of Connecticut)

ORCID: 0000-0001-9228-7675

Emails: chaohu@iastate.edu; chao.hu@uconn.edu

1.3. Associated publication:

Predicting Battery Lifetime Under Varying Usage Conditions from Early Aging Data

(The preprint is available on arXiv at: https://doi.org/10.48550/arXiv.2307.08382)

1

2.  Dataset Overview

The ISU-ILCC battery aging dataset was collected jointly by the System Reliability and Safety

Laboratory  at  Iowa  State  University  (ISU),  now  the  Reliability  Engineering  and  Informatics

Laboratory (REIL) at the University of Connecticut, and Iowa Lakes Community College (ILCC).

The dataset is designed to study the dependency of battery capacity fade from three stress factors:

charge rate, discharge rate, and depth of discharge. The dataset contains cycle aging data from 251

lithium-ion  (Li-ion)  polymer  cells  (also  called  lithium  polymer  cells)  cycled  under  63  unique

conditions.

Figure 1: Summary of test conditions and sequence.

3.  Experiment Design

3.1. Cell specification

The battery cells used in this aging test campaign are 502030 Li-ion polymer cells manufactured

by Shenzhen Honghaosheng Electronics Co., Ltd. in Shenzhen, China. These cells have lithium

nickel manganese cobalt oxide (NMC) as the cathode active material and graphite as the anode

active material. The rated capacity is 250 mAh, and the operating voltage window is between 3.0

V and 4.2 V.

3.2. Test equipment

The cells were cycle-aged using two 64-channel Neware BTS-4000 battery cyclers, one located at

ISU and the other one at ILCC. Cells’ terminals were clipped to individual cell holders and placed

inside two Thermo Scientific™ incubators set at a constant temperature of 30 °C. Figure 2 shows

the equipment setup at ILCC, which is also similar to the one at ISU.

2

Figure 2: Equipment setup at ILCC.

3.3. Regular cycling test

The  regular  cycling  test  was  designed  with  three  varying  stress  factors:  charging  C-rate,

discharging  C-rate,  and  depths  of  discharge  (DoD).  One  charge/discharge  cycle  consisted  of  a

constant-current/constant-voltage (CC/CV) charging step and a constant-voltage discharging step.

The depths of discharge for different groups were determined by estimating the voltage cutoffs

during the CC discharging step. The cycling profiles are shown in Figure 3.

Figure 3: Charge and discharge profiles for the cycling test.

3.4.Reference performance test

3

64-channel Neware BTS 4000 cyclerThermoScientific™HERATHERM incubatorRack for individual cell holders

A reference performance test (RPT) was periodically run on every cell to measure the full discharge

capacity and collect data for lifetime prediction. Using an RPT to check cell capacity is important

for measuring the full capacity of cells cycled with partial DoDs. During the RPT, two full cycles

of CC/CV charging and CC discharging at different cycling rates were performed, one at C/5 and

the other at C/2. The RPT discharge capacity at C/5 is used in generating capacity fade plots. The

voltage-capacity data from a complete C/5 discharge cycle are used for feature extraction lifetime

prediction. Additionally, for groups 30–64, we added a cycle with pulse tests at different SoC levels

to obtain the DC internal resistances. The RPT profiles are shown in Figure 4.

The RPT is performed after 7 days of cycling. Groups 20 through 64 have an additional RPT after

the first 3.5 days of cycling (i.e., after the first half week of cycling) to better capture the initial

capacity fade.

Figure 4: Charge and discharge profiles for the RPT.

3.5. Cell ID

Each cell was assigned a unique identifier (i.e., cell ID) that consisted of the cell’s group number

and the cell’s index within the group. For example. G3C1 is the first cell in group three.

4.  Data Structure

In the published dataset, each cell has two separate data files, one for the RPT data and the other

for the cycling data. All data files are processed using Python and saved in JSON format. Files are

named by the cell ID. To convert the data to Python dictionaries, a sample code has been provided

with this dataset (“load_data.py”).

4

* The 0.5-week RPT is only for groups 20–64.

Notation

Description

Unit

Capacity_discharge

Total  Capacity  discharged  or  charged  of  a

Ah

Capacity_charge

specific cycle.

start_stop_time (RPT)  Start  and  stop  time  of  a  specific  RPT.

YYYY-MM-DD

(For calculating time on test)

hh:mm:ss

start_stop_time

Start and stop time of a specific week’s cycling.

YYYY-MM-DD

(Cycling)

(For calculating time on test)

hh:mm:ss

time_series_charge

The  start  and  stop  times  of  each  cycle’s

YYYY-MM-DD

time_series_discharge

charging and discharging steps.

hh:mm:ss

Q

V

I

E

t

Charge recordings during a specific cycle.

Ah

Voltage recordings during a specific cycle.

Current recordings during a specific cycle.

V

A

Energy recordings during a specific cycle.

Wh

Time  stamps  of  recordings  during  a  specific

YYYY-MM-DD

cycle

hh:mm:ss

4.1. File directory

1.  RPT_json [folder] – Raw data

1.1. G1C1.json … G64C4.json – RPT data for each cell in JSON format.

2.  Cycling_json [folder] – Raw data

2.1. G1C1.json … G64C4.json – Cycling data for each cell in JSON format.

3.  Q_interpolated [folder] – Processed data

3.1. G1C1.csv  …  G64C4.csv  –  Interpolated  Q  data  with  respect  to  a  voltage  vector

containing 1000 elements equally spaced between 3V and 4.2V. Each column contains

the Q reading from one RPT.

4.  capacity_fade [folder] – Processed data

4.1. G1C1.csv … G64C4.csv – Two-column tabular data for capacity fade curves of each

cell.  The  first  column  is  the  time  on  test,  and  the  second  column  is  the  remaining

capacity.

5

5.  Valid_cells.csv – CSV file contains the Cell ID for all the cells published in the current

release.

6.  process_data.py – A sample code containing functions converting the RPT and the cycling

JSON files to Python dictionaries. Also, this sample code provided processing functions to

obtain the data for interpolated Q-V curves and capacity fade curves.

This code is developed in the following environment:

?  python: 3.7.13 (Version 3.9.9 is compatible with packages below)

?  pandas: 1.3.5

?  scipy: 1.7.3

?  numpy: 1.21.5

Note: An interpolation warning is triggered on line 164 for several cells when the assigned

smoothing factor ("precision_C_5") is too low. Without intervention, this would result in

an array of NaN for the  variable "tck". To  resolve this problem,  lines 165-167 loops to

correct the smoothing factor until the variable "tck" is no longer an array of NaN to ensure

correct output. Therefore, you may ignore the warning.

6

4.2. Structure of RPT data

7

G1C1.jsoncapacity_discharge_C_5capacity_charge_C_5Week 0Week 0.5*Week 1Week 2…Python dictionaryPython listNumpyarraycapacity_discharge_C_2capacity_discharge_C_2QV_discharge_C_5Q00.5*12…V00.5*12…E00.5*12…I00.5*12…t00.5*12…QV_charge_C_5Same structure as QV_discharge_C_5QV_discharge_C_2Same structure as QV_discharge_C_5QV_charge_C_2Same structure as QV_discharge_C_5start_stop_timestartstopWeek 0Week 0.5*Week 1Week 2…Week 0Week 0.5*Week 1Week 2…Week 0Week 0.5*Week 1Week 2…Week 0Week 0.5*Week 1Week 2…Week 0Week 0.5*Week 1Week 2…

4.3. Structure of cycling data

8

G1C1.jsoncapacity_dischargecapacity_chargeCycle 1Cycle 2Cycle 3Cycle 4…Python dictionaryPython listNumpyarrayQV_dischargeQ1234…QV_chargeSame structure as QV_dischargestartstopCycle 1Cycle 2Cycle 3Cycle 4…V1234…E1234…I1234…t1234…start_stop_timestartstoptime_series_dischargeCycle 1Cycle 2Cycle 3Cycle 4…Cycle 1Cycle 2Cycle 3Cycle 4…time_series_chargeSame structure as time_series_dischargeWeek 0.5*Week 2Week 3…Week 1Week 0.5*Week 2Week 3…Week 1

5.  Acknowledgment

The authors of this ISU-ILCC battery aging dataset acknowledge the support of Iowa Economic

Development Authority under the Iowa Energy Center Grant No. 20-IEC-018. The authors also

acknowledge the meaningful discussion on this dataset with Dr. David Howey and Zihao Zhou

from University of Oxford.

6.  License

This work is licensed under the Creative Commons Attribution (CC-BY) 4.0 International License.

For more information visit: https://creativecommons.org/licenses/by/4.0. Please cite the associated

7.  Update for This Release

•  The dataset of 251 cells is fully released.

•  Table A1 is revised to include cycling conditions for G11.

9

Appendix

A1.  Cycling conditions

Group #
1
2
3
4
5
6
7
8
9
10
11
12
13
14
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31
32
33
34
35
36
37
38
39
40
41

Charging C-rate
0.500
0.500
0.500
1.000
1.000
2.000
2.000
2.000
2.000
2.500
2.500
3.000
3.000
3.000
0.500
1.000
2.500
2.500
0.800
1.200
1.400
1.600
1.800
1.800
1.400
0.600
2.400
1.600
0.800
1.200
1.000
2.000
2.200
1.825
2.075
0.725
1.875
1.475
1.825
2.075

Discharging C-rate
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.500
0.600
2.200
2.400
1.600
1.800
0.800
1.000
1.400
1.200
2.000
0.500
0.500
0.500
0.500
0.500
1.025
1.775

10

Mean DoD
25.90%
46.11%
67.77%
47.27%
97.54%
27.23%
46.86%
67.24%
96.93%
47.21%
95.98%
28.60%
47.26%
66.32%
97.62%
67.53%
27.53%
65.70%
98.16%
97.98%
97.88%
97.61%
97.51%
51.43%
4.16%
57.85%
80.99%
52.48%
77.59%
61.43%
38.86%
40.65%
27.60%
97.02%
97.06%
98.08%
95.83%
97.14%
31.94%
67.02%

Group #
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64

Charging C-rate
0.725
1.875
0.775
1.125
1.225
2.325
2.375
0.975
2.425
2.275
1.425
2.025
0.925
1.025
2.175
1.775
2.475
1.325
0.675
2.125
1.575
1.975
1.175

Discharging C-rate
2.375
2.325
1.275
1.725
2.025
1.925
2.225
0.675
1.625
1.875
0.875
0.825
1.125
2.475
0.975
1.175
0.575
1.825
1.325
1.975
2.425
1.675
1.425

Mean DoD
36.32%
38.00%
37.12%
80.26%
75.36%
48.27%
58.57%
18.82%
20.10%
53.64%
83.55%
91.54%
27.05%
61.44%
53.81%
17.42%
42.03%
31.64%
83.63%
54.07%
64.19%
80.57%
91.44%

A2.  Notes for known abnormalities

•  For groups 20–29, we have unrecoverable data loss for the 4th week’s RPTs. During the

data processing, all of the data was replaced by empty Python lists.

•  For cells G25C1, G26C1, G26C2, G26C3, and G26C4, we have unrecoverable data loss

for the 23rd and 24th weeks’ RPTs, and the 24th week’s cycling tests.

11


