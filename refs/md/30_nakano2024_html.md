# Advancing state of health estimation for electric vehicles: Transformer-based approach leveraging real-world data ☆
URL: https://www.sciencedirect.com/science/article/pii/S266679242400026X

Advancing state of health estimation for electric vehicles: Transformer-based approach leveraging real-world data - ScienceDirect

- Download full issue
- View PDF

Search ScienceDirect

## Advances in Applied Energy

Volume 16, December 2024, 100188

# Advancing state of health estimation for electric vehicles: Transformer-based approach leveraging real-world data☆

Kosaku Nakano a, Sophia Vögler b, Kenji Tanaka a

Show more

Outline

Add to Mendeley

https://doi.org/10.1016/j.adapen.2024.100188 Get rights and content

Under a Creative Commons license

Open access

## Highlights

•

A transformer for estimating battery health in electric vehicles is proposed.

•

A real-world electric vehicle dataset with reliable state of health labels is used.

•

Our model accurately estimates state of health using single-trip operation data.

•

Pre-training with unlabeled data enhances the model’s predictive performance.

•

Attention intensity analysis clarifies the model’s estimation process.

- Next article in issue
- Previous article in issue

## Keywords

Lithium-ion battery

Electric vehicle

State of health estimation

Deep learning

Transformer

## Nomenclature

### Abbreviations

BN

Batch normalization

CCCV

Constant current constant voltage

CNN

Convolutional neural network

DoD

Depth of discharge

EV

Electric vehicle

FFN

Feed-forward network

IC

Incremental capacity

IEA

International Energy Agency

LiB

Lithium-ion battery

LN

Layer normalization

LSTM

Long short-term memory

MAE

Mean absolute error

MHA

Multi-head attention

MLP

Multi-layer perceptron

MSE

Mean squared error

OCV

Open-circuit voltage

RMSE

Root mean squared error

RPT

Reference performance test

RUL

Remaining useful life

SA

Self-attention

SOC

State of charge

SOH

State of health

### Symbols

α

Ratio of labeled training data

γ

Learning rate decay factor

b

Bias vector

P

Positional encoding

W

Weight matrix

x

Input data

z

Latent representation

D

Dataset

L

Loss function

C

Number of data channels

d

Embedding dimension

E

Energy capacity

f

Model function

k

Kernel size of convolutional layers

L

Number of 1D-convolutional layers

M

Number of samples in dataset

m

Accumulated mileage

N

Number of transformer blocks

p

Probability

s

Stride of convolutional layers

T

Number of data points

y

SOH

### Subscripts

ℓ

Index for convolutional blocks

cls

CLS token

h

Attention head index

k1,k2

SOH reference points

k

Key in attention mechanism

o

Output of attention mechanism

q

Query in attention mechanism

v

Value in attention mechanism

### Superscripts

(i)

Index for samples in dataset

0

First token of sequence

## 1. Introduction

Electric vehicles (EVs) play a pivotal role in decarbonizing the road transport sector, which accounts for over 15% of global energy-related emissions [1]. The growing awareness of EVs’ environmental benefits has led to a significant increase in their adoption, with global sales projected to reach 35% of total vehicle sales by 2030 [2]. A critical component of EVs is their battery system, primarily lithium-ion batteries (LiBs) [3], chosen for their high energy and power density [4], [5], [6]. However, these batteries face a significant challenge: degradation in power and capacity over time [7]. This degradation, influenced by factors such as state of charge (SOC), temperature, voltage, and current, critically affects battery safety and performance [8], [9], [10]. Moreover, the fact that the degree of degradation cannot be directly measured [11] further complicates this challenge.

To quantify battery degradation, the State of Health (SOH) serves as a crucial metric [12]. SOH represents the current condition of a battery relative to its ideal, unused state. Accurate SOH estimation in EVs is vital for several reasons. Firstly, it ensures vehicle safety and performance during operation [13]. Secondly, it enables efficient battery management, reducing ownership costs [13], [14]. Thirdly, it optimizes the battery supply chain, informing decisions on recycling, reuse, or repurposing of retiring batteries [15]. This optimization is particularly important given the increasing number of retiring EVs [16]. Lastly, it aids in planning for sustainable sourcing of critical battery materials. This planning is critical in the clean energy transition [17], especially given the rising geopolitical competition over those materials [18]. Given these critical applications and the inherent difficulty in measuring degradation directly, developing accurate SOH estimation methods for EVs is essential for supporting the sustainable transition to electric mobility. Particularly, online SOH estimation, which does not disrupt regular battery use during the estimation process, is more suitable for EV applications as it allows for continuous monitoring without impacting vehicle operation.

Due to the critical nature of accurately estimating SOH for EVs, various methods have been proposed to estimate SOH online. These methods include Coulomb counting methods, which integrate currents and open circuit voltage (OCV) based methods [19]. Furthermore, the field has seen substantial contributions due to the advancements of machine learning, with numerous data-driven approaches being explored [20]. More recently, attention-based deep learning models, particularly Transformers, have inspired researchers to propose SOH estimation strategies utilizing attention mechanisms or Transformer architectures [21], and they show promising results, (which is reviewed in Section 2.1).

The studies of SOH estimation techniques can be categorized into two clusters based on data types: lab-experimented and real-world operational data-based studies. In lab-experimented data-based SOH estimation studies, a variety of methods have been proposed [22], [23]. These methods, though precise under controlled conditions, fall short in real-world EV applications for two primary reasons. First, they rely on cell-level data to estimate SOH, but such data is often inaccessible in EV application contexts [24]. Second, these methods typically rely on controlled lab settings with consistent charging and discharging conditions. They often assume uniform cycle intervals, depth of discharge (DoD), and temperature, sometimes even presuming full charge–discharge cycles. However, in real-world scenarios, these factors vary significantly and greatly influence battery degradation [25], [26]. Moreover, while lab battery cycle tests can emulate driving patterns, synthetic driving cycles fail to accurately replicate the impact of real driving profiles on battery cell lifetime and degradation [27]. This mismatch between lab-derived data and real-world conditions can lead to SOH estimation models that are less effective when applied outside the laboratory, failing to accurately predict the battery’s health under real operational stresses. Although some laboratory-based studies have attempted to simulate real-world conditions through partial cycles or complex operations (reviewed in Section 2.1), their effectiveness in actual operational conditions of EVs has not been empirically validated. Meanwhile, studies based on real-world EV operational data have shown significant progress [28], [29], yet still face challenges such as unreliable reference SOH and limited applicability across diverse real-world scenarios. A detailed literature review of these studies is provided in Section 2.2.

In this study, we introduce a SOH estimation Transformer for Electric Cars (SOH-TEC) to tackle these challenges by leveraging complex, noisy, real-world EV operation data. While there are several definitions of SOH [30], this study focuses on energy capacity-based SOH, which is a critical factor directly related to the cruising range in EVs. SOH-TEC incorporates a transformer encoder [31], inspired by recent high-performing SOH estimation works [21]. This architecture processes raw vehicle and battery data from individual trips, eliminating the need for feature engineering and enhancing applicability across diverse real-world driving scenarios.

SOH-TEC is trained and evaluated in a supervised manner using real-world EV operation data collected over a period of nearly three years from three EVs in Japan. This approach marks a significant departure from traditional lab-based studies, directly addressing the gap between controlled experimental conditions and the complexities of real-world applications. While labeling accurate SOH in real-world EVs is challenging in the lab environment [32], we address this by periodically conducting reference performance tests (RPTs) for each vehicle to obtain reliable reference SOH. This test involves a constant-current full-discharge test under 25 °C using a chassis dynamometer.

SOH-TEC utilizes vehicle dynamics and battery profiles during the driving session, or the discharging process, because the controlled charging process in our dataset may not fully capture uncontrolled diverse real-world scenarios. Additionally, the discharging process is less explored in existing research, primarily due to the challenges of replicating these conditions in a laboratory setting. This focus allows us to provide new insights into SOH estimation, filling a critical gap in the field. Moreover, SOH-TEC offers an optional pre-training phase using EV operation data without SOH labels to improve the model’s predictive capabilities in a subsequent SOH estimation task. We propose two pre-training methods: masked token prediction and SOH ordinal comparison. This pre-training is crucial for practical applications, as acquiring SOH labels is time-consuming and expensive.

We evaluate SOH-TEC through three experiments: (1) using entire trips as input, (2) using partial trips with only urban driving segments, and (3) investigating pre-training strategies with unlabeled data followed by fine-tuning with limited labeled data. The first two experiments assess the model’s foundational predictive capability without pre-training through the comparison with baseline models, while the third explores the effectiveness of pre-training. In addition to these experiments, our study provides insights into the model’s development and dataset design. We analyze the self-attention map to identify the model’s focus areas and conduct ablation studies to determine optimal settings. Additionally, we discuss strategies for future data collection to address current dataset limitations, such as route diversity and repetitiveness.

To the best of our knowledge, this is the first study to propose a transformer-based SOH estimation model for EVs using real-world operation data. Our main contributions are summarized as follows:

•

We develop the transformer-based EV SOH estimation model, SOH-TEC, that processes raw EV operation data from a single trip (Section 3). We also introduce an optional pre-training phase using data without SOH labels. We confirm the effectiveness of the model and the pre-training through experiments (Sections 5 Experimental setup, 6 Experiments).

•

We create a real-world EV operation dataset with reliable reference SOH to evaluate SOH-TEC’s performance in diverse driving conditions (Section 4). The reference SOH labels are obtained by conducting periodical RPTs.

•

We reveal through a self-attention map analysis that the model focuses on specific driving conditions, such as stationary periods and consistent driving segments (Section 7.1).

•

We analyze the impact of hyperparameters on SOH-TEC’s performance and identify the optimal configurations through ablation studies (Section 7.2).

•

We provide insights for future dataset creation, proposing strategies to enhance data diversity and systematic collection (Section 7.3).

## 2. Related work

This section provides a comprehensive review of recent SOH estimation studies, focusing on two key areas: studies that leverage attention mechanisms, and work that utilizes actual EV operational data.

### 2.1. Attention-based SOH estimation studies

Inspired by recent advancements in models utilizing attention mechanisms, including the Transformer, researchers have started applying these techniques to various battery-related tasks. These tasks include SOC estimation [33], [34] and battery aging related tasks such as remaining useful life (RUL) prediction [35], early life prediction [36], end of discharge prediction [37] and degradation mode estimation [38].

In parallel, similar approaches have been developed for SOH estimation, highlighting the broad applicability and effectiveness of attention-based models in battery monitoring and diagnostics. Several researchers approach SOH estimation as a time-series prediction task using attention-based models such as the combination of attention and mixture of expert [39], Transformer [40], [41], and Temporal Fusion Transformer [42]. In this formulation, models forecast the SOH value (yt) at time step t, based on historical data (y1:t−1) and/or other relevant variables. However, this formulation assumes the availability of the past SOH or consistent usage pattern, which is not the case in the real-world scenario.

A lot of studies have succeeded in applying attention-based models to online SOH estimation under lab-controlled conditions. The most conventional approach is using the model to process features (or health indicators) extracted based on the domain knowledge [26], [43], [44], [45]. This approach is effective for estimating the SOH of LiBs under controlled conditions, but it may not be directly applicable to real-world scenarios due to the difficulty of extracting features from complex real-world operation data.

Taking advantage of the attention-based models’ ability to process sequences, various studies have proposed approaches that do not rely on domain knowledge-based features. Fan et al. [46] combined Transformer with Long Short-Term Memory (LSTM), while Zou et al. [47] introduced a Deep Cycle Attention Network for SOH estimation. Gao et al. [48] utilized PCC analysis for feature sequence selection before applying a Transformer. Chen et al. [49] adapted the Vision Transformer for SOH estimation, and Bai et al. [50] proposed a Convolutional Transformer-based multi-view information perception framework. Shi et al. [51] developed a Transformer-based model incorporating a dual-encoder architecture and a gating mechanism. These diverse approaches demonstrate the flexibility and potential of attention-based models in SOH estimation tasks. Notable among these studies are the works of Gu et al. [22] and Cai et al. [52]. Gu et al. [22] proposed a convolutional neural network (CNN)-Transformer model, processing feature sequences created with PCC and principal component analysis. Cai et al. [52] developed a CNN-attention model capable of simultaneously estimating SOC, SOH, and RUL, showcasing the potential for multi-task learning in battery diagnostics. Although these studies have made significant contributions, they face limitations in real-world applications due to their dependence on controlled laboratory conditions, including constant current discharge, uniform charging patterns, and complete charge–discharge cycles.

To tackle these challenges, recent studies have begun to focus on more realistic scenarios that better reflect the complexities of EV operation in the real world. For instance, Ke et al. [53] developed a temporal convolutional network with a self-attention mechanism to estimate SOH of battery cells cycled on driving profiles based on their charging process. Tang et al. [54] introduced a method capable of estimating SOH from partial charging profiles, addressing the common scenario where EVs rarely experience full charge–discharge cycles. Sun et al. [55] designed a dual-branch CNN transformer for estimating SOH from a fast-charging profile with an arbitrary SOC range. Chen et al. [56] proposed a self-attention knowledge domain adaptation network. Their model can estimate SOH from shallow cycle data by leveraging knowledge transfer from labeled full cycle data. While these studies on complex battery operations have primarily focused on the charging process, which is a valuable research direction, they still rely on lab-experiment data-based studies and their applicability to real-world EV users’ uncontrolled charging behavior remains unconfirmed.

### 2.2. SOH estimation studies based on EV data

In this section, we review recent studies on SOH estimation based on EV data. While these studies have made valuable contributions, they still need improvement in terms of limited applicability to real-world scenarios and unreliable reference SOH values.

Some researchers have focused on estimating the resistance-based SOH of LiBs using EV operation data. For example, Giordano et al. [57] defined SOH as the 10-second discharge resistance and introduced a model-based estimation approach. Similarly, Wang et al. [15] predicted the internal resistance of EVs as a measure of SOH, treating it as a time-series prediction task. While these resistance-based methods show promise, they currently lack applicability in estimating capacity fade.

In contrast, many studies focus on estimating capacity-based SOH. Zhang et al. [58] utilized a dataset of 7,296 plug-in hybrid EVs to recursively estimate capacity fade at each time step. However, this recursive approach accumulates errors, which may limit its usefulness in practical applications. Further exploring capacity-based approaches, She et al. [59] developed a radial basis function neural network to predict the incremental capacity (IC) curve peak value, which is a key indicator in battery aging. Zhao et al. [60] devised an extreme learning machine-based SOH estimation framework where the target SOH was modeled as a function of accumulated mileage. Similarly, Song et al. [61] estimated SOH using a feed-forward network (FFN) and evaluated their method on a dataset from 700 EVs. Although these studies achieved high performance and offer valuable insights, they rely on mileage as an input feature. This reliance may not be suitable for vehicles that do not drive consistently, particularly those for which calendar degradation is the predominant mode of deterioration.

Another notable approach is presented by Wen et al. [28], who proposed the NGBoost model to estimate the reference capacity computed by ampere-time integration divided by depth of charge. However, this method’s reliability is impacted by SOC inaccuracies and temperature effects. Addressing these issues, Liu et al. [29] pointed out the problems of this ampere-time integration and introduced an improved integration method. Their method focused on identifying segments where SOC estimation is most accurate, enhancing reliability. Despite its accuracy, this method requires specific conditions for application, such as certain EV rest durations and SOC ranges, which may not be universally applicable in real-world scenarios. Lastly, Zhao et al. [62] employed machine learning models to predict cell-level capacity and pack-level RUL of EV batteries, utilizing features derived from IC and differential voltage analysis. While their approach demonstrates robustness, the authors noted that their method lacks applicability in uncontrolled charging scenarios, including partial and fast charging, which are common in everyday EV usage.

## 3. SOH-TEC: SOH estimation transformer for electric cars

The SOH-TEC model estimates the SOH using EV operation data from a single trip, as depicted in Fig. 1. The problem formulation and the SOH-TEC architecture are provided in Section 3.1 and Section 3.2, respectively. The model is trained in a supervised manner for the SOH estimation task (Section 3.3). Additionally, SOH-TEC can be optionally pre-trained on datasets without SOH labels to further improve its performance (Section 3.4). The training pipeline that includes pre-training and supervised learning for SOH estimation is explained in Section 3.5.

1. Download: Download full-size image
2. Download: Download high-res image (458KB)

Fig. 1. An overview of the SOH estimation by SOH-TEC. The left side shows an example of trip routes where a vehicle drives and the corresponding vehicle and battery-related data obtained during the trip.1This sequence is used as an input to the model. The right side illustrates the architecture of the transformer-based SOH estimation model. The input sequence is embedded by an input embedding module and then processed by the transformer encoder. The latent representation corresponding to the CLS token is fed into an MLP head, resulting in an estimated SOH.

### 3.1. Problem formulation

We first define the task of estimating SOH using data from a single EV trip. A single trip is defined as the consecutive period during which the EV is in drive mode. The data from a single trip is represented as x∈RC×T. Here, C is the number of data channels, which can include vehicle and battery-related data, and T is the number of data points or time steps. In this study, the data channels include vehicle speed, battery voltage, current, and SOC, thus C=4. The data is recorded at one-second intervals, so T corresponds to the trip’s duration in seconds. The SOH y∈[0,100], which is the estimation target, is defined as: (1)y=EcurrentEinitial×100%,where Ecurrent is the current energy capacity in kWh and Einitial is the initial energy capacity in kWh. The objective is to develop a model f:RC×T→R that maps the input data x to the SOH y.

### 3.2. Network architecture

To accurately deduce the SOH using data from a single EV trip, we develop SOH-TEC, a neural network architecture that incorporates the transformer encoder. The motivation behind leveraging the transformer encoder is its competency in recognizing the dependencies inherent within sequential data. A visual representation of the proposed model architecture can be found on the right side of Fig. 1.

#### 3.2.1. Input embedding

Tokenization or patching is essential for Transformers to effectively process sequential data, as demonstrated in natural language processing [63], computer vision [64], and audio processing [65]. This approach is similarly utilized in our model, where raw time-series data x∈RC×T is converted by the input embedding module into a high-dimensional latent space. The input embedding module of SOH-TEC is composed of a sequence of L convolutional blocks. Each block comprises a 1D-convolutional layer, a batch normalization (BN) [66], and a ReLU activation function. The convolutional layer of the first block applies a kernel size k1 and stride s1, expanding the data’s dimensionality C to the embedding dimension d (Eq. (2)). The convolutional layers of the subsequent blocks apply a kernel size k and stride s, and the embedding dimension is unchanged (if L>2, Eq. (3)). The final block returns logits without applying BN or activation functions (Eq. (4)). In this study, a number of embedding layers, kernel sizes, strides, and embedding dimensions are set as L=2, k1=4, k=3, s1=2, s=2, and d=256, respectively. (2)x1=ReLU(BN(Conv(x;k1,s1,d)))(3)xℓ=ReLU(BN(Conv(xℓ−1;k,s,d))),ℓ=2,…,L−1(4)xL=Conv(xL−1;k,s,d).

#### 3.2.2. CLS token and positional encoding

The embedding process incorporates a learnable CLS token, analogous to those used in BERT [63] and Vision Transformer [64]. The CLS token xcls∈Rd is prepended to the output sequence xL from the input embedding module. This token aggregates and represents the sequence’s information for tasks such as SOH estimation. Additionally, learnable positional encoding P∈Rd×(T′+1) is added to maintain the sequence order, where T′ is the length of xL. Both the CLS token and positional encoding are initialized with a truncated normal distribution (mean μ=0, standard deviation σ=0.2, truncation limits [−2,2]) to stabilize early training. (5)z0=([xcls;xL]+P)⊤

#### 3.2.3. Transformer encoder

The Transformer encoder in SOH-TEC, depicted on the right side of Fig. 1, consists of N=4 transformer blocks. Each transformer block consists of two sub-layers: a Multi-head Attention (MHA) layer (Eq. (6)) and a FFN layer (Eq. (7)). Each sub-layer includes residual connections and employs a pre-norm architecture with Layer Normalization (LN) [67] where normalization precedes the sub-layers. Additionally, DropPath is applied to the output of each sub-layer to enhance the model’s generalization and prevent overfitting. Drop-path involves randomly dropping the output of sub-layers while training, in which case the input from the residual connection is the only contribution passed to the next sub-layer. We employ a drop-path rate of pdrop-path×(i/N) for ith transformer block, implementing a stochastic depth approach. In this study, we set pdrop-path=0.1. (6)zi′=zi−1+DropPath(MHA(LN(zi−1)))(7)zi=zi′+DropPath(FFN(LN(zi′))).

MHA in the first sub-layer is composed of multiple self-attention (SA) heads, and MHA is calculated by concatenating the output of H=16 SA heads and passing them through a linear layer. (Appendix A.1 provides more details about MHA). To address variable sequence lengths and avoid overfitting the input sequence, we apply a key mask to MHA. The key mask works by setting the attention score of masked positions before the softmax operation to −∞ in the SA calculation, which effectively removes the contribution of the masked positions to the SA calculation. In addition to masking, we also apply attention dropout with dropout rate pattn-dropout=0.1.

The FFN in the second sub-layer is a simple two-layer MLP with a GeLU activation function. We employ the dimension of the hidden layer as dFFN=4d. While the FFN can apply dropout, the dropout rate is set to pffn-dropout=0.0.

#### 3.2.4. Multilayer perceptron (MLP) head

The latent representation corresponding to the CLS token is used for the regression task of SOH estimation. This representation is denoted as zcls∈Rd. Specifically, zcls is the first token of the last transformer block’s output, as zcls=zN0. The MLP head for SOH estimation consists of two fully connected layers with a ReLU activation function in the hidden layer. The hidden layer dimension is set to dMLP=d/2. The output layer has a dimension of 1 and does not employ an activation function.

### 3.3. Supervised learning for SOH estimation with SOH-labeled dataset

The SOH-TEC model is trained in a supervised manner utilizing a dataset D={(x(i),y(i))}i=1M, where M is the number of samples in the dataset. The mean squared error (MSE) loss function is used for the training process. The model is trained for 300 epochs. The learning rate is set to 5e-5 at the beginning and 1e-5 after 150 epochs. The purpose of this learning rate decay is to help convergence. AdamW [68] is employed as the optimizer. Gradient clipping is applied with a max norm of 10 to the gradients to prevent the problem of exploding gradients.

For data augmentation purposes, the input sequence undergoes random cropping during training. The lengths of these cropped sequences are sampled from a discrete uniform distribution U(λS,S). Here, λ represents the minimum length ratio and S denotes the original sequence length. For evaluation, the sequence length is fixed at S. In this study, the values are set as λ=0.9 and S=1800. This random cropping helps simulate varying driving conditions and durations. Additionally, we apply random key masking (explained in Section 3.2.3) to the input sequence while training. The random masking ratio, pmask, is sampled from a uniform distribution U(0.1,0.3) for each input. The mask is applied starting from a randomly chosen point t∈{0,…,T−1} (where T is the sequence length) and extends for ⌊pmask⋅T⌋ positions in the sequence. This masking technique helps the model avoid overfitting by preventing it from relying too heavily on specific parts of the input data.

### 3.4. Pre-training with unlabeled data

Creating SOH-labeled datasets for EVs is notably resource-intensive because it requires years of driving data collection coupled with periodic RPTs to accurately measure the SOH. The transformer models have demonstrated exceptional capabilities across various applications through the utilization of pre-training paradigms, particularly with unlabeled data [63], [64], [69]. In the context of battery state estimation, the use of pre-training and transfer learning protocols has been identified as a particularly promising approach [70]. Building on this progression, this study proposes two pre-training methods and verifies their effectiveness: namely masked token prediction and SOH ordinal comparison. These methods enhance the SOH-TEC model’s understanding of SOH progression, improving predictive accuracy in downstream SOH estimation tasks. The pre-training methods are illustrated in Fig. 2.

1. Download: Download full-size image
2. Download: Download high-res image (454KB)

Fig. 2. Overview of the pre-training methods for SOH-TEC. (Left) Masked token prediction: the model learns to predict original input tokens from masked versions of the input sequences. (Right) SOH ordinal comparison: the model processes pairs of input sequences from the same EV and compares their SOH values based on mileage.

#### 3.4.1. Masked token prediction

In the masked token prediction pre-training, the SOH-TEC model is trained to predict the original input tokens from masked versions of the input sequences (see the left side of Fig. 2). This pre-training guides the model in learning meaningful representations of the input data by effectively predicting the masked tokens. The process unfolds as follows: initially, the input sequence undergoes embedding, positional encoding, and the addition of a CLS token. Subsequently, each token in the sequence, except for the CLS token, is replaced with a learnable mask token with a probability of 50%. This masked sequence is then fed into the transformer encoder, whose output tokens are processed by a two-layer MLP token-wise. The MLP head consists of two linear layers with a hidden dimension of d and a ReLU activation function in between. The loss is calculated as the MSE between the masked original tokens and their corresponding reconstructed tokens. For the training process, the same hyperparameters are used as in the SOH estimation task, which is described in Section 3.3.

#### 3.4.2. SOH ordinal comparison

In the SOH ordinal comparison pre-training phase, the model performs an ordinal comparison by predicting which of the two input trips has a higher SOH (see the right side of Fig. 2). The pair of input trips are sampled from the same EV, and which trip has a higher SOH is determined based on their accumulated mileage. This SOH comparison through the mileage is feasible because the SOH decreases monotonically with mileage. The pre-training employs a Siamese network architecture, where both input sequences are processed by the same network. This pre-training is designed to help the model learn better input representations for SOH estimation without requiring SOH labels.

To process the input sequences, we use the SOH-TEC model without the MLP head used for the SOH estimation task. After the process by the SOH-TEC model, the embedded tokens corresponding to the CLS tokens from both input sequences are concatenated and fed into a two-layer MLP head. This MLP head consists of a linear layer followed by a ReLU activation function, another linear layer, and a sigmoid activation function. The input dimension of the MLP head is 2d, the hidden dimension is d, and the output dimension is 1. The output represents the probability that the mileage of the first input sequence is smaller than that of the second one. This probability corresponds to the likelihood that the SOH of the first input trip is greater than that of the second, given the inverse relationship between mileage and SOH. The binary cross-entropy (BCE) loss is used as the loss function.

For the training process, all valid trip pairs in the dataset are used. For instance, if the dataset includes n trips for a vehicle, n2 pairs of trips are used. In this study, due to the quadratic growth of the dataset size with the number of trips, the SOH ordinal comparison pre-training is limited to 5 epochs. Other hyperparameters remain the same as those used in SOH estimation.

### 3.5. Training pipeline

The SOH-TEC model can learn the SOH estimation task in a supervised manner using an SOH-labeled dataset, or it can first be pre-trained on a dataset without SOH labels and then fine-tuned on a dataset with SOH labels. Fine-tuning is the process of training the model for the SOH estimation task after the pre-training process. This SOH-TEC training pipeline is illustrated in Fig. 3. The first two training steps are pre-training, which is optional and can be skipped. Here, the model uses the SOH-unlabeled dataset only for pre-training. The pre-training process does not employ any dataset split; instead, the model is trained to minimize the loss on the entire unlabeled dataset. The final step is the supervised learning for SOH estimation, or fine-tuning if the pre-training process is conducted. In this process, the model uses the dataset with SOH labels. The dataset is split to separate the training, validation, and test datasets. In the transition between these training steps, only the MLP head is replaced for the subsequent training step, while the input embedding module and transformer encoder remain the same. For instance, the model is trained for SOH ordinal comparison. After this phase, the MLP head is replaced, and the model is then trained for SOH estimation.

1. Download: Download full-size image
2. Download: Download high-res image (366KB)

Fig. 3. Training pipeline for SOH estimation. The SOH-TEC model can be optionally pre-trained on a dataset without SOH labels. If pre-trained, the model is then fine-tuned on a dataset with SOH labels for SOH estimation. If no pre-training is conducted, the weight-initialized model is directly trained on the dataset with SOH labels for SOH estimation.

## 4. Dataset

This section details the dataset D={(x(i),y(i))}i=1M used in this study. Data was collected from three EVs of the same mass-market model by the Japan Automobile Research Institute. The collection period spanned from August 2011 to June 2014, with missing data from September 2012 to March 2013. The data collection consists of two parts: collecting EV real-world operation data (Section 4.1) and obtaining ground truth SOH from RPTs (Section 4.2).

### 4.1. EV operation data collection

The driving tests were designed to promote battery degradation while collecting comprehensive data across various conditions. Each vehicle followed predefined schedules comprising six main routes: three highway routes (Highway 1a, 1b, 2) and three urban routes (Urban 1a, 1b, 2). Routes not matching these categories were labeled as “Others”, which included driving within the research facilities. To ensure data quality, only trips lasting 10-90 min and covering 10–90 km were included in the dataset. The testing protocol involved distinct phases, each lasting from several months to over two years. A phase was composed of one or two designated routes. During the phase, a vehicle drove these routes one or several times a day, depending on the route length. After completing a phase, the vehicle switched to different routes for the next phase. Each vehicle experienced several phases throughout the testing period, following a unique combination. Vehicles underwent either fast or normal charging using the constant current constant voltage (CCCV) protocol.

Fig. 4 provides a comprehensive overview of the trip routes. (Individual route visualizations and trip counts are included in Appendix A.2). The left side of the figure displays a map of the six primary routes. Highways 1a and 1b traverse the same path in opposite directions, with 1a starting at point A and ending at B. The other routes are round trips, beginning and ending at point A. Urban 1a is a single loop, while Urban 1b is a double loop on the same route. The right side of Fig. 4 presents a bar chart showing the mean and standard deviation of key metrics for each route type: SOC range, average speed, trip duration, and total distance traveled. Highway routes generally exhibit a higher SOC range, average speed, and total distance, while urban routes show a lower SOC range, lower average speed, and shorter duration. “Others” routes display larger variances across all metrics, as they comprise trips not fitting the highway or urban categories.

During the drive, speed, voltage, and current — used as inputs for the SOH estimation task — are recorded every second. SOC, however, is logged every minute. For consistency with the second-interval input data x required by SOH-TEC, the SOC data is linearly interpolated to match the one-second frequency. Fig. 5 illustrates examples of the input data x for each route. Highway driving sections, characterized by higher (>75 km/h) and more consistent speeds, exhibit steeper voltage and SOC decreases over time. In contrast, urban driving sections show lower speeds and less pronounced voltage and SOC decreases. While more than half of Highway 1a and 1b trips consist of highway driving segments, Highway 2 trips are mostly urban, with only about 10 min of highway driving (refer to speed profiles in Fig. 5).

1. Download: Download full-size image
2. Download: Download high-res image (532KB)

Fig. 4. Overview of trip routes.2 The trips in the dataset are labeled according to their route type. Highway routes (1a, 1b, 2) include travel on highways, with 1a and 1b covering the same path in opposite directions. Urban routes (1a, 1b, 2) stay within the city, with 1a being a single loop and 1b a double loop. Trips not fitting these categories are labeled “Others”. The map on the left shows the trip routes, with Highway 1a starting at point A and ending at B, Highway 1b going in the opposite direction, and all other routes both starting and ending at point A. The bar chart on the right displays the mean and standard deviation of key metrics for each route type, including SOC range, average speed, trip duration, and total distance traveled.

1. Download: Download full-size image
2. Download: Download high-res image (637KB)

Fig. 5. Speed (km/h), voltage (V), current (A), and SOC (%) profiles over time for examples from six trip routes—Highway 1a, Highway 1b, Highway 2, Urban 1a, Urban 1b, and Urban 2.

### 4.2. Ground truth SOH

To obtain the dependent variable y(i), which represents the SOH of the battery, periodic RPTs were conducted for each vehicle alongside the collection of the operation data. The RPT involved a constant-current full discharge with a C-rate of C/3 under a controlled temperature of 25 °C. The C-rate is defined as the current rate relative to the battery’s nominal capacity, meaning that a C/3 discharge would fully deplete a non-degraded battery in three hours. Before the full discharge test, the vehicle was charged to 100% SOC and rested for at least a few hours at about 25 °C. These controlled environments ensure consistent battery capacity measurements. These tests were performed using a chassis dynamometer, which enables vehicle operation while stationary. Fig. 6 illustrates this setup, where the vehicle’s wheels are placed on rollers simulating road conditions. During the RPT, the vehicle was operated to maintain a constant current of C/3. The test continued until the vehicle could no longer sustain the C/3 discharge. RPTs were conducted approximately every six months to evaluate battery degradation throughout the data collection period.

The SOH is calculated based on the current and voltage records from the RPT. However, since RPTs are conducted only approximately every six months, linear interpolation is necessary to estimate SOH values for trips occurring between these tests. This interpolation is applied based on accumulated mileage obtained from the vehicle’s odometer. The method is reasonably robust due to the monotonic decrease of SOH over time and cycle, as well as the repetitive nature of the test routes and consistent driving patterns.

1. Download: Download full-size image
2. Download: Download high-res image (166KB)

Fig. 6. Illustration of the full discharge test with a chassis dynamometer. A driver drives the vehicle to maintain the constant current of C/3. The vehicle is driven as long as it can keep the C/3 discharge rate.

To construct the dataset D={(x(i),y(i))}i=1M, each trip is paired with the accumulated mileage from the vehicle’s odometer at the start of the trip. For each trip of a particular vehicle, we have corresponding input data denoted as x(i). The associated SOH y(i) for this trip is determined through linear interpolation using the RPT results of the vehicle and the odometer reading for that specific trip. Specifically, the RPTs provide SOH values at various mileages for each vehicle, and the interpolation is conducted between the two nearest reference points surrounding the trip’s odometer reading. For example, if the trip’s odometer reading is m(i), and the nearest reference points are mk1 (with SOH of yk1) and mk2 (with SOH of yk2), the SOH for the trip is estimated as Eq. (8). This method ensures that the interpolated approximation is realistic and grounded in the actual vehicle usage between RPTs. (8)y(i)=yk1+m(i)−mk1mk2−mk1×(yk2−yk1).

## 5. Experimental setup

To evaluate the effectiveness of SOH-TEC, we employ the following nine most fundamental models as comparative baselines: Dummy Regressor, Route-aware Dummy Regressor, MLP, CNN, LSTM, Linear Regression, Ridge Regression, Random Forest, and LightGBM. The detailed descriptions of these models are provided in Appendix A.3. While recent SOH estimation models have shown significant advancements, they are primarily designed for specific contexts such as controlled lab settings or charging processes. Thus, they may not align well with the real-world discharging processes central to our study. Adapting these models without considering their original context could lead to skewed results and misinterpretations, which is why they were not included as baselines.

For the model training process, we randomly split the dataset into training, validation, and test sets, with a ratio of 8:1:1. Throughout the whole experiment, the same data split is used. The model is trained using the training dataset, and its performance is assessed with the validation dataset at the end of each epoch. The best model checkpoint, determined by the lowest validation loss, is then evaluated on the test dataset to assess its effectiveness. We use the root mean square error (RMSE), mean absolute error (MAE), and coefficient of determination R2 as evaluation metrics. The four deep learning-based models (SOH-TEC, MLP, CNN, and LSTM) and two tree-based models (Random Forest and LightGBM) are trained with eight different random seeds to ensure the reproducibility of the results. The models’ hyperparameters and their searching process are detailed in Appendix A.4.

## 6. Experiments

We conducted three experiments to evaluate the SOH-TEC model. The base setting experiment utilized full trips from the dataset for training and testing (Section 6.1). The urban driving setting focused on urban driving segments to assess performance under typical urban conditions (Section 6.2). Both these experiments compared SOH-TEC against nine baseline models for SOH estimation, using only labeled data in a supervised manner. The third experiment explored the effectiveness of masked token prediction and SOH ordinal comparison pre-training strategies. This experiment used partially unlabeled data for pre-training, followed by fine-tuning on the remaining labeled data (Section 6.3). Detailed results and analysis for each experiment are presented in the following subsections.

### 6.1. Experiment 1: base setting

In this experiment, we used the full trips from the dataset for the training and testing. This experiment aims to evaluate the basic estimation performance of SOH-TEC and compare it with the baseline models. The comprehensive results of the experiment are shown in Table 1. (The training and validation loss curve can be found in Appendix A.5.) Table 1 provides a quantitative performance outcome through three metrics: RMSE, MAE, and R2. Lower RMSE, MAE, and higher R2 indicate better performance. As indicated in Table 1, the SOH-TEC model outperforms all other models significantly across all metrics (RMSE, MAE, and R2). Specifically, SOH-TEC achieved an RMSE of 1.17 (±0.17) and an MAE of 0.72 (±0.04). In contrast, the best-performing baseline model, LSTM, recorded an RMSE of 1.80 (±0.13) and an MAE of 1.12 (±0.05). The effectiveness of SOH-TEC’s transformer encoder-based approach for EV SOH estimation is evident from these results, underscoring its advanced capability over traditional models.

Fig. 7 shows scatter plots (true SOH vs. estimated SOH) for the top four models: SOH-TEC, LSTM, CNN, and LightGBM. (Full scatter plots are available in Appendix A.6.) In the scatter plot, each point represents a test sample, color-coded by trip route and the black dashed line represents perfect estimation. Here, we observe that SOH-TEC’s predictions are tightly clustered around this line. In contrast, other baseline models show broader point dispersion. Notably, SOH-TEC accurately estimates SOH for challenging trips that other models struggle with, such as the trip in the ‘Others’ cluster with true SOH around 67%. These results indicate the SOH-TEC’s superiority in terms of high accuracy and consistency across various driving conditions. The 3% margin delineated in Fig. 7 further highlights SOH-TEC’s precision; most predictions fall within this narrow error margin, clearly demonstrating the model’s reliability.

Table 1. Comparison of SOH estimation performance for different models in Experiment 1: base setting using the full dataset. The best-performing model is highlighted in bold.

1. Download: Download full-size image
2. Download: Download high-res image (582KB)

Fig. 7. The estimation results of Experiment 1: base setting. The scatter plot illustrates true SOH vs. estimated SOH by the best-performing models for the test dataset. Marker colors represent different trip routes, and the gray region illustrates the 3% error margin. The insets show the error distributions for each model.

### 6.2. Experiment 2: urban driving setting

In addressing the challenge posed by repeated and limited trip routes in the dataset, our approach involved random masking and cropping techniques to foster a more generalized learning process. However, recognizing the potential over-representation of highway driving characteristics and their correlation with the SOH estimations, our second experiment narrowed the focus to urban driving conditions. This choice was driven by two reasons: to reduce the risk of overfitting to specific highway routes and to assess model performance in more challenging and diverse urban driving scenarios, which are the most common in daily life, such as commuting and shopping.

Our methodology isolates urban driving segments from the collected data. First, we identify the longest continuous segment in each trip where the vehicle’s speed (smoothed over 180 s) remains below 70 km/h. This threshold reflects the highway speeds recorded in the dataset. These segments are then refined by cropping to the points most representative of urban driving: starting where the vehicle’s speed drops to zero and ending where it does not exceed 60 km/h. This 60 km/h threshold effectively distinguishes urban from highway driving. Examples of these cropped urban driving segments are shown in Fig. 8.

The quantitative results of Experiment 2 are shown in Table 2. (The training and validation loss curve can be found in Appendix A.5). Our proposed SOH-TEC model demonstrates a remarkable performance and outperforms all other models significantly across all metrics. Fig. 9 illustrates the comparison of the SOH estimations between the proposed SOH-TEC model and the top three baseline models (LSTM, CNN, and LightGBM) in the urban driving setting. Full scatter plots of the test results can be found in Appendix A.6. Due to the complex and shorter input data of the urban driving setting, the baseline models exhibit high dispersion in their estimations, highlighting their limitations under such demanding conditions. In contrast, our SOH-TEC model demonstrates remarkable resilience and maintains high performance, consistently delivering accurate SOH estimations across varied trip routes. This robustness highlights the advanced capability of SOH-TEC to effectively handle the complexity of real-world urban driving conditions.

1. Download: Download full-size image
2. Download: Download high-res image (216KB)

Fig. 8. Example of the urban trip segments extracted from the highway route trips. Blue lines are the urban trip parts that are used for the input data of Experiment 2.

The comparative analysis of Experiments 1 and 2 highlights the superior performance of the SOH-TEC model. In Experiment 1, SOH-TEC outperformed other models, showing a clear advantage in the base setting with mixed driving segments. In Experiment 2, focusing on complex urban driving, SOH-TEC maintained high performance with minimal accuracy degradation. Specifically, while the second-best performing LSTM model’s RMSE and MAE increased by 0.33 and 0.14 respectively, SOH-TEC’s increases were only 0.13 and 0.05. This underscores SOH-TEC’s robustness and its ability to effectively handle complex urban driving data for SOH estimation.

Table 2. Comparison of SOH estimation performance for different models in Experiment 2: urban driving setting. The best-performing model is highlighted in bold.

1. Download: Download full-size image
2. Download: Download high-res image (593KB)

Fig. 9. The estimation results of Experiment 2: urban driving setting. The scatter plot illustrates true SOH vs. estimated SOH by the best-performing models. Marker colors represent different trip routes, and the gray region illustrates the MAE within a 3% error margin. The insets show the error distributions for each model.

### 6.3. Experiment 3: pre-training and fine-tuning using fewer labeled data

In this experiment, we investigate the effectiveness of our two proposed pre-training methods leveraging unlabeled data: masked token prediction and SOH ordinal comparison, detailed in Section 3.4. These pre-training approaches are particularly crucial given the considerable cost and time of acquiring SOH labels for real-world EVs.

To simulate realistic scenarios where only a limited amount of SOH-labeled data is available, we remove SOH labels from some of the training data used in Experiments 1 and 2. An illustration of the dataset configuration for Experiment 3 is shown in Fig. 10. Here, only α of the training split of the original dataset is still used as the labeled training dataset, and 1−α is the SOH unlabeled training dataset used for pre-training. The unlabeled data are randomly selected. The validation and test dataset remains the same as in Experiments 1 and 2. While this experimental setup provides valuable insights into the effectiveness of models and pre-training strategies in a controlled scenario with mixed labeled and unlabeled data, it should be noted that the setup may not fully capture the complexities of real-world environments. We explore these limitations and discuss potential avenues for future research in further detail in Section 7.4.

We compare the performance of models trained with different combinations of the pre-training strategies against models trained without any pre-training. We evaluate the performance of the models using the RMSE, MAE, and R2 over α∈{0.1,0.2,0.3,0.4,0.5}. The model is trained over eight different random seeds for each combination of the pre-training strategies and α values. The training and validation loss curves for the fine-tuning stage of the experiment are presented in Appendix A.5.

1. Download: Download full-size image
2. Download: Download high-res image (204KB)

Fig. 10. Illustration of the datasets used in Experiment 3. A randomly selected portion α (where α<1) of the original dataset’s training split is used as the labeled training dataset for supervised learning of SOH estimation. The remaining 1−α portion is used as the unlabeled SOH training dataset for pre-training purposes.

Fig. 11 shows the average RMSE and MAE versus α for the three different pre-training strategies and the no pre-training scenario. (The comprehensive results of the experiment are summarized in Appendix A.7.) The results clearly indicate that pre-training significantly enhances model performance, particularly when the amount of labeled data (or α) is low. This highlights the effectiveness of the pre-training approach leveraging unlabeled data to improve the model’s capability in the downstream task of SOH estimation. For example, when α=0.1, SOH ordinal comparison pre-training enhances the model’s performance by 36.4% for RMSE and 47.8% for MAE compared to the model without pre-training and Masked Token Prediction pre-training improves it by 14.2% for RMSE and 17.0% for MAE.

Among the pre-training strategies, SOH ordinal comparison consistently outperformed masked token prediction across different values of α. The combination of masked token prediction and SOH ordinal comparison performed similarly to SOH ordinal comparison alone, suggesting that masked token prediction does not provide additional benefits when used in conjunction with SOH ordinal comparison.

1. Download: Download full-size image
2. Download: Download high-res image (242KB)

Fig. 11. RMSE and MAE of SOH estimation models for different α values. α is the ratio of the labeled training data to the total training data, meaning that the smaller α, the less SOH-labeled data is used for learning the model on the task of SOH estimation while the model can use more data for pre-training. MaskPred and SOH-Comp stand for masked token prediction and SOH ordinal comparison, respectively.

A noteworthy finding is that the model pre-trained with both masked token prediction and SOH ordinal comparison, utilizing only 50% of the labeled data (α=0.5), achieved performance nearly identical to the model trained on the full labeled dataset. Specifically, the RMSE and MAE for this pre-trained model are 1.243(±0.14) and 0.716(±0.05), while the RMSE and MAE for the model trained on the full labeled dataset are 1.167(±0.17) and 0.719(±0.04), respectively. This quantitative result underscores the significant impact of pre-training in drastically reducing the dependency on labeled data while maintaining high performance, highlighting its potential to make SOH estimation more efficient and cost-effective.

## 7. Discussion and limitations

### 7.1. Analyzing the self-attention map

Understanding the interpretative mechanisms of our model is crucial for reliable SOH estimation from EV operation data. The self-attention mechanism of the model differentially weights input features, highlighting the most relevant information for estimating SOH. In our context, the CLS token aggregates the sequence representation upon which the final SOH estimation is based. We analyze the self-attention weights assigned to this CLS token in the last transformer layer across various inputs to understand the model’s focus under different driving conditions.

Fig. 12 illustrates the self-attention maps for different trip routes. The heatmaps visually represent the model’s attention intensity, demonstrating distinct patterns for different driving environments. Notably, the heatmap from the highway trip in Fig. 12a shows a high concentration of attention by heads such as Head 1 and Head 5 on segments where the EV maintains consistent speed. Fig. 12b reveals that during mixed highway and city driving, attention shifts towards periods of stationary behavior, particularly in Head 2, Head 4, and Head 9, while Head 14 is focused on the consistent driving segments. In urban driving scenarios, as illustrated in Fig. 12c, the self-attention mechanism notably adjusts its focus, with Head 3 and Head 15 predominantly attending to the stationary segments where the EV’s speed is zero.

These self-attention map analysis results reveal the model’s concentration on data points from consistent driving or stationary phases, indicating that these patterns are particularly informative for SOH estimation. This insight can guide the refinement of data collection strategies to focus on the most impactful driving conditions and help hypothesize the crucial features for future algorithm enhancements. Additionally, the observed inter-head variability suggests that each head captures different driving data aspects, a design feature that facilitates a thorough analysis of input features. Further research into these differences could lead to more specialized model architectures or input data selection strategies, enhancing the model’s predictive accuracy.

1. Download: Download full-size image
2. Download: Download high-res image (1MB)

Fig. 12. Attention score corresponding to CLS token demonstrated by heatmap on the input sequence. (a) Highway driving input, (b) Mixed highway and city driving input, (c) City driving input.

### 7.2. SOH-TEC ablation study

To systematically understand the influence of various hyperparameters (and feature selection) on the performance of our transformer model, we conducted an extensive ablation study. We experimented with different configurations, varying one at a time while keeping others constant. This methodology allowed us to isolate and assess its specific impact on the model’s accuracy in estimating SOH, as measured by RMSE. For consistency, this ablation study replicated the training and dataset setup from Experiment 1 (Section 6.1).

First, we examined five critical hyperparameters: the number of transformer blocks (N), the hidden dimension size (d), the kernel size of the first embedding layer (k1), the number of self-attention heads (H), and the drop-path rate (pdrop-path). Fig. 13 illustrates the average RMSE across five random seeds with 95% confidence intervals, revealing key insights into hyperparameter performance. The model achieves the lowest RMSE with six transformer blocks, while the performance remains robust from two to eight blocks. For the hidden dimension size, performance peaks at 512, indicating that larger dimensions do not enhance accuracy. The kernel size of the first embedding layer optimizes at 8, suggesting that overly detailed or overly general representations are less effective. The number of attention heads shows a nearly monotonic decrease in RMSE with increasing heads. A moderate drop-path rate slightly enhances results, indicating the benefits of balanced regularization. This analysis reveals that while each hyperparameter exerts an influence on model performance, even the least optimal hyperparameter configuration in our study outperforms the baseline models, underlining the robustness of the SOH-TEC model against variations in hyperparameter settings.

The ablation study in Fig. 14 examines data augmentation and input feature effects on model performance. For data augmentation (Fig. 14a), we varied the random masking ratio pmask and minimum length ratio λ. Optimal RMSE results occur at moderate levels of both parameters, with the lowest at pmask=0.1 and λ=0.8, followed by pmask=0.2 and λ=0.9. This suggests moderate data augmentation slightly improves performance. For input features (Fig. 14b), models including speed features marginally outperform those without. This result indicates that speed data, unique to the EV context, contributes valuable information for SOH estimation in EVs.

1. Download: Download full-size image
2. Download: Download high-res image (294KB)

Fig. 13. Hyperparameter ablation study results of the transformer model. The plot line shows the average RMSE across the five random seeds for each hyperparameter setting, with the shaded region indicating the 95% confidence interval of the RMSE.

1. Download: Download full-size image
2. Download: Download high-res image (161KB)

Fig. 14. Ablation study results. (a) The impact of data augmentation parameters on RMSE. The heatmap shows mean RMSE values over five random seeds for different combinations of random masking ratio pmask and minimum length ratio λ. (b) Comparison of RMSE for models trained with and without speed features. The box plots represent the distribution of RMSE values over the eight random seeds.

### 7.3. Dataset limitation and insights for future dataset creation

While the proposed method attains satisfactory accuracy, a noteworthy limitation of our study hinges on the limited variety and repetitiveness of driving routes in the dataset. This may cause the model to mistakenly correlate specific driving patterns to SOH, potentially preventing accurate learning of the relationship between EV operation data and SOH. For example, Highway 2 and Urban 2 routes were only driven during a short period toward the end of the data collection, which could lead to unintended associations. To improve and further confirm the model’s performance and robustness, it is essential to incorporate a broader variety of driving scenarios that encompass a wide spectrum of environmental and operational conditions. Future iterations should implement a well-planned data collection strategy focused specifically on SOH estimation. We propose the following strategies to enhance dataset quality:

•

Avoid spurious correlations: The dataset should be designed to minimize misleading correlations between SOH and incidental factors such as specific routes or SOC patterns.

•

Diverse diving behaviors: The dataset should include driving patterns that are comprehensive enough to cover the entire spectrum of typical driving behavior.

•

Comprehensive SOH range: The dataset should encompass a broad range of SOH values to ensure the model can accurately predict SOH across different stages of battery life.

•

Consistent driving: The vehicle should be driven consistently throughout the data collection period so that battery degradation is consistent and the linearly interpolated SOH based on the accumulated mileage can be justified.

Considering these elements, one potential strategy is to diversify the driving routes. The driven routes should be randomly chosen or systematically repeated to eliminate spurious correlations between driving patterns and SOH. For instance, a dataset could include 10 distinct urban routes that collectively represent typical urban driving patterns. Each route would be driven 50 times spread evenly over the course of a year to cover a wide range of SOH values. Ideally, data collection should span multiple years to mitigate seasonal effects. Since our model performs well with 30-minute operational data inputs, each route in the dataset can be relatively short. This approach ensures that the dataset includes a sufficient number of diverse instances to support robust model training and evaluation.

Another potential data collection strategy involves gathering driving data from a large number of corporate or privately owned EVs and conducting periodic RPTs. This approach, while promising, presents several challenges. First, there are high costs associated with collecting data and conducting RPTs. Second, data collection raises privacy concerns. Third, uncontrolled driving intervals necessitate devising a reliable method for SOH interpolation. Despite these challenges, this strategy could yield a dataset with diverse real-world driving scenarios.

### 7.4. Experiment setup limitation and further potential of pre-training

Considering real-world conditions where obtaining comprehensive SOH labels is often impractical, pre-training with unlabeled data is an important direction for real-world EV SOH estimation. Experiment 3 (in Section 6.3) was designed to confirm the effectiveness of this pre-training approach by employing a controlled mix of labeled and unlabeled data, aiming to replicate situations where labeled data is scarce. The results revealed that the proposed pre-training strategies leveraging unlabeled data enhanced the model’s performance in the downstream SOH estimation task.

However, it is important to recognize the limitations of our experimental setup. Specifically, the random selection of unlabeled data from a relatively small dataset, while useful for initial validation, may not accurately represent real-world scenarios where diverse and vast amounts of unlabeled data are available. To build on the current work, future experiments could explore larger and more diverse SOH unlabeled datasets. This could enhance the model’s performance and robustness across different driving conditions. Additionally, the flexibility of our model and its pre-training methods hints at the potential for adaptation across different domains and vehicle types. Incorporating data from multiple domains and vehicle types would be another important direction for future work to broaden the scope of its applicability.

## 8. Conclusion

This research introduces SOH-TEC, a transformer-based model for estimating the State of Health (SOH) of electric vehicle (EV) batteries using raw single-trip operation data. We have created a real-world EV-driving dataset with reliable SOH labels, collected over nearly three years from three EVs in Japan, including periodic reference performance tests for accurate labeling. Our experiments demonstrate SOH-TEC’s superior performance compared to baseline models, with a root mean square error of 1.17 and a mean absolute error of 0.72 in the base setting. The model maintains robust performance even in challenging urban driving scenarios. Self-attention map analysis reveals the model’s focus on stationary or consistent driving periods as key indicators for SOH estimation. Pre-training strategies, particularly SOH ordinal comparison, significantly improve performance when labeled data is limited. With only 50% labeled data, the pre-trained model performs comparably to training on the full labeled dataset.

However, the model’s performance is constrained by the repetitiveness and limited variety of driving routes in the dataset. Future work should expand the dataset to include more diverse driving scenarios. Additionally, our model currently focuses on the vehicle driving session (discharging process), but integrating charging processes could provide a more holistic view of battery health and enhance model robustness and accuracy. This study confirms the effectiveness of transformer-based models for EV SOH estimation using real-world data. We hope this work paves the way for further research in EV battery management and supports the transition to cleaner energy solutions.

## CRediT authorship contribution statement

Kosaku Nakano: Writing – review & editing, Writing – original draft, Visualization, Validation, Software, Methodology, Investigation, Data curation, Conceptualization. Sophia Vögler: Writing – review & editing, Writing – original draft, Investigation. Kenji Tanaka: Writing – review & editing, Supervision, Data curation, Conceptualization.

## Declaration of Generative AI and AI-assisted technologies in the writing process

During the preparation of this work, the authors used ChatGPT and Claude in order to improve the clarity of the manuscript. After using this tool/service, the authors reviewed and edited the content as needed and take full responsibility for the content of the publication.

## Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## Acknowledgment

This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors. We thank the Japan Automobile Research Institute for providing the data.

## Appendix A. Supplementary information

### A.1. Attention mechanism

Fig. A.15 illustrates the SA and MHA architecture. Each self-attention head computes a different attention score from query, key, and value. Query q, key k, and value v are mapped from the input z by linear projection respectively (Eq. (A.2) to Eq. (A.4)). The self-attention score is computed by the dot product of query and key, followed by a softmax function. Before the softmax is applied, the dot product is divided by the square root of the dimension of the key dh. The self-attention score is then used to compute the weighted sum of the value vectors (Eq. (A.1)) [31].

(A.1)SA(z)=softmaxqk⊤dhv,(A.2)whereq=zWqWq∈Rd×dh,(A.3)k=zWkWk∈Rd×dh,(A.4)v=zWvWv∈Rd×dh.

1. Download: Download full-size image
2. Download: Download high-res image (212KB)

Fig. A.15. A graphical representation of the self-attention mechanism and multi-head attention.

MHA is calculated by concatenating the output of H self-attention heads and passing them through a linear layer: (A.5)MHA(z)=Concat(SA1(z),…,SAH(z))Wo,where Wo∈RHdh×d represents the learnable weight matrix for the output linear layer. Here, H denotes the number of self-attention heads, and dh indicates the dimension of each self-attention head.

### A.2. Trip routes

Table A.3 shows the number of trips for each route pattern included in the dataset. Fig. A.16 illustrates the geographical layout of the trip routes.

Table A.3. Number of trips across different routes included in the dataset.

| Route | Number of trips |
| --- | --- |
| Highway 1a | 484 |
| Highway 1b | 320 |
| Highway 2 | 187 |
| Urban 1a | 1701 |
| Urban 1b | 406 |
| Urban 2 | 208 |
| Others | 39 |

1. Download: Download full-size image
2. Download: Download high-res image (409KB)

Fig. A.16. Six trip routes visualization.3

1. Download: Download full-size image
2. Download: Download high-res image (213KB)

Fig. A.17. Training and validation loss curves for Experiment 1. Both curves have their vertical axes truncated at 50.0. The validation loss curves are smoothed using a moving average over 11 epochs.

1. Download: Download full-size image
2. Download: Download high-res image (219KB)

Fig. A.18. Training and validation loss curves for Experiment 2. Both curves have their vertical axes truncated at 50.0. The validation loss curves are smoothed using a moving average over 11 epochs.

1. Download: Download full-size image
2. Download: Download high-res image (369KB)

Fig. A.19. Training and validation loss curves for SOH estimation task in Experiment 3. Both curves have their vertical axes truncated at 50.0.

### A.3. Comparative baseline models

In this section, we provide a detailed description of the comparative baseline models used in our study. All the deep learning-based models are implemented in PyTorch [71], and automatic mixed precision with fp16 was used for training and inference.

#### A.3.1. Dummy regressor

A Dummy Regressor outputs the average SOH of the training dataset as the predicted SOH. A modified version, the Route-aware Dummy Regressor, outputs the average SOH for each trip route. Given the dataset’s repetitive and limited trip routes, the Route-aware Dummy Regressor serves as a sufficiently strong baseline.

#### A.3.2. MLP

The model referred to as MLP for simplicity, includes a convolutional embedding layer similar to SOH-TEC, followed by fully connected layers. The input sequence first passes through a convolutional layer (kernel size 8, stride 2) mapping it to 256 channels. This is followed by three fully connected layers with output dimensions of 1024, 256, and 1. ReLU activations are applied after the first two layers. The final output predicts the SOH.

#### A.3.3. CNN

The CNN model is composed of multiple convolutional layers, each followed by BN and ReLU activation functions. The detailed configuration of the model is shown in Table A.4. The final output (estimated SOH) is produced by a linear layer that takes the flattened output from the last convolutional block as an input. No activation function is applied to the final layer.

Table A.4. Convolutional layers of the CNN model.

| No. | Input channels | Output channels | Kernel size | Stride |
| --- | --- | --- | --- | --- |
| 0 | 4 | 256 | 4 | 2 |
| 1 | 256 | 256 | 4 | 2 |
| 2 | 256 | 256 | 4 | 2 |
| 3 | 256 | 128 | 16 | 1 |
| 4 | 128 | 128 | 4 | 1 |

Table A.5. Summary of hyperparameters for models training.

| Model | Batch size | Grad clip max norm | Sequence crop range | Learning rate |
| --- | --- | --- | --- | --- |
| Empty Cell | Empty Cell | Empty Cell | Empty Cell | Base | Decay step size | γ |
| MLP | 16 | 5 | (1800,1800) | 1e−4 | 100 | 0.1 |
| LSTM | 32 | 1 | (2400,2400) | 5e−5 | 100 | 0.1 |
| CNN | 16 | – | (1920,2400) | 1e−4 | 100 | 0.1 |
| SOH-TEC (Ours) | 32 | 10 | (1620,1800) | 5e−5 | 150 | 0.2 |

Table A.6. Parameter search configuration of SOH-TEC.

| Parameter | Values |
| --- | --- |
| Attention Drop Rate pattn-dropout | 0, 0.1, 0.2 |
| Batch Size | 16, 32 |
| Number of Transformer Blocks N | 4, 6, 8, 10 |
| Drop Path Rate pdrop-path | 0, 0.1 |
| FFN Drop Rate pffn-dropout | 0, 0.1, 0.2 |
| Embedding Dimension d | 256, 512 |
| Gradient Clipping Max Norm | null, 3, 5, 10 |
| Learning Rate | 1e−4, 5e−5, 1e−5, 5e−6 |
| Random Masking Ratio Range | (0,0),(0,0.1),(0,0.2),(0.1,0.2),(0.1,0.3) |
| Random Masking Type | arbitrary, continuous |
| Minimum Length Ratio λ | 1, 0.9, 0.8, 0.6 |
| Number of Embed Layers L | 1, 2, 3, 5 |
| Number of Heads H | 16 |
| Kernel Size of First Embedding Layer k1 | 4, 8, 16 |
| Position Drop Rate ppos-dropout | 0, 0.1 |
| Pre-embed Norm | LayerNorm, BatchNorm, InstanceNorm, null |
| Sequence Length S | 1200, 1500, 1800, 2100, 2400 |
| Learning Rate Decay Gamma | 0.1, 0.2 |
| Learning Rate Decay Step Size | 100, 150 |
| Stride of First Embedding Layer s1 | 2, 4 |

Table A.7. Parameter search configuration of MLP.

| Parameter | Values |
| --- | --- |
| Batch Size | 16, 32, 64 |
| Dropout Rate | 0, 0.1, 0.2 |
| Embedding Dimension d | 128, 256, 512, 768 |
| Gradient Clipping Max Norm | null, 1, 3, 5, 10 |
| Learning Rate | 1e−4, 5e−5, 1e−5, 5e−6 |
| Minimum Length Ratio λ | 1, 0.9, 0.8, 0.6 |
| First Hidden Layer Dimension | 256, 512, 1024, 2048 |
| Second Hidden Layer Dimension | 256, 512, 1024, 2048 |
| Patch Size | 4, 8, 16, 32 |
| Pre-embed Norm | LN, LN1D, BatchNorm, InstanceNorm, null |
| Sequence Length S | 1200, 1500, 1800, 2100, 2400 |
| Learning Rate Decay Gamma | 0.1, 0.2 |
| Learning Rate Decay Step Size | 100, 150 |
| Stride of First Embedding Layer s1 | 1, 2, 4, 8 |

Table A.8. Parameter search configuration of CNN.

| Parameter | Values |
| --- | --- |
| Batch Size | 16, 32 |
| Convolutional Block 1 Channels | 128, 256, 512 |
| Convolutional Block 1 Kernel Size | 2, 4, 8, 16 |
| Convolutional Block 1 Stride | 1, 2, 4 |
| Convolutional Block 2 Channels | 64, 128, 256, 512 |
| Convolutional Block 2 Kernel Size | 2, 4, 8, 16 |
| Convolutional Block 2 Stride | 1, 2, 4 |
| Convolutional Block 3 Channels | 32, 64, 128, 256 |
| Convolutional Block 3 Kernel Size | 2, 4, 8, 16 |
| Convolutional Block 3 Stride | 1, 2, 4 |
| Batch Norm First | True, false |
| Number of Convolutional Blocks 1 | 1, 2, 3 |
| Number of Convolutional Blocks 2 | 1, 2, 3 |
| Number of Convolutional Blocks 3 | 0, 1, 2, 3 |
| Dropout rate | 0, 0.1, 0.2 |
| Gradient Clipping Max Norm | Null, 1, 3, 5, 10 |
| Learning Rate | 1e−4, 5e−5, 1e−5, 5e−6 |
| Minimum Length Ratio λ | 1, 0.9, 0.8, 0.6 |
| Sequence Length S | 1200, 1500, 1800, 2100, 2400 |
| Learning Rate Decay Gamma | 0.1, 0.2 |
| Learning Rate Decay Step Size | 100, 150 |

Table A.9. Parameter search configuration of LSTM.

| Parameter | Values |
| --- | --- |
| Batch Size | 16, 32, 64 |
| Dropout Rate | 0, 0.1, 0.2 |
| Embedding Dimension d | 128, 256, 512, 768 |
| Gradient Clipping Max Norm | null, 1, 3, 5, 10 |
| Learning Rate | 1e−4, 5e−5, 1e−5, 5e−6 |
| LSTM Bidirectional | true, false |
| LSTM Hidden Size | 128, 256, 512, 768 |
| LSTM Number of Layers | 1, 2, 3, 4 |
| Minimum Length Ratio λ | 1, 0.9, 0.8, 0.6 |
| Number of Embed Layers L | 1 |
| Patch Size | 4, 8, 16, 32 |
| Pre-embed Norm | LN, LN1D, BatchNorm, InstanceNorm |
| Sequence Length S | 1200, 1500, 1800, 2100, 2400 |
| Learning Rate Decay Gamma | 0.1, 0.2 |
| Learning Rate Decay Step Size | 100, 150 |
| Stride of First Embedding Layer s1 | 1, 2, 4, 8 |

#### A.3.4. LSTM

The LSTM baseline uses a BN layer, followed by a 1D convolutional layer (512 output features, kernel size 32, stride 8) to reduce sequence length. After LN, features are processed by a bidirectional LSTM (hidden size 768), then mapped to a single SOH prediction via a linear layer. This architecture is often referred to as CNN-LSTM, which is widely adopted for battery state estimation tasks.

#### A.3.5. Feature-based models

In addition to the deep learning models, we also evaluate the performance of four feature-based models: Linear Regression, Ridge Regression, Random Forest, and LightGBM, which were found to be the best-performing models for SOH estimation for lab-experimented cell data [72]. These models utilize a comprehensive set of features extracted from the dataset to predict the SOH. The features include statistical metrics such as mean, standard deviation, minimum, maximum, skewness, and kurtosis for speed, voltage, current, and SOC. Additionally, incremental capacity (IC) is calculated, along with voltage differences across SOC ranges, mean voltage to mean current ratios, and voltage range. Voltage and SOC values at maximum incremental capacity, trip duration, and various discharge metrics (amp-hours and kilowatt-hours) are also included. It should be noted that feature extraction is more challenging on real-world driving data than on lab-experimented data due to the fluctuations and variability inherent in real-world conditions. These fluctuations can introduce noise and make it more difficult to extract meaningful features, thereby impacting the performance of feature-based models.

1. Download: Download full-size image
2. Download: Download high-res image (847KB)

Fig. A.20. The estimation results of Experiment 1: base setting. The scatter plot illustrates true SOH vs. estimated SOH by the best-performing models for the test dataset. Marker colors represent different trip routes, and the gray region illustrates the 3% error margin. The insets show the error distributions for each model.

1. Download: Download full-size image
2. Download: Download high-res image (871KB)

Fig. A.21. The estimation results of Experiment 2: urban driving setting. The scatter plot illustrates true SOH vs. estimated SOH by the best-performing models for the test dataset. Marker colors represent different trip routes, and the gray region illustrates the 3% error margin. The insets show the error distributions for each model.

### A.4. Hyperparameters

The training hyperparameters for the deep learning-based baseline models (MLP, CNN, and LSTM) and our proposed model (SOH-TEC) are summarized in Table A.5. During training, each sequence is cropped at a randomly selected starting point to a length that is uniformly sampled from a sequence crop range (same as random cropping explained in Section 3.3). The learning rate is decayed by γ for every decay step size. For example, in MLP, the learning rate starts with 1e−4, and after every 100 epoch, it is decayed by 0.1.

These hyperparameters and others regarding the model architecture were determined by a random search for each model using training and validation datasets. Table A.6, Table A.7, Table A.8, Table A.9 show the hyperparameter search configuration of SOH-TEC, MLP, CNN, and LSTM, respectively. We employed random search with Hyperband [73] early stopping. The maximum epoch was set to 200. The random masking type of SOH-TEC can be either ‘arbitrary’ or ‘continuous.’ When set to ‘arbitrary,’ the masking locations within the sequence are chosen randomly. When set to ‘continuous,’ the masking is applied over a continuous subsequence of the input sequence. The sequence length S and the minimum length ratio λ are used to determine the length range to which the original input sequence is cropped, where the length is sampled from U(λS,S). The pre-embed norm refers to the normalization method before the embedding module. The position drop rate ppos-dropout in SOH-TEC is a dropout in the positional encoding layer, which is set to 0 in this study.

### A.5. Training and validation loss curves

Fig. A.17, Fig. A.18, and Fig. A.19 show the training and validation loss curves for Experiments 1, 2, and 3, respectively.

### A.6. Full scatter plots of test results

Fig. A.20 and Fig. A.21 show the full scatter plots of the estimated SOH vs. the true SOH for the test dataset of Experiment 1 and Experiment 2, respectively.

### A.7. Comprehensive results of experiment 3

The comprehensive results of Experiment 3 are summarized in Table A.10. For each value of α, we report the average RMSE, MAE, and R2 along with their standard deviations. These results further confirm the superior performance of the SOH ordinal comparison and the effectiveness of pre-training in enhancing model performance.

Table A.10. SOH estimation results with different pre-training strategies over different α values. α is the ratio of the labeled training data to the total training data.

Special issue articlesRecommended articles

## Data availability

The data that has been used is confidential. The code will be made available on request.

## References

[1]

International Energy Agency

Tracking clean energy progress 2023

(2023)

https://www.iea.org/reports/tracking-clean-energy-progress-2023. [Accessed: April 12, 2024]

Google Scholar

[2]

International Energy Agency

Global EV outlook 2023

(2023)

https://www.iea.org/reports/global-ev-outlook-2023. [Accessed: April 12, 2024]

Google Scholar

[3]

Miao Y., Hynan P., Von Jouanne A., Yokochi A.

Current Li-ion battery technologies in electric vehicles and opportunities for advancements

Energies, 12 (6) (2019), p. 1074

Crossref View in Scopus Google Scholar

[4]

Lu L., Han X., Li J., Hua J., Ouyang M.

A review on the key issues for lithium-ion battery management in electric vehicles

J Power Sources, 226 (2013), pp. 272-288

View PDF View article View in Scopus Google Scholar

[5]

Saw L.H., Ye Y., Tay A.A.

Integration issues of lithium-ion battery into electric vehicles battery pack

J Clean Prod, 113 (2016), pp. 1032-1045

View PDF View article View in Scopus Google Scholar

[6]

Ding Y., Cano Z.P., Yu A., Lu J., Chen Z.

Automotive Li-ion batteries: current status and future perspectives

Electrochem Energy Rev, 2 (2019), pp. 1-28

Google Scholar

[7]

Han X., Lu L., Zheng Y., Feng X., Li Z., Li J., et al.

A review on the key issues of the lithium ion battery degradation among the whole life cycle

ETransportation, 1 (2019), Article 100005

View PDF View article View in Scopus Google Scholar

[8]

Barré A., Deguilhem B., Grolleau S., Gérard M., Suard F., Riu D.

A review on lithium-ion battery ageing mechanisms and estimations for automotive applications

J Power Sources, 241 (2013), pp. 680-689

View PDF View article View in Scopus Google Scholar

[9]

Xiong R., Tian J., Mu H., Wang C.

A systematic model-based degradation behavior recognition and health monitoring method for lithium-ion batteries

Appl Energy, 207 (2017), pp. 372-383

View PDF View article View in Scopus Google Scholar

[10]

Kausthubharam R., Koorata P.K., Panchal S., Fraser R., Fowler M.

Investigation of the thermal performance of biomimetic minichannel-based liquid-cooled large format pouch battery pack

J Energy Storage, 84 (2024), Article 110928

View in Scopus Google Scholar

[11]

Huang S.-C., Tseng K.-H., Liang J.-W., Chang C.-L., Pecht M.G.

An online SOC and SOH estimation model for lithium-ion batteries

Energies, 10 (4) (2017), p. 512

Crossref View in Scopus Google Scholar

[12]

Berecibar M., Gandiaga I., Villarreal I., Omar N., Van Mierlo J., Van den Bossche P.

Critical review of state of health estimation methods of Li-ion batteries for real applications

Renew Sustain Energy Rev, 56 (2016), pp. 572-587

View PDF View article View in Scopus Google Scholar

[13]

Ozkurt C., Camci F., Atamuradov V., Odorry C.

Integration of sampling based battery state of health estimation method in electric vehicles

Appl Energy, 175 (2016), pp. 356-367

View PDF View article View in Scopus Google Scholar

[14]

Babin A., Rizoug N., Mesbahi T., Boscher D., Hamdoun Z., Larouci C.

Total cost of ownership improvement of commercial electric vehicles using battery sizing and intelligent charge method

IEEE Trans Ind Appl, 54 (2) (2018), pp. 1691-1700

Crossref View in Scopus Google Scholar

[15]

Wang J., Yang H., Wang Z., Zhou Y., Liu P., Hong J.

State of health analysis of batteries at different stages based on real-world vehicle data and machine learning

J Energy Storage, 88 (2024), Article 111616

View PDF View article View in Scopus Google Scholar

[16]

Chen M., Ma X., Chen B., Arsenault R., Karlson P., Simon N., et al.

Recycling end-of-life electric vehicle lithium-ion batteries

Joule, 3 (11) (2019), pp. 2622-2646

View PDF View article View in Scopus Google Scholar

[17]

Zhang C., Yan J., You F.

Critical metal requirement for clean energy transition: a quantitative review on the case of transportation electrification

Adv Appl Energy, 9 (2023), Article 100116

View PDF View article View in Scopus Google Scholar

[18]

Ku A.Y., Alonso E., Eggert R., Graedel T., Habib K., Hool A., et al.

Grand challenges in anticipating and responding to critical materials supply risks

Joule, 8 (5) (2024), pp. 1208-1223

View PDF View article View in Scopus Google Scholar

[19]

Ungurean L., Cârstoiu G., Micea M.V., Groza V.

Battery state of health estimation: a structured review of models, methods and commercial devices

Int J Energy Res, 41 (2) (2016), pp. 151-181

Google Scholar

[20]

Oji T., Zhou Y., Ci S., Kang F., Chen X., Liu X.

Data-driven methods for battery soh estimation: Survey and a critical analysis

Ieee Access, 9 (2021), pp. 126903-126916

Crossref View in Scopus Google Scholar

[21]

Zhao J., Han X., Ouyang M., Burke A.F.

Specialized deep neural networks for battery health prognostics: Opportunities and challenges

J Energy Chem, 87 (2023), pp. 416-438

View PDF View article View in Scopus Google Scholar

[22]

Gu X., See K.W., Li P., Shan K., Wang Y., Zhao L., et al.

A novel state-of-health estimation for the lithium-ion battery using a convolutional neural network and transformer model

Energy, 262 (2023), Article 125501

View PDF View article View in Scopus Google Scholar

[23]

Bockrath S., Lorentz V., Pruckner M.

State of health estimation of lithium-ion batteries with a temporal convolutional neural network using partial load profiles

Appl Energy, 329 (2023), p. 120307

View PDF View article View in Scopus Google Scholar

[24]

Weng C., Feng X., Sun J., Peng H.

State-of-health monitoring of lithium-ion battery modules and packs via incremental capacity peak tracking

Appl Energy, 180 (2016), pp. 360-368

View PDF View article View in Scopus Google Scholar

[25]

Pozzato G., Allam A., Pulvirenti L., Negoita G.A., Paxton W.A., Onori S.

Analysis and key findings from real-world electric vehicle field data

Joule, 7 (9) (2023), pp. 2035-2053

View PDF View article View in Scopus Google Scholar

[26]

Zhao Y., Behdad S.

State of health estimation of electric vehicle batteries using transformer-based neural network

J Energy Resour Technol, 146 (10) (2024), Article 101703

View in Scopus Google Scholar

[27]

Baure G., Dubarry M.

Synthetic vs. real driving cycles: A comparison of electric vehicle battery degradation

Batteries, 5 (2) (2019), p. 42

Crossref View in Scopus Google Scholar

[28]

Wen S., Lin N., Huang S., Wang Z., Zhang Z.

Lithium battery health state assessment based on vehicle-to-grid (V2G) real-world data and natural gradient boosting model

Energy, 284 (2023), Article 129246

View PDF View article View in Scopus Google Scholar

[29]

Liu H., Deng Z., Yang Y., Lu C., Li B., Liu C., et al.

Capacity evaluation and degradation analysis of lithium-ion battery packs for on-road electric vehicles

J Energy Storage, 65 (2023), Article 107270

View PDF View article View in Scopus Google Scholar

[30]

Rezvanizaniani S.M., Liu Z., Chen Y., Lee J.

Review and recent advances in battery health monitoring and prognostics technologies for electric vehicle (EV) safety and mobility

J Power Sources, 256 (2014), pp. 110-124

View PDF View article View in Scopus Google Scholar

[31]

Vaswani A., Shazeer N., Parmar N., Uszkoreit J., Jones L., Gomez A.N., et al.

Attention is all you need

Advances in neural information processing systems (neurIPS) (2017), pp. 6000-6010

View in Scopus Google Scholar

[32]

He Z., Ni X., Pan C., Hu S., Han S.

Full-process electric vehicles battery state of health estimation based on informer novel model

J Energy Storage, 72 (2023), Article 108626

View PDF View article View in Scopus Google Scholar

[33]

Hannan M.A., How D.N., Lipu M.H., Mansor M., Ker P.J., Dong Z., et al.

Deep learning approach towards accurate state of charge estimation for lithium-ion batteries using self-supervised transformer model

Sci Rep, 11 (1) (2021), p. 19541

View in Scopus Google Scholar

[34]

Singh S., Budarapu P.

Deep machine learning approaches for battery health monitoring

Energy, 300 (2024), Article 131540

View PDF View article View in Scopus Google Scholar

[35]

Zhang W., Jia J., Pang X., Wen J., Shi Y., Zeng J.

An improved transformer model for remaining useful life prediction of lithium-ion batteries under random charging and discharging

Electronics, 13 (8) (2024), p. 1423

Crossref View in Scopus Google Scholar

[36]

Zhao W., Ding W., Zhang S., Zhang Z.

Enhancing lithium-ion battery lifespan early prediction using a multi-branch vision transformer model

Energy, 302 (2024), Article 131816

View PDF View article View in Scopus Google Scholar

[37]

Biggio L., Bendinelli T., Kulkarni C., Fink O.

Ageing-aware battery discharge prediction with deep learning

Appl Energy, 346 (2023), Article 121229

View PDF View article View in Scopus Google Scholar

[38]

Costa N., Anseán D., Dubarry M., Sánchez L.

ICFormer: A deep learning model for informed lithium-ion battery diagnosis and early knee detection

J Power Sources, 592 (2024), Article 233910

View PDF View article View in Scopus Google Scholar

[39]

Chen D., Zhou X.

AttMoE: Attention with mixture of experts for remaining useful life prediction of lithium-ion batteries

J Energy Storage, 84 (2024), Article 110780

View PDF View article View in Scopus Google Scholar

[40]

Wang W., Yang K., Zhang L., Zhou S., Ren B., Lu Y., et al.

An end-cloud collaboration approach for online state-of-health estimation of lithium-ion batteries based on multi-feature and transformer

J Power Sources, 608 (2024), Article 234669

View PDF View article View in Scopus Google Scholar

[41]

Fauzi M.R., Yudistira N., Mahmudy W.F.

State-of-health prediction of lithium-ion batteries using exponential smoothing transformer with seasonal and growth embedding

IEEE Access, 12 (2024), pp. 14659-14670

Crossref View in Scopus Google Scholar

[42]

Gomez W., Wang F.-K., Chou J.-H.

Li-ion battery capacity prediction using improved temporal fusion transformer model

Energy, 296 (2024), Article 131114

View PDF View article View in Scopus Google Scholar

[43]

Luo K., Zheng H., Shi Z.

A simple feature extraction method for estimating the whole life cycle state of health of lithium-ion batteries using transformer-based neural network

J Power Sources, 576 (2023), Article 233139

View PDF View article View in Scopus Google Scholar

[44]

Jia C., Tian Y., Shi Y., Jia J., Wen J., Zeng J.

State of health prediction of lithium-ion batteries based on bidirectional gated recurrent unit and transformer

Energy, 285 (2023), Article 129401

View PDF View article View in Scopus Google Scholar

[45]

Zhao H., Chen Z., Shu X., Shen J., Lei Z., Zhang Y.

State of health estimation for lithium-ion batteries based on hybrid attention and deep learning

Reliab Eng Syst Saf, 232 (2023), Article 109066

View PDF View article View in Scopus Google Scholar

[46]

Fan Y., Li Y., Zhao J., Wang L., Yan C., Wu X., et al.

Online state-of-health estimation for fast-charging lithium-ion batteries based on a transformer–long short-term memory neural network

Batteries, 9 (11) (2023), p. 539

Crossref View in Scopus Google Scholar

[47]

Zou C., Chen X., Zhang Y.

State of health prediction of lithium-ion batteries based on temporal degeneration feature extraction with deep cycle attention network

J Energy Storage, 65 (2023), Article 107367

View PDF View article View in Scopus Google Scholar

[48]

Gao M., Shen H., Bao Z., Deng Y., He Z.

A correlation-augmented informer-based method for state-of-health estimation of Li-ion batteries

IEEE Sens J, 24 (3) (2023), pp. 3342-3353

Google Scholar

[49]

Chen L., Xie S., Lopes A.M., Bao X.

A vision transformer-based deep neural network for state of health estimation of lithium-ion batteries

Int J Electr Power Energy Syst, 152 (2023), Article 109233

View PDF View article View in Scopus Google Scholar

[50]

Bai T., Wang H.

Convolutional transformer-based multi-view information perception framework for lithium-ion battery state-of-health estimation

IEEE Trans Instrum Meas, 72 (2023), pp. 1-12

Crossref Google Scholar

[51]

Shi D., Zhao J., Wang Z., Zhao H., Eze C., Wang J., et al.

Cloud-based deep learning for co-estimation of battery state of charge and state of health

Energies, 16 (9) (2023), p. 3855

Crossref View in Scopus Google Scholar

[52]

Cai N., Qin Y., Chen X., Wu K.

Dual time-scale state-coupled co-estimation of state of charge, state of health and remaining useful life for lithium-ion batteries via deep inter and intra-cycle attention network

J Energy Storage, 77 (2024), Article 109797

View PDF View article View in Scopus Google Scholar

[53]

Ke L., Fang L., Meng J., Peng J., Wu J., Lin M., et al.

Identification of the aging state of lithium-ion batteries via temporal convolution network and self-attention mechanism

J Energy Storage, 84 (2024), Article 110999

View PDF View article View in Scopus Google Scholar

[54]

Tang A., Jiang Y., Yu Q., Zhang Z.

A hybrid neural network model with attention mechanism for state of health estimation of lithium-ion batteries

J Energy Storage, 68 (2023), Article 107734

View PDF View article View in Scopus Google Scholar

[55]

Sun Z., Fan G., Liu Y., Zhou B., Wang Y., Chen S., et al.

Interactive fusion of local and global degradation representations for rapid estimation of lithium-ion battery state-of-health

J Energy Storage, 90 (2024), Article 111832

View PDF View article View in Scopus Google Scholar

[56]

Chen X., Qin Y., Zhao W., Yang Q., Cai N., Wu K.

A self-attention knowledge domain adaptation network for commercial lithium-ion batteries state-of-health estimation under shallow cycles

J Energy Storage, 86 (2024), Article 111197

View PDF View article View in Scopus Google Scholar

[57]

Giordano G., Klass V., Behm M., Lindbergh G., Sjöberg J.

Model-based lithium-ion battery resistance estimation from electric vehicle operating data

IEEE Trans Veh Technol, 67 (5) (2018), pp. 3720-3728

Crossref View in Scopus Google Scholar

[58]

Zhang Y., Wik T., Bergström J., Pecht M., Zou C.

A machine learning-based framework for online prediction of battery ageing trajectory and lifetime using histogram data

J Power Sources, 526 (2022), Article 231110

View PDF View article View in Scopus Google Scholar

[59]

She C., Wang Z., Sun F., Liu P., Zhang L.

Battery aging assessment for real-world electric buses based on incremental capacity analysis and radial basis function neural network

IEEE Trans Ind Inf, 16 (5) (2020), pp. 3345-3354

Crossref View in Scopus Google Scholar

[60]

Zhao X., Hu J., Hu G., Qiu H.

A state of health estimation framework based on real-world electric vehicles operating data

J Energy Storage, 63 (2023), Article 107031

View PDF View article View in Scopus Google Scholar

[61]

Song L., Zhang K., Liang T., Han X., Zhang Y.

Intelligent state of health estimation for lithium-ion battery pack based on big data analysis

J Energy Storage, 32 (2020), Article 101836

View PDF View article View in Scopus Google Scholar

[62]

Zhao J., Ling H., Liu J., Wang J., Burke A.F., Lian Y.

Machine learning for predicting battery capacity for electric vehicles

ETransportation, 15 (2023), Article 100214

View PDF View article View in Scopus Google Scholar

[63]

Devlin J., Chang M.-W., Lee K., Toutanova K.

BERT: Pre-training of deep bidirectional transformers for language understanding

Proceedings of the 2019 conference of the North American chapter of the association for computational linguistics: human language technologies (NAACL-HLT) (2019), pp. 4171-4186

Crossref View in Scopus Google Scholar

[64]

Dosovitskiy A., Beyer L., Kolesnikov A., Weissenborn D., Zhai X., Unterthiner T., et al.

An image is worth 16 × 16 words: Transformers for image recognition at scale

International conference on learning representations, ICLR (2021)

Google Scholar

[65]

Baevski A., Zhou Y., Mohamed A., Auli M.

wav2vec 2.0: A framework for self-supervised learning of speech representations

Advances in neural information processing systems (neurIPS) (2020), pp. 12449-12460

Google Scholar

[66]

Ioffe S, Szegedy C. Batch normalization: Accelerating deep network training by reducing internal covariate shift. In: International conference on machine learning. ICML, 2015, p. 448–56.

Google Scholar

[67]

Ba J.L., Kiros J.R., Hinton G.E.

Layer normalization

(2016)

arXiv preprint arXiv:1607.06450

Google Scholar

[68]

Loshchilov I., Hutter F.

Decoupled weight decay regularization

(2017)

arXiv preprint arXiv:1711.05101

Google Scholar

[69]

Radford A., Wu J., Child R., Luan D., Amodei D., Sutskever I., et al.

Language models are unsupervised multitask learners

(2019)

preprint

Google Scholar

[70]

Liu K., Peng Q., Che Y., Zheng Y., Li K., Teodorescu R., et al.

Transfer learning for battery smarter state estimation and ageing prognostics: Recent progress, challenges, and prospects

Adv Appl Energy, 9 (2023), Article 100117

View PDF View article View in Scopus Google Scholar

[71]

Ansel J, Yang E, He H, Gimelshein N, Jain A, Voznesensky M, et al. PyTorch 2: Faster Machine Learning Through Dynamic Python Bytecode Transformation and Graph Compilation. In: International conference on architectural support for programming languages and operating systems. ASPLOS, 2024, p. 929–47.

Google Scholar

[72]

Zhang H, Gui X, Zheng S, Lu Z, Li Y, Bian J. BatteryML: An Open-source Platform for Machine Learning on Battery Degradation. In: International conference on learning representations. ICLR, 2024.

Google Scholar

[73]

Li L., Jamieson K., DeSalvo G., Rostamizadeh A., Talwalkar A.

Hyperband: A novel bandit-based approach to hyperparameter optimization

J Mach Learn Res, 18 (185) (2018), pp. 1-52

Google Scholar

### State-of-health estimation for EV battery packs via incremental capacity curves and S-transform

2025, Applied Energy

Show abstract

### Domain-adaptive state of health prediction of vehicle batteries powered by deep learning

2025, Cell Reports Physical Science

Show abstract

### Towards digitized electrochemical power source for electric vehicles

2025, Etransportation

Show abstract

### Fast Battery Capacity Estimation Method Based on State of Charge and IC Curve Peak Value

2025, World Electric Vehicle Journal

### Repurposing Second-Life EV Batteries to Advance Sustainable Development: A Comprehensive Review

2024, Batteries

### Prediction of Lithium-Ion Battery State of Health Using a Deep Hybrid Kernel Extreme Learning Machine Optimized by the Improved Black-Winged Kite Algorithm

2024, Batteries

View all citing articles on Scopus

☆

The short version of the paper was presented at ICAE2023, Doha, Qatar, Dec 3–5, 2023. This paper is a substantial extension of the short version of the conference paper.

1

Map data from OpenStreetMap (openstreetmap.org/copyright).

2

Map data from OpenStreetMap (openstreetmap.org/copyright) and CARTO (https://carto.com/).

3

Map data from OpenStreetMap (openstreetmap.org/copyright) and CARTO (https://carto.com/).

© 2024 The Authors. Published by Elsevier Ltd.