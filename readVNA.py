#!/usr/bin/env python

"""readVNA.py:
"""

__author__      = "Joab Apaza"
__email__   = "japaza@igp.gob.pe"
##############################################################################################
import numpy as np
import h5py 
from matplotlib import pyplot  as plt
import os 
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime


class spectraVNA():
    
    def __init__(self):
        self.dBm = None
        self.freq = None
        self.dateTime = None
        self.empty = True
        self.cpuTemp = None
        self.loTemp = None
        ##############################################################################################
        ##                          metadata SA
        ##############################################################################################
        self.rbw = 0
        self.start = 0
        self.stop=0
        self.detector = None
        self.avg = 1
        self.window = "None"

    @property
    def span(self):
        return self.stop - self.start
    
    def locateFiles(self, path):
        fileList=[]
        list =  os.listdir(path)      #read all files
        list.sort()
        for file in list:
            if file.endswith(".h5"):  #h5 spc
                fileList.append(os.path.join(path,file))
        return fileList

    def getData(self, files, port=1):
         
        for file in files:
            try:
                with  h5py.File(file, 'r') as f:
                    dBm =  f.get("/Data/dBm")[:]
                    
                    if self.empty:
                        #dBm =  f.get("/Data/dBm")[:] 
                        self.dBm = dBm[:,:,port-1] if len(dBm.shape)>2  else  dBm[:]
                        self.freq =  f.get("/Data/frequency")[:]
                        self.dateTime = f.get("/Data/datetime")[:]
                        self.cpuTemp = f.get("/Data/CPUtemperature")[:]
                        self.loTemp = f.get("/Data/LOtemperature")[:]
                        #get the SA Metadata...
                        self.rbdw = f.get("/MetaData").attrs['Resolution Frequency']
                        self.start = f.get("/MetaData").attrs['Start Frequency']
                        self.stop = f.get("/MetaData").attrs['Stop Frequency']
                        self.detector = f.get("/MetaData").attrs['detector']
                        self.navg = f.get("/MetaData").attrs['navg']
                        self.window = f.get("/MetaData").attrs['window']
                        self.empty = False
                    else:
                        self.dBm  = np.concatenate( (self.dBm, dBm[:,:,port-1]), axis=0) if len(dBm.shape)>2  else  np.concatenate( (self.dBm, dBm[:]), axis=0)
                        #self.dBm = np.concatenate( (self.dBm, dBm[:,:,port-1]), axis=0)
                        self.dateTime = np.concatenate( (self.dateTime, f.get("/Data/datetime")[:]), axis=0)
                        self.cpuTemp = np.concatenate( (self.cpuTemp, f.get("/Data/CPUtemperature")[:]), axis=0)
                        self.loTemp = np.concatenate( (self.loTemp, f.get("/Data/LOtemperature")[:]), axis=0)
            except Exception as e:
                print("FILE->", file)
                print(e)
                continue

    def plot3D(self, mindB=-100, maxdB=-30 ):
        ## Matplotlib Sample Code using 2D arrays via meshgrid
        x = (self.dateTime -self.dateTime[0])/3600 #to hours
        y = self.freq/1000000  #To MHz
        X, Y = np.meshgrid(x, y)
        
        Z = self.dBm
        #print(Z)
        fig = plt.figure(num=1)

        ax = plt.axes(projection='3d')
        #ax.xaxis_date()
        surf = ax.plot_surface(X, Y, Z.T, rstride=1, cstride=1, cmap=cm.jet,
                           linewidth=0, antialiased=False, vmin=mindB, vmax=maxdB )
        ax.set_zlim(mindB, maxdB)
        # ax.zaxis.set_major_locator(LinearLocator(10))
        # ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
        cb = fig.colorbar(surf, shrink=0.4, aspect=5)
        plt.title('3D surface RFI')
        ax.set_xlabel('hours')
        ax.set_ylabel('MHz')
        ax.set_zlabel('dBm')

        ax.view_init(elev=30, azim=-20)
        plt.show()
    
    def plot2D(self, mindB=-100, maxdB=-20):

        x = self.freq/1000000  #To MHz
        # y = (self.dateTime -self.dateTime[0])/3600 #to hours
        #print(self.dateTime)
        y = [datetime.fromtimestamp(ts) for ts in self.dateTime]
        X, Y = np.meshgrid(x, y)
        Z = self.dBm
        fig = plt.figure(num=3)

        ax = plt.axes()
        #ax.yaxis_date(tz="America/Bogota")
        mesh = ax.pcolormesh(X, Y, Z,  cmap=cm.jet, vmin=mindB, vmax=maxdB )

        cb = fig.colorbar(mesh, shrink=0.5, aspect=5)
        plt.title('2D map RFI')
        plt.xlabel("MHz")
        plt.ylabel("hours")
        plt.show()


    def plotAvg(self):
        x = self.freq/1000000  #To MHz
        y = self.dBm.mean(axis=0)
        fig = plt.figure(num=2)
        ax = plt.axes()
        ax.plot(x, y)
        plt.grid()
        plt.title('Average Spectrum RFI')
        plt.xlabel("MHz")
        plt.ylabel("dBm")
        
        plt.show() 


##############################################################################################
##############################################################################################

path = "/home/japaza/Documents/MRI/LibreVNApy/spcVNA4_2pol"
# path = "/home/japaza/Documents/MRI/LibreVNApy/spcVNA3_2pol"
path = "/home/japaza/Documents/MRI/LibreVNApy/spcTest" ##clean data n-s
# # spcVNA3_2Pol  port1 = E-W
# # spcVNA3_2Pol  port2 = N-S

vna = spectraVNA()
files = vna.locateFiles(path)

vna.getData(files, port=2)

# vna.plot3D()
vna.plot2D()
#vna.plotAvg()
