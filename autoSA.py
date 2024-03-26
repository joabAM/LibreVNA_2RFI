#!/usr/bin/env python

"""autoSA.py:
"""

__author__      = "Joab Apaza"
__email__   = "japaza@igp.gob.pe"
##########################################################################################

import os
import subprocess
from datetime import datetime
from time import sleep
import h5py
from libreVNA import libreVNA
NPOINTS = 1001

##########################################################################################
##########################################################################################
##########################################################################################
################################ CONFIG PARAMETERS  ######################################
pathVNAgui = "/home/japaza/Documents/MRI/LibreVNA-GUI"
outPath = "/home/japaza/Documents/MRI/LibreVNApy/out/"
RBW = 50
minF = 1
maxF = 100
window = "KAISER"
detector = "AVERAGE"
navg = 1
nblocks = 3


##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################


#os.system(pathVNAgui)
subprocess.call(["gnome-terminal", "-x", "sh", "-c", pathVNAgui])

sleep(1)
print("Setting VNA parameters")
vna = libreVNA('localhost', 19542)
vna.connect()
#vna.connect("2069358B3750")
sleep(1)

while(not vna.set_mode("SA")):
    sleep(1)


#frequency range 1 to 100 MHz
vna.set_saStart(minF)
vna.set_saStop(maxF)
sleep(0.1)
#Resolution bandwidth set to 12KHz
vna.set_saRBW(RBW)
sleep(0.1)
#Acquisition window set to kaiser
vna.set_saWindow(window)
sleep(0.1)
#Configuring the detector as Average
vna.set_saDetector(detector)
sleep(0.1)
#number of integrations
vna.set_saAvgNumber(navg)
sleep(0.1)
#IMPORTANT TO SET THIS
vna.set_saSignalID(True)



def newFile(name, columns, freq):
    f = h5py.File(name, 'w')
    a = f.create_group('Data')
            
    b = f.create_group('MetaData')
    b.attrs['Start Frequency'] = minF*1000000
    b.attrs['Stop Frequency'] = maxF*1000000
    b.attrs['Resolution Frequency'] = RBW*1000
    b.attrs['window'] = window
    b.attrs['detector'] = detector
    b.attrs['navg'] = navg
    a.create_dataset("dBm", (nblocks,columns, 2), maxshape=(500, columns, 2))
    a.create_dataset("frequency", (columns,), data=freq)
    a.create_dataset("datetime", (nblocks,), maxshape=(500,))

    a.create_dataset("LOtemperature", (nblocks,), maxshape=(500,))
    a.create_dataset("CPUtemperature", (nblocks,), maxshape=(500,))
    return f

block = 0
while( vna.get_saCurrentAvg() < 1):
    sleep(1)
dat = vna.get_saData()
(dim, length) = dat.shape
freqs = dat[0, :]
f = None
while(True):
    
    if (vna.get_saCurrentAvg()==navg):
        if block==nblocks or block==0:
            try:
                f.close()
            except:
                pass
            filename = "spc_"+datetime.now().strftime("%Y%m%d-%H%M%S")+".h5"
            try:
                fullFile = os.path.join(outPath, filename)
            except:
                print("Output path does not exist")
                SystemExit(-1)
            print("Creating file -> ", filename)
            f = newFile(fullFile,length,freqs )
            block = 0

        data = vna.get_saData(port=1)
        time = datetime.now().timestamp() 
        dset = f["Data/dBm"]
        #print(dset, dset.shape)
        utc =  f["Data/datetime"]
        dset[block,:,0] = data[1] #update dBm = data[1] port 1
        data = vna.get_saData(port=2)
        dset[block,:,1] = data[1] #update dBm = data[1] port 2
        utc[block] = time #update dBm data
        f["Data/LOtemperature"][block] = vna.get_loTemp()
        f["Data/CPUtemperature"][block] = vna.get_cpuTemp()
        block+=1
        vna.set_saAvgNumber(navg, msg=False) #restart the acquisition



