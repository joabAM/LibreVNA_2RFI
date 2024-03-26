import socket
from asyncio import IncompleteReadError  # only import the exception class
import time
from signal import signal, alarm, SIGALRM
from os.path import exists
from numpy import asarray

class SocketStreamReader:
    def __init__(self, sock: socket.socket):
        self._sock = sock
        self._sock.setblocking(0)
        self._recv_buffer = bytearray()
        self.timeout = 1.0

    def read(self, num_bytes: int = -1) -> bytes:
        raise NotImplementedError

    def readexactly(self, num_bytes: int) -> bytes:
        buf = bytearray(num_bytes)
        pos = 0
        while pos < num_bytes:
            n = self._recv_into(memoryview(buf)[pos:])
            if n == 0:
                raise IncompleteReadError(bytes(buf[:pos]), num_bytes)
            pos += n
        return bytes(buf)

    def readline(self) -> bytes:
        return self.readuntil(b"\n")

    def readuntil(self, separator: bytes = b"\n") -> bytes:
        if len(separator) != 1:
            raise ValueError("Only separators of length 1 are supported.")

        chunk = bytearray(4096)
        start = 0
        buf = bytearray(len(self._recv_buffer))
        bytes_read = self._recv_into(memoryview(buf))
        assert bytes_read == len(buf)

        timeout = time.time() + self.timeout
        while True:
            idx = buf.find(separator, start)
            if idx != -1:
                break
            elif time.time() > timeout:
                raise Exception("Timed out waiting for response from GUI")

            start = len(self._recv_buffer)
            bytes_read = self._recv_into(memoryview(chunk))
            buf += memoryview(chunk)[:bytes_read]

        result = bytes(buf[: idx + 1])
        self._recv_buffer = b"".join(
            (memoryview(buf)[idx + 1 :], self._recv_buffer)
        )
        return result

    def _recv_into(self, view: memoryview) -> int:
        bytes_read = min(len(view), len(self._recv_buffer))
        view[:bytes_read] = self._recv_buffer[:bytes_read]
        self._recv_buffer = self._recv_buffer[bytes_read:]
        if bytes_read == len(view):
            return bytes_read
        try:
            bytes_read += self._sock.recv_into(view[bytes_read:], 0)
        except:
            pass
        return bytes_read

class libreVNA():

    cmd0 = "**LST?"

    def __init__(self, host='localhost', port=19542):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((host, port))
        except:
            raise Exception("Unable to connect to LibreVNA-GUI. Make sure it is running and the TCP server is enabled.")
        self.reader = SocketStreamReader(self.sock)

    def __del__(self):
        self.sock.close()

    def __read_response(self):
        return self.reader.readline().decode().rstrip()

    def cmd(self, cmd):
        self.sock.sendall(cmd.encode())
        self.sock.send(b"\n")
        resp = self.__read_response()
        if len(resp) > 0:
        	raise Exception("Expected empty response but got "+resp)
        
    def query(self, query):
        self.sock.sendall(query.encode())
        self.sock.send(b"\n")
        return self.__read_response()
    
    @staticmethod
    def parse_VNA_trace_data(data):
        ret = []
        # Remove brackets (order of data implicitly known)
        data = data.replace(']','').replace('[','')
        values = data.split(',')
        if int(len(values) / 3) * 3 != len(values):
            # number of values must be a multiple of three (frequency, real, imaginary)
            raise Exception("Invalid input data: expected tuples of three values each")
        for i in range(0, len(values), 3):
            freq = float(values[i])
            real = float(values[i+1])
            imag = float(values[i+2])
            ret.append((freq, complex(real, imag)))
        return ret
    
    @staticmethod
    def parse_SA_trace_data(data):
        ret = []
        # Remove brackets (order of data implicitly known)
        data = data.replace(']','').replace('[','')
        values = data.split(',')
        if int(len(values) / 2) * 2 != len(values):
            # number of values must be a multiple of two (frequency, dBm)
            raise Exception("Invalid input data: expected tuples of two values each")
        for i in range(0, len(values), 2):
            freq = float(values[i])
            dBm = float(values[i+1])
            ret.append((freq, dBm))
        return ret

    #####################################################################################
    #####################################################################################
    #####################################################################################
    #####################################################################################
    #####################################################################################
    #####################################################################################
    #####################################################################################
    #####################################################################################
    #####################################################################################


    def get_id(self):
       return self.query("*IDN?")
    
    def get_opc(self):
        return self.query("*OPC?")
    
    
    def get_list(self):
        txt = self.query("*LST?")
        while(1):
            if txt!="ERROR":
                print(txt)
            else:
                break   
            txt = self.__read_response()
            if txt==self.cmd0:
                break 

    #####################################################################################
    #####################################################################################
    #                                DEVICE COMMANDS
    #####################################################################################
    #####################################################################################
    def get_devices(self):
        try:
            txt = self.query(":DEV:LIST?")
            while(1):
                if txt!="ERROR":
                    print(txt)
                else:
                    break   
                txt = self.__read_response()
        except:
            print("No more devices detected")

    def connect(self, dev=""):
        cmd = ":DEV:CONN "+ dev
        self.cmd(cmd)
        time.sleep(0.2)
        dev = self.query(":DEV:CONN?")
        if dev == "Not connected":
            print("Not connected to any device, aborting")
            exit(-1)
        else:
            print("Connected to "+dev)
    
    def disconnect(self):
        cmd = ":DEV:DISC "
        self.cmd(cmd)


    def set_mode(self,mode):
        mod = None
        modes={ "VNA":"Vector Network Analyzer", "GEN":"Signal Generator", "SA":"Spectrum Analyzer"}
        if mode in ["vna", "VNA"]:
            mod = "VNA"
        elif mode in ["sg", "SG", "GEN"]:
            mod = "GEN"
        elif mode in ["sa", "SA"]:
            mod = "SA"
        else:
            print("No valid mode selected")
            return 0

        cmd = ":DEV:MODE "+ mod
        self.cmd(cmd)
        time.sleep(0.2)
        ans = self.query(":DEV:MODE?")
        if ans != mod:
            print("Failed to set mode")
            return 0
        else:
            print("Device mode: "+modes[ans])
            return 1
        
    def get_mode(self):
        return self.query(":DEV:MODE?")

    def save_setup(self, path, filename="GuiConfig"):
        if not exists(path):
            print("Path {} doesn't exist".format(path))
            return 0
        fullpath = path+"/"+filename
        cmd = ":DEV:SETUP:SAVE "+fullpath
        self.cmd(cmd)
        time.sleep(0.2)
        return 1
    
    def load_setup(self, file):
        if not exists(file):
            print("Setup file {} doesn't exist".format(file))
            return 0
        return self.query(":DEV:SETUP:LOAD? "+file)


    def set_refOutFreq(self, freq):
        cmd = ":DEV:REF:OUT  "+ str(freq)
        self.cmd(cmd)
        time.sleep(0.2)
        ans = self.query(":DEV:REF:OUT?")
        if float(ans) != freq:
            print("Failed to set output reference")
            return 0
        else:
            print("Reference output frequency: {} MHz".format(ans))
            return 1
        
    def get_refOutFreq(self):
        return self.query(":DEV:REF:OUT?")
    

    def set_refIn(self, ref="INT"):
        if ref not in ["INT", "EXT", "AUTO"]:
            return False
        cmd = ":DEV:REF:IN  "+ ref
        self.cmd(cmd)
        time.sleep(0.2)
        ans = self.query(":DEV:REF:IN?")
        if ans not in ["INT", "EXT", "AUTO"]:
            print("Failed to set input reference")
            return 0
        else:
            print("Reference input set to : {} ".format(ans))
            return 1
        
    def get_refIn(self):
        return self.query(":DEV:REF:IN?")


    def get_pllStatus(self):
        return self.query(":DEV:STA:UNLO?")


    def get_adcStatus(self):
        return self.query(":DEV:STA:ADCOVER?")
    

    def get_lvlStatus(self):
        return self.query(":DEV:STA:UNLEV?")
    

    def get_sourceTemp(self):
        t = self.query(":DEV:INF:TEMP?")
        temps = t.split("/")
        return float(temps[0])

    def get_loTemp(self):
        t = self.query(":DEV:INF:TEMP?")
        temps = t.split("/")
        return float(temps[1])
    
    def get_cpuTemp(self):
        t = self.query(":DEV:INF:TEMP?")
        temps = t.split("/")
        return float(temps[2])


    def get_fullInfo(self):
        print("Libre VNA")
        print("---------------------------------------------------------------")
        print("Firmware             :",self.query(":DEV:INF:FWREV?") )
        time.sleep(0.2)
        print("Revision             : ",self.query(":DEV:INF:HWREV?") )
        time.sleep(0.2)   
        t = self.query(":DEV:INF:TEMP?")
        temps = t.split("/")
        print("Source Temperature   : {} °C".format(temps[0]) )
        print("LO Temperature       : {} °C".format(temps[1]) )
        print("CPU Temperature      : {} °C".format(temps[2]) )
        
        mn = self.query(":DEV:INF:LIM:MINF?")
        time.sleep(0.2)
        mx = self.query(":DEV:INF:LIM:MAXF?")
        print("Minimum measurable frequency     : {:.3f} KHz".format(float(mn)/1000) )
        print("Minimum measurable frequency     : {:.3f} GHz".format(float(mx)/1000000))

        print("Maximum number of trace points   :", self.query(":DEV:INF:LIM:MAXP?") )
        time.sleep(0.2)
        mn =  self.query(":DEV:INF:LIM:MINPOW?")
        time.sleep(0.2)
        mx = self.query(":DEV:INF:LIM:MAXPOW?")
        print("Output power range               : {} to {} dmB".format( mn,mx ) )

        mn =  self.query(":DEV:INF:LIM:MINRBW?")
        time.sleep(0.2)
        mx = self.query(":DEV:INF:LIM:MAXRBW?")
        print("Resolution bandwidth range       : {:.2f} Hz to {:.2f} kHz".format( float(mn),float(mx)/1000 ) )

        print("Maximum harmonic                 : {:.2f} MHz".format(float(self.query(":DEV:INF:LIM:MAXHARM?"))/1000000 ))

    #####################################################################################
    #####################################################################################
    #                                VNA COMMANDS
    #####################################################################################
    #####################################################################################

    #in progress...

    #####################################################################################
    #####################################################################################
    #                                SA COMMANDS
    #####################################################################################
    #####################################################################################

    

    def set_saSpan(self, span):
        '''
        Span frequency in MHz
        '''
        span *= 1000000
        cmd = ":SA:FREQ:SPAN "+ str(span)
        self.cmd(cmd)
        time.sleep(0.2)
        ans = self.query(":SA:FREQ:SPAN?")
        if float(ans) != span:
            print("Failed to set span")
            return 0
        else:
            print("Span frequency set to: {:.3f} MHz".format(span/1000000))
            return 1
        
    def get_saSpan(self):
        return self.query(":SA:FREQ:SPAN?")



    def set_saStart(self, freq):
        '''
        Span frequency in MHz
        '''
        freq *= 1000000
        cmd = ":SA:FREQ:START "+ str(int(freq))
        #print(cmd)
        self.cmd(cmd)
        time.sleep(0.2)
        ans = self.query(":SA:FREQ:START?")
        if float(ans) != freq:
            print("Failed to set start frequency")
            return 0
        else:
            print("Start frequency set to: {:.3f} MHz".format(freq/1000000))
            return 1
        
    def get_saStart(self):
        return self.query(":SA:FREQ:START?")
    

    def set_saCenter(self, freq):
        '''
        Span frequency in MHz
        '''
        freq *= 1000000
        cmd = ":SA:FREQ:CENT "+ str(freq)
        self.cmd(cmd)
        time.sleep(0.2)
        ans = self.query(":SA:FREQ:CENT?")
        if float(ans) != freq:
            print("Failed to set center frequency")
            return 0
        else:
            print("Center frequency set to: {:.3f} MHz".format(freq/1000000))
            return 1
        
    def get_saCenter(self):
        return self.query(":SA:FREQ:CENT?")

    
    def set_saStop(self, freq):
        '''
        Span frequency in MHz
        '''
        freq *= 1000000
        cmd = ":SA:FREQ:STOP "+ str(freq)
        self.cmd(cmd)
        time.sleep(0.2)
        ans = self.query(":SA:FREQ:STOP?")
        if float(ans) != freq:
            print("Failed to set stop frequency")
            return 0
        else:
            print("Stop frequency set to: {:.3f} MHz".format(freq/1000000))
            return 1
        
    def get_saStop(self):
        return self.query(":SA:FREQ:STOP?")


    def set_saFullRange(self):
        return self.query(":SA:FREQ:FULL")

    def set_saNullRange(self):
        return self.query(":SA:FREQ:ZERO")
        
    #####################################################################################
    #     

    def set_saRBW(self, freq):
        '''
        RBW in KHz
        '''
        freq *= 1000
        cmd = ":SA:ACQ:RBW "+ str(freq)
        self.cmd(cmd)
        time.sleep(0.2)
        ans = self.query(":SA:ACQ:RBW?")
        if float(ans) != freq:
            print("Failed to set resolution bandwidth")
            return 0
        else:
            print("Resolution bandwidth set to: {:.3f} KHz".format(freq/1000))
            return 1
        
    def get_saRBW(self):
        return self.query(":SA:ACQ:RBW?")


    def set_saWindow(self,window=None):
        w = None
  
        if window in ["KAISER", "kaiser"]:
            w = "KAISER"
        elif window in ["HANN", "hann", "hanning", "HANNING"]:
            w = "HANN"
        elif window in ["FLATTOP", "flattop", "flatTop"]:
            w = "FLATTOP"
        else:
            w="NONE"
        
        cmd = ":SA:ACQ:WIND "+ w
        self.cmd(cmd)
        time.sleep(0.2)
        ans = self.query(":SA:ACQ:WIND?")
        if ans != w:
            print("Failed to set window")
            return 0
        else:
            print("Window set to: "+ans)
            return 1
        
    def get_saWindow(self):
        return self.query(":SA:ACQ:WIND?")


    def set_saDetector(self,detector=None):
        d = None
  
        if detector in ["+PEAK", "+peak", "PEAK+", "peak+"]:
            d = "+PEAK"
        elif detector in ["-PEAK", "-peak", "PEAK-", "peak-"]:
            d = "-PEAK"
        elif detector in ["NORMAL", "normal"]:
            d = "NORMAL"
        elif detector in ["SAMPLE", "sample"]:
            d = "SAMPLE"
        elif detector in ["AVERAGE", "average", "AVG", "avg"]:
            d = "AVERAGE"
        else:
            d="NORMAL"
        
        cmd = ":SA:ACQ:DET "+ d
        self.cmd(cmd)
        time.sleep(0.2)
        ans = self.query(":SA:ACQ:DET?")
        if ans != d:
            print("Failed to set detector type")
            return 0
        else:
            print("Detector set to: "+ans)
            return 1
        
    def get_saDetector(self):
        return self.query(":SA:ACQ:DET?")


    def set_saAvgNumber(self,avg=1, msg=True):
        cmd = ":SA:ACQ:AVG "+ str(int(avg))
        self.cmd(cmd)
        time.sleep(0.2)
        ans = self.query(":SA:ACQ:AVG?")
        if float(ans) != avg:
            if msg:
                print("Failed to set the average number")
            return 0
        else:
            if msg:
                print("Average trace set to: {:.1f} ".format(avg))
            return 1
        
    def get_saAvgNumber(self):
        return self.query(":SA:ACQ:AVG?")


    def get_saCurrentAvg(self):
        return int(self.query(":SA:ACQ:AVGLEV?"))


    def is_saAvgDone(self):
        return bool(self.query(":SA:ACQ:FIN?"))


    def is_saLimit(self):
        ans = self.query(":SA:ACQ:LIM?")
        if ans=="PASS":
            return True 
        elif ans=="FAIL":
            return False


    def set_saSingleSweep(self, st=True):
        value=None
        if st:
            value="TRUE" 
        else:
            value="FALSE"
        return self.query(":SA:ACQ:SINGLE "+value)

    def get_saSingleSweep(self):
        return bool(self.query(":SA:ACQ:SINGLE?"))


    def set_saSignalID(self, st=True):
        value=None
        if st:
            value="TRUE" 
        else:
            value="FALSE"
        return self.query(":SA:ACQ:SIG "+value)

    def get_saSignalID(self):
        return bool(self.query(":SA:ACQ:SIG?"))

    #####################################################################################


    def set_saTracking(self, st=True):
        value=None
        if st:
            value="TRUE" 
        else:
            value="FALSE"
        return self.query(":SA:TRACK:EN "+value)

    def get_saTracking(self):
        return bool(self.query(":SA:TRACK:EN?"))


    def set_saTrackingPort(self, port=1):
        if port>2 or port <1:
            print("Invalid port number")
            return False
        return self.query(":SA:TRACK:PORT "+str(port))

    def get_saTrackingPort(self):
        return int(self.query(":SA:TRACK:PORT?"))


    def set_saTrackingLevel(self, level=-10):
        if level>0 or level <-40:
            print("Invalid output level <-40, 0> dBm")
            return False
        return self.query(":SA:TRACK:LVL "+level)

    def get_saTrackingLevel(self):
        return int(self.query(":SA:TRACK:LVL?"))


    def set_saTrackingOff(self, off=0):
        return self.query(":SA:TRACK:OFF "+off)

    def get_saTrackingOff(self):
        return int(self.query(":SA:TRACK:OFF?"))


    def set_saTrackingNorm(self, st=True):
        value=None
        if st:
            value="TRUE" 
        else:
            value="FALSE"
        return self.query(":SA:TRACK:NORM:EN "+value)

    def get_saTrackingNorm(self):
        return bool(self.query(":SA:TRACK:NORM:EN?"))


    def set_saTrackingNorm(self): #Measure
        return int(self.query(":SA:TRACK:NORM:MEAS"))

    
    def set_saTrackingRef(self, ref=-10):
        if ref>0 or ref <-40:
            print("Invalid normalization reference level <-40, 0> dBm")
            return False
        return self.query(":SA:TRACK:NORM:LVL "+str(ref))

    def get_saTrackingRef(self):
        return int(self.query(":SA:TRACK:NORM:LVL?"))

    #####################################################################################


    def get_saTraces(self):
        t = self.query(":SA:TRAC:LIST?")
        return t.split(",")


    def get_saData(self, port=1):
        "alternative to use: parse_SA_trace_data()"
        #return freq, dmb
        val = None
        if port == 1:
            val = "PORT1"
        elif port == 2:
            val = "PORT2"
        else:
            print("Invalid port selected  <1 , 2>")
            return False
        data = self.query(":SA:TRAC:DATA? "+val)
        data = data.replace("[", "").replace("]", "")
        b = data.split(",")
        c = []
        for i in range(len(b)//2):
            c.append([float(b[i*2]), float(b[i*2 +1])])
        return asarray(c).T

    def get_saPower(self,trace, freq): #in KHz
        freq *=1000
        return self.query(":SA:TRAC:AT? "+trace+ " "+str(freq))

    """ 
    The following functions can be obtain from the previous one
    SA:TRACe:MAXFrequency
    SA:TRACe:MINFrequency
    SA:TRACe:MAXAmplitude
    SA:TRACe:MINAmplitude
    """
    
    def set_saTrace(self, name="NEW TRACE", type="MAXHOLD", port=1):
        t = self.query(":VNA:TRAC:LIST?")
        return t.split(",")


    def set_saTraceName(self, name="0", rename="MAXHOLD"):
        if  isinstance(name, int):
            name = str(name)
        return self.query(":SA:TRAC:RENAME "+name +" "+rename)

    def set_saTracePause(self, trace):
        if  isinstance(trace, int):
            trace = str(trace)
        return self.query(":SA:TRAC:PAUSE "+trace)
    
    def set_saTraceResume(self, trace):
        if  isinstance(trace, int):
            trace = str(trace)
        return self.query(":SA:TRAC:RESUME "+trace)

    def is_tracePaused(self, trace):
        if isinstance(trace, int):
            trace = str(trace)
        return bool(self.query(":SA:TRAC:PAUSED? "+trace))


    def set_saTracePort(self, name, port=1):
        if port>2 or port <1:
            print("Invalid port number")
            return False
        return self.query(":SA:TRAC:PARAM "+name, +" "+str(port))

    def get_saTracePort(self, name):
        if  isinstance(name,int):
                name = str(name)
        return self.query(":SA:TRAC:PARAM? "+name)


    def set_saTraceType(self, name, traceType="MAXHOLD"):
        if  isinstance(name,int):
                name = str(name)
        if traceType not in ["OVERWRITE", "MAXHOLD" , "MINHOLD"]:
            print("Invalid type selected <OVERWRITE, MAXHOLD,MINHOLD>")
            return False
        return self.query(":SA:TRAC:TYPE "+name, +" "+traceType)

    def get_saTraceType(self, name):
        if  isinstance(name,int):
                name = str(name)
        return self.query(":SA:TRAC:TYPE? "+name)
























