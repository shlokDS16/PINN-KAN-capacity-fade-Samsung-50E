Contents lists available at ScienceDirect

Mechanical Systems and Signal Processing

journal homepage: www.elsevier.com/locate/ymssp

Battery health management using physics-informed machine
learning: Online degradation modeling and remaining useful
life prediction

Junchuan Shi, Alexis Rivera, Dazhong Wu *

Department of Mechanical and Aerospace Engineering, University of Central Florida, Orlando, FL 32816, USA

A R T I C L E  I N F O

A B S T R A C T

Communicated by Dong Wang

Keywords:
Physics-informed machine learning
Remaining useful life
Lithium-ion battery
Degradation

Lithium-ion batteries have been extensively used to power portable electronics, electric vehicles,
and unmanned aerial vehicles over the past decade. Aging decreases the capacity of Lithium-ion
batteries. Therefore, accurate remaining useful life (RUL) prediction is critical to the reliability,
safety, and efficiency of the Lithium-ion battery-powered systems. However, battery aging is a
complex electrochemical process affected by internal aging mechanisms and operating conditions
(e.g.,  cycle  time,  environmental  temperature,  and  loading  condition).  In  this  paper,  a  physics-
informed machine learning method is proposed to model the degradation trend and predict the
RUL of Lithium-ion batteries while accounting for battery health and operating conditions. The
proposed physics-informed long short-term memory (PI-LSTM) model combines a physics-based
calendar  and  cycle  aging  (CCA)  model  with  an  LSTM  layer.  The  CCA  model  measures  the
aging effect  of  Lithium-ion batteries  by  combining  five  operating  stress  factor  models.  The PI-
LSTM uses an LSTM layer to learn the relationship between the degradation trend determined
by the CCA model and the online monitoring data of different cycles (i.e., voltage, current, and
cell temperature). After the degradation pattern of a battery is estimated by the PI-LSTM model,
another  LSTM  model  is  then  used  to  predict  the  future  degradation  and  remaining  useful  life
(RUL) of the battery by learning the degradation trend estimated by the PI-LSTM model. Moni-
toring  data  of  eleven  Lithium-ion  batteries  under  different  operating  conditions  was  used  to
demonstrate the proposed method. Experimental results have shown that the proposed method
can accurately model the degradation behavior as well as predict the RUL of Lithium-ion batteries
under different operating conditions.

1. Introduction

Lithium-ion batteries have a wide range of applications in defense, aerospace, automotive, communication, and consumer elec-
tronics due to their lightweight, high-energy density, high galvanic potential, and long lifetime compared to other battery technologies
[1,2]. However, cyclic and calendar aging are two aging mechanisms that lead to the degradation of battery capacity (capacity fade).
Cyclic aging causes batteries to degrade over repeated charge and discharge cycles. Calendar aging causes batteries to degrade over
time regardless of the number of charge and discharge cycles. One of the challenges associated with Li-ion batteries is that they reach

* Corresponding author.

E-mail address: dazhong.wu@ucf.edu (D. Wu).

https://doi.org/10.1016/j.ymssp.2022.109347
Received 6 January 2022; Received in revised form 16 May 2022; Accepted 20 May 2022

MechanicalSystemsandSignalProcessing179(2022)109347Availableonline1June20220888-3270/©2022ElsevierLtd.Allrightsreserved.J. Shi et al.

their end-of-life (EOL) earlier than expected due to battery degradation [3–5]. Therefore, battery health monitoring (BHM) systems are
crucial to the safety and reliability of lithium-ion batteries [6].

Calendar aging is caused by internal aging mechanisms such as loss of lithium inventory, anode damage, and Lithium plating, while
cyclic aging is caused by aging mechanisms such as passivation layers and electrolyte oxidation [7,8]. The long-term performance and
health states of a battery can be represented by the capacity fade [9]. Moreover, the capacity fade is also highly correlated to the short-
term performance of batteries such as state-of-charge (SOC) and end-of-discharge time (EOD) [10]. Therefore, accurate degradation
modeling and capacity fade estimation are critical to BHM systems. The capacity fade of lithium-ion batteries can be estimated using
various approaches reported in recent literature. Physics-based methods such as Ah counting [11] and coulomb counting [12] are the
most commonly used methods for capacity estimation. Kalman filtering methods such as joint extended Kalman filter [13] and un-
scented Kalman filter [14] are also widely used to estimate the SOC and capacity fade of lithium-ion batteries. More recently, new
methods such as particle filtering [15,16] and machine learning/deep learning [17,18] are extensively used for capacity fade modeling
of lithium-ion batteries. However, little work has been reported when modeling the battery degradation with respect to both calendar
aging and cyclic aging using the following operating conditions: cycle time, rest time, environmental temperature, SOC level, and
loading condition. Furthermore, the calendar and cyclic aging rates vary throughout the life cycle of a battery, which is not well
studied when building the physics-based model of operating conditions.

The remaining useful life (RUL) of a lithium-ion battery is the number of charge–discharge cycles that remain before the capacity
fade reaches the end-of-life (EOL) threshold, typically in the range of 70% to 80% of its initial rated capacity [19,20]. In order to
maintain the safe operation of electronic systems, lithium-ion batteries need to be replaced before the RUL drops to zero [8,20].
Accurate prediction of RUL is critical to ensure the safety and reliability of lithium-ion batteries and help decision-makers develop
efficient maintenance schedules for electronic systems. The RUL of lithium-ion batteries can be predicted using physics-based and data-
driven approaches. Physics-based methods such as electrochemical models determine capacity fade as well as predict the RUL based on
electrochemical  reactions  in  batteries.  However,  there  is  a  trade-off  between  prediction  accuracy  and  model  complexity  [21].
Compared to physics-based methods, data-driven methods do not require complex mathematical models and can be used when large
battery health monitoring data is available. Data-driven methods extract correlations and patterns from battery health monitoring data
to model capacity fade and predict RUL without the need to consider electrochemical reactions and failure mechanisms within a
lithium-ion battery [22]. However, the accuracy of online RUL prediction for batteries under different operating conditions may suffer
because: (i) Some methods update the model with each cycle using the actual degradation value and providing capacity estimation for
the next cycle, which is not considered online RUL prediction. (ii) Other methods make predictions by learning the degradation trend
from actual capacity fade of the past. However, the capacity fade of past cycles (ground truth) may not be available in real world
applications.

This  paper  introduces  a  physics-informed  machine  learning  framework  to  address  the  aforementioned  issues  of  degradation
modeling and RUL prediction. A physics-informed long short-term memory (PI-LSTM) model was constructed by combining a physics-
based calendar and cycle aging (CCA) model and a long short-term memory (LSTM) layer for degradation modeling. The CCA model
can calculate the calendar aging and cyclic aging by combining operating stress factors such as cycle time, rest time, environmental
temperature, SOC level, and loading condition. However, the capacity fade per cycle is significantly higher during the early and end
cycle stages. Therefore, the PI-LSTM model uses an LSTM layer to learn the relationship between the CCA degradation model and the
actual degradation rate throughout the  life of the  battery  using monitoring  data. The PI-LSTM model can accurately capture  the
degradation trend of Li-ion batteries by considering battery health and operating conditions.

As the actual capacity fade of each discharge cycle is not always available in real world applications, the capacity fade estimated by
the proposed PI-LSTM model will be used for RUL prediction. After the capacity fade of each cycle is estimated by the PI-LSTM model
using operating stress factors and a portion of the monitoring data, a separate LSTM model is used to learn the degradation trend and
predict the capacity fade of future cycles. Online RUL prediction can be achieved by counting the number of cycles until the estimated
capacity fade reaches the EOL threshold.

The remainder of this paper is structured as follows: A literature review on lithium-ion battery capacity fade estimation and RUL
prediction is presented in Section 2. Section 3 presents the details of the models proposed in this work. Section 4 demonstrates the
proposed method through a case study. Section 5 presents the conclusion of this study.

2. Related work

2.1. Physics-based methods

Currently, model-based and data-driven techniques are used for battery degradation modeling and RUL prediction. Lui et al. [23]
proposed a physics-based approach to predict the capacity and RUL of implantable-grade lithium-ion battery cells by modeling the
degradation mechanisms such as loss of active materials from the electrodes and the loss of lithium inventory. The half-cell model was
used to  extract degradation parameters  from voltage  and  capacity measurements. The  results have  shown that the  physics-based
approach  can  achieve  higher  accuracy  in  the  lifetime  prediction  of  lithium-ion  batteries  than  the  traditional  capacity-based
approach. Dong et al. [24] proposed a physics-based model that couples chemical and mechanical degradation mechanisms to pre-
dict the capacity fade during cycling and storage. The model can predict the capacity fade by modeling the formation and growth of the
solid-electrolyte interphase (SEI). Compared to experimental results, the model achieved less than 5% RMSE for capacity fade pre-
diction and can be applied to RUL prediction for battery management systems. Downey et al. [19] developed a physics-based approach
to achieve lithium-ion battery RUL prediction using a non-linear least squares (NLLS) method with dynamic bounds. This method can

MechanicalSystemsandSignalProcessing179(2022)1093472J. Shi et al.

estimate the battery capacity using the half-cell model and capture the degradation trend of the following parameters: loss of active
materials from the positive electrode, loss of active material from the negative electrode, and the loss of lithium inventory. The NLLS
method outperformed the classical capacity-based approach in 97.5% of the test cases. Baghdadi et al. [25] proposed a physics-based
method based on Dakin’s degradation approach to model the linear degradation of batteries. The aging rate of a battery was expressed
using Eyring’s law. Their model can represent the capacity fade and resistance increase using discharge time and temperature.

Existing physics-based models can represent the degradation behavior of batteries by developing governing equations using aging
factors  such  as  discharge  time  and  temperature.  However,  these  models  are  not  able  to  capture  the  change  of  degradation  rates
throughout the life of the battery. Moreover, these models are not able to predict the RUL of batteries because these models cannot
predict capacity fade without data from future cycles.

2.2. Data-driven methods

Miao et al. [15] developed an unscented particle filtering method to predict the RUL of lithium-ion batteries. The results have
shown  that  this  particle  filter-based  method  that  combines  particle  filtering  and  unscented  Kalman  filter  can  predict  the  RUL  of
lithium-ion  batteries  with  less  than  5%  error.  Sun  et  al.  [26]  developed  an  integrated  battery  health  indicator  by  incorporating
capacitance, resistance, and constant current charge time (CCCT) to represent SOH. RUL prediction based on the integrated SOH was
accomplished by combing a three-order polynomial model and a particle filter algorithm. Wei et al. [27] proposed a method that
combined support vector regression (SVR) with a particle filter to predict the RUL of lithium-ion batteries. The battery aging behavior
was predicted using SVR and the impedance degradation parameters by particle filter. Compared to an artificial neural network (ANN),
the results have shown that the SVR and particle filter combination can predict battery capacity with smaller root mean square error
(RMSE) and predict the RUL with high estimation accuracy. Ren et al. [28] developed a method called Auto-CNN-LSTM, which utilizes
an autoencoder to augment the dimensions of data to effectively train a convolutional neural network (CNN) and LSTM to predict the
RUL of lithium-ion batteries. The RUL predictions were smoothed using a first-order filter and the model achieved a root mean square
error (RMSE) of 4.8%. The Auto-CNN-LSTM significantly outperformed support vector machine (SVM) and autoencoder deep neural
network (ADNN) which achieved an RMSE of 18.2% and 11.8%, respectively.

While existing data-driven methods can predict the RUL of batteries using the actual degradation or the estimated degradation
trend, few methods can achieve online RUL prediction with sufficient accuracy using online monitoring data. Moreover, online RUL
prediction under different operating conditions remains a challenge as the degradation trends learned from one training dataset is
usually not generalizable to different operating conditions.

3. Methodology

The proposed method consists of two parts: degradation modeling using a PI-LSTM model and online RUL prediction using an LSTM
model. For degradation modeling, the PI-LSTM model can estimate the capacity fade of a battery using operating conditions and a
portion of monitoring data. The degradation of future cycles is then predicted using the LSTM model by learning the degradation trend
and capacity fade from the PI-LSTM model.

During degradation modeling, the aging rate of a battery is usually modeled by estimating the discharge capacity of each cycle. The
discharge capacity is affected by two kinds of factors: (1) battery health condition and (2) operating conditions [29,30]. Therefore, the
proposed PI-LSTM model is composed of two models: (1) A physics-based CCA model that captures the degradation of a battery while
accounting for cycle time, rest time, environmental temperature, SOC level, and loading condition as the operating conditions and (2)

Fig. 1. The framework of the physics-informed LSTM method.

MechanicalSystemsandSignalProcessing179(2022)1093473J. Shi et al.

an LSTM model that predicts the impact of battery health condition on the degradation modeled by the CCA model.

Fig.  1  illustrates  the  overall  framework  of  the  proposed  method  including  (1)  training  the  PI-LSTM  degradation  model  using
training data, (2) modeling the degradation trend of testing batteries using the PI-LSTM model, and (3) online RUL prediction for
future cycles of testing batteries using a separate LSTM model. The training process of the PI-LSTM degradation model consists of two
stages:  the  linear  stage  (CCA)  and  the  non-linear  stage  (PI-LSTM).  The  CCA  model  is  formulated  with  a  series  of  semi-empirical
equations for five operating stress factors. The coefficient of each operating stress factor is determined using one battery from the
training set. The formulated CCA model is then used to calculate the degradation trends of the remaining batteries of the training set
using their respective operating stress factors. During the non-linear degradation stage, the LSTM layer in the PI-LSTM model learns the
relationship between the degradation trend determined by the CCA model and the monitoring data of different cycles. The PI-LSTM
model  can  learn  the  cumulative  aging  effect  sequentially  from  each  cycle  of  the  training  batteries.  During  the  testing  process  of
degradation modeling, the degradation trend of each test battery is modeled using the PI-LSTM model by predicting the discharge
capacity of each discharge cycle. An LSTM model is then used during the RUL prediction process to learn the degradation patterns and
trends  from  the  discharge  capacity  estimated  by  the  PI-LSTM  model  and  predict  the  capacity  fade  of  future  cycles.  The  RUL  is
determined by counting the number of cycles until the discharge capacity drops below the EOL threshold.

The remainder of this section is organized as follows: Section 3.1 presents the details on modeling the linear degradation of bat-
teries using the CCA model. Section 3.2 presents the details on modeling the non-linear degradation of batteries using the PI-LSTM
model. Section 3.3 presents the details on learning the degradation patterns and predicting RUL using the LSTM model.

3.1. Calendar and cycle aging-based model of linear degradation

The CCA model represents the aging behavior of batteries in terms of the impact of time (calendar aging) and cycling parameters
(cycle aging) [30–32]. In this work, the CCA model proposed by Xu et al. [32] (Eq. (1) to Eq. (5)) was adopted to quantify the linear
portion of the battery degradation behavior.

Calendar aging comprises the inherent aging processes that lead to a capacity degradation of a battery cell. Calendar aging is mainly
caused by lithium migration over time, which is independent of charge–discharge cycling. The rate of calendar aging is affected by the
average temperature and the average state-of-charge (SOC) of the battery. Therefore, calendar aging Lcal  can be expressed as:

Lcal = ft(t, ?, Tc)

(1)

where ft  is a function of time t, average SOC ?, and average temperature Tc.

Unlike calendar aging, cycle aging is the life lost due to the usage of each charge–discharge cycle. The discharge capacity fade of the
ith  cycle represents the cycle aging and is affected by the average SOC (?i), the average environment temperature (Tc,i), the average C-
rate (C), and the rest time factor (FRest). The C-rate, which is used to indicate the load stress in this study, is defined as the actual current
draw of a battery divided by the theoretical current draw to discharge the battery with one hour [33]. As the accumulated degradation
is the sum of the capacity fade of each cycle. The total cycle aging Lcyc  of N cycles can be expressed as:

Lcyc =

?N

(

fc

i

?i, T c,i, Ci, FRest,i

)

(2)

where fc  is a function of average SOC ?i, average temperature Tc,i, average C-rate Ci, and rest time factor FRest,i  of the ith cycle.

By combining Eq. (1) and Eq. (2), the CCA model can represent the degradation of batteries caused by both the inherent aging
process and the usage of each cycle. The total capacity fade fd  of N cycles can be written as the sum of calendar aging Lcal  and cycle
aging Lcyc, as shown in Eq. (3):

fd(t, ?, T, C, FRest) = ft(t, ?, Tc) +

(
?i, T c,i, Ci, FRest,i

)

fc

?N

i

(3)

When calculating the capacity fade of each cycle, the average temperature and average SOC of calendar aging are the same as the
average  temperature  and  average  SOC  of  cycle  aging.  The  time  t  in  calendar  aging  then  equals  to  the  duration  of  each  cycle  tc.
Therefore, the capacity fade of one cycle f cyc

d  can be simplified as:

f cyc
d (t, ?, Tc, C, FRest) = ft(tc, ?, Tc) + fc(?, Tc, C, FRest)

(4)

When the battery is operating under the same condition for each cycle, the capacity fade of each cycle f cyc

constant. The total capacity fade f Linear
shown in Eq. (5):

d

can be expressed using the capacity fade of each cycle f cyc

d

d  can be considered as
times the number of cycles N, as

f Linear
d

(t, ?, Tc, C, FRest) = N • (ft(tc, ?, Tc) + fc(?, Tc, C, FRest))

(5)

Eq. (5) is the linear CCA model by assuming that the degradation of batteries is not affected by the battery health condition.
Therefore, the linearized capacity fade modeled by the CCA model only depends on the operating conditions which include cycle time,
rest time, environmental temperature, SOC level, and C-rate.

It has been well studied that environmental temperature is an operating stress factor that positively affects battery degradation

MechanicalSystemsandSignalProcessing179(2022)1093474J. Shi et al.

[34–36]. C-rate is also shown to have positive effects on battery degradation because it is correlated with environmental temperature
[36–38]. Higher environmental temperature and C-rate will accelerate the rate of battery degradation. Therefore, the calendar aging
model ft  and cycle aging model fc  can be represented using the following equations:

ft(tc, ?, Tc) = St,?(t, ?) • ST (Tc)

fc(?, Tc, C, FRest) = S?,F(?, FRest) • SC(C) • ST (Tc)

(6)

(7)

where ST  and SC  are the proposed temperature stress model and C-rate stress model that have positive relationships with battery
degradation rate. The St,?  and S?,F  are mixed models of operating stress factors whose relationships with battery degradation rate are
not clearly explained [31] such as SOC, cycle time and rest time ratio. As described previously, calendar aging ft  measures the aging
process according to time. This aging process will be accelerated with a higher average SOC [29,36]. Therefore, the St,?  and S?,F can be
further divided into two accelerating factors, the time stress model St  and the SOC stress model S?. The impact of rest time on battery
aging is also investigated by adding the rest time ratio stress model SR. The calendar aging ft  and cycle aging fc  are finally represented
using the following stress models:

ft(tc, ?, Tc) = St(t) • S?(?) • ST (Tc)

fc(?, Tc, C, FRest) = SC(C) • SR(FRest) • S?(?) • ST (Tc)

(8)

(9)

where St  is the time stress model, S?  is the SOC stress model, ST  is the temperature stress model, SC  is the C-rate stress model and SR  is
the rest time ratio stress model.

3.1.1. Temperature stress model

The degradation rate of Li-ion batteries will change when the environmental temperature is higher or lower than the reference
temperature  (room  temperature).  The  temperature  stress  model  quantifies  the  effect  of  environmental  temperature  on  battery
degradation. Eq. (10) [34] is used in this work as the temperature stress model to measure the change in degradation rate when
operating at environmental temperatures higher or lower than the reference temperature:

ST (T) = eKT(T?Tref )Tref

T

(10)

where KT  is the coefficient of the temperature stress model that needs to be determined and Tref  is the reference temperature (room
temperature) of the batteries. Assuming that we have the calendar aging of cycles at temperature  TA  and cycles at the reference
temperature Tref , the degradation rate contributed by the calendar aging model ft  of the two temperatures can be modeled as:

ST (TA) =

ft[T=TA]
ft[T=Tref ]

(11)

Once  the  ST(TA) for  the  battery  under  temperature  TA  is  determined,  the  temperature  coefficient  KT  can  be  determined  by

substituting the average value of ST(TA) back into Eq. (10).

The degradation of batteries will increase under low environmental temperature, especially when the temperature is lower than
?
C [39]. This accelerated aging phenomenon is caused by the reacting of lithium ions and electrolytes [29]. The performance of
15
batteries will decrease under low temperatures due to impedance rise [40–42]. Therefore, the actual impact of temperature on battery
aging is not strictly linearly correlated as shown in Eq. (11). The non-linear relationship between temperature and degradation will be
modeled by the PI-LSTM model, which will be described in section 3.2.

3.1.2. State-of-charge stress model

The SOC stress model quantifies the effect of SOC on battery degradation. The SOC stress model proposed by Millner [36] is used in

this paper. This model is similar to the temperature stress model:

S?(?) = eK?(???ref )

(12)

where K?  is the coefficient of the SOC stress model, which needs to be determined, and ?ref  is the reference SOC level, which is usually
set between 0.4 and 0.5 [36]. Assuming that we have the calendar aging of cycles at SOC level ?A and cycles at the reference SOC level
?ref , the degradation rate contributed by the calendar aging model ft  of the two SOC levels can be determined using:

S?(?A) =

ft[?=?A]
ft[?=?ref ]

(13)

Once the S?(?A) for battery under SOC level ?A  is determined, the SOC coefficient K?  can be determined by applying the average

value of S?(?A) back into Eq. (12).

The SOC stress model (Eq. (12)) we adopt in this work assumes that the decrement of the degradation rate is linearly correlated to
the decrement of the SOC level. However, while the SOC level is very low, the degradation rate does not decrease linearly. This is

MechanicalSystemsandSignalProcessing179(2022)1093475J. Shi et al.

because the low SOC level increases the impedance and power fading rapidly [43,44]. The non-linear relationship between SOC and
degradation will be modeled by the PI-LSTM model.

3.1.3. Time stress model

The time stress model quantifies the effect of time on battery degradation. As life-dependence factors are isolated from the calendar

aging, the remaining of the calendar aging ft  is the time stress model, which can be modeled as a linear function of time t:

St(t) = Kt • t

(14)

where Kt is the coefficient of the time stress model that needs to be fitted. As the SOC coefficient K?  and temperature coefficient KT have
been determined, the time coefficient Kt  can be determined using the calendar aging ft:

Kt =

ft[T=TA,?=?A]
tST (TA)S?(?A)

(15)

where ft[T=TA,?=?A] is the linearized calendar aging model determined under temperature TA and SOC level ?A, and t denotes the elapsed
time of this period.

3.1.4. Rest time stress model

Rest time, usually defined as the time between a charge cycle and the following discharge cycle, will also impact the degradation
rate of lithium-ion batteries. It has been shown that a shorter rest time will increase the degradation rate [45]. To model the impact of
rest time on battery degradation, we used the rest time factor FRest  which normalizes the rest time by dividing the rest time over the
duration of the charge–discharge cycle. The negative correlation between rest time and the degradation rate can be modeled using:

SR(FRest) = eKR(1?FRest )

(16)

where KR  is the coefficient of the rest time stress model that needs to be fitted using experimental data and FRest  is the rest time factor
measured using:

FRest =

TR
TO

(17)

where TR  is the duration of rest time and TO is the overall duration of the entire cycle. Assuming that we have the cycle aging of cycles
with rest time FA  and cycles without rest, the degradation rate contributed by the cycle aging model fc  of the two rest times can be
determined using:

SR(FA) =

fc[Frest =FA]
fc[Frest =0]

(18)

Once the SR(FA) for battery with rest time FA  is determined, the rest time coefficient KR  can be determined by applying the average

value of SR(FA) back into Eq. (16).

3.1.5. C-rate stress model

A few studies have found strong collinearity between battery degradation and load conditions [46]. It has been shown that a larger
load will result in an increase in the degradation rate of the battery [46–48]. C-rate, the most commonly used load factor, was adopted
in this work to represent load conditions. The positive correlation between the C-rate C and degradation rate can be expressed as:

SC(C) = eKC •C

(19)

where KC is the coefficient of the C-rate stress model that needs to be fitted. The C-rate coefficient KC can be determined using the cycle
aging fC:

KC = ln

(

fC[T=TA,?=?A,Frest =FA]
SF(FRest)S?(?)ST (Tc)

)/

C

(20)

where fC[T=TA,?=?A,Frest =FA] is the linearized cycle aging model determined under rest time FA, temperature TA and SOC level ?A, and C
denotes the C-rate of the test.

3.2. Physics-informed long short-term memory model of nonlinear degradation

The degradation rate of lithium-ion batteries is not constant throughout the lifespan of a battery. Cycling tests have shown that the
capacity fade per cycle is significantly higher during the early and end cycles than other cycles. The impact of the battery health
condition on the CCA model should be captured for better degradation modeling. To accurately measure the actual capacity fade for
each cycle, we proposed the PI-LSTM model that can estimate the overall capacity fade of the nth cycle, Ln, as shown in Eq. (21).

MechanicalSystemsandSignalProcessing179(2022)1093476J. Shi et al.

Ln = f PILSTM
d

(
Ln?1, f Linear
d

)

(21)

where f PILSTM

d

is a function of the overall capacity of the previous cycle Ln?1  and the capacity fade modeled by CCA model f Linear

d

.

The training process of the proposed PI-LSTM model is conducted after the coefficients of the CCA model are determined using one
of the training batteries. Only a portion of the online monitoring data (current, voltage, and cell temperature) of all the training
batteries is used as training data for the PI-LSTM model. The PI-LSTM model will learn the relationship between actual aging status and
the capacity fade modeled by the CCA cumulatively for each cycle and capture the impact of the battery health condition.

As shown in Fig. 2, the structure of an LSTM cell consists of the monitoring data (Xn) of the nth discharge cycle of a battery, the
previous and current memory cell Cn?1 and Cn, as well as the previous and current hidden unit Hn?1 and Hn. The memory cell Cn stores
the PI-LSTM function updated by the nth discharge cycle (f PILSTM
). There are four gates within the PI-LSTM model architecture, an input
gate in, an output gate on, an input modulation gate  ?cn  and a forget gate fn. The hidden units Hn?1  and Hn  are also connected to the
actual capacity of the previous and current cycle Ln?1 and Ln. The relationship between Hn and Ln will be used for updating the PI-LSTM
cell of past cycles and predicting the capacity L of future cycles.

d,n

The forget gate fn, as shown in Eq. (22), is used to clear unrelated information from memory. In this layer, the previous hidden unit
are weighted

Hn?1, the monitoring data of the current cycle Xn, and the capacity of the current cycle estimated by the CCA f Linear
concatenated. The sigmoid activation function is used to extract the relevancy from the concentrated units. The output of this layer
ranges from 0 to 1 and indicates the percentage of information that needs to be forgotten.

d,n

The input gate in  and input modulation gate  ?cn  shown in Eq. (23) and Eq. (24) are used to extract functional information from the
. The input gate in  produces a

monitoring data of the current cycle Xn  and the capacity of the current cycle estimated by the CCA f Linear
number ranging between 0 and 1 using the sigmoid function for each data point in Xn  and f Linear
. This number indicates which data
point will be used for updating the memory. The input modulation gate ?cn is used to generate a matrix of candidate values for memory
updating using the hyperbolic tangent function.

d,n

d,n

The current memory cell Cn  is updated in two parts, as shown in Eq. (25). The unimportant information is removed from the
previous memory cell Cn?1 using the indicator generated by the forget gate fn. The critical information is added by the candidate matrix
determined by the input modulation  ?cn  and the indicator generated by the input gate in.

The last step is to extract features into hidden units Hn  for capacity estimation. The output gate on  generates a number ranging
between 0 and 1 for each data in the current memory cell Cn  using the previous hidden unit Hn?1, the monitoring data of the current
cycle Xn, and the capacity of the current cycle estimated by the CCA f Linear
as shown in Eq. (26). The values in the current memory cell
Cn  is activated by the output gate on  as shown in Eq. (27) [49].

d,n

(
Wf • Xn + Wf • Hn?1 + Wf • f Linear

d,n + bf

)

fn = ?

(
Wi • Xn + Wi • Hn?1 + Wi • f Linear

d,n + bi

)

in = ?

?cn = tanh

(
Wc • Xn + Wc • Hn?1 + Wc • f Linear

d,n + bc

?
Cn = fn ? C

n?1 + ?cn ? in

)

(22)

(23)

(24)

(25)

Fig. 2. The PI-LSTM cell structure.

MechanicalSystemsandSignalProcessing179(2022)1093477J. Shi et al.

(

on = ?

?
Wo • Xn + Wo • H

n?1 + Wo • f Linear

d,n + bo

Hn = on ? tanh(Cn)

)

(26)

(27)

The weights and biases (Wx  and bx  where x = f, i, c, o) of each gate are the parameters to be updated during each iteration to
improve the feature extraction and learning process. The mean squared error loss function, which is shown in Eq. (28), is used to
determine the performance of each iteration. Weights and biases are optimized by reducing the mean squared error of the previous
iteration.

Loss =

1
M

?M

i=1

(yi ? ?yi)2

(28)

where M represents the number observations, yi  denotes the i th actual value of independent variables, and ?yi  is the prediction of the i
th independent variables.

The gradients (?) of the loss function is optimized using the stochastic gradient descent function shown in Eq. (29).

[
? ? ? ? ?

?

?R(?)
??

+

]
?L(?T xi + b, yi)
??

(29)

where xi  is the ith input, yi  is the ith output, ? is the learning rate that defines the updated size in the parameter space, and ? is a non-
negative  hyperparameter  that controls  the  regularization  strength. The intercept  b is  updated  with  additional  decay and  without
regularization. R(?) is the regularization term that penalizes model complexity as defined by Eq. (30).

R(?) =

?m
j=1

1
2

?2
j

where m is the total number of iterations and j is the current iteration.

3.3. Remaining useful life prediction

(30)

The actual capacity fade of each discharge cycle is not always available for real world applications as the batteries may not be fully
discharged or tested for the ground truth. Therefore, the capacity fade estimated by the PI-LSTM degradation model is used for RUL
prediction. An LSTM model is used to predict the discharge capacity of future cycles and the RUL by learning the degradation trend
estimated by the PI-LSTM model. The input of the LSTM multi-step forecasting framework is the sequence of estimated discharge
capacity of each previous cycle as shown in Fig. 3. The LSTM cell can learn the historical patterns from the input sequence and update
the extracted information into hidden units (H0,H1,?) recurrently. The hidden units are connected to the actual discharge capacity to
update the bias and weights of each gate of the LSTM cell during the training process. After the bias and weights are optimized, the
model can capture the critical information from the previous cycles of a test battery and then predict the capacities of future cycles.
Each prediction is generated based on the previous prediction by self-updating the hidden units (Ha, Hb, ?) sequentially.

4. Case study

The performance of the proposed method was demonstrated using the lithium-ion battery aging dataset published by the NASA
Ames Prognostics Center of Excellence (PCoE) [50]. Commercially available lithium-ion 18,650 rechargeable batteries were tested

Fig. 3. Sequence forecast using LSTM.

MechanicalSystemsandSignalProcessing179(2022)1093478J. Shi et al.

under different temperatures and discharge voltage thresholds until reaching the EOL threshold. Voltmeters, ammeters, and ther-
mocouples were used to measure the voltage, current, and cell temperature of batteries at a sampling rate of 10 Hz.

Three different operational profiles including charge, discharge, and impedance were used on the test batteries. In the charge
cycles, the batteries were charged using a constant current (CC) at 1.5 A until the charge voltage reached 4.2 V then continued under
constant voltage (CV) until the charge current fell below 0.02 A. The battery was operated at the designed load during each discharge
cycle until the voltage fell under the discharge voltage threshold. During the impedance cycles, the impedance of the batteries was
recorded as the damage criterion using electrochemical impedance spectroscopy (EIS). The details about the dataset will be presented
in the following subsection.

4.1. Data description

The aging dataset contains nine datasets with different testing parameters and criteria. Three datasets with the were used to test the
proposed method under three operating conditions: 2 A, 4 A, and 4 A square wave. The 1 C-rate for all batteries is 2 A. The 4 A load and
4 A square wave load are used to test the impact of heavy load and varying load on battery, respectively. Two environmental tem-
peratures were used across the three datasets to test the temperature stress model. Four different SOC levels were used in each dataset
to test the SOC stress model. There are four batteries in the first two datasets and three batteries in the third dataset. The environmental
temperatures, load conditions, and discharge voltage thresholds for the battery cells used in this study are shown in Table 1.

The degradation trends of all datasets are shown in Fig. 4. The degradation trends of each dataset are different because the batteries
were operated at different environmental temperatures, SOC levels, and C-rates. Energy recovery caused by long rest times can also be
observed in Fig. 4. It can also be seen that the degradation rate of a battery changes during different life stages even though the same
parameters are used for each discharge cycle. Therefore, the proposed method is expected to perform better than the linear CCA.

4.2. Experimental results and performance comparison

The output of the proposed method contains two parts: the result of the degradation modeling for the past discharge cycle and the
result of the RUL prediction for the future discharge cycles. The results of degradation modeling will be presented in subsections 4.2.1
and  4.2.2 and  the  performance of  RUL prediction  will  be presented  in  section 4.2.3.  For  degradation modeling,  subsection 4.2.1
presents the details of the linear degradation modeled by CCA and subsection 4.2.2 presents the results of the PI-LSTM degradation
model as well as the comparison between the linear CCA and the PI-LSTM models.

4.2.1. Linear degradation modeling

The CCA model can capture the linear degradation trend of batteries as described in section 3.1. The coefficients of the five stress
models are highly correlated to the characteristics of batteries and varies for different types of batteries. Therefore, the coefficients of
the CCA model need to be determined using the average value of cycle time, rest time, SOC level, environmental temperature, and C-
rate.

In this work, the coefficients of all stress models were determined using battery #5 from dataset 1, as battery #5 was operated at
?
C), recommended voltage thresholds, and 1 C-rate. After the coefficients were determined, the model was then
room temperature (24
used to estimate the capacity fade of the remaining three batteries in dataset 1 as shown in Fig. 5. The results show that the CCA model
can accurately estimate the capacity fade of batteries under the same load and environmental temperature but different SOC level,
cycle times, and rest time. The mean absolute percentage errors (MAPEs) of capacity fade estimation are 6.85%, 12.20%, and 3.59% for
batteries # 6, #7, and #18, respectively. The results also show that the linear model usually overestimates the capacity fade during the
early life stage.

The CCA model fitted using battery #5 was also tested using the batteries from the other two datasets with different loads and
environmental temperatures. The results for the batteries in dataset 2 are shown in Fig. 6. This figure demonstrates that the CCA model
is not generalizable under different load conditions. The accuracy of the CCA model significantly decreased for the higher temperature
and C-rate. The MAPEs of the capacity fade estimation are 44.76%, 23.20%, and 45.38% for batteries #29, #30, and #31, respectively.
The degradation rate estimated using the CCA model is less than the actual degradation rate, as the slope of the estimated capacity fade
is less than that of the actual capacity fade for dataset 2. The impacts of high C-rate and environmental temperature on batteries were
not taken into account by this model.

The results for batteries in dataset 3 are shown in Fig. 7. The MAPEs of capacity fade estimation are 16.78% and 11.23% for
batteries #25 and #26, respectively. The average load of dataset 3 is less than dataset 2 (very close to 1 C-rate) and the environmental
temperature of dataset 3 is the same as dataset 1. The performance of the CCA model on dataset 3 is better than dataset 2 because it has

Table 1
Temperature, load condition, and discharge voltage threshold of the selected datasets.

Dataset ID

?
Temperature (

C)

Load Condition

Discharge Voltage Threshold (Battery ID)

1
2

3

24
43

24

2 A
4 A

4 A Square Wave

2.2 V (#7), 2.5 V (#6, #18), 2.7 V (#5)
2.0 V (#29), 2.2 V (#30), 2.5 V (#31),
2.7 V (#32)
2.0 V (#25), 2.2 V (#26), 2.5 V (#27)

MechanicalSystemsandSignalProcessing179(2022)1093479J. Shi et al.

Fig. 4. Degradation trend of batteries under load condition (a) 2 A, (b) 4 A, and (c) 4 A square wave.

Fig. 5. Capacity fade modeled under 2 A load using CCA for batteries (a) #6, (b) #7, and (c) #18.

Fig. 6. Capacity fade modeled 4 A load using CCA for batteries (a) #29, (b) #30, and (c) #31.

similar operating conditions to dataset 1. However, the performance for dataset 3 is still not as good as dataset 1 due to the varying load
condition. The degradation rate estimated using the CCA model is less than the actual degradation rate because the slope of the
estimated capacity fade is less than that of the actual capacity fade for dataset 3.

MechanicalSystemsandSignalProcessing179(2022)10934710J. Shi et al.

Fig. 7. Capacity fade modeled 4 A square wave load using CCA for batteries (a) #25 and (b) #26.

4.2.2. Nonlinear degradation modeling

As shown in section 4.2.1, the CCA cannot accurately model the actual capacity fade of batteries under different operating con-
ditions  throughout  the  life  of  the  battery.  The  non-linear  portion  of  battery  degradation  caused  by  different  battery  health  and
operating conditions is not well modeled. The proposed method is expected to outperform the CCA model by learning the non-linear
portion of battery degradation. As described in section 3.2, the non-linear portion can be learned by updating the relationship between
linear capacity fade and actual capacity fade of each discharge cycle sequentially using the PI-LSTM model. One battery from each
dataset, which is 25% of a dataset (33% for dataset 3), was used to train the PI-LSTM model for different operating conditions during
the training process. The remaining three batteries of each dataset (2 for dataset 3) were used to test the performance of the PI-LSTM
model. For each test, the discharge capacity of the test battery was predicted using 50% of the monitoring data of each cycle for
performance comparison.

As described in the previous subsection, the CCA model can accurately model the degradation trend of batteries in dataset 1 as the
coefficients were determined using the same operating conditions. The main error of the CCA model is due to the change in the
degradation rate caused by different battery health conditions. The PI-LSTM model was trained using battery #5 to learn the non-linear
portion of the degradation behavior. The results for the remaining three batteries are shown in Fig. 8. The MAPEs of capacity fade
estimation decreased from 6.85%, 12.20%, and 3.59% to 0.92%, 1.41%, and 1.17% for batteries #6, #7, and #18, respectively. The
training time is 272 s and the testing time is less than 0.4 s for each testing battery. The results show that the PI-LSTM model can
provide fast and accurate capacity estimation for history cycles by learning the non-linear relationship between the CCA model and the
actual capacity fade.

For dataset 2, the error of the CCA model consists of the changes in the degradation rate caused by different battery health and
operating conditions. The PI-LSTM model was trained using battery #32 to learn the non-linear portion of the degradation trend. The
results for the remaining three batteries are shown in Fig. 9. The MAPEs of capacity fade estimation are decreased from 44.76%,
23.20%, and 45.38% to 1.72%, 1.66%, and 3.39% for batteries #29, #30, and #31, respectively. The training time is 192 s and the

Fig. 8. Capacity fade modeled under 2 A load using the PI-LSTM model for batteries (a) #6, (b) #7, and (c) #18.

MechanicalSystemsandSignalProcessing179(2022)10934711J. Shi et al.

testing time is less than 0.2 s for each testing battery. The results show that the PI-LSTM model can provide fast and accurate capacity
estimation for historic cycles under different operating conditions.

For dataset 3, the error of the CCA model consists of the changes in the degradation rate caused by different battery health and
varying load conditions. The PI-LSTM model was trained using battery #27 to learn the non-linear portion of the degradation trend.
The results for the remaining two batteries are shown in Fig. 10. The MAPEs of capacity fade estimation are decreased from 16.78%
and 11.23% to 4.19% and 5.59% for batteries #25 and #26, respectively. The training time is 165 s and the testing time is less than 0.2
s for each testing battery. The results show that the PI-LSTM model can provide fast and accurate capacity estimation for historic cycles
under varying load conditions.

The performance of  the  proposed PI-LSTM method  is  compared with  three  baseline methods.  A CCA model as  well  as  a con-
volutional neural network (CNN) and a Bi-directional LSTM (BiLSTM) were used as baseline methods for comparison. The baseline
CCA model was determined using the operating stress factors of battery #5 which are the same as the operating stress factors used in
the CCA model in the proposed PI-LSTM method. The baseline CNN and BiLSTM were trained the same as the LSTM layer in the
proposed PI-LSTM method by using 50% of the monitoring data of a single battery from each dataset. The comparison results sum-
marized in Table 2 demonstrate that by combining monitoring data and operating stress factors, the PI-LSTM model can outperform
the CCA model which only uses operating stress factors as well as both CNN and BiLSTM which only use monitoring data.

4.2.3. Remaining useful life prediction

After the capacity fade of past discharge cycles are estimated by the PI-LSTM model, a separate LSTM model is used to learn the
degradation patterns from each cycle sequentially. The capacity fade of future cycles is predicted by the LSTM model using the learned
degradation patterns determined by the PI-LSTM model. The RUL is calculated by counting the cycles until the capacity fade reaches
the end-of-life (EOL) threshold. For  each dataset, three batteries (two for dataset 3) were used to train  the LSTM model and  the
remaining battery was used for testing. 30%, 40%, 50%, 60%, 70%, and 80% of the test battery life cycle are used as starting points to
predict the discharge capacity of the future cycles while using the estimated capacity of the past cycles. The RUL is then calculated at
each of the five battery life cycle percentages.

For dataset 1, the estimated capacity fades of batteries #5, #6, and #17 were used to train the LSTM model. The performance of the
trained model was tested by predicting the RUL of battery #18 from the 40th discharge cycle (30% of the battery life cycle) to the
106th discharge cycle (80% of the battery life cycle). Fig. 11 (a) shows the process of predicting the RUL of battery #18 at the 66th
cycle (50% of battery life cycle). The discharge capacities of cycle 1 to cycle 66 are estimated by the PI-LSTM model using monitoring
data. The discharge capacities of the future cycles are then predicted by the LSTM model based on the trend of past estimated discharge
capacities. The RUL is calculated when discharge capacity of a future cycle reaches the threshold. As shown in Fig. 11 (a), the RUL is 73
cycles until the predicted discharge capacity reaches the threshold. The mean absolute error (MAE) and MAPE at 50% of the battery life
cycle are 7 and 10.61%, respectively. The RUL predictions of all five starting points are shown in Fig. 11 (b) and the numerical results
are shown in Table 3.

For dataset 2, the estimated capacity fades of batteries #29, #30, and #31 were used to train the LSTM model. The performance of
the trained model was tested by predicting the RUL of battery #32 from the 11th discharge cycle (30% of the battery life cycle) to the
29th discharge cycle (80% of the battery life cycle). Fig. 12 (a) shows the process of predicting the RUL of battery #32 at the 18th cycle
(50% of battery life cycle). The discharge capacities of cycle 1 to cycle 18 are estimated by the PI-LSTM model using monitoring data.
The discharge capacities of future cycles are then predicted by the LSTM model based on the trend of past estimated discharge ca-
pacities. The RUL is calculated when discharge capacity of a future cycle reaches the threshold. As shown in Fig. 12 (a), the RUL is 19
cycles until the predicted discharge capacity reaches the threshold. The MAE and MAPE at 50% of the battery life cycle are 1 and
5.56%, respectively. The RUL predictions of all five starting points are shown in Fig. 12 (b) and the numerical results are shown in
Table 3.

Fig. 9. Capacity fade modeled under 4 A load using the PI-LSTM model for batteries (a) #29, (b) #30, and (c) #31.

MechanicalSystemsandSignalProcessing179(2022)10934712J. Shi et al.

Fig. 10. Capacity fade modeled under 4 A square wave load using the PI-LSTM model for batteries (a) #25 and (b) #26.

Table 2
Performance comparison between the baseline methods (CCA, CNN, and BiLSTM) and the proposed PI-LSTM method in terms of MAPE.

Dataset 1
(2 A)
#6

6.85%
10.69%
5.33%
0.92%

CCA
CNN
BiLSTM
PI-LSTM

#7

12.20%
14.74%
8.54%
1.41%

#18

3.59%
11.31%
4.12%
1.17%

Dataset 2
(4 A load)
#29

44.76%
21.18%
16.51%
1.72%

#30

#31

Dataset 3
(4 A square wave)
#25

#26

23.20%
17.90%
14.39%
1.66%

45.38%
22.74%
19.88%
3.39%

16.78%
19.34%
14.84%
4.19%

11.23%
17.21%
12.10%
5.59%

Fig. 11. RUL prediction using LSTM for battery #18 under 2 A load at (a) 50% of the battery life cycle and (b) all five starting points.

For dataset 3, estimated capacity fades of batteries #25 and #26 were used to train the LSTM model. The performance of the trained
model was tested by predicting the RUL of battery #27 from the 8th discharge cycle (30% of the battery life cycle) to the 22nd
discharge cycle (80% of the battery life cycle). Fig. 13 (a) shows the process of predicting the RUL of battery #27 at the 14th cycle (50%
of battery life cycle). The discharge capacities of cycle 1 to cycle 14 are estimated by the PI-LSTM model using monitoring data. The
discharge capacities of future cycles are then predicted by the LSTM model based on the trend of past estimated discharge capacities.
The RUL is calculated when discharge capacity of a future cycle reaches the threshold. As shown in Fig. 13 (a), the RUL is 12 cycles
until the predicted discharge capacity reaches the threshold. The MAE and MAPE at 50% of the battery life cycle are 2 and 14.28%,
respectively. The RUL predictions of all five starting points are shown in Fig. 13 (b) and the numerical results are shown in Table 3.
The performance of the LSTM model for each test battery is summarized in Table 3. The MAE of battery #32 at 80% percent of

MechanicalSystemsandSignalProcessing179(2022)10934713J. Shi et al.

Table 3
Performance of RUL Prediction using LSTM in terms of MAE and MAPE.

RUL Prediction Starting Point

Predicted Capacity

Actual Capacity

MAE

MAPE (%)

#18

(2 A)

#32

(4 A)

#27

(4 A square wave)

30%
40%
50%
60%
70%
80%
30%
40%
50%
60%
70%
80%
30%
40%
50%
60%
70%
80%

109
91
73
47
43
23
31
19
19
16
10
5
24
19
12
12
9
5

92
79
66
53
40
26
25
22
18
14
11
7
20
17
14
11
8
6

17
12
7
6
3
3
6
3
1
2
1
2
4
2
2
1
1
1

18.48
15.19
10.61
11.32
7.5
11.54
24
13.64
5.56
14.29
9.09
28.57
20
11.76
14.28
9.09
12.5
16.67

Fig. 12. RUL prediction using LSTM for battery #32 under 4 A load at (a) 50% of life cycle and (b) all five starting points.

Fig. 13. RUL prediction using LSTM for battery #27 under 4 A square wave load at (a) 50% of life cycle and (b) all five starting points.

MechanicalSystemsandSignalProcessing179(2022)10934714J. Shi et al.

battery life cycle is larger than the MAE at 70% percent. This is because the batteries in this dataset exhibit unexpected energy re-
coveries due to a longer rest time between some cycles. Such unexpected energy recoveries will have a large impact on RUL of a battery
during the end of a battery life cycle. The proposed method is not able to predict the energy recoveries that will occur in future cycles
since monitoring data of future cycles is not available during online prediction. However, the results show that the proposed method
can provide accurate RUL predictions for batteries under different operating conditions and battery life cycle stages using online
monitoring data.

5. Conclusions and future work

In this paper, a novel physics-informed machine learning method was developed for battery degradation modeling and online RUL
prediction under different operating conditions. First, the linear portion of battery degradation was represented by the CCA model
using environmental temperature, SOC level, cycle time, rest time, and C-rate as the operating stress factors. A PI-LSTM model was
developed by combining the CCA model and an LSTM layer to reveal the relationship between the actual battery degradation and the
linear model estimation using monitoring data such as voltage, current, and temperature. The PI-LSTM model can accurately predict
the capacity fade by learning how the operating stress factors and battery health condition affect battery degradation. After the ca-
pacity fade of each discharge cycle was estimated by the PI-LSTM model, the degradation behavior was learned by a separate LSTM
model to predict the battery RUL.

The proposed method was demonstrated using the Li-ion battery aging datasets collected from the battery prognostics testbed built
by NASA. The experimental results have shown that the proposed PI-LSTM model can estimate the capacity fade of batteries efficiently
(prediction time less than 0.4 s) and accurately (1.72%, 1.66%, 3.39%, and 4.19% in terms of MAPE for batteries #29, #30, #31, and
#25, respectively) without fully discharging the battery or conducting any tests such as an EIS test. It was demonstrated that the PI-
LSTM model can outperform CNN and BiLSTM in predicting the capacity fade of batteries under different operating conditions. This is
because the PI-LSTM model can consider the operating conditions using the operating stress factors of the CCA model. The results also
show that the proposed method can accurately predict the RUL of batteries under different operating conditions using online moni-
toring data (10.61%, 5.56%, and 14.28% in terms of MAPE for batteries #18, #32, and #27, respectively, when 50% life is remaining).
In the future, we plan to test the proposed method under varying temperatures and loads. We will also test the proposed method using
different types of batteries.

Declaration of Competing Interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to

influence the work reported in this paper.

Acknowledgement

This  research  was  in  part  supported  by  the  National  Science  Foundation  under  Grant  No.  2131619.  We  would  also  like  to

acknowledge the support of NVIDIA Corporation with the donation of the Titan Xp GPU used for this research.

References

[1] Y. Zhou, M. Huang, Y. Chen, Y. Tao, A novel health indicator for on-line lithium-ion batteries remaining useful life prediction, J. Power Sources 321 (2016)

1–10.

[2] W. He, N. Williard, M. Osterman, M. Pecht, Prognostics of lithium-ion batteries based on Dempster-Shafer theory and the Bayesian Monte Carlo method,

J. Power Sources 196 (2011) 10314–10321.

[3] Y. Zhang, R. Xiong, H. He, M.G. Pecht, Lithium-Ion Battery Remaining Useful Life Prediction With Box-Cox Transformation and Monte Carlo Simulation, IEEE

Trans. Ind. Electron. 66 (2019) 1585–1597.

[4] R.G. Nascimento, M. Corbetta, C.S. Kulkarni, F.A.C. Viana, Hybrid physics-informed neural networks for lithium-ion battery modeling and prognosis, J. Power

Sources 513 (2021), 230526.

[5] M. Lucu, E. Martinez-Laserna, I. Gandiaga, H. Camblong, A critical review on self-adaptive Li-ion battery ageing models, J. Power Sources 401 (2018) 85–101.
[6] H. Zhang, Q. Miao, X. Zhang, Z. Liu, An improved unscented particle filter approach for lithium-ion battery remaining useful life prediction, Microelectron.

Reliab. 81 (2018) 288–298.

[7] R. Xiong, L. Li, J. Tian, Towards a smarter battery management system: A critical review on battery state of health monitoring methods, J. Power Sources 405

(2018) 18–29.

[8] D. Wang, Y. Zhao, F. Yang, K.-L. Tsui, Nonlinear-drifted Brownian motion with multiple hidden states for remaining useful life prediction of rechargeable

batteries, Mech. Syst. Sig. Process. 93 (2017) 531–544.

[9] N.A. Samad, Y. Kim, J.B. Siegel, A.G. Stefanopoulou, Battery capacity fading estimation using a force-based incremental capacity analysis, J. Electrochem. Soc.,

163 (2016) A1584.

[10] C. Chen, R. Xiong, W. Shen, A lithium-ion battery-in-the-loop approach to test and validate multiscale dual H infinity filters for state-of-charge and capacity

estimation, IEEE Trans. Power Electron. 33 (2017) 332–342.

[11] N. Yang, X. Zhang, G. Li, State of charge estimation for pulse discharge of a LiFePO4 battery by a revised Ah counting, Electrochim. Acta 151 (2015) 63–71.
[12] K.S. Ng, C.-S. Moo, Y.-P. Chen, Y.-C. Hsieh, Enhanced coulomb counting method for estimating state-of-charge and state-of-health of lithium-ion batteries, Appl.

Energy 86 (2009) 1506–1511.

[13] C. Hu, B.D. Youn, J. Chung, A multiscale framework with extended Kalman filter for lithium-ion battery SOC and capacity estimation, Appl. Energy 92 (2012)

694–704.

[14] G.L. Plett, Sigma-point Kalman filtering for battery management systems of LiPB-based HEV battery packs: Part 2: Simultaneous state and parameter estimation,

J. Power Sources 161 (2006) 1369–1384.

MechanicalSystemsandSignalProcessing179(2022)10934715J. Shi et al.

[15] Q. Miao, L. Xie, H. Cui, W. Liang, M. Pecht, Remaining useful life prediction of lithium-ion battery with unscented particle filter technique, Microelectron.

Reliab. 53 (2013) 805–810.

[16] J. Wei, G. Dong, Z. Chen, Remaining useful life prediction and state of health diagnosis for lithium-ion batteries using particle filter and support vector

regression, IEEE Trans. Ind. Electron. 65 (7) (2018) 5634–5643.

[17] D. Roman, S. Saxena, V. Robu, M. Pecht, D. Flynn, Machine learning pipeline for battery state-of-health estimation, Nat. Mach. Intellig. 3 (5) (2021) 447–456.
[18] Y. Wang, D. Yang, X. Zhang, Z. Chen, Probability based remaining capacity estimation using data-driven and neural network model, J. Power Sources 315

(2016) 199–208.

[19] A. Downey, Y.-H. Lui, C. Hu, S. Laflamme, S. Hu, Physics-based prognostics of lithium-ion battery using non-linear least squares with dynamic bounds, Reliab.

Eng. Syst. Saf. 182 (2019) 1–12.

[20] K. Park, Y. Choi, W.J. Choi, H.-Y. Ryu, H. Kim, LSTM-Based Battery Remaining Useful Life Prediction With Multi-Channel Charging Profiles, IEEE Access 8

(2020) 20786–20798.

[21] X. Hu, L.e. Xu, X. Lin, M. Pecht, Battery Lifetime Prognostics, Joule 4 (2) (2020) 310–346.
[22] S. Wang, S. Jin, D. Deng, C. Fernandez, A Critical Review of Online Battery Remaining Useful Lifetime Prediction Methods, Front. Mechan. Eng. 7 (2021).
[23] Y.H. Lui, M. Li, A. Downey, S. Shen, V.P. Nemani, H. Ye, C. Vanelzen, G. Jain, S. Hu, S. Laflamme, C. Hu, Physics-based prognostics of implantable-grade

lithium-ion battery for remaining useful life prediction, J. Power Sour., 485 (2021) 229327.

[24] G. Dong, J. Wei, A physics-based aging model for lithium-ion battery with coupled chemical/mechanical degradation mechanisms, Electrochim. Acta, 395

(2021) 139133.

[25] I. Baghdadi, O. Briat, J.-Y. Del´etage, P. Gyan, J.-M. Vinassa, Lithium battery aging model based on Dakin’s degradation approach, J. Power Sources 325 (2016)

273–285.

[26] Y. Sun, X. Hao, M. Pecht, Y. Zhou, Remaining useful life prediction for lithium-ion batteries based on an integrated health indicator, Microelectron. Reliab.

88–90 (2018) 1189–1194.

[27] J. Wei, G. Dong, Z. Chen, Remaining Useful Life Prediction and State of Health Diagnosis for Lithium-Ion Batteries Using Particle Filter and Support Vector

Regression, IEEE Trans. Ind. Electron. 65 (2018) 5634–5643.

[28] L. Ren, J. Dong, X. Wang, Z. Meng, L. Zhao, M.J. Deen, A Data-Driven Auto-CNN-LSTM Prediction Model for Lithium-Ion Battery Remaining Useful Life, IEEE

Trans. Ind. Inf. 17 (2021) 3478–3487.

[29] J. Vetter, P. Nov´ak, M.R. Wagner, C. Veit, K.-C. M¨oller, J. Besenhard, M. Winter, M. Wohlfahrt-Mehrens, C. Vogler, A. Hammouche, Ageing mechanisms in

lithium-ion batteries, J. Power Sources 147 (2005) 269–281.

[30] J. Wang, P. Liu, J. Hicks-Garner, E. Sherman, S. Soukiazian, M. Verbrugge, H. Tataria, J. Musser, P. Finamore, Cycle-life model for graphite-LiFePO4 cells,

J. Power Sources 196 (2011) 3942–3948.

[31] I. Laresgoiti, S. K¨abitz, M. Ecker, D.U. Sauer, Modeling mechanical degradation in lithium ion batteries during cycling: Solid electrolyte interphase fracture,

J. Power Sources 300 (2015) 112–122.

[32] B. Xu, A. Oudalov, A. Ulbig, G. Andersson, D.S. Kirschen, Modeling of lithium-ion battery degradation for cell life assessment, IEEE Trans. Smart Grid 9 (2)

(2018) 1131–1140.

[33] J. Johnson, Designing with the mind in mind: Simple guide to understanding user interface design rules, Morgan Kaufmann, 2010.
[34] G. Ning, B.N. Popov, Cycle life modeling of lithium-ion batteries, J. Electrochem. Soc. 151 (10) (2004) A1584.
[35] B.Y. Liaw, E.P. Roth, R.G. Jungst, G. Nagasubramanian, H.L. Case, D.H. Doughty, Correlation of Arrhenius behaviors in power and capacity fades with cell

impedance and heat generation in cylindrical lithium-ion cells, J. Power Sources 119 (2003) 874–886.

[36] A. Millner, Modeling lithium ion battery degradation in electric vehicles, 2010 IEEE Conference on Innovative Technologies for an Efficient and Reliable

Electricity Supply, IEEE, 2010, pp. 349-356.

[37] F. Wankmüller, P.R. Thimmapuram, K.G. Gallagher, A. Botterud, Impact of battery degradation on energy arbitrage revenue of grid-level energy storage,

J. Storage Mater. 10 (2017) 56–66.

[38] S.B. Peterson, J. Apt, J. Whitacre, Lithium-ion battery cell degradation resulting from realistic vehicle and vehicle-to-grid utilization, J. Power Sources 195

(2010) 2385–2392.

[39] L. Lam, P. Bauer, E. Kelder, A practical circuit-based model for Li-ion battery cells in electric vehicle applications, 2011 IEEE 33rd International

Telecommunications Energy Conference (INTELEC), IEEE, 2011, pp. 1-9.

[40] B. Ratnakumar, M. Smart, L. Whitcanack, R. Ewell, The impedance characteristics of Mars Exploration Rover Li-ion batteries, J. Power Sources 159 (2006)

1428–1439.

[41] C.K. Huang, J. Sakamoto, J. Wolfenstine, S. Surampudi, The limits of low-temperature performance of Li-ion cells, J. Electrochem. Soc. 147 (2000) 2893.
[42] S. Zhang, K. Xu, T. Jow, The low temperature performance of Li-ion batteries, J. Power Sources 115 (2003) 137–140.
[43] M. Safari, M. Morcrette, A. Teyssot, C. Delacourt, Life-prediction methods for lithium-ion batteries derived from a fatigue approach: I. introduction: Capacity-

loss prediction based on damage accumulation, J. Electrochem. Soc. 157 (6) (2010) A713.

[44] K. Amine, C. Chen, J. Liu, M. Hammond, A. Jansen, D. Dees, I. Bloom, D. Vissers, G. Henriksen, Factors responsible for impedance rise in high power lithium ion

batteries, J. Power Sources 97 (2001) 684–687.

[45] L. Deng, W. Shen, H. Wang, S. Wang, A rest-time-based prognostic model for remaining useful life prediction of lithium-ion battery, Neural Comput. Appl. 33

(2021) 2035–2046.

[46] D. Wang, J. Coignard, T. Zeng, C. Zhang, S. Saxena, Quantifying electric vehicle battery degradation from driving vs. vehicle-to-grid services, J. Power Sources

332 (2016) 193–203.

[47] M. Ouyang, X. Feng, X. Han, L. Lu, Z. Li, X. He, A dynamic capacity degradation model and its applications considering varying load for a large format Li-ion

battery, Appl. Energy 165 (2016) 48–59.

[48] Y. Wang, S.J. Moura, S.G. Advani, A.K. Prasad, Power management system for a fuel cell/battery hybrid vehicle incorporating fuel cell and battery degradation,

Int. J. Hydrogen Energy 44 (16) (2019) 8479–8492.

[49] S. Hochreiter, J. Schmidhuber, Long short-term memory, Neural Comput. 9 (8) (1997) 1735–1780.
[50] B. Saha, K. Goebel, Battery data set, NASA AMES prognostics data repository, (2007).

MechanicalSystemsandSignalProcessing179(2022)10934716
