import pandas as pd
from matplotlib import pyplot as plt
'exec(%matplotlib inline)'
import seaborn as sns
import numpy as np
import scipy as sp
import plotly.express as px
import plotly.graph_objects as go
from statsmodels.graphics.mosaicplot import mosaic

class GraphsStatistics :
    
    def readDB(self,filename):
        return pd.read_csv(filename, header = 0)

    def Data_Shape(self,Data):
        dataset_type=type(Data)
        # the shape of data 
        shape=Data.shape
        #variables in data
        col_names=Data.columns
        return dataset_type,shape,col_names

    def Data_Describe(self,Data):
        num_des=Data.describe()
        cate_des=Data.describe(include=['object'])

        return num_des,cate_des

    def CountBar_plot(self,Data,nombre, titulo):
        #Bar plot cout of name
        fig = px.bar(Data, names=nombre, title=titulo)
        fig.show()

    def Scatter_Plot(self,data,x_line:list,y_line:list): 
        # Grahp x vs y
        fig = px.scatter(data,x=x_line, y=y_line)
        fig.show()

    def Scatter_Matrix(self,data,dim,color):
        #Scater matrix of dim (list[]) by color
        fig = px.scatter_matrix(data, dimensions=dim, color=color)
        fig.show()


    def Box_plot(self,data,x_line,y_line,orient):
        #Box plot
        fig = px.box(data,x=x_line, y=y_line,orientation=orient)
        fig.show()

    def Bar_Stacket(self,data,X,Y):
        # Bar stacket color =Y, count X
        ax1=pd.crosstab(data.X,data.Y).plot.barh(stacked=True)

        return ax1

    def Histogram_plot(self,data,x_line,color):
        #Histogram of X_line per color
        fig = px.histogram(data, x=x_line, color=color, barmode='group')
        fig.show()

    def plot_corr(self,data):
        corr = data.corr()
        # Generate a mask for the upper triangle
        mask = np.zeros_like(corr, dtype=np.bool)
        mask[np.triu_indices_from(mask, k=1)] = True

        # Generate a custom diverging colormap
        cmap = sns.diverging_palette(220, 10, as_cmap=True)
        sns.heatmap(corr, cmap=cmap, mask = mask)

    def Mosaic_square(self,data,x,y):
        ax=mosaic(data,[x,y])
        return ax 

    def Circulo(self,Data,name,titulo):
        fig=px.pie(data_frame=Data,names=name,title=titulo)
        fig.show()
        
    



