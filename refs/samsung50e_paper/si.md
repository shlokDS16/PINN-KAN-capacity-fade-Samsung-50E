A multi-stage lithium-ion battery aging dataset using
various experimental design methodologies

Florian Stroebl1, Ronny Petersohn2, Barbara Schricker3, Florian Schaeufl1, Oliver
Bohlen1,*, and Herbert Palm1,*

1Institute for Sustainable Energy Systems (ISES), Munich University of Applied Sciences, Munich, 80335, Germany
2Hoppecke Systemtechnik GmbH, Advance Development, Zwickau, 08056, Germany
3Siemens AG, Technology, Erlangen, 91058, Germany
*Corresponding Author(s): H. Palm (palm@hm.edu), O. Bohlen (bohlen@hm.edu)

S.1 Supplemental

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

S.1.1 Semi-empirical aging models

Motivated by Muehlbauer et al.90, the total relative capacity loss of a lithium ion battery cell Qloss,rel is assumed to result from a

linear superposition of independent calendar aging Qcal

loss,rel and cycle aging Qcyc

loss,rel related losses according

Qloss,rel = Qcal

loss,rel + Qcyc

loss,rel ,

where the calendar aging aspect of the model can be described by

Qcal

loss,rel(T, SOC,t; ??? cal) = (1 ? EOLC) ·

and the cycle aging aspect by

(cid:16)
e?? cal

0 ·( 1

T ? 1

T ref )(cid:17)

(cid:19) 1
? cal
1

(cid:18) SOC
SOCref

·

(cid:19)? cal
2

,

(cid:18) t
tref

·

Qcyc

loss,rel(T, SOCmax,Cch,Cdch, DOD, FEC; ??? cyc) =

(1 ? EOLC) ·

(cid:18)
e

?? cyc
0 ?

(cid:16) 1
T ? 1
Tref

(cid:17)(cid:19)

(cid:18) SOCmax
SOCmax,ref

·

(cid:19) 1
cyc
?
1

(cid:19) 1
cyc
?
2

(cid:18) Cch
Cch,ref

·

(cid:18) Cdch
Cdch,ref

·

(cid:19) 1
cyc
?
3

(cid:18) DOD
DODref

·

(cid:19) 1
cyc
?
4

(cid:18) FEC
FECref

·

(S.1)

(S.2)

(S.3)

(cid:19)? cyc

5

.

Both aging submodels are describing the relative capacity loss Qloss,rel above a capacity end-of-life criterion EOLC, where

each aging factor is scaled by a reference value and associated to one parameter of a parameter vector ??? . The calendar aging

model depicts the Qcal

storage condition for t days by the parameter vector ??? cal = (? cal

loss,rel dependence on ambient storage temperature T and storage state of charge (SOC) during an open-loop
1 , ? cal

2 ). The cycle aging model describes the Qcyc

0 , ? cal

loss,rel

dependence on ambient temperature T , maximum state of charge during cycling SOCmax, the charge and discharge C-rates

Cch and Cdch with a cycle depth of discharge DOD along FEC fully equivalent cycles on capacity loss during cycling by its
corresponding parameter vector ??? cyc = (? cyc

). The relative capacity extracted from the i-th reference performance

, · · · , ? cyc

0

5

test (RPT) is always related to the initial capacity Q0 measured during the initial RPT ("Eingangstest" - ET):

Qrel,i =

Qi
Q0

References

(S.4)

90. Muehlbauer, M., Rang, F., Palm, H., Bohlen, O. & Danzer, M. A. Pareto-optimal power flow control in heterogeneous

battery energy storage systems. J. Energy Storage 48, 103803, https://doi.org/10.1016/j.est.2021.103803 (2022).

11

12

13

S2/S2


