# LibreVNA_2RFI
Complementary scripts to use the LibreVNA device for RFI measurements. 
Unattended data recording for two channel vna.<br>
Script to automatically acquire the 2 LibreVNA channels, to measure RFI.

## Getting Started

### Dependencies

* Ubuntu system for LibreVNA-GUI operation. LibreVNA-1.4.1 was used.

### Installing

* No installation needed, just run the Python script (configure the script according to your system before)
* https://github.com/joabAM/LibreVNA_2RFI 

### Executing program

* To start acquisition:
```
python3 autoSA.py
```
* To make the plots:
Comment or uncomment the final lines as needed.
```
python3 readNVA.py
```

## Authors

Contributors names and contact info

Joab Apaza, japaza@igp.gob.pe, https://github.com/joabAM

