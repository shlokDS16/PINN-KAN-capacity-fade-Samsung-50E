# (no title)
URL: https://ut3-toulouseinp.hal.science/hal-05482347v1/document

HAL Id: hal-05482347
https://ut3-toulouseinp.hal.science/hal-05482347v1
Submitted on 28 Jan 2026
HAL is a multi-disciplinary open access
archive for the deposit and dissemination of scientific research documents, whether they are published or not. The documents may come from
teaching and research institutions in France or
abroad, or from public or private research centers.
L’archive ouverte pluridisciplinaire HAL, est
destinée au dépôt et à la diffusion de documents
scientifiques de niveau recherche, publiés ou non,
émanant des établissements d’enseignement et de
recherche français ou étrangers, des laboratoires
publics ou privés.
Distributed under a Creative Commons CC BY 4.0 - Attribution - International License
A generic physics-informed machine learning framework
for battery remaining useful life prediction using small
early-stage lifecycle data
Weikun Deng, Hung Le, Khanh T.P. Nguyen, Christian Gogu, Kamal
Medjaher, Jérôme Morio, Dazhong Wu
To cite this version:
Weikun Deng, Hung Le, Khanh T.P. Nguyen, Christian Gogu, Kamal Medjaher, et al.. A generic
physics-informed machine learning framework for battery remaining useful life prediction using small
early-stage lifecycle data. Applied Energy, 2025, 384, pp.125314. ff10.1016/j.apenergy.2025.125314ff.
ffhal-05482347ff
Contents lists available at ScienceDirect
Applied Energy
journal homepage: www.elsevier.com/locate/apenergy
A generic physics-informed machine learning framework for battery
remaining useful life prediction using small early-stage lifecycle data
Weikun Deng a ,∗, Hung Le d, Khanh T.P. Nguyen a, Christian Gogu b, Kamal Medjaher a,
Jérôme Morio c, Dazhong Wu d
a Laboratoire Génie de Production, LGP, Université de Technologie Tarbes Occitanie Pyrénées (UTTOP), 47 Avenue d’Azereix, 65000, Tarbes, France
b
Institut Clément Ader (ICA), Université de Toulouse, ISAE-SUPAERO, UPS, CNRS, INSA, Mines Albi, 3 rue Caroline Aigle, 31400 Toulouse, France
c ONERA/DTIS, Université de Toulouse, F-31055 Toulouse, France
d Additive Manufacturing and Intelligent Systems Laboratory, University of Central Florida Orlando, United States
A R T I C L E I N F O
Keywords:
Physics informed machine learning
Dual branches parallel framework
Three steps training strategy
Solid electrolyte interphase growth
Lithium-ion batteries
Remaining discharging cycles prediction
A B S T R A C T
Predicting the remaining useful life (RUL) of fast-charging lithium-ion batteries using early-stage lifecycle
data is remains challenging due to limited run-to-failure data and lack of knowledge on battery degradation
mechanisms. To address this issue, a generic Physics-Informed Machine Learning (PIML) framework is
developed. The PIML framework consists of two parallel branches: a physics-informed (PI) branch and a datadriven branch. The PI branch is a neural network stacked by the linear projection layers with embedded
physics knowledge, while the data-driven branch is a task-specific machine-learning model. In addition, a
three-step training strategy is introduced, including (1) Training the data-driven branch, (2) Training the PI
branch for aligning physical consistency without updating the hyperparameters in the data-driven branch, and
(3) Fine-tuning both branches simultaneously to achieve optimal performance. To validate this framework, a
physics-based model that represents the growth of solid electrolyte interphase (SEI) and a dilated convolutional
neural network are implemented in the PI and data-driven branches, respectively. The solid electrolyte
interphase-informed dilated convolutional neural network (SEI-DCN) model is demonstrated on the Stanford–
MIT–Toyota-battery dataset. Using only four lifecycle data, the SEI-DCN model achieves very high prediction
accuracy compared to standard dilated CNNs and other state-of-the-art models under various testing conditions
and lifetime ranges. Moreover, the framework is generalizable to different physics-based battery degradation
models.
1. Introduction
Due to high performance in terms of capacity, rechargeability,
maintenance requirements, and environmental friendliness, lithium-ion
batteries play a vital role in energy storage systems for a wide range
of industrial and daily life applications such as automotive, aerospace,
telecommunication and industrial production systems. Precise prognostics in lithium battery health are crucial to ensure safe, reliable, and
cost-effective utilization of their full potential [1]. Particularly with
fast-charging batteries, as few as 25 rapid charging cycles can initiate
irreversible damage to batteries [2]. Predicting the Remaining Useful
Life (RUL) is a significant focus in battery health prognostics. The RUL
of a battery is typically represented as the number of operational cycles
left before the battery reaches the end of its lifespan. This endpoint is
commonly defined as when the battery’s capacity diminishes to either
80% or 70% of its nominal capacity [3].
∗ Corresponding author.
E-mail address: weikun.deng@enit.fr (W. Deng).
Currently, two primary paradigms exist for Lithium-ion battery
prognostics. The first model’s battery degradation mechanisms aim to
identify common patterns that cause and permeate the degradation
process, especially usage patterns related factors [4,5]. Initially, efforts
focused on developing empirical formulas [6], semi-empirical models [7], or building physical knowledge related to real degradation [8].
These empirical or semi-empirical models are designed to fit degradation curves using predefined parametric functions [9,10]. Although
they have been proven effective when applied to laboratory data under
controlled conditions, extending these models to complex real-world
battery systems reduces predictive accuracy and potential bias [11].
Therefore, many studies attribute the primary cause of battery aging
to chemical changes at the negative electrode’s electrode/electrolyte
interface [12]. Specifically, the solid electrolyte interface (SEI) which
happens at the beginning of usage is responsible for capacity degradation and increased resistance, resulting in power loss [13]. Other
https://doi.org/10.1016/j.apenergy.2025.125314
Received 23 March 2024; Received in revised form 9 December 2024; Accepted 3 January 2025
Applied Energy 384 (2025) 125314
Available online 5 February 2025
0306-2619/© 2025 The Authors. Published by Elsevier Ltd. This is an open access article under the CC BY license (http://creativecommons.org/licenses/by/4.0/).
W. Deng et al.
factors, such as alterations in active material and electrode composition, also contribute to aging, though to a lesser extent [14]. Identifying
the mechanism factors is difficult because battery degradation arises
from various interconnected nonlinear processes [15], making it impossible to accurately describe all these degradation processes with
a single quantitative model. Secondly, observing the electro-chemical
state’s evolution is nearly impossible with current sensing techniques
because it involves a range of state-dependent parameters that are extremely challenging to calibrate [16]. Thus, fully understanding battery
degradation physics remains a challenge due to ambiguous analytical
relationships and unclear parameter estimates.
The second paradigm is data-driven-based RUL prediction, where
statistical and machine learning (ML) techniques use extensive data
to automatically establish the connection between cycles data and
RUL, as summarized in research [17]. In particular, neural networks
(NN) that consist of a series of linear and nonlinear transformations
facilitate the extraction of highly representative features across multiple
levels. The typical NN models applied in battery prognostics, such as
auto-encoder (AE), deep neural network (DNN), deep belief network
(DBN), convolution neural network (CNN), recurrent neural network
(RNN), and generative adversarial network (GAN) are reviewed in [18].
The ML accuracy of RUL prediction depends greatly on the available
charge/discharge data, the lithium-ion batteries system’s complexity,
and the appropriate selection of NN structure and hyperparameters
[19]. However, the large battery monitoring datasets are often huge
in data volume rather than degradation information. Complete run-tofailure data on battery charge/discharge cycles is rarely accessible, and
usage history is often unknown, which challenges the data-intensive
nature of ML. Furthermore, these ML models do not cover the system’s
underlying physics, making their performance enhancements more difficult [20]. Therefore, data-driven methods are facing a sparse data and
physics-agnosticism dilemma.
Especially, accurate early-cycle based lifetime prediction is vital for
applications such as fast-charging optimization, production evaluation,
and battery design. This task is challenging due to limited data, but
recent studies have developed innovative deep-learning methods to address this issue. One method integrates early-cycle voltage, current, and
temperature data into a high-dimensional tensor, employing a convolutional sparse autoencoder and regularized logistic regression for classification, achieving high accuracy even with minimal data [21]. Another approach, the attention-assisted temporal convolutional memoryaugmented network (ATCMN), predicts remaining useful life (RUL)
using only 10 cycles of incomplete data, utilizing attention modules and
temporal convolution to learn latent features, demonstrating superior
performance and generalizability across different battery chemistries
and conditions [22]. Additionally, a three-stage deep learning framework combines convolutional neural network-based latent feature extraction with handcrafted features and wrapper feature selection, improving early-stage battery lifetime predictions and generalizing well
to various operational conditions [23].
On these basis, predicting the RUL of batteries falls into a regime
where limited data and partial understanding of the degradation mechanism intersect [24]. In this context, ‘‘Physics-informed Machine Learning (PIML)’’ emerged as a promising solution to improve RUL prediction
performance in recent years. Therefore, our paper first offers a detailed
review of PIML in battery prognostics(see Section 2). Furthermore, we
identify the challenges in applying PIML from the perspective of the architecture and learning strategies. Accordingly, we propose a new PIML
paradigm for battery RUL prognostic. It is a novel parallel dual-branch
framework (See Section 3) with the effective branch-independently
multi-step training methodology outlined in Section 4, marking the
major contribution of this paper. This paradigm provides a flexible and
generalizing solution for knowledge embedding from the perspective
of viewing PI parts as ML extensions. We validate the effectiveness of
our proposed method on a degraded dataset of fast-charging lithium
batteries in Section 5. Meanwhile, its flexibility and generalization
performance are tested in Section 6. Finally, the conclusion and future
work are presented in Section 7.
2. Related works
PIML in battery seeks to seamlessly incorporate physics knowledge
into the cycle data processing pipeline in ML. As summarized in the surveys [25,26], there are three main PIML categories: ‘‘Physics-informed
features (PIF)’’, ‘‘Physics-guided algorithm structures (PGAS)’’, and
‘‘Physics-informed training constraints (PITC)’’. The potential for different physics knowledge that can be utilized to integrate battery
degradation physics into ML in different ways is discussed in Guo et al.’s
review [27]. The general summary of different categories is presented
in Table 1.
In detail, PIF extends traditional ‘‘Feature engineering’’ and ‘‘Surrogate model-based data generation’’ approaches by utilizing physics
knowledge to guide data processing and augmentation [28,29]. Regarding the knowledge type, the Equivalent circuit model (ECM) [28]
and pseudo-2D model [30] are the most commonly used analytical
relations to describe the internal electro-chemical processes of battery degradation. These analytical relationships also include numerical modeling of thermogenesis and heat transfer to mimic various
battery operating conditions, which are solved by finite elements or
volume methods [31]. The simulated results are the supplementary
input information. In addition, it is worth noting that the geometrical characteristics of the data distribution and its feature shape are
also regarded as physical knowledge, such as indicating the battery
aging process by a left shift of the discharge curve and a decrease
in the area under the energy curve [32] or identify Loss of Lithium
Inventory (LLI) and Loss of Active Material (LAM) based on IC curve
peak shape [33]. These geometric characteristics are the empirical
awareness of monitoring phenomena, often pointing to specific battery
degradation processes. Training the PIF model is generally purely datadriven, with the complexity of algorithms and PIML models increasing
in line with the complexity of the input data. For simple data features, models like Gaussian regression [28,32] and one-dimensional
LSTM [30] suffice for mapping features to degradation. For inputs with
structural characteristics, such as 2D images or inputs integrating multiple physical models like the five-equivalent-stress model [34] or the
SOC estimation model [35], more complex structures including CNNLSTM, Two-Dimensional LSTM [33], dimensional grid LSTM [31], and
Stacked LSTM [34] are utilized. PIF is straightforward to implement,
but it is crucial to notice that PIF modifies the input space without
altering and considering the inputs’ physical relationships, which are
also important for the final prognostic decision. In addition, possible
biases in feature extraction guided by incomplete physics are difficult
to address by the following model learning process.
‘‘Physics-guided algorithm structures (PGAS)’’ improve traditional
ML’s physics consistency by integrating analytical relations from battery degradation models into the design and optimization of ML algorithms, such as the Nernst, Butler–Volmer, Fick’s laws, and Arrhenius
equations [34,36–40]. It replaces ML’s local operators with physical
modules and links them through logical relations between equations
like decoupling voltage and current sequences or differential–algebraic
relations [35,41]. PGAS encodes unknown physics equation parameters as ML trainable parameters, with MLPs modeling corrections
for physics-based computations. For example, internal resistance and
maximum charge are incorporated as trainable parameters that merge
physics with learning [42]. PGAS employs deep structures like DNNs
and Autoencoders [41,42] alongside RNNs and LSTMs. What is important to note is that the deeper the embedded position of physical
knowledge, the stronger the physics constraints on the final output.
[43] PGAS adjusts the local input–output relationships of ML models.
Existing PGAS designs use physical operators as intermediate bilaterals in the ML data flow. This paradigm could negatively impact
results if the embedded knowledge and its integration are not aptly
considered. Moreover, embedding at a superficial layer minimally affects the outcomes regarding physical consistency, while overly deep
embedding rigidifies network outputs, necessitating strict adherence
Applied Energy 384 (2025) 125314
2
W. Deng et al.
Table 1
Integration strategies for physics-based model (PBM) and data-driven model for battery prognostic. (There are three broad forecasting architectures,
namely, A: Sequential Integration, B: Hybrid models, C: Parallel extension). 𝑝ℎ𝑦𝑜𝑢𝑡 is the output features or simulated data of the PBM.
to physical input–output relationships. These constraints culminate in
(1) conflicts between embedding physical knowledge and the inherent
optimization trajectories and boundaries of machine learning, leading
to mutual hindrance; (2) a high dependency on experts’ understanding
Applied Energy 384 (2025) 125314
3
W. Deng et al.
and experience with ML for controlling the embedding method, positioning, and form [44,45]. Accordingly, developing an effective PGAS
is challenging.
Compared to PGAS and PIF, ‘‘Physics-informed training constraints
(PITC)’’ integrates physical constraints directly into the objective function, affecting the optimization of parameters on a global scale, thereby
facilitating machine learning models to approximate physical systems
with reasonable accuracy [46]. PITC incorporates physical knowledge
in two primary forms: (1) Derived from parameter relationships or phenomena, such as charge conservation, electrode averaging equations,
and the assumption of discharge capacity’s monotonic decrease with a
concave downtrend [41,47]. (2) Enforcing outputs to satisfy derived
relationships, often through Partial Differential Equations (PDEs) or
Ordinary Differential Equations (ODEs), such as linking capacity loss
rate to health state, cycle number, initial Solid-Electrolyte Interphase
(SEI) formation, and capacity loss, and solid-phase diffusion equations [42,48]. A novel approach distinct from traditional fixed models
involves calibrating physics-based simulation models to showcase a bidirectional synergy between informed ML and physics. For example, to
adapt to data-driven Long Short-Term Memory (LSTM) networks. This
integration allows for real-time predictions via LSTM, complemented
by precise but delayed health indicator evaluations from simulation
models. An adaptive mechanism triggers model updates with new
simulation data for LSTM retraining if prediction errors surpass a
defined threshold [49]. The problem of solving the governing equations
directly is converted to an optimization problem with a loss function
to find partial differential equation solutions. However, higher-order
or inappropriate PDEs can contaminate the back-propagation gradient and prevent optimal convergence [50]. Forcing physical target
constraints on the output can lead to computationally expensive and
difficult-to-converge model training results.
We assert that the key to addressing the above-mentioned problems
lies in rethinking the relationship between informed knowledge and
the ML module from a novel perspective. Therefore, we advocate for
adopting a parallel (or dual branch) architecture, wherein a portion of
the PIML is incorporated into the ML model as external plug-in modules
for ML. Sections 3 and 4 will detail our proposed approach.
3. Dual-branch physics-informed machine learning framework
The novel physics-informed machine learning model is based on
a dual parallel branch end-to-end framework shown in Fig. 1. The
hybrid model comprising a Physics-Informed (PI) branch and a datadriven branch. The data-driven branch can operate independently as
a standalone data-driven model. The PI branch significantly enhances
the functionality of the data-driven branch by contributing augmented
features 𝑝 to the latent space of the data-driven model. PI branch also
outputs the features 𝑝𝑜𝑢𝑡 for final decision. Without integrating the datadriven branch’s output layer, the standalone PI branch falls short of
generating predictions that align with expectations. Therefore, the PI
branch is a complementary extension to the data-driven branch within
this model.
In detail, the physics-informed (PI) and data-driven branches share
some of their inputs but process them differently. The data-driven
branch processes the integrated input space formed by all measured
samples through an encoding module. Therefore, the dimension of each
training batch is [𝑏𝑎𝑡𝑐ℎ𝑠𝑖𝑧𝑒, 𝑚, 𝑙𝑒𝑛, 𝑛]. This encoding module aims to
uncover latent trends within the same measurement type and hidden
features among different measurements. The architecture of the ‘‘Encoding module’’ and the following ‘‘Final output module’’ are tailored
to specific data processing needs.
Conversely, the PI branch leverages finite physics measurements
selected by the embedded formula as inputs. These inputs are processed
individually or jointly by a finite number of each embedding inputrelated formula 𝑓𝑖
(⋅) in the shallow layer of the PI branch as shown
in Fig. 1. For example, 𝑓2
considers the physical relationship between
the two input variables simultaneously. There are many similar connections between cross-layers that are customized based on the logical
relationships between different equations and parameters encapsulated
in the physical knowledge. The output of each custom layer with 𝑓𝑖(⋅)
as the activation function will be merged to generate two-dimensional
(2D) feature tensors. These 2D features will, on the one hand, be
incorporated into the hidden layer space of the data-driven branch
to provide physical information gain. On the other hand, they will
be fed into the subsequent custom layers which embedded outputrelated physical formulas 𝐹 in the deeper position of the PI branch.
The resulting features 𝑝𝑜𝑢𝑡 that satisfy the physical output relationship
will be incorporated into the final output of the data-driven branch as
physics consistency constraints. The undetermined parameters within
𝑓𝑖(⋅) and 𝐹 serve as learnable parameters within the PI branch, where
the NN weights 𝑤 in custom layers are used to represent the coefficients
of the formula, and the bias 𝑏 is the constant term.
This paper uses a battery solid electrolyte interphase healthy indicator mode for building the formula-embedded layers in the PI branch
as shown in Fig. 2. More details regarding the models are presented in
Sections 3.2 and 3.3.
3.1. End to end input
Raw sensor data are initially truncated to construct the inputs 𝑥𝑖𝑛.
The sliding window technique splits continuous time series data into
overlapping training samples from the start to the end of the monitoring
sequence, as shown in Fig. 3. For instance, when truncating temperature measurements, the sliding window length parameter 𝑚 determines
the number of samples in each window, with each sample having a
fixed dimension of [𝑙𝑒𝑛, 1]. Another parameter, 𝛿, consecutive windows
to ensure the continuity of the truncated samples. Each training sample
gathers data from the period starting at 𝑡
𝑖 + 𝑚 × 𝑙𝑒𝑛, retaining its 2Ddimensional structure for subsequent channel merging and splitting
processes. As a result, each training sample 𝑥𝑖(where 𝑖 = 1, 2, … , 𝑛) has
a dimension of [𝑚, 𝑙𝑒𝑛, 1]. The number of discharge cycles remaining 𝑐𝑖
at the time point 𝑡
𝑖 + 𝑚 × 𝑙𝑒𝑛 is recorded as the sample’s RUL label. The
parameters 𝑙𝑒𝑛 and 𝑚 determine the extent of cyclic data covered in a
training sample. Smaller values of 𝑙𝑒𝑛 and 𝑚 can enhance the proposed
model’s practical value by increasing the data’s granularity and thereby
improving the model’s prediction accuracy.
It is worth noting that within each truncated data segment, we
have used a fixed length of time rather than a fixed number of cycles,
as pinpointing the exact timing of the 3–4 charge/discharge cycles
is difficult and results in a variable length of the input sequence
segments. The window length 𝑙𝑒𝑛 roughly contains the information
of 3–4 complete charge/discharge cycles. Since this is an end-to-end
model for online prediction in real-world applications, ‘‘sample i’’ in
Fig. 3 may start or end at any point within a discharge or charge cycle.
Although the specific start and end points within a cycle can vary,
the fixed time length ensures that the data spans approximately 3–4
cycles. This model’s predictive ability does not rely on complete cycle
granularity, making it more practical for real-world applications.
3.2. End to end data-driven branch
The data-driven branch employs an end-to-end (E2E) deep learning
(DL) paradigm to acquire degradation-related features for the battery
RUL prediction from raw data directly. This approach eliminates the
need for intricate signal processing or expert domain intervention.
The input comprises three parallel channels: temperature, voltage,
and current. The samples within each channel are partitioned into
multiple batches. In each learning batch, these independent physics
measurements are combined through ‘‘Concatenate’’ layers to construct
the inputs 𝑋𝑖𝑛 with the dimension [𝑚, 𝑙𝑒𝑛, 3].
A Dilated convolution Neural Network (D-CNN) is shown in Fig. 4
to demonstrate the application of the E2E paradigm above. D-CNN has
Applied Energy 384 (2025) 125314
4
W. Deng et al.
Fig. 1. Embedding physical knowledge into NN models in the form of parallel architectures.
Fig. 2. SEI informed DCNN model diagram.
a series of dilated convolution layers with increasing dilation factors
(𝑑𝑖𝑙𝑎𝑡𝑒𝑑𝑟𝑎𝑡𝑒) to encapsulate the interdependences between temperature,
voltage, and current concerning the battery’s discharge cycles. By
leveraging dilated convolutions, DCN can encompass larger receptive
fields of each layer by incorporating gaps between weight connections
to build positional jump connections.
Applied Energy 384 (2025) 125314
5
W. Deng et al.
Fig. 3. Truncate the original sequence in a fixed-length time window to construct an end-to-end input.
Fig. 4. Schematic diagram of D-CNN with a data flow.
Subsequently, the final feature representation is obtained through
a dense layer with 𝑑1 neurons, yielding the data-driven feature ℎ𝑙
(dimension: [𝑏𝑎𝑡𝑐ℎ 𝑠𝑖𝑧𝑒, 𝑑1]).
3.3. Physics informed branch
The physics-informed branch utilizes the ‘‘physics-embedded algorithm structure’’ paradigm, as detailed in [45], to obtain the physicsconsistency features and insights relevant to degradation.
The PI branch utilizes the SEI growth formula proposed by Attia
et al. [51] as shown in Eqs. (1) and (2). This approach incorporates temperature-dependent kinetic models to effectively correlate SEI
growth with cycle life, providing a robust and analyzable framework for
predicting degradation under varying charging conditions. In Eq. (1), 𝐷
is the SEI degradation parameter. 𝐷0represents the initial or baseline
SEI degradation parameter. 𝐸𝑎is the effective activation energy for
SEI growth, determined by the Arrhenius relation. 𝑘𝐵 denotes Boltzmann’s constant, a fundamental physical constant. 𝑇 is the monitoring
temperature of the battery. This expression captures the exponential
dependence of SEI degradation, aligning with the Arrhenius equation’s
insights into temperature-dependent chemical processes.
𝐷 = 𝐷0exp (−
𝐸𝑎
𝑘𝐵𝑇
)
(1)
The 𝑝𝑜𝑢𝑡 of is estimated using the equation:
𝑝out =
𝐶
𝐷
+ 𝑏 (2)
In this context, at the data-flow level, the calculation of 𝐷 relies solely
on the temperature input (̂𝑥1), which is processed through a stacked
dense layer to produce the hidden layer output 𝑇̂ . This intermediate representation (𝑇̂) is then transformed using a custom-designed
physics-informed (PI) layer, where the activation function is defined
by Eq. (1). The resulting output, 𝐷, serves as a critical input to the
2D fully connected layer, where it is used to compute 𝑝, a PI-derived
hidden feature. This feature (𝑝) is subsequently integrated into the datadriven branch for feature fusion, as well as the PI branch, to generate
the physically informed insights 𝑝out. 𝑝𝑜𝑢𝑡 refers to an approximate
lifespan indicator, as it is not the final RUL output of the proposed
PIML model. This distinction arises due to the simplified nature of
the models, often incorporating empirical parameters and assumptions
that do not fully capture the complexities of actual battery operation
and degradation phenomena. This formulation emulates the Paris laws
in material fatigue and posits that a battery’s cycle life is inversely
proportional to the rate of SEI degradation, adjusted by the empirical
factor 𝐶.
Considering the input–output relationships and the logical relationship between Eqs. (1) and (2), only the temperature data are taken as
the input of the PI branch. and the cross-layer connections are used
in Fig. 2. Eqs. (1) and (2) are the activation functions of these custom
design layers.
3.4. Merge the two branches’ information
In the output part, the final ‘‘Full connectivity neural network
(FCNN)’’ considers the output 𝑝𝑜𝑢𝑡 of the PI branch in the decisionmaking process and the data insights from feature 𝑝. FCNN is tailored
for the many-to-one process to generate the output of the remaining
discharging cycles.
The data flow processing of the entire PIML framework can be
represented by the following equation. In data-driven branch, the input
tensors 𝑥1, …, 𝑥𝑛 undergo processing through 𝐿 hidden layers, where
each layer progressively extracts higher-level features. This process can
be modeled in Eq. (3):
ℎ
[𝑙] = 𝑔[𝑙]
(
𝐖[𝑙]
ℎ
𝑔
[𝑙−1] (
𝐖[𝑙−1]
ℎ ⋯ 𝑔
[2] (
𝐖[2]
ℎ
𝑔
[1] (
𝐖[1]
ℎ
𝐱 + 𝐛
[1]
ℎ
)
+ 𝐛
[2]
ℎ
)
⋯ +
𝐛
[𝑙−1]
ℎ
)
+ 𝐛
[𝑙]
ℎ
)
(3)
Applied Energy 384 (2025) 125314
6
W. Deng et al.
𝑦 = ℎ𝑓
⎛
⎜
⎜
⎜
⎜
⎜
⎜
⎜
⎜
⎝
Decision fusion
⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞
𝑤1𝑠
[𝑟]
⎛
⎜
⎜
⎜
⎜
⎝
𝐖[𝑟]
𝑑
𝑠
[𝑟−1]
⎛
⎜
⎜
⎜
⎜
⎝
𝐖[𝑟−1]
𝑑 ⋯ 𝑠
[2]
⎛
⎜
⎜
⎜
⎜
⎝
𝐖[2]
𝑑
𝑠
[1]
⎛
⎜
⎜
⎜
⎜
⎝
𝐖[𝑝]
𝑓
𝑝 + 𝐖
[ℎ𝑙]
𝑓
ℎ
[𝑙] + 𝐛
[1]
𝑓
⏟⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏟⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏞⏟
Feature fusion
⎞
⎟
⎟
⎟
⎟
⎠
+ 𝐛
[2]
𝑑
⎞
⎟
⎟
⎟
⎟
⎠
⋯ + 𝐛
[𝑟−2]
𝑑
⎞
⎟
⎟
⎟
⎟
⎠
⎞
⎟
⎟
⎟
⎟
⎠
+ 𝑤2𝑝out + 𝐛
[𝑟]
𝑑
⎞
⎟
⎟
⎟
⎟
⎟
⎟
⎟
⎟
⎠
(5)
Box I.
Each layer apples a linear transformation (via the weights 𝑊 [𝑙] and
biases 𝑏
[𝑙]
) followed by a non-linear activation function 𝑔
[𝑙]
. The final
network output is a continuous transformation product from the inputs
with dimensions [𝑚, 𝑙𝑒𝑛, 𝑛] to the last hidden layer output features ℎ𝑙.
Simultaneously, in 𝐾 layers PI-branch, the entire process can be
represented as a data flow in the NN through Eq. (4):
𝑝 = 𝑔
[𝐾]
(
𝐖[𝐾]
𝑝
𝐹
[𝐾−1] (
𝐖[𝐾−1]
𝑝 ⋯ 𝑔
[2] (
𝐖[2]
𝑝
𝑓
[1] (
𝐖[1]
𝑝
𝐱 + 𝐛
[1]
𝑝
)
+ 𝐛
[2]
𝑝
)
⋯
+𝐛
[𝐾−1]
𝑝
)
+ 𝐛
[𝐾]
𝑝
)
(4)
Comparing Eq. (4) with Eq. (3), it is worth noting that the custom
architecture in the PIML branch replaces the conventional intermediate
hidden layer to represent the physics input–output relationship.
In summary, the complete proposed PIML model can be represented
by Eq. (5) which is given in Box I.
In this context, 𝑝 is defined and elucidated in Eq. (4), while ℎ𝑙is
formulated and expounded upon in Eq. (3). The weights 𝑤1 and 𝑤2
pertain to the final output layer of the proposed PIML model, while
𝐛
[𝑟]
represents the bias associated with this final output layer.
4. A novel PIML training method
The difficulty of successfully combining a small-parameter physicsinformed branch with a large-parameter data-driven branch in parallel
architectures becomes clear when we follow the traditional approach
of directly training the suggested PIML model. This challenge, underscored by Eq. (5), involves balancing physical insights and data-driven
complexities.
In detail, the PI and data-driven branches exhibit notable disparities in the size and complexity of their parameter spaces. Consequently, these differences can lead to inconsistent optimization rates
during training, thereby presenting a formidable obstacle to achieving
simultaneous convergence of the two branches. Furthermore, while
large-parameter branches are susceptible to overfitting, their smallparameter counterparts may suffer from underfitting. Hence, numerous
approaches in the realm of PIML may fall short of achieving the
anticipated synergy between these models, even impeding to preserve
the original data-driven model’s fitting capabilities.
This paper proposes that a novel training method for the proposed
dual branch model. We believe that the starting point for training a
PIML model after embedding physical knowledge should be the original
pre-trained ML model, rather than training it as a completely new
model. Such a PIML model can be guaranteed to perform at the lower
bound of the ML model’s performance by a suitable training method.
Therefore, we develop this branch-independent learning paradigm
which consists of three steps: ‘‘Data-driven pre-training’’, ‘‘Physicsinformed alignment’’, and ‘‘Joint training’’ as shown in Fig. 5.
In ‘‘Step 1: data-driven pretraining’’, only the data-driven branch is
trained, including the ‘‘Feature extractor’’ and the ‘‘Decision module’’.
The parameters of the PI-branch are set to untrainable. In addition, the
PI branch is initialized with a 0-mean to ensure that its output 𝑝 and
𝑝𝑜𝑢𝑡 are 𝟎. At this point, it learns useful weights and biases only for
the data-driven branch, i.e., the error feedback optimizes a data-driven
pre-trained branch.
In ‘‘Step 2: physics-informed alignment’’, the pre-trained ‘‘Feature
extractor’’ in data-driven branch is loaded and frozen with the trainable
‘‘Decision module’’. Meanwhile, the parameters of the PI branch are
initialized randomly and are made trainable. The parameters in the
final FCNN are relearned. In this configuration, the data-driven branch
functions act as a fixed feature extractor for PI branch. The PI branch
will be adapted and optimized concerning the knowledge already available in the data-driven branch, which improves the fit between the two.
On this basis, the whole model is physically aligned.
Given that the pre-trained data-driven branch has already reached
convergence, coupled with the PI branch with a smaller parameter
space, the overall proposed PIML model exhibits enhanced ease of
training. The independent training of the PI and data-driven branches
eliminates the hampering interference of weight coupling during random initialization learning. In particular, compared to existing PIMLs
that require training the entire model from scratch, ‘‘Step 2’’ only
requires training a small number of PI branches with a small number
of parameters, which saves training resources, especially given that
existing public pre-trained models can be used for the data-driven
branch.
After completing ‘‘Step 2’’, it can evaluate the appropriateness,
relevance, and integration of embedded knowledge and the informed
ways after the ‘‘physics-informed alignment’’ training step. It compares
the model’s performance with that of the original pre-trained model. If
there is an improvement, the method deems the knowledge integration
acceptable.
Building upon the preceding steps, this paper proposes ‘‘Step 3:
joint training’’. The fundamental objective of this approach extends
beyond rectifying the inconsistency between the physical insights of
the data-driven approach and the embedded physical knowledge. It
also addresses enhancing the incomplete physical perspectives through
data mining within the data-driven framework. Consequently, once the
data-driven branch has been fine-tuned to a local optimum, demonstrating strong performance, and the PI branch has been optimized to a
local optimum, considering its alignment with the data-driven branch’s
performance, the pre-training weights of the PI branch are loaded.
Subsequently, the weights of the data-driven branch and PI branch
are configured as trainable, enabling the entire model to undergo
retraining. This iterative process aims to bring the model closer to
achieving a global optimal solution for the problem.
As shown in Fig. 6, this approach preserves the original architecture’s ability to fit the data, a feature of considerable importance
for enhancing the generalization and broader applicability of PIML.
Although the traditional PIML learning can add physical consistency
to the ML model, but the physical consistency is there and ML itself
in the data-driven conditions of the optimization objectives are inconsistent or even want to conflict with the situation, want to let a single
model at the same time to meet the existence of potentially conflicting
multiple optimization objectives, the model will appear to end up in
the Pareto surface to take the global sub-optimal solution of the case,
for this reason, we are from the structural design of the model, will
be satisfied with the For this reason, we design the structure to make
the subjects that satisfy different optimization objectives independent
of each other, and at the same time, in the learning strategy, we make
Applied Energy 384 (2025) 125314
7
W. Deng et al.
Fig. 5. Novel PIML learning mechanism: a multi-step learning process based on pre-training and physical alignment in a parallel architecture.
Fig. 6. Schematic illustration of the mechanism of multi-step learning strategies.
the potentially conflicting learning objectives separate from each other,
which guarantees that the final model has the ability to approximate
the better optimum under the condition that the two branches reach
their respective localities and the PI-branch is locally optimal with the
incorporation of the insights of data-driven insights.
This learning paradigm shift is the key to bringing PIML to a wider
world of applications, as it directly allows PIML to use a large number
of mature data-driven pre-trained models to form a wide variety of
PIML models by simply mounting PI-branches loaded with different
knowledge.
5. Case study
5.1. Data description
The fast-charging lithium-ion battery dataset used as case study is
developed by the MIT–Stanford team and described in the article [51].
This dataset comprises three experiments. The battery sets from ‘‘2017-
05’’ and ‘‘2017-06’’ are set up for model training and testing. Initially, a
random data splitting method equally divides the dataset into training
and testing subsets. This involves shuffling the dataset indices before
splitting them into two groups to ensure a balanced partition. As
clarified in [51], the battery sets recorded in ‘‘2018-04’’ are different
from the sets in ‘‘2017-05’’ and ‘‘2017-06’’. It can be used as the second
test set to evaluate the model’s generalization ability on entirely new
data.
5.2. The configuration of the PIML model
Table 2 presents the benchmark model’s data processing and optimized learning hyperparameters for reference.
Combining the optimized DCNN architecture as the data-driven
branch in the proposed PIML framework, the hyperparameters of the
‘‘PI branch’’ and the ‘‘decision network’’ in Fig. 2 are detailed in Table 3.
Additionally, the coefficients utilized in the physics model equations,
Eqs. (1) and (2), are also provided in Table 3 for reference.
5.3. Comparative study
A standard DCNN model developed by Hong et al. [52] serves as
a benchmark model for investigating the superior performance of the
PIML paradigm. The DCNN model has been validated on the MIT–
Stanford dataset [52,53]. In addition to directly referencing the existing
models in the literature that has been validated on the MIT–Stanford
dataset, we further performed structural parameter optimization on the
DCNN in developed by Hong et al. [52] to construct a DCNN that
outperforms the original one. This new DCNN is also used as the model
in the data-driven branch of the SEI-DCN proposed in this paper. The
key distinction between DCNN in SEI-DCN and benchmark model lies in
the presence of a PI branch and the incorporation of ‘‘Physics-informed
alignment’’ and ‘‘Joint training’’ throughout the model. Consequently,
we set the control variables as detailed in Table 4.
Applied Energy 384 (2025) 125314
8
W. Deng et al.
Table 2
Data processing and learning hyperparameters for benchmark experiments.
Parameters Physics meaning/Description Setting
𝑙𝑒𝑛 The length of time represented by the sliding window 2500 (s), approximately 3 4 cycle length
𝛿 The overlap area of two windows 2250 (s)
Hyperparameters
Input channels Number of types of input monitoring quantities 3
Batch size The number of processed samples in one forward and backward pass 256
Input shape Input data shape [Batch size, 1, 2500]
Concatenatein Inputs’ concatenation layer output shape [Batch size, 2500, 3]
Conv1D-Bat𝑛 The number of 1D convolution layers with batch normalization after inputs concatenation 3
Kernel size The 1D convolution layer kernel size 3
Conv1D-Bat𝑑 1D convolution layer output shape [Batch size, 2500, 64]
Dilatedrate Jump interval of dilated convolution [1, 2, 4, 8, 16]
Knum The number of kernels used in 1D convolution layer 64
Padding mode The specific way in NN in which extra values (usually zeros) are added to the edges of input data Casual
Flatten Flattened output shape (None, 160 000)
Stack-Dense 1 3 stacked dense layers as the decision NN in the data-driven branch Knum in each dense layer: [128, 64, 1]
Activation 1 Activation function for all dense and convolution layers ReLU
Optimizer Type of optimizer used Adam (learning rate = 0.001)
Validation ratio How much data is randomly divided in the training set as the validation set 0.2
Loss function Loss function used for model training Mean squared error
Table 3
Hyperparameters in physics informed branch.
Parameters Physics meaning/Description Setting
Units1 Number of neurons corresponding to SEI growth’s Arrhenius equation terms 64
𝐸𝑎 Activation energy parameter in the Arrhenius equation, indicative of SEI growth rate 0.122 eV
𝑘𝐵 Boltzmann constant, relates temperature to energy 1.380649 × 10−23 J/K
𝐷0 Pre-exponential factor in the Arrhenius equation, a rate constant 1.0 s
−1
Extractor
Frozen data-driven branch serves as the feature extractor for the feature fusion and
decision fusion
Inputs: 3 × [Batch size, 1, 2500]
Output 1, data-driven branch feature: [Batch size, 64]
Output 2, data-driven branch RUL: [Batch size, 1]
Fusion𝑑
Number of features from different branches in concatenate layer Concatenate layer dimension: [Batch size, 128]
Feature from data-driven branch: [Batch size, channel 1–64]
Feature from PI branch: [Batch size, channel 64–128]
Dense-PI Dense layer preceding the physics-informed (PI) layer Number of neurons: 64
PI-output Output layer of the PI branch, predicting the physical informed metrics Output dimension: [Batch size, 1]
Stack-Dense 1 Three successive dense layers in the decision-making neural network branch Neurons in each layer: [128, 64, 1]
Activation 2 Activation function for all dense layers in the decision network ReLU
Table 4
Schematic representation of the differences in SEI-DCN compared to the original DCNN model.
Control variables Benchmark DCNN SEI-DCN
Learning strategy One-time supervised training The proposed 3 steps training strategy
Network architecture Multi-Channel Input - Deep Null Convolution -
Stacked Fully Connected Layers Output
Adding a parallel PI branch to the DCNN
Parameters scale 20,559,681 20,749,976
In evaluating the performance of ML models, two key metrics are
commonly employed: the number of monitoring data cycles required
for prediction and the calculation accuracy of the predicted RUL,
which are indicated by the predicted mean absolute error (MAE) of
the remaining discharging cycles. The number of data cycles required
is a critical measure [20] for predicting remaining discharging cycles,
making timely decision-making and achieving efficient resource allocation. In the time span of the sample used to pre-RUL, the less lifecycle
involved, the higher model capacity to make accurate predictions with
limited data. Concurrently, the mean absolute error (MAE) quantifies
the agreement between the model’s predictions and the actual cycle
life, indicating its reliability.
The encoder structure we selected has already been validated on
the benchmark dataset as a published paper in Applied energy [52],
maintaining the same structure, hyperparameters, and sample truncation lengths for consistent comparison. The key difference of our
approach compared to the state-of-the-art DCNN is the addition of
a PI branch and the application of our proposed multi-step training
method. This controlled variable experiment aims to highlight the
specific advantages of our method.
Moreover, our framework is flexible and can accommodate other
data-driven models beyond DCNN. Notable alternatives that effectively
utilize partial cycle information include the bilateral-branched visual
transformer with dilated self-attention or RNN-LSTM. These options are
also worth exploring for their potential benefits, as their ability in this
‘‘small-early cycles’’ scenarios are already detailed in Refs. [54], and
[55].
5.3.1. Comparison with benchmark model in SOTA
Table 5 compares various ML models’ performance. This includes
several SOTA models and the DCNN model reproduced and optimized
specifically in this paper, serving as an ablation study. Table 5 highlights significant advancements in predicting cycle errors for battery life
estimation, with the proposed parallel model standing out by achieving
the lowest predicted MAE of 15 cycles. This outcome is achieved using
a data sample truncated to 2500 s, typically spanning 3 to 4 cycles. It
Applied Energy 384 (2025) 125314
9
W. Deng et al.
Table 5
Performance of different models.
Model Required cycles length Predicted cycle error (MAE)
Shallow MLP [52] 4 150
MLP [52] 4 174
Full model [53] 100 99
Variance [53] 100 112
SVR [52] 100 245
CNN [52] 4 82
CNN + LSTM [52] 4 72
DCNN in research [52] 4 65
DCNN in our research 4 55
The proposed PIML model 4 15
demonstrates that our SEI-DCN can deliver more precise usage insights
with short-term data, enhancing the adaptability of prediction algorithms to real-time user habits. In addition, using a platform equipped
with a single 16 GB NVIDIA T4 Tensor Core GPU, the prediction time
for one test sample is approximately 3.5 × 10−5 s.
5.3.2. Comparison with predictions solely based on the data-driven branch
The qualitative and quantitative comparison is made between the
DCNN model alone and the SEI-DCN model, whose data-driven branch
is identical to the DCNN model in terms of structure, parameters,
inputs, and outputs. The qualitative prediction results are detailed in
Fig. 7, with a detailed quantitative comparison of predictions for each
test cell presented in Fig. 8. Fig. 7’s ‘‘Identity line’’ represents perfect
predictions, where predicted values match true values. The ‘‘Regression
line’’ indicates the general trend of predictions. Ideally, the ‘‘Regression
line’’ should align with the ‘‘Identity line’’. The blue scatter points
show the actual predictions. Results in Fig. 7 reveal that both models
effectively capture the linear decay trend of remaining discharging
cycles. However, our SEI-DCN model outperforms traditional DCNNs
by providing more accurate predictions, aligning better with trends,
reducing prediction deviation, with fewer outliers. This improvement
underscores the value of incorporating physics and tailored learning
strategies, providing the enhanced system security prognostic service.
To further compare the two models, we utilized box plots to visualize
the predictions for each group. Fig. 8 presents the results of this
comparison. The range of Remaining Discharge Cycles (RDC) values
for each test battery is categorized as follows: Test Batteries 1 and 2
have RDC values spanning [0, 1200], while Test Batteries 3, 14, and 15
span [0, 1000]. Batteries 4, 7, 8, 9, 16, 17, and 18 exhibit ranges of
[0, 800], and Test Batteries 6, 19, and 20 span [0, 600]. In contrast, Test
Batteries 21 through 35 primarily fall within [0, 450], except for Test
Battery 30, which uniquely covers [0, 500]. This distribution highlights
the comprehensive evaluation of the model across both extended and
shorter lifecycle ranges, demonstrating its robustness in predicting
battery degradation across varying RDC values.
Both methods accurately predicted the RUL decreasing trend for
batteries with varying lifespans (45 to 1200 remaining charge cycles)
despite the measurements missing gaps (batteries 19, 27). However,
early in the battery life, the DCNN’s predictions are significantly higher
than actual values, in contrast to the more accurate SEI-DCN (our approach) predictions for batteries 4, 11, 12, and 29. This accuracy makes
SEI-DCN more suitable for early-life task planning in fast-charging
batteries. Towards the end of the battery life, with RUL nearing zero,
DCNN’s predictions remained overly optimistic compared to actual values and SEI-DCN predictions for batteries 1, 2, 23, and 28. This suggests
that SEI-DCN provides more reliable information for safely operating
fast-charging batteries in their late degradation stages. Moreover, a
comparison of overall prediction errors revealed that SEI-DCN had a
narrower error distribution with fewer outliers, indicating its greater
robustness and reliability over the purely data-driven DCNN.
It is worth noted that the gap appears in Battery 17 and 29, given
that our model is designed as an end-to-end solution ready for deployment, we did not perform extensive data cleaning, which includes
retaining instances of sparse data. The dataset authors assert [53] that
raw data for each cell is available in CSV format. It is important to
note that the CSV files occasionally exhibit discrepancies in test time
and step time, with test time sometimes resetting to zero mid-cycle.
Additionally, temperature measurements were taken by securing Ttype thermocouples to the exposed battery can with thermal epoxy
(OMEGATHERM 201) and Kapton tape after removing a small portion
of plastic insulation. These temperature measurements are unreliable
due to potential variations in thermal contact between the thermocouples and the battery can. Sometimes, the thermocouples lost contact
during cycling, resulting in data gaps. These errors were considered
while directly reading the raw data, leading to noticeable gaps in the
data for cells 17 and 29. However, the prediction results demonstrate
that the model maintained robust end-to-end predictive capability even
under these conditions. This underscores the reliability of the method,
particularly its ability to make accurate predictions using small-cycle
data without relying on long historical sequences.
In test cell 5, SEI-DCN slightly the underperformed compared to
DCNN, with a predicted MAE of 28 versus 22, even though the upper
and lower quartiles of SEI-DCN’s box plots are closer. This demonstrates
that SEI-DCN has more predicted outliers smaller than the true value
for cell 5, whereas the predicted outliers for the DCNN are all larger
than the true value. Combined with the overall prediction results, we
argue that the predictions of the SEI-DCN are biased towards conservatism by the constraints of knowledge of physics. Moreover, in cells
6 to 9 and 17, SEI-DCN has worse performance with an MAE higher
than 15 compared to its performance in other cells. This suggests the
potential for further model improvements and adjustments to enhance
its generalization across different cells by finding more representative
physics and applying long-term learning.
5.3.3. Comparison of performance robustness test results on new data
without relearn conditions
The performance of the DCNN and SEI-informed DCNN models
are compared on the data collected in experiment ‘‘2018-04’’ without
retraining (see Table 6).
The battery sets recorded in ‘‘2018-04’’ differ from those in ‘‘2017-
05’’ and ‘‘2017-06’’ due to distinct charging policies and resulting
variations in cycle life distributions. The overview of the cycle life
distribution is in Table Table 6. Specifically, the ‘‘2018-04’’ set exhibits
more batteries in the higher cycle life ranges ([1000–1500] and [1500–
2000]), whereas the earlier sets have more batteries in the lower cycle
life ranges ([0–500] and [500–1000]). For instance, the ‘‘2018-04’’
set includes charging policies like 5C(67%)-4C and 5.9C(60%)-3.1C,
which are different from those in ‘‘2017-05’’ and ‘‘2017-06’’ such
as 3.6C(80%)-3.6C and 4C(80%)-4C. These differences highlight the
impact of varied charging protocols on battery degradation patterns,
making the ‘‘2018-04’’ set an ideal second test set to evaluate the
model’s generalization ability on entirely new data. The robustness
testing results are shown in Fig. 9.
In this generalization ability test, several observations are made that
are illustrated in Fig. 9,:
Applied Energy 384 (2025) 125314
10
W. Deng et al.
Fig. 7. Demonstration of predicted trajectory results for remaining discharging cycles of test battery packs.
Fig. 8. Box plots the prediction errors of remaining discharging cycles (RDCs) for DCNN and SEI-DCN (our approach). (The x-axis of each subplot represents the true RUL, while
the y-axis represents the predicted RUL. The embedded boxplot of each subplot has boxes on the left representing the prediction error of DCNN as a benchmark model and boxes
on the right representing the prediction error of SEI-DCN as a PIML model. The number above the boxplot is the predicted MAE).
Applied Energy 384 (2025) 125314
11
W. Deng et al.
Table 6
Cycle life distribution.
Frequency of cycle life distribution 2017-05-12 2017-06-30 2018-04-12
[0–500] 0 35 0
[500–1000] 36 12 21
[1000–1500] 10 1 18
[1500–2000] 0 0 5
Fig. 9. Predicted trajectory results for remaining discharging cycles of test battery packs on the new dataset.
1. It is clear that although the purely DCNN model captures the
overall trend, there is a significant difference between the predicted and actual values, indicating that the accuracy of the
model could be significantly improved.
2. Considering that the RUL span in the training set does not
include the case where the remaining discharging cycle life is
greater than 2000, it can be seen that DCNN does not have
the prediction ability in that case. Still, SEI-DCN does match
the real data significantly better, which proves that SEI-DCN
has a superior generalization ability by embedding physical
knowledge.
3. The predictions of the SEI-DCN model (our approach) have
higher variability on this new dataset, along with outliers with
relatively large deviations from the true values in the deep
degradation stage. However, its performance declined much less
than that of the DCNN.
4. The SEI-DCN model’s MAE is 81. Whereas the pure DCNN is 311,
which quantifies the significant generalization advantage our the
proposed physics informed approach.
5. The sudden increases in deviation observed in Fig. 9 are primarily attributable to the introduction of a new dataset characterized by distinct cycle life ranges and charging policies, coupled
with the limited representation of late-stage battery life samples
in the training data. Specifically, some samples may be nearing
the end of their life cycle, while under similar conditions, other
batteries remain in the midst of their degradation phase. This
overlap results in pronounced deviations, particularly near the
terminal values of the life cycle.
6. Although our PIML model mitigates some of these challenges by
incorporating embedded physical knowledge, further enhancements are necessary to fully capture the complex degradation
behaviors present in the new dataset.
6. Investigating the learning mechanism of the proposed PIML
In this section, our main focus lies in examining the learning mechanism underlying the proposed approaches. This analysis investigates
how the PIML model effectively amalgamates physical and data-driven
knowledge into the prediction process, as detailed in Section 6.1.
Furthermore, we explore the adaptability of the framework and training
methodology for screening embedded physical knowledge in more
detail in Section 6.2.
6.1. Mechanisms for improving data-driven model performance
In a hybrid model that combines data-driven and physics-informed
branches, efficiently exploiting useful features from both branches is
essential. We focus on the proposed PIML model’s treatment of fused
features [ℎ𝑙, 𝑝] within the concatenate layer with dimensions [Batch
size, 128]. This layer effectively merges data-driven features spanning
channels 1 to 64 with PI features spanning channels 64 to 128. We plotted a 3D schematic of the channel weights to illustrate the integration
process, as shown in Fig. 10.
We transformed it from a cartesian coordinate system to a cylindrical coordinate system which unveils the relative significance assigned
to the features from each branch. This visualization is a valuable tool
for understanding the rationale behind the prioritization of certain
features and the consequential impact of their weights on prediction
outcomes. The weights distribution map generated after the two-step
training process reveals a dense matrix of weights across numerous
units in the dense layer. This indicates a comprehensive consideration
of features across various channels during the model’s decision-making
process.
When the model is trained in three steps, Fig. 10(b) shows a sparser
distribution of weights with more pronounced extremes. This suggests
that the model learns to assign more pronounced weights to specific
hidden layer features after completing the three-step joint training
process. This is desirable in many machine learning tasks, as it is often
associated with a more refined and potentially more generalized model.
At this point, the weights for PI branch have decreased in magnitude.
We believe that the knowledge from both branches has been unified
and integrated into a more expressive data-driven branch. Weight distribution analysis reveals that the model selectively emphasizes features
after the joint training step, indicating a more refined and robust
model. The PI branch is a regularization mechanism, guiding the datadriven branch towards a better optimum and enhancing the model’s
generalization ability.
Applied Energy 384 (2025) 125314
12
W. Deng et al.
Fig. 10. Schematic depiction of the modulation in channel weights subsequent to integrating features across various branches during the multi-step learning phases. (The model
above has been trained in the second step, and the model below has been trained in the full three steps.)
6.2. Evaluating the robustness of the PI branch for knowledge switching
To evaluate the flexibility of PI branching in knowledge switching,
this study changes the knowledge model embedded in the PI-branch
while keeping the data-driven branch intact, using a new empirical
SEI model [56] to constrain the output relationship of the PI branch.
The new empirical formula elucidates the relationship between the
thickness (𝐿(𝑡)) of the SEI layer and time (𝑡). It provides the following
Eq. (6):
𝐿(𝑡) =
√
2𝐷𝑠𝐶0
𝑠
𝜖𝑡
𝑐𝑃
(6)
The entire SEI-informed DCNN model is shown in Fig. 11.
The model in Fig. 2 is denoted as ‘‘PIML model 1’’, the model in
Fig. 11 is denoted as ‘‘PIML model 2’’ Their comparison results are
shown in Table 7.
Figs. 11 and 2 illustrate specific application cases of the proposed
framework shown in Fig. 1, demonstrating its generalized performance
in both PIML establishment and application performance assurance.
The primary distinction between these cases lies in the type of knowledge incorporated into the PI branch: the knowledge in Fig. 2 is
derived directly from the dataset, while that in Fig. 11 is sourced
from another SOTA research. These validation cases highlight two key
characteristics of the framework: (1) standardized integration of diverse
physical knowledge, ensuring adaptability across different scenarios
and datasets; and (2) robustness and consistency in model performance,
maintaining reliable outcomes regardless of variations in the incorporated physical knowledge. Together, these attributes showcase the
flexibility and reliability of the framework in accommodating diverse
physical insights while preserving overall model integrity. Table 7
summarizes the performance metrics for two PIML models, each designed with distinct SEI growth knowledge. Within our proposed parallel framework, it becomes evident that models presented in Eqs. (1)
and (2) outperform the model described in Eq. (6) after two steps.
This suggests that PIML model 1 and its incorporation of physics
exhibit superiority within the same data-driven branch and informed
framework.
Another conclusion that can be drawn is that the three-step training process outperforms the two-step training process for both of the
proposed PIML models. Specifically, the MAPE of ‘‘PIML model 1’’
improves from 10.9% to 8.4%, and the cycle error is reduced from
Applied Energy 384 (2025) 125314
13
W. Deng et al.
Fig. 11. SEI layer thickness growth model informed DCNN functional module integration diagram.
Table 7
Performance metrics of different PIML models.
Model Mean absolute percentage error (%) Cycle error (MAE)
After ‘‘Physics-informed
alignment’’ training
After ‘‘Joint
training’’ training
After ‘‘Physics-informed
alignment’’ training
After ‘‘Joint
training’’ training
PIML model 1 10.9 8.4 15 11
PIML model 2 12.7 8.3 17 9
15 to 11. Similarly, the MAPE of PIML Model 2 improved from 12.7%
to 8.3%, and the cycle error was reduced from 17 to 9. Even though
the overall MAPE declined by only a limited number of percentage
points, the actual forecast cyclic error was reduced by a very large
amount. These improvements suggest that the additional training step
effectively enhances the model’s accuracy and ensures the model’s
flexibility in embedding different physics knowledge. This optimization
enables improved generalization and more accurate predictions. This
highlights that even if the initial knowledge is sub-optimal in that it is
not directly generating certain RUL-related metrics, but rather an empirical understanding of changes in system behavior (e.g., SEI thickness
growth), it can be refined through this complementary training step to
achieve superior performance.
7. Conclusion and future works
A generic physics-informed machine learning (PIML) framework for
battery RUL prediction was developed. The PIML framework consists of
two parallel branches: a data-driven model tailored to the requirements
of the task, and a hybrid model that incorporates machine learning
components designed around the input–output dynamics of physical
models. To better coordinate the training of different parts of this
framework, a three-step training strategy was introduced to build an
optimal joint model between two branches. A solid electrolyte interphase healthy indicator model informed dilated convolutional neural
network (SEI-DCN) was developed according to this framework. DCNN
was used to build the data-driven branches of SEI-DCN. The physicsbased model estimates the indicator about solid electrolyte interphase
(SEI) growth is used as the hidden layer of the hybrid model in the
PI branch of SEI-DCN. SEI-DCN was validated on the MIT–Stanford
fast-charging lithium-ion battery dataset and compared to other models
in SOTA. The results demonstrate that our method outperforms SOTA
models. The SEI-DCN achieved a mean absolute error (MAE) of 15 using
only 4 lifecycle data, whereas the conventional DCNN, despite having
the same structure, hyperparameters, and pre-learned weights as the
SEI-DCN’s data-driven branches, had an MAE of 65. Furthermore, absent re-learning, data-driven DCNN models lost their predictive ability
for completely new data that is different from the training dataset.
Compared to the 311 MAE of DCNN, the SEI-DCN model has an MAE of
81, which maintained the prediction accuracy and achieved the average
level in SOTA on the new data testing.
This study also assessed how well the PI branch could accommodate
knowledge exchange across different SEI models. It was observed that
replacing the SEI degradation model with a model estimating SEI layer
thickness resulted in poorer performance (MAE of 17) compared to the
original SEI-DCN model (MAE of 15) when the SEI-DCN underwent
only the initial two-step training, halting at the ‘‘Physics alignment’’
stage. However, completing the ‘‘Joint training’’ third step improved
the performance of the SEI layer thickness estimation model informed
DCNN, yielding an MAE of 9, comparable to the original SEI-DCN’s
MAE of 11. These findings suggest that evaluating a model’s performance after two-step training can gauge the efficacy of the integrated
knowledge and the adopted paradigm. The co-training third step has
the potential to notably enhance the model’s performance, especially
when incorporating sub-optimal knowledge or embedding knowledge
in sub-optimal methods.
Currently, PI and data-driven branches integrate at the level of
hidden layer features and outputs. Future work should concentrate on
Applied Energy 384 (2025) 125314
14
W. Deng et al.
more advanced integration techniques, specifically the dynamic position adjustment of the PI output’s embedding within the data-driven
branch. This would involve varying the embedding across different
layers in response to changes in inputs and targets. Additionally, the
process through which embedded physics knowledge influences both
branches warrants more research. In the end, more cross-disciplinary
and cross-application research using the framework or similar PIML architectural approaches is desired to promote PIML development. While
the current study focuses on SEI growth as the dominant degradation
mechanism under the experimental conditions of the MIT–Stanford
dataset, future work should consider the roles of LLI (Loss of Lithium
Inventory) and LAM (Loss of Active Material) to better capture the
complex, intertwined degradation processes in real-world scenarios.
Integrating models for LLI and LAM into the framework will enable a
more comprehensive assessment of their combined effects, improving
the prediction and understanding of battery degradation across diverse
operating conditions. Moreover, Capacity diving — characterized by
a nonlinear and rapid decline in battery capacity, arises from factors such as lithium metal deposition, electrode saturation, abnormal
resistance growth, and mechanical deformations. While our dataset
does not explicitly represent these mechanisms, our approach provides
systematic pathways for addressing this challenge through staged and
intelligent charging protocols, material and thermal management enhancements, and advanced battery management systems (BMS). By
integrating physicochemical optimizations, such as improved electrode
materials and thermal regulation, with dynamic model learning in the
building advanced BMS. Extending our approach to the BMS involves
real-time monitoring of battery status and developing dynamic model
parameter learning mechanisms linked to charging parameters. Such
advancements would protect the battery from overcharging and other
adverse conditions, thereby actively preventing Capacity diving.
CRediT authorship contribution statement
Weikun Deng: Writing – original draft, Visualization, Software,
Methodology, Investigation, Formal analysis, Data curation, Conceptualization. Hung Le: Investigation, Formal analysis, Data curation.
Khanh T.P. Nguyen: Writing – review & editing, Supervision, Conceptualization. Christian Gogu: Writing – review & editing, Supervision,
Methodology, Funding acquisition, Conceptualization. Kamal Medjaher: Writing – review & editing, Supervision, Resources, Project
administration. Jérôme Morio: Writing – review & editing, Supervision, Formal analysis. Dazhong Wu: Writing – review & editing,
Supervision, Resources, Formal analysis.
Declaration of competing interest
The authors declare that they have no known competing financial interests or personal relationships that could have appeared to
influence the work reported in this paper.
Acknowledgments
This research was in part supported by the Thomas Jefferson Fund
of the Embassy of France in the United States and the FACE Foundation,
United States. This research also extends its gratitude to Tarbes and the
X-IMS ANR project for their valuable support.
Data availability
Data will be made available on request.
References
[1] Li P, Zhang Z, Grosu R, Deng Z, Hou J, Rong Y, Wu R. An end-to-end
neural network framework for state-of-health estimation and remaining useful
life prediction of electric vehicle lithium batteries. Renew Sustain Energy Rev
2022;156:111843.
[2] Sebastian SS, Dong B, Zerrin T, Pena PA, Akhavi AS, Li Y, Ozkan CS, Ozkan M.
Adaptive fast charging methodology for commercial Li-ion batteries based on the
internal resistance spectrum. Energy Storage 2020;2(4):e141.
[3] Che Y, Hu X, Lin X, Guo J, Teodorescu R. Health prognostics for lithium-ion
batteries: mechanisms, methods, and prospects. Energy Environ Sci 2023.
[4] O’Kane SE, Ai W, Madabattula G, Alonso-Alvarez D, Timms R, Sulzer V, Edge JS,
Wu B, Offer GJ, Marinescu M. Lithium-ion battery degradation: how to model
it. Phys Chem Chem Phys 2022;24(13):7909–22.
[5] Sadabadi KK, Jin X, Rizzoni G. Prediction of remaining useful life for a composite
electrode lithium ion battery cell using an electrochemical model to estimate the
state of health. J Power Sources 2021;481:228861.
[6] Tang X, Zou C, Yao K, Lu J, Xia Y, Gao F. Aging trajectory prediction for
lithium-ion batteries via model migration and Bayesian Monte Carlo method.
Appl Energy 2019;254:113591.
[7] Varini M, Campana PE, Lindbergh G. A semi-empirical, electrochemistry-based
model for Li-ion battery performance prediction over lifetime. J Energy Storage
2019;25:100819.
[8] Yang X-G, Leng Y, Zhang G, Ge S, Wang C-Y. Modeling of lithium plating induced
aging of lithium-ion batteries: Transition from linear to nonlinear aging. J Power
Sources 2017;360:28–40.
[9] Lucu M, Martinez-Laserna E, Gandiaga I, Camblong H. A critical review on
self-adaptive Li-ion battery ageing models. J Power Sources 2018;401:85–101.
[10] Li Y, Liu K, Foley AM, Zülke A, Berecibar M, Nanini-Maury E, Van Mierlo J,
Hoster HE. Data-driven health estimation and lifetime prediction of lithium-ion
batteries: A review. Renew Sustain Energy Rev 2019;113:109254.
[11] Zhang Y, Wik T, Bergström J, Pecht M, Zou C. A machine learning-based
framework for online prediction of battery ageing trajectory and lifetime using
histogram data. J Power Sources 2022;526:231110.
[12] Liu W, Liu P, Mitlin D. Review of emerging concepts in SEI analysis and artificial
SEI membranes for lithium, sodium, and potassium metal battery anodes. Adv
Energy Mater 2020;10(43):2002297.
[13] Chen X-R, Zhao B-C, Yan C, Zhang Q. Review on Li deposition in working
batteries: from nucleation to early growth. Adv Mater 2021;33(8):2004128.
[14] Barcellona S, Piegari L. Effect of current on cycle aging of lithium ion batteries.
J Energy Storage 2020;29:101310.
[15] Reniers JM, Mulder G, Howey DA. Review and performance comparison of
mechanical-chemical degradation models for lithium-ion batteries. J Electrochem
Soc 2019;166(14):A3189–200.
[16] Wei Z, Hu J, Li Y, He H, Li W, Sauer DU. Hierarchical soft measurement of load
current and state of charge for future smart lithium-ion batteries. Appl Energy
2022;307:118246.
[17] Rauf H, Khalid M, Arshad N. Machine learning in state of health and remaining
useful life estimation: Theoretical and technological development in battery
degradation modelling. Renew Sustain Energy Rev 2022;156:111903.
[18] Zhang Y, Li Y-F. Prognostics and health management of lithium-ion battery using
deep learning methods: A review. Renew Sustain Energy Rev 2022;161:112282.
[19] Lipu MH, Ansari S, Miah MS, Meraj ST, Hasan K, Shihavuddin A, Hannan M, Muttaqi KM, Hussain A. Deep learning enabled state of charge, state of health and
remaining useful life estimation for smart battery management system: Methods,
implementations, issues and prospects. J Energy Storage 2022;55:105752.
[20] Kohtz S, Xu Y, Zheng Z, Wang P. Physics-informed machine learning model for
battery state of health prognostics using partial charging segments. Mech Syst
Signal Process 2022;172:109002.
[21] Fei Z, Zhang Z, Yang F, Tsui K-L. Deep learning powered rapid lifetime
classification of lithium-ion batteries. ETransportation 2023;18:100286.
[22] Fei Z, Zhang Z, Yang F, Tsui K-L. A deep attention-assisted and memoryaugmented temporal convolutional network based model for rapid lithium-ion
battery remaining useful life predictions with limited data. J Energy Storage
2023;62:106903.
[23] Fei Z, Zhang Z, Yang F, Tsui K-L, Li L. Early-stage lifetime prediction for lithiumion batteries: A deep learning framework jointly considering machine-learned and
handcrafted data features. J Energy Storage 2022;52:104936.
[24] Karniadakis GE, Kevrekidis IG, Lu L, Perdikaris P, Wang S, Yang L.
Physics-informed machine learning. Nat Rev Phys 2021;3(6):422–40.
[25] Aykol M, Gopal CB, Anapolsky A, Herring PK, van Vlijmen B, Berliner MD,
Bazant MZ, Braatz RD, Chueh WC, Storey BD. Perspective—combining
physics and machine learning to predict battery lifetime. J Electrochem Soc
2021;168(3):030525.
[26] Finegan DP, Zhu J, Feng X, Keyser M, Ulmefors M, Li W, Bazant MZ, Cooper SJ.
The application of data-driven methods and physics-based learning for improving
battery safety. Joule 2021;5(2):316–29.
[27] Guo W, Sun Z, Vilsen SB, Meng J, Stroe DI. Review of ‘‘grey box’’ lifetime
modeling for lithium-ion battery: Combining physics and data-driven methods.
J Energy Storage 2022;56:105992.
Applied Energy 384 (2025) 125314
15
W. Deng et al.
[28] Zhang Y, Zhao M. Cloud-based in-situ battery life prediction and classification
using machine learning. Energy Storage Mater 2023.
[29] Duquesnoy M, Liu C, Dominguez DZ, Kumar V, Ayerbe E, Franco AA. Machine
learning-assisted multi-objective optimization of battery manufacturing from
synthetic data generated by physics-based simulations. Energy Storage Mater
2023;56:50–61.
[30] Xu L, Deng Z, Xie Y, Lin X, Hu X. A novel hybrid physics-based and data-driven
approach for degradation trajectory prediction in Li-ion batteries. IEEE Trans
Transp Electr 2022.
[31] Li W, Zhang J, Ringbeck F, Jöst D, Zhang L, Wei Z, Sauer DU. Physics-informed
neural networks for electrode-level state estimation in lithium-ion batteries. J
Power Sources 2021;506:230034.
[32] Zhang Y, Feng X, Zhao M, Xiong R. In-situ battery life prognostics amid mixed
operation conditions using physics-driven machine learning. J Power Sources
2023;577:233246.
[33] Xu X, Tang S, Han X, Lu L, Wu Y, Yu C, Sun X, Xie J, Feng X, Ouyang M.
Fast capacity prediction of lithium-ion batteries using aging mechanisminformed bidirectional long short-term memory network. Reliab Eng Syst Saf
2023;234:109185.
[34] Shi J, Rivera A, Wu D. Battery health management using physics-informed machine learning: Online degradation modeling and remaining useful life prediction.
Mech Syst Signal Process 2022;179:109347.
[35] Tian J, Xiong R, Lu J, Chen C, Shen W. Battery state-of-charge estimation
amid dynamic usage with physics-informed deep learning. Energy Storage Mater
2022;50:718–29.
[36] Nascimento RG, Corbetta M, Kulkarni CS, Viana FA. Hybrid physics-informed
neural networks for lithium-ion battery modeling and prognosis. J Power Sources
2021;513:230526.
[37] Nascimento RG, Viana FA, Corbetta M, Kulkarni CS. A framework for Li-ion
battery prognosis based on hybrid Bayesian physics-informed neural networks.
Sci Rep 2023;13(1):13856.
[38] Fernández J, Corbetta M, Kulkarni CS, Chiachío J, Chiachío M. Training of
physics-informed Bayesian neural networks with ABC-SS for prognostic of Li-ion
batteries. Comput Ind 2024;155:104058.
[39] Giorgiani do Nascimento R, Viana F, Corbetta M, Kulkarni CS. Usage-based lifing
of lithium-ion battery with hybrid physics-informed neural networks. In: AIAA
aviation 2021 forum. 2021, p. 3046.
[40] Giorgiani do Nascimento R, Viana F, Corbetta M, Kulkarni CS. Quantifying uncertainty in Li-ion battery aging due to unknown usage with hybrid
physics-informed neural networks. In: AIAA scitech 2023 forum. 2023, p. 0536.
[41] Huang Y, Zou C, Li Y, Wik T. MINN: Learning the dynamics of differentialalgebraic equations and application to battery modeling. 2023, arXiv preprint
arXiv:2304.14422.
[42] Wen P, Ye Z-S, Li Y, Chen S, Xie P, Zhao S. Physics-informed neural networks
for prognostics and health management of lithium-ion batteries. IEEE Trans Intell
Veh 2023.
[43] Ngo Q-H, Nguyen BLH, Vu TV, Zhang J, Ngo T. Physics-informed graphical
neural network for power system state estimation. Appl Energy 2024;358:122602.
[44] Xu Y, Kohtz S, Boakye J, Gardoni P, Wang P. Physics-informed machine learning
for reliability and systems safety applications: State of the art and challenges.
Reliab Eng Syst Saf 2023;230:108900.
[45] Weikun D, Nguyen KT, Medjaher K, Christian G, Morio J. Physics-informed
machine learning in prognostics and health management: State of the art and
challenges. Appl Math Model 2023;124:325–52.
[46] Navidi S, Thelen A, Li T, Hu C. Physics-informed neural networks for degradation
diagnostics of lithium-ion batteries. In: International design engineering technical
conferences and computers and information in engineering conference. Vol.
87301, American Society of Mechanical Engineers; 2023, V03AT03A049.
[47] Najera-Flores DA, Hu Z, Chadha M, Todd MD. A physics-constrained Bayesian
neural network for battery remaining useful life prediction. Appl Math Model
2023.
[48] Zheng Q, Yin X, Zhang D. State-space modeling for electrochemical performance
of Li-ion batteries with physics-informed deep operator networks. J Energy
Storage 2023;73:109244.
[49] Sun B, Pan J, Wu Z, Xia Q, Wang Z, Ren Y, Yang D, Guo X, Feng Q. Adaptive
evolution enhanced physics-informed neural networks for time-variant health
prognosis of lithium-ion batteries. J Power Sources 2023;556:232432.
[50] Basir S. Investigating and mitigating failure modes in physics-informed neural
networks (pinns). 2022, arXiv preprint arXiv:2209.09988.
[51] Attia PM, Grover A, Jin N, Severson KA, Markov TM, Liao Y-H, Chen MH,
Cheong B, Perkins N, Yang Z, et al. Closed-loop optimization of fast-charging
protocols for batteries with machine learning. Nature 2020;578(7795):397–402.
[52] Hong J, Lee D, Jeong E-R, Yi Y. Towards the swift prediction of the remaining
useful life of lithium-ion batteries with end-to-end deep learning. Appl Energy
2020;278:115646.
[53] Severson KA, Attia PM, Jin N, Perkins N, Jiang B, Yang Z, Chen MH, Aykol M,
Herring PK, Fraggedakis D, et al. Data-driven prediction of battery cycle life
before capacity degradation. Nat Energy 2019;4(5):383–91.
[54] Fei Z, Zhang Z, Tsui K-L. Deep learning powered online battery health estimation
considering multitimescale aging dynamics and partial charging information.
IEEE Trans Transp Electr 2023;10(1):42–54.
[55] Chinomona B, Chung C, Chang L-K, Su W-C, Tsai M-C. Long short-term memory
approach to estimate battery remaining useful life using partial data. IEEE Access
2020;8:165419–31.
[56] Kamyab N, Weidner JW, White RE. Mixed mode growth model for the solid
electrolyte interface (SEI). J Electrochem Soc 2019;166(2):A334.
Applied Energy 384 (2025) 125314
16