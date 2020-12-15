import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler
from Load_data import LoadDataset
import matplotlib.pyplot as plt
import numpy as np
from torch.utils.data import DataLoader
from torch.utils.data import TensorDataset
import torch
import plotly.graph_objects as go

def getDLo(x, y, params):
    """Given the inputs, labels and dataloader parameters, returns a pytorch dataloader
    Args:
        x ([list]): [inputs list]
        y ([list]): [target variable list]
        params ([dict]): [Parameters pertaining to dataloader eg. batch size]
    """
    training_set = LoadDataset(x, y)
    training_generator = torch.utils.data.DataLoader(training_set, **params)
    return training_generator

def train_val_split(x, y, train_pct):
    """Given the input x and output labels y, splits the dataset into train, validation and test datasets
    Args:
        x ([list]): [A list of all the input sequences]
        y ([list]): [A list of all the outputs (floats)]
        train_pct ([float]): [% of data in the test set]
    """
    # Perform a train test split (It will be sequential here since we're working with time series data)
    N = len(x)
    
    trainX = x[:int(train_pct * N)]
    trainY = y[:int(train_pct * N)]

    valX = x[int(train_pct * N):]
    valY = y[int(train_pct * N):]

    trainX = torch.from_numpy(trainX).float()
    trainY = torch.from_numpy(trainY).float()

    valX = torch.from_numpy(valX).float()
    valY = torch.from_numpy(valY).float()

    return (trainX, trainY, valX, valY)


def standardizeData(X, SS = None, train = False):
    """Given a list of input features, standardizes them to bring them onto a homogenous scale
    Args:
        X ([dataframe]): [A dataframe of all the input values]
        SS ([object], optional): [A StandardScaler object that holds mean and std of a standardized dataset]. Defaults to None.
        train (bool, optional): [If False, means validation set to be loaded and SS needs to be passed to scale it]. Defaults to False.
    """
    if train:
        SS = StandardScaler()   
        new_X = SS.fit_transform(X)
        return (new_X, SS)
    else:
        new_X = SS.transform(X)
        return (new_X, None)

def time_series_plot(census_path, theft_path = "./Data/Bicycle_Thefts_Toronto_geo.csv", year = None, threshold = None, isprint = True):
    # Read data and clean
    df_census = pd.read_csv(census_path, index_col = 0, dtype = {"GeoUID":str})
    df_census = df_census[df_census["Region Name"] == "Toronto"]
    df_census = df_census[["GeoUID", "Area (sq km)", "v_CA16_5807: Bicycle"]].replace({"x":np.nan, "F":np.nan}) # Keep important variables
    df_census["GeoUID"] = df_census["GeoUID"].apply(lambda x: x if len(x.split(".")[-1]) > 1 else x + "0") # Fix important bug
    for col in df_census: # Type change
        df_census[col] = df_census[col].astype(float) if col != "GeoUID" else df_census[col]
    df_theft = pd.read_csv(theft_path, dtype = {"GeoUID":str})
    df_theft["GeoUID"] = df_theft["GeoUID"].apply(lambda x: x if len(x.split(".")[-1]) > 1 else x + "0") # Fix important bug
    
    # Data process: Get Total theft by sum registers and mean cost of bike by CT and date
    df_theft["Occurrence_Date"] = pd.to_datetime(df_theft["Occurrence_Date"])
    df_theft = df_theft[df_theft["Status"] == "STOLEN"].groupby(["GeoUID", pd.Grouper(key="Occurrence_Date", freq="1W-MON")]).\
        agg({"X":"count", "Cost_of_Bike":"mean", "Occurrence_Year":lambda x: x.iloc[0]}).\
        reset_index().rename(columns={"X":"Total_Theft_Bikes"}).sort_values("Occurrence_Date")
    
    # Merge data with census info and corr plot
    df_theft = df_theft[df_theft["Occurrence_Year"] <= 2019]
    if isprint: display(df_theft)
    df_census_theft = df_census.merge(df_theft, on = "GeoUID", how = "right").fillna(0.0) # NaN = 0 thefts
    if isprint: display(df_census_theft[["Total_Theft_Bikes", 'v_CA16_5807: Bicycle', 'Area (sq km)']].describe())
    df_proof = df_census.loc[df_census['v_CA16_5807: Bicycle'] == 0, "GeoUID"].unique()
#     print(len(df_proof), df_proof)
    df_proof = df_census_theft.loc[df_census_theft['v_CA16_5807: Bicycle'] == 0, "GeoUID"].unique()
#     print(len(df_proof), df_proof)
    df_census_theft = df_census_theft[df_census_theft['v_CA16_5807: Bicycle'] != 0.0]
    df_census_theft["Theft_Density/Area"] = df_census_theft["Total_Theft_Bikes"] * 100.0
    df_census_theft["Theft_Density/Area"] /= df_census_theft['v_CA16_5807: Bicycle'] * df_census_theft['Area (sq km)']
    
    if isprint: display(df_census_theft["Theft_Density/Area"].describe())
    if isprint: display(df_census_theft.groupby("GeoUID").size().sort_values(ascending = False).head(30))
    
    # Plot
    fig = go.Figure()
    df_census_theft = df_census_theft.sort_values("Occurrence_Date")
    total_df = []
    if year is not None: df_census_theft = df_census_theft[df_census_theft["Occurrence_Year"] == year]
    for ct in df_census_theft["GeoUID"].unique():
        df_census_theft_ct = df_census_theft[df_census_theft["GeoUID"] == ct].set_index("Occurrence_Date")
        area = df_census_theft_ct["Area (sq km)"].iloc[0] # Store values
        bike = df_census_theft_ct["v_CA16_5807: Bicycle"].iloc[0]
        if threshold is None or len(df_census_theft_ct) > threshold:
            df_census_theft_ct = df_census_theft_ct.reindex(pd.date_range(start = '01/01/2014', end = '31/12/2019', freq = 'W-MON')).fillna(0.0)
            # Restore values
            df_census_theft_ct["GeoUID"] = ct; df_census_theft_ct.loc[:, "Area (sq km)"] = area
            df_census_theft_ct.loc[:, "v_CA16_5807: Bicycle"] = bike
            total_df.append(df_census_theft_ct.drop(columns = ["Occurrence_Year"]).reset_index().rename(columns = {"index":"Occurrence_Date"}))
            if isprint: 
                fig.add_trace(go.Scatter(x = df_census_theft_ct.index, y = df_census_theft_ct["Theft_Density/Area"], 
                                         mode = 'lines', name = 'CT-' + ct))
    if isprint: 
        fig.update_xaxes(visible = False)
        fig.update_yaxes(title = "%Vol de vélo/Area")
        fig.show()
    return pd.concat(total_df, ignore_index = True)


def load_database(census_path = "./Data/census_data.csv", theft_path = "./Data/Bicycle_Thefts_Toronto_geo.csv", 
                  threshold = 100, CTs = [], start_date = None, end_date = None, tscol = 'Theft_Density/Area', 
                  ini_states = [], step_past = 1, step_future = 1):
    # Merge data and filter it by dates and CTs
    time_series = time_series_plot(census_path = census_path, theft_path = theft_path, threshold = threshold, isprint = False)
    # Keep important data by date
    init_values = [] # Save initial states
    for ini_val in ini_states: init_values.append(time_series[time_series["Occurrence_Date"] == ini_val])
    #print(init_values)
    if len(init_values) > 0: 
        init_values = pd.concat(init_values, ignore_index = True)
        init_values = init_values.sort_values("Occurrence_Date")
    if start_date is not None: time_series = time_series[time_series["Occurrence_Date"] >= start_date] 
    if end_date is not None: time_series = time_series[time_series["Occurrence_Date"] <= end_date]
    # Keep important data by CT 
    time_series_filter = []
    for ct in CTs:
        time_series_filter.append(time_series[time_series["GeoUID"] == ct])
    if len(time_series_filter) > 0: time_series = pd.concat(time_series_filter, ignore_index = True)
    #display(time_series, time_series.shape)
    
    # Process: data organize by batches: (i0,i1,i2,i3, x0,x1,x2,x3, x4)
    time_series = time_series.sort_values("Occurrence_Date")
    total_batches = None
    code = {}
    for ct in time_series["GeoUID"].unique():
        CT_time_series = time_series.loc[time_series["GeoUID"] == ct, tscol].to_numpy()
        if len(init_values) > 0: CT_init_values = init_values.loc[init_values["GeoUID"] == ct, tscol].to_numpy()
        N = len(CT_time_series) - (step_past + step_future) + 1
        # Get matrix window-slider
        CT_time_series = CT_time_series[np.arange(N)[None, :] + np.arange(step_past + step_future)[:, None]].T
        if len(init_values) > 0: # Add initial values
            code[ct] =  CT_init_values
            CT_init_values = np.ones((len(CT_time_series),1)) * CT_init_values[None]
            CT_time_series = np.append(CT_init_values, CT_time_series, axis = 1)
        if total_batches is None: total_batches = CT_time_series # Join all data
        else: 
            total_batches = np.append(total_batches, CT_time_series, axis = 0)
          
    return total_batches , code

def Create_DataLoaders(CTs,step_past,batch_size,threshold = 150):
    ## User parameters
    # CT list to filter in data
    set_dates = {"train": ('14-04-2014', '31-12-2018'), # Start/End date for each dataset
                "valid": ('01-01-2019', '30-06-2019'), "test": ('01-07-2019', '31-12-2019')}
    ini_states = ["2014-04-14", "2014-04-21","2014-04-28","2014-05-05","2014-05-12"] # Initial states
    #ini_states = ["2015-04-01", "2015-04-08","2015-04-15","2015-04-22","2015-04-29"]
    step_past = step_past # Past values in order to predict ...
    step_future = 1 # Future steps
    batch_size = batch_size

    ## Datasets creation
    batch_datasets = {key: load_database(threshold = threshold, CTs = CTs, start_date = dates[0], end_date = dates[1],
                                        ini_states = ini_states, step_past = step_past, step_future = step_future) 
                    for key, dates in set_dates.items()}

    code = batch_datasets['train'][1]
    batch_datasets = {key: value[0] for key, value in batch_datasets.items()}

    batch_datasets = {key: TensorDataset(torch.from_numpy(value[:,:-step_future]).float(), 
                            torch.from_numpy(value[:,-step_future:]).float()) for key, value in batch_datasets.items()}

    dataloaders = {key: DataLoader(value, batch_size = batch_size, shuffle = False) for key, value in batch_datasets.items()}
    datasets_sizes = {key: len(value) for key, value in batch_datasets.items()}
    #print(dataloaders['train']) #aqui estan los datos ini_state,train,valid
    return dataloaders['train'] ,dataloaders['valid'] , dataloaders['test'] , code , datasets_sizes

def Extract_Data_CT(code , xbatch, ybatch):
    
    identifier = xbatch[:,:5]
    total_batch_x = []
    total_batch_y = []

    code = torch.as_tensor(code[None])
    index= torch.sum(torch.abs(code - identifier ), 1)
    index = (index < 1e-5).nonzero(as_tuple=False)
    total_batch_x.append(xbatch[index])
    total_batch_y.append(ybatch[index])

    return torch.cat(total_batch_x,0).squeeze() , torch.cat(total_batch_y,0).squeeze(1)



def graph_pred(real, prediccion,title,fig):
    plt.plot(real[0:len(prediccion)],color='red', label='Ground truth')
    plt.plot(prediccion, color='blue', label='Predicted Value')
    #plt.ylim(1.1 * np.min(prediccion)/2, 1.1 * np.max(prediccion))
    plt.xlabel('Time')
    plt.ylabel('Prediction Value')
    plt.title(title)
    plt.legend()
    plt.savefig(fig)
    plt.show()

def graph_loss(train_loss, val_loss,title,fig):
    plt.plot(train_loss,color='red', label='Train lost')
    plt.plot(val_loss, color='blue', label='Validation lost')
    #plt.ylim(1.1 * np.min(prediccion)/2, 1.1 * np.max(prediccion))
    plt.xlabel('Epoch')
    plt.ylabel('Value')
    plt.title(title)
    plt.legend()
    plt.savefig(fig)
    plt.show()

