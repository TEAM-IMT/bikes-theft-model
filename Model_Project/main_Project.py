import numpy as np
np.random.seed(4)
import torch
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from torch import nn
from Model_LSTM import RNN_LSTM
from CreatingData import *
from Load_data import LoadDataset
from math import *
from TrainVal import *

# General parameters
device = "cpu"


# CTs=['5350008.01', '5350008.02', '5350010.02', '5350011.00',
#        '5350012.01', '5350012.03', '5350012.04', '5350013.01',
#        '5350013.02', '5350016.00', '5350017.00', '5350032.00',
#        '5350034.02', '5350035.00', '5350037.00', '5350038.00',
#        '5350044.00', '5350062.02', '5350064.00', '5350066.00',
#        '5350089.00', '5350091.01', '5350092.00','5350014.00']

hidden_dim = 800 #Neurons in hidden layer of the LSTM #H
rnn_layers = 10 #Number of RNN Hidden layers / Stacked lstm #rn
dropout =0.8 #Dropout percentage #d
learning_rate = 1e-3 #lr 
n_epochs = 200 #ep

batch_size=128 #b
time_step = 5
time_step_past=10 #st

model_name = './Cluster3/model_H800_rn10_d08_lr1e3_ep200.pt'



training_generator, validation_generator ,test_generator,code,sizeData = Create_DataLoaders(CTs,time_step,batch_size,100)


print("Data ready !")
print(code)
print(sizeData)

# Create the model
model = RNN_LSTM(time_step_past, hidden_dim, rnn_layers, dropout).to(device)

# Define the loss function and the optimizer
criterion = nn.MSELoss(reduction='sum')


#optimizer_rnn = torch.optim.RMSprop(model.parameters(), lr = learning_rate)
optimizer_rnn = torch.optim.Adam(model.parameters(), lr = learning_rate,weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.StepLR(optimizer_rnn, step_size = 200, gamma = 0.5)

# # #Train Model
Train(n_epochs,model,training_generator,optimizer_rnn,criterion,validation_generator,scheduler,model_name,'./Cluster1/Lost.png')

# Validación (predicción del valor de las acciones)
model.load_state_dict(torch.load(model_name))

Ct_prueba =['5350014.00']
Names = ['Train','Validation','Test']
for i in Ct_prueba:

    prediction_title= 'Prediction in Train for CT :'+i
    Validation(model,training_generator,code,i,prediction_title,'./Cluster3/train_{}.png'.format(i),prediction_title)
    prediction_title= 'Prediction in Validation for CT :'+i
    Validation(model,validation_generator,code,i,prediction_title,'./Cluster3/Val_{}.png'.format(i),prediction_title)
    prediction_title= 'Prediction in Test for CT :'+i
    Validation(model,test_generator,code,i,prediction_title,'./Cluster3/test_{}.png'.format(i),prediction_title)
