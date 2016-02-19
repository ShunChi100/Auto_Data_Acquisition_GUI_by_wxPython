import visa
import time
import numpy as np
import wx

from threading import Thread
from wx.lib.pubsub import setuparg1
from wx.lib.pubsub import pub as Publisher

import GlobalFlag

class sr850ltc21(Thread):
    def __init__(self,filename,trange,SR850scanlength,SR850SinRMS,CurrentResistance,GainRatio,dT,dTfluc,description,WaitTimeForT):
        Thread.__init__(self)
        wx.CallAfter(Publisher.sendMessage, "update", msg = "S") ## "S" means "Setting up SR850 and LTC21"

        ## Initialize input parameters
        self.CurrentResistance = CurrentResistance
        self.SR850SinRMS = SR850SinRMS
        self.GainRatio = GainRatio
        self.SR850Current = SR850SinRMS/CurrentResistance*self.GainRatio
        self.SR850scanlength = SR850scanlength
        self.trange = trange
        self.dT = dT
        self.dTfluc = dTfluc
        self.WaitTimeForT = WaitTimeForT
        ## Get GPIB connection
        rm  = visa.ResourceManager()
        self.ltc21 = rm.open_resource('GPIB0::10::INSTR')
        self.ltc21.timeout = 60000
        self.sr850 = rm.open_resource('GPIB0::12::INSTR')
        self.sr850.timeout = 60000
        
        ## open data file and write file header
        self.file = open(filename, "a",0)
        self.file.write("##")
        self.file.write(time.ctime())
        self.file.write("\n")
        self.file.write("##")
        self.file.write("User Description: %s" % description)
        self.file.write("\n")
        self.file.write("##")
        self.file.write(self.sr850.query("*IDN?\n;"))
        self.file.write("##")
        self.file.write(self.ltc21.query("*IDN?\n;"))
        self.file.write("##")
        self.file.write("SR850 scan length is %.1f\n" % SR850scanlength)
        self.file.write("##")
        self.file.write("SR850 Sine RMS is %.3fV\n" % SR850SinRMS)
        self.file.write("##")
        self.file.write("Current Source Resistance is %.5f\n" % CurrentResistance)
        self.file.write("##")
        self.file.write("T_Stable flags: 0--Unstable, 1--Stable, 2--Measurement Stopped\n")  
        self.file.write("##")
        self.file.write("Time(s),\t T_in(K),\t R_s(ohm),\t Rstd_s(ohm),\t Tstd_in(K),\t T_out(K),\t Tstd_out(K),\t SR850_V(V),\t Temperature_Set(K),\t T_Stable?\n")
        

        ## Setting SR850 and LTC21
        ## set autoGain for the measurement
        #self.sr850.write("AGAN\n;")
        #time.sleep(10)
        ## set 1 (= top display) to be 3 (Chart)
        self.sr850.write("DTYP1,3\n;")
        time.sleep(0.5)
        
        ## set Chart scan length to be 10 sec and the scan rate to be 64Hz
        self.sr850.write("SLEN%.0f;SRAT10\n;" % SR850scanlength)
        self.sr850.write("SLVL%.3f" % SR850SinRMS)
        
        ## set the initial SET point to be 0.5K lower than the base T reading. Somehow, the command need \n;        
        Tinit = self.ltc21.query("QSAMP?1;")
        Tinit = float(Tinit[0:-3])

        self.ltc21.write("SETP1,%.3f\n;" % (Tinit-0.5))
        self.ltc21.write("SCONT\n;")
            
        ## Initialize stable-T-mean and stable-T-std values to be off from the real readings, so it will run the first loop (10s) for checking stable temperature
        self.tstablemean = 0
        self.tstablestd = 1
        
        GlobalFlag.init()
        
        self.start()
        
        
    ## acquire data   
    def run(self):
        if GlobalFlag.stopFlag == False:
            #print "pass right at the beginning"
            pass
        elif self.trange.size == 0:
            if GlobalFlag.stopFlag == False:
                #print "trange.size = 0"
                pass 
            else:
                ## set ltc21 to MONitor mode
                self.ltc21.write("SMON\n;") 
                for ii in range(0,10000):
                    if GlobalFlag.stopFlag == False:
                        #print("break Cooling scan")
                        break
                
                    time.sleep(self.WaitTimeForT)
                    #################################################
                    #########SR850 measureing unit###################
                    ## reset trace and start scan
                    self.sr850.write("REST;STRT\n;")
                    
                    tstable1 = np.zeros(100) 
                    tstable2 = np.zeros(100) 
                    ## get average T from ltc21
                    wx.CallAfter(Publisher.sendMessage, "update", msg = "M") ## "M" means "Measuring R and T"
                    T_read_flag1 = 1.0
                    T_read_flag2 = 1.0
                    ## During SR850 scan, keep query Temperature data from LTC21 and then average them 
                    for ii in range(0,100):
                        tmp1 = self.ltc21.query("QSAMP?1\n;")
                        #See if LTC21 display a value or "......", if the later, tstable1[ii] = -1.0, T_read_flag1 = 0.0
                        if tmp1[0] != ".":
                            tstable1[ii] = float(tmp1[0:-3])
                        else:
                            tstable1[ii] = -1.0
                            T_read_flag1 = 0.0 
                        tmp2 = self.ltc21.query("QSAMP?2\n;")
                        if tmp2[0] != ".":
                            tstable2[ii] = float(tmp2[0:-3])
                        else:
                            tstable2[ii] = -1.0
                            T_read_flag2 = 0.0
                        time.sleep(self.SR850scanlength/105)    
                                
                    ## See if LTC21 display a value or "......", if the later, tstd and tmean are set to be -1
                    if T_read_flag1 == 1.0: 
                        tstd1 = np.std(tstable1)
                        tmean1 = np.mean(tstable1) 
                    elif T_read_flag1 == 0.0:
                        tstd1 = -1.0
                        tmean1 = -1.0   
                        
                    if T_read_flag2 == 1.0: 
                        tstd2 = np.std(tstable2)
                        tmean2 = np.mean(tstable2) 
                    elif T_read_flag2 == 0.0:
                        tstd2 = -1.0
                        tmean2 = -1.0   
                    
                    self.sr850.write("ASCL\n;")
                    ## Statistically analyze the data within i = 0(%) and j = 100(%) from the left edge.
                    self.sr850.write("STAT0,100\n;")
                    time.sleep(1.5)
                    #print(time.time(), time.clock())  
                    ## Query the Statistical results mean (0), standard dev (1), total (2) or delta time (3).
                    V = float(self.sr850.query("SPAR?0\n"))
                    Vstd = float(self.sr850.query("SPAR?1\n"))
                    R = V/self.SR850Current
                    Rstd = Vstd/self.SR850Current
                    #print(time.time(), time.clock())  
            
                    ## write data to file
                    tset = -1
                    T_stable_flag = -1
                    self.file.write("%.1f,\t %.3f,\t %.6e,\t %.6e,\t %.3f,\t %.3f,\t %.3f,\t %.6e,\t %.3f,\t %.0f\n" % (time.clock(), tmean2, R, Rstd, tstd2, tmean1, tstd1, V, tset,T_stable_flag))
        else:

            for tset in self.trange:
                
                #print(GlobalFlag.stopFlag)
                if GlobalFlag.stopFlag == False:
                    break
                
                ltcStatus = self.ltc21.query("QISTATE?\n;")
                if ltcStatus == "1":
                    pass
                else: 
                    ## set ltc21 in control mode                
                    self.ltc21.write("SCONT\n;")    
                    
                    
                ## set Temperature
                self.ltc21.write("SETP1,%.3f\n;" %tset)
                time.sleep(self.WaitTimeForT)
                
                tstabletest1 = np.zeros(100)
                tstabletest2 = np.zeros(100)
                tstable1 = np.zeros(100) 
                tstable2 = np.zeros(100) 
                
                ## collect T data for 10s and see if it is stable  
                counttime = 0
                while abs(self.tstablemean-tset) > self.dT or self.tstablestd > self.dTfluc :
                    wx.CallAfter(Publisher.sendMessage, "update", msg = "A") ## "A" means "Attempting to stablize T"               
                    for ii in range(0,100):
                        tmp1 = self.ltc21.query("QSAMP?1\n;")
                        tmp2 = self.ltc21.query("QSAMP?2\n;")
                        tstabletest1[ii] = float(tmp1[0:-3])
                        tstabletest2[ii] = float(tmp2[0:-3])
                        time.sleep(0.08)
                    self.tstablestd = np.std(tstabletest2)
                    self.tstablemean = np.mean(tstabletest1)
                    counttime += 1
                    if counttime > 120:
                        T_stable_flag = 0
                        break
                    if GlobalFlag.stopFlag == False:
                        T_stable_flag = 2
                        break
                else:
                    T_stable_flag = 1 
                    
                    
                if GlobalFlag.stopFlag == False:
                    pass 
                else:
                    #################################################
                    #########SR850 measureing unit###################
                    ## reset trace and start scan
                    self.sr850.write("REST;STRT\n;")
                    
                    ## get average T from ltc21
                    wx.CallAfter(Publisher.sendMessage, "update", msg = "M") ## "M" means "Measuring R and T"
                    T_read_flag1 = 1.0
                    T_read_flag2 = 1.0
                    ## During SR850 scan, keep query Temperature data from LTC21 and then average them 
                    for ii in range(0,100):
                        tmp1 = self.ltc21.query("QSAMP?1\n;")
                        #See if LTC21 display a value or "......", if the later, tstable1[ii] = -1.0, T_read_flag1 = 0.0
                        if tmp1[0] != ".":
                            tstable1[ii] = float(tmp1[0:-3])
                        else:
                            tstable1[ii] = -1.0
                            T_read_flag1 = 0.0 
                        tmp2 = self.ltc21.query("QSAMP?2\n;")
                        if tmp2[0] != ".":
                            tstable2[ii] = float(tmp2[0:-3])
                        else:
                            tstable2[ii] = -1.0
                            T_read_flag2 = 0.0
                        time.sleep(self.SR850scanlength/105)    
                                
                    ## See if LTC21 display a value or "......", if the later, tstd and tmean are set to be -1
                    if T_read_flag1 == 1.0: 
                        tstd1 = np.std(tstable1)
                        tmean1 = np.mean(tstable1) 
                    elif T_read_flag1 == 0.0:
                        tstd1 = -1.0
                        tmean1 = -1.0   
                        
                    if T_read_flag2 == 1.0: 
                        tstd2 = np.std(tstable2)
                        tmean2 = np.mean(tstable2) 
                    elif T_read_flag2 == 0.0:
                        tstd2 = -1.0
                        tmean2 = -1.0   
                    
                    self.sr850.write("ASCL\n;")
                    ## Statistically analyze the data within i = 0(%) and j = 100(%) from the left edge.
                    self.sr850.write("STAT0,100\n;")
                    time.sleep(1.5)
                    #print(time.time(), time.clock())  
                    ## Query the Statistical results mean (0), standard dev (1), total (2) or delta time (3).
                    V = float(self.sr850.query("SPAR?0\n"))
                    Vstd = float(self.sr850.query("SPAR?1\n"))
                    R = V/self.SR850Current
                    Rstd = Vstd/self.SR850Current
                    #print(time.time(), time.clock())  
            
                    ## write data to file
                    self.file.write("%.1f,\t %.3f,\t %.6e,\t %.6e,\t %.3f,\t %.3f,\t %.3f,\t %.6e,\t %.3f,\t %.0f\n" % (time.clock(), tmean2, R, Rstd, tstd2, tmean1, tstd1, V, tset,T_stable_flag))

            ## write a data end indicator
            self.file.write("######\n")
                 
        
        ## set ltc21 to MONitor mode
        self.ltc21.write("SMON\n;") 
        time.sleep(1)
        
        ## close the data file
        self.file.close()
        time.sleep(1) 
        
        ## close the instruments
        self.sr850.close()
        self.ltc21.close()
        time.sleep(1) 
        ## Send message for finishing
        wx.CallAfter(Publisher.sendMessage, "update", msg = "Measurement finished!")   


        