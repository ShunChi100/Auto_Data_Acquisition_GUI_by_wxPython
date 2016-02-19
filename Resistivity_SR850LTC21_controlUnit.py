#!/usr/bin/env python
"""
This module creates a GUI interface for real time data acqusition and visualization.
Data acqusitioin instruments used here are LTC-21 temperature controller na dSR850 DSP Lock-in amplifier.
Any other GPIB controlled instruments can be added in this module.

Developed by Shun Chi, Feb-11-2016

"""

import wx  ## wxpython
from wx.lib.pubsub import pub as Publisher  ## for threading update status
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation    ## for realtime data plot
from matplotlib import style     ## for nice graph

## Module that control the SR850 and LTC21 and taking data
import SR850LTC21_measure as MEAsure
## Module for a global stop measurement flag
import GlobalFlag

# Create a Gui frame, derived from the wxPython Frame.
class MyFrame(wx.Frame):
    
    def __init__(self, parent, id, title):
        # First, call the base class' __init__ method to create the frame
        wx.Frame.__init__(self, parent, id, title, size=(500,600))

        # Add a panel
        panel = wx.Panel(self)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        
        # Add a directory selection button
        bottonDic=wx.Button(panel,label="Directory",pos=(10,10),size=(60,30))
        self.Bind(wx.EVT_BUTTON,self.directorybutton, bottonDic)
        # Text box for showing the directory
        self.txtDic = wx.TextCtrl(panel, -1, pos=(75,10),size=(400,30))
        self.txtDic.SetValue('C:\Users\Supercon\Desktop\Dropbox\FeSe_Projects\Dip_Probe\GPIB_communication\data')
        # disable the textbox, so no one can edit it
        self.txtDic.Disable()        
        
        # Add a filename Button, taking the data file name from user
        bottonFil=wx.Button(panel,label="FileName",pos=(10,40),size=(60,30))
        self.Bind(wx.EVT_BUTTON,self.filenamebutton, bottonFil)
        # Text box for showing the filename
        self.txtFil = wx.TextCtrl(panel, -1, pos=(75,40),size=(400,30))
        self.txtFil.SetValue('temp.txt')
        # disable the textbox, so no one can edit it
        self.txtDic.Disable() 
        
  
        # Add a plot realtime data button
        bottonPlot=wx.Button(panel,label="Plot Live",pos=(10,70),size=(80,30))
        self.Bind(wx.EVT_BUTTON, self.plotbutton, bottonPlot)
        # Add a plot static/previous data button
        bottonPlotStatic=wx.Button(panel,label="Plot Static Data",pos=(90,70),size=(100,30))
        self.Bind(wx.EVT_BUTTON, self.plotbuttonstatic, bottonPlotStatic)
        
        self.XplotLabel = wx.StaticText(panel, -1, "X:",pos=(200,70),size=(20,30))
        self.plotdict = {u"Time":0, u"T_in": 1 , u"R":2, u"Rstd":3, u"Tin_std":4, u"T_out":5, u"Tout_std":6, u"V_SR850":7, u"T_set":8,u"T_stable":9}
        self.XplotChoices =  [u"T_in", u"T_out", u"Time", u"T_stable"]       
        self.Xplot = wx.Choice(panel,pos=(221,70),size=(100,30),choices=self.XplotChoices)
        self.Xplot.SetSelection( 0 )
        #self.choice.Bind(wx.EVT_CHOICE, self.onChoice)
        self.XplotLabel = wx.StaticText(panel, -1, "Y:",pos=(330,70),size=(20,30))
        self.YplotChoices = [u"Time", u"T_in", u"R", u"Rstd", u"Tin_std", u"T_out", u"Tout_std", u"V_SR850", u"T_set",u"T_stable"]        
        self.Yplot = wx.Choice(panel,pos=(351,70),size=(100,30),choices = self.YplotChoices)
        self.Yplot.SetSelection( 2 )

        
        
        ######################################
        # Temperature start, end, interval input, five of them, so one can choose five different T range
        self.tStart = wx.StaticText(panel, -1, "T1 Start(K):",pos=(10,100),size=(60,30))
        self.tStartval = wx.TextCtrl(panel, -1, "4.2",pos=(75,100),size=(60, 20))
        self.tStartval.SetInsertionPoint(0)
        self.tEnd = wx.StaticText(panel, -1, "T End(K):",pos=(160,100),size=(60,30))
        self.tEndval = wx.TextCtrl(panel, -1, "30",pos=(225,100),size=(60, 20))
        self.tEndval.SetInsertionPoint(0)
        self.tDividen = wx.StaticText(panel, -1, "Dividen:",pos=(300,100),size=(60,30))
        self.tDividenval = wx.TextCtrl(panel, -1, "0.2",pos=(365,100),size=(40, 20))
        self.tDividenval.SetInsertionPoint(0)
        
        
        self.tStart2 = wx.StaticText(panel, -1, "T2 Start(K):",pos=(10,130),size=(60,30))
        self.tStartval2 = wx.TextCtrl(panel, -1, "N",pos=(75,130),size=(60, 20))
        self.tStartval2.SetInsertionPoint(0)
        self.tEnd2 = wx.StaticText(panel, -1, "T End(K):",pos=(160,130),size=(60,30))
        self.tEndval2 = wx.TextCtrl(panel, -1, "N",pos=(225,130),size=(60, 20))
        self.tEndval2.SetInsertionPoint(0)
        self.tDividen2 = wx.StaticText(panel, -1, "Dividen:",pos=(300,130),size=(60,30))
        self.tDividenval2 = wx.TextCtrl(panel, -1, "N",pos=(365,130),size=(40, 20))
        self.tDividenval2.SetInsertionPoint(0)
        
        
        self.tStart3 = wx.StaticText(panel, -1, "T3 Start(K):",pos=(10,160),size=(60,30))
        self.tStartval3 = wx.TextCtrl(panel, -1, "N",pos=(75,160),size=(60, 20))
        self.tStartval3.SetInsertionPoint(0)
        self.tEnd3 = wx.StaticText(panel, -1, "T End(K):",pos=(160,160),size=(60,30))
        self.tEndval3 = wx.TextCtrl(panel, -1, "N",pos=(225,160),size=(60, 20))
        self.tEndval3.SetInsertionPoint(0)
        self.tDividen3 = wx.StaticText(panel, -1, "Dividen:",pos=(300,160),size=(60,30))
        self.tDividenval3 = wx.TextCtrl(panel, -1, "N",pos=(365,160),size=(40, 20))
        self.tDividenval3.SetInsertionPoint(0)        
        
        
        self.tStart4 = wx.StaticText(panel, -1, "T4 Start(K):",pos=(10,190),size=(60,30))
        self.tStartval4 = wx.TextCtrl(panel, -1, "N",pos=(75,190),size=(60, 20))
        self.tStartval4.SetInsertionPoint(0)
        self.tEnd4 = wx.StaticText(panel, -1, "T End(K):",pos=(160,190),size=(60,30))
        self.tEndval4 = wx.TextCtrl(panel, -1, "N",pos=(225,190),size=(60, 20))
        self.tEndval4.SetInsertionPoint(0)
        self.tDividen4 = wx.StaticText(panel, -1, "Dividen:",pos=(300,190),size=(60,30))
        self.tDividenval4 = wx.TextCtrl(panel, -1, "N",pos=(365,190),size=(40, 20))
        self.tDividenval4.SetInsertionPoint(0)  


        self.tStart5 = wx.StaticText(panel, -1, "T5 Start(K):",pos=(10,220),size=(60,20))
        self.tStartval5 = wx.TextCtrl(panel, -1, "N",pos=(75,220),size=(60, 20))
        self.tStartval5.SetInsertionPoint(0)
        self.tEnd5 = wx.StaticText(panel, -1, "T End(K):",pos=(160,220),size=(60,20))
        self.tEndval5 = wx.TextCtrl(panel, -1, "N",pos=(225,220),size=(60, 20))
        self.tEndval5.SetInsertionPoint(0)
        self.tDividen5 = wx.StaticText(panel, -1, "Dividen:",pos=(300,220),size=(60,20))
        self.tDividenval5 = wx.TextCtrl(panel, -1, "N",pos=(365,220),size=(40, 20))
        self.tDividenval5.SetInsertionPoint(0)  
        ####################################
        
        
        # Add a textbox for user description of the measurement
        self.description = wx.TextCtrl(panel, -1, "None",pos=(10,248),size=(460, 30))
        
        
        ####################################
        ## Start Measurement Button
        self.bottonMeasure=wx.Button(panel,label="Measure",pos=(10,280),size=(60,30))
        self.Bind(wx.EVT_BUTTON,self.measurebutton, self.bottonMeasure)
        
        ## Stop Measurement Button
        bottonStop=wx.Button(panel,label="STOP",pos=(80,280),size=(60,30))
        self.Bind(wx.EVT_BUTTON,self.stopbutton, bottonStop)   
        
        # Textbox for status update from SR850LTC21 threading
        self.statusMeasure = wx.StaticText(panel, -1, "Status:",pos=(145,280),size=(50,30))
        self.statusMeasureinput = wx.TextCtrl(panel, -1, "None",pos=(200,280),size=(270, 20))
        self.statusMeasureinput.SetBackgroundColour((230,230,230))
        self.statusMeasureinput.Disable()
        
        # create a pubsub receiver for receiving updates from SR850LTC21 threading
        Publisher.subscribe(self.updateDisplay, "update")        
        
        # initialize the global stop flag
        GlobalFlag.init()
        ####################################        

        
        ###########################################################
        # User input parameters for measurement: SR850scanlength,SR850SinRMS,CurrentResistance     
        self.sr850control1 = wx.StaticText(panel, -1, "SR850 Scanlength (s):",pos=(10,320),size=(160,30))
        self.sr850control1input = wx.TextCtrl(panel, -1, "10.0",pos=(175,320),size=(80, 20))
        
        self.sr850control2 = wx.StaticText(panel, -1, "SR850 Output RMS (V):",pos=(10,350),size=(160,30))
        self.sr850control2input = wx.TextCtrl(panel, -1, "1.0",pos=(175,350),size=(80, 20))
        self.Bind(wx.EVT_TEXT, self.updateCurrent, self.sr850control2input)
        
        self.sr850control3 = wx.StaticText(panel, -1, "R (kOhm) for Const. I:",pos=(10,380),size=(160,30))
        self.sr850control3input = wx.TextCtrl(panel, -1, "100.0",pos=(175,380),size=(80, 20))
        self.Bind(wx.EVT_TEXT, self.updateCurrent, self.sr850control3input)
        
        # Calculate running current
        Current = 1000.0*float(self.sr850control2input.GetValue())/float(self.sr850control3input.GetValue())
        self.sr850control4_2 = wx.StaticText(panel, -1, "I (uA):",pos=(10,410),size=(160,30))
        self.sr850control4output = wx.TextCtrl(panel, -1, "%.1f"%Current,pos=(175,410),size=(60,20))
        self.sr850control4output.Disable()        
        
        self.sr850control6 = wx.StaticText(panel, -1, "Transformer Amplifier:",pos=(10,440),size=(160,30))
        self.sr850control6input = wx.TextCtrl(panel, -1, "100.0",pos=(175,440),size=(80, 20))
        
        self.sr850control4 = wx.StaticText(panel, -1, "dT Allowrance (K) (No-Func):",pos=(10,470),size=(160,30))
        self.sr850control4input = wx.TextCtrl(panel, -1, "0.1",pos=(175,470),size=(80, 20))
        
        self.sr850control5 = wx.StaticText(panel, -1, "Max dT Fluctuation:",pos=(10,500),size=(160,30))
        self.sr850control5input = wx.TextCtrl(panel, -1, "0.1",pos=(175,500),size=(80, 20))
        
        self.sr850control7 = wx.StaticText(panel, -1, "Wait time for T stable (s):",pos=(10,530),size=(160,30))
        self.sr850control7input = wx.TextCtrl(panel, -1, "5",pos=(175,530),size=(80, 20))
        
        

        ##########################################################


    ######################################
    ## Bind function for directorybutton
    def directorybutton(self,event):
        ## Standard directory dialog
        # Args below are: parent, question, dialog title, default answer
        dd = wx.DirDialog(None, "Select directory to open", "~/", 0, (10, 10), wx.Size(400, 300))
 
        # This function returns the button pressed to close the dialog
        ret = dd.ShowModal()

        # Let's check if user clicked OK or pressed ENTER
        if ret == wx.ID_OK:
            print('You selected: %s\n' % dd.GetPath())
        else:
            print('You clicked cancel')
        
        ## Display directory in directory textbox  
        self.txtDic.SetValue(dd.GetPath())
        # The dialog is not in the screen anymore, but it's still in memory
        #for you to access it's values. remove it from there.
        dd.Destroy()
        return True
    
    #######################################    
    def filenamebutton(self,event):
        ## Standard text entry dialog
        # create a text entry dialog
        filenameinit = self.txtFil.GetValue()
        box = wx.TextEntryDialog(None,"Data File Name","Enter File Name",filenameinit)
        if box.ShowModal() == wx.ID_OK:
            filename = box.GetValue()
            print('You filename: %s\n' % filename)
            
        ## Display filename entered by user
        self.txtFil.SetValue(box.GetValue())
        
    
    ##################################################        
    def OnCloseWindow(self, event):
        ## Standard closing GUI
        self.Destroy()
        
        
    ###################################################
    def plotbuttonstatic(self, event):
        ## use ggplot style from matplotlib styles
        style.use('ggplot')
        fig = plt.figure()
        ax1 = fig.add_subplot(1,1,1)
        ## Set the title of the figure window 
        fig.canvas.set_window_title('Static Data Plot')
        ## Standard open file dialog from wxpython
        openFileDialog = wx.FileDialog(self, "Open XYZ file", "", "",
                                       "XYZ files (*.txt)|*.txt", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if openFileDialog.ShowModal() == wx.ID_CANCEL:
            return     # the user changed idea...

        ## get the filename and directory: filedic = filedirectory + filename 
        filedic = openFileDialog.GetPath()
 
        ## Open data file and Read data
        """
         In order to distinguish data taken from different times but saved in 
         the same file, I used a separator '######' at the end of the data after each measurement.
         Data are also plot in different color.
        """
        #filedic = "C:\Users\User\Dropbox\FeSe_Projects\Dip_Probe\GPIB_communication\data\\temp3.txt"
        fid = open(filedic,'r')
        graph_data = fid.read()
        lines = graph_data.split('\n')
        headerNo = 0;
        ## Initialize data reading in 2D-list, get the X-axis and Y-axis input from users
        xs = self.plotdict[self.XplotChoices[self.Xplot.GetCurrentSelection()]]
        ys = self.plotdict[self.YplotChoices[self.Yplot.GetCurrentSelection()]]
        dataread = [[],[],[],[],[],[],[],[],[],[]]
        ## Read and Plot data
        for line in lines:
            if line[0:6] == "######":
                headerNo = headerNo + 1
                ## Plot with different color
                if headerNo <= 6:
                    ax1.plot(dataread[xs], dataread[ys],'--o', lw = 1, ms = 5, mew =0, mfc = [0, 0, 0.2* (headerNo-1)], c = [0.5, 0.5, 0.1* (headerNo-1)+0.5])
                elif headerNo > 6 and headerNo <10:
                    ax1.plot(dataread[xs], dataread[ys],'--o', lw = 1, ms = 5, mew =0, mfc = [0.2*(headerNo-6), 0, 1-0.2* (headerNo-6)], c = [0.1*(headerNo-6)+0.5, 0.5, 1-0.1* (headerNo-6)])
                else:
                    ax1.plot(dataread[xs],dataread[ys],'--*', lw = 1, ms = 5, mew =0, mfc = [0,0,0], c = [0.5,0.5,0.5])
                dataread = [[],[],[],[],[],[],[],[],[],[]]

            if len(line) > 1 and line[0:2] != "##":
                Time,T_in,R,Rstd,Tstd_in,T_out,Tstd_out,Vsr850,T_set,T_stable= line.split(',')#,T_stable 
                dataread[0].append(Time)
                dataread[1].append(T_in)
                dataread[2].append(R)
                dataread[3].append(Rstd)
                dataread[4].append(Tstd_in)
                dataread[5].append(T_out)
                dataread[6].append(Tstd_out)
                dataread[7].append(Vsr850)
                dataread[8].append(T_set)
                dataread[9].append(T_stable)
                
        ## Close reading file
        fid.close()
        ## Set the figure title
        ax1.set_title(filedic.split('\\')[-1])
        ## Show the plot
        plt.show()
        
    ##################################################
    def plotbutton(self, event):
        ## Standard Realtime data visualization
        style.use('ggplot')
        fig = plt.figure()
        ax1 = fig.add_subplot(1,1,1)
        fig.canvas.set_window_title('Realtime Data Plot')
        directory = self.txtDic.GetValue()
        filename = self.txtFil.GetValue()
        filedic = directory+'\\'+filename 
        ## Create a animate method for updating realtime data in the plot
        def animate(i):
            fid = open(filedic,'r')
            graph_data = fid.read()
            fid.close()
            lines = graph_data.split('\n')
            ## Initialize data reading in 2D-list, get the X-axis and Y-axis input from users
            xs = self.plotdict[self.XplotChoices[self.Xplot.GetCurrentSelection()]]
            ys = self.plotdict[self.YplotChoices[self.Yplot.GetCurrentSelection()]]
            dataread = [[],[],[],[],[],[],[],[],[],[]]
            ## Read data
            for line in lines:
                if len(line) > 1 and line[0:2] != "##":
                    Time,T_in,R,Rstd,Tstd_in,T_out,Tstd_out,Vsr850,T_set, T_stable= line.split(',')#,T_stable 
                    dataread[0].append(Time)
                    dataread[1].append(T_in)
                    dataread[2].append(R)
                    dataread[3].append(Rstd)
                    dataread[4].append(Tstd_in)
                    dataread[5].append(T_out)
                    dataread[6].append(Tstd_out)
                    dataread[7].append(Vsr850)
                    dataread[8].append(T_set)
                    dataread[9].append(T_stable)
            ## clear previous graph
            ax1.clear()
            ## plot data
            ax1.plot(dataread[xs], dataread[ys],'--o', lw = 0.5, ms = 5, mew =0 , c = [0.5,0.5,0.5],mfc = [0,0,1])
        ## Set graph title
        ax1.set_title(filedic.split('\\')[-1]) 
        ## animation
        ani = animation.FuncAnimation(fig, animate, interval=1000)  
        plt.show()
        
    #######################################################
    def updateCurrent(self,event):
        VV = float(self.sr850control2input.GetValue())
        RR = float(self.sr850control3input.GetValue())
        II = 1000.0*VV/RR
        self.sr850control4output.SetValue(str(II))
        
    #########################################################
    def measurebutton(self, event):
        ## Get Temperature Setting Values
        if self.tStartval.GetValue() == 'N' or self.tEndval.GetValue() == 'N' or self.tDividenval.GetValue() == 'N':
            trange1 = np.empty( 0 )
        else:
            Ts1 = float(self.tStartval.GetValue())
            Te1 = float(self.tEndval.GetValue())
            di1 = float(self.tDividenval.GetValue())
            ## Create T setting sequence
            if Te1 >= Ts1 :
                trange1 = np.arange(Ts1,Te1+0.01,di1)
            elif Te1 < Ts1:
                trange1 = np.arange(Ts1,Te1-0.01,-di1)        
        
        ## Getting more T setting values from input range 2,3,4,5        
        if self.tStartval2.GetValue() == 'N' or self.tEndval2.GetValue() == 'N' or self.tDividenval2.GetValue() == 'N':
            trange2 = np.empty( 0 )
        else:
            Ts2 = float(self.tStartval2.GetValue())
            Te2 = float(self.tEndval2.GetValue())
            di2 = float(self.tDividenval2.GetValue())  
            if Te2 >= Ts2 :
                trange2 = np.arange(Ts2,Te2+0.01,di2)
            elif Te2 < Ts2:
                trange2 = np.arange(Ts2,Te2-0.01,-di2)
                
        if self.tStartval3.GetValue() == 'N' or self.tEndval3.GetValue() == 'N' or self.tDividenval3.GetValue() == 'N':
            trange3 = np.empty( 0 )
        else:
            Ts3 = float(self.tStartval3.GetValue())
            Te3 = float(self.tEndval3.GetValue())
            di3 = float(self.tDividenval3.GetValue())
            if Te3 >= Ts3 :
                trange3 = np.arange(Ts3,Te3+0.01,di3)
            elif Te3 < Ts3:
                trange3 = np.arange(Ts3,Te3-0.01,-di3)

                
        if self.tStartval4.GetValue() == 'N' or self.tEndval4.GetValue() == 'N' or self.tDividenval4.GetValue() == 'N':
            trange4 = np.empty( 0 )
        else:
            Ts4 = float(self.tStartval4.GetValue())
            Te4 = float(self.tEndval4.GetValue())
            di4 = float(self.tDividenval4.GetValue())
            if Te4 >= Ts4 :
                trange4 = np.arange(Ts4,Te4+0.01,di4)
            elif Te4 < Ts4:
                trange4 = np.arange(Ts4,Te4-0.01,-di4)

                
        if self.tStartval5.GetValue() == 'N' or self.tEndval5.GetValue() == 'N' or self.tDividenval5.GetValue() == 'N':
            trange5 = np.empty( 0 )
        else:
            Ts5 = float(self.tStartval5.GetValue())
            Te5 = float(self.tEndval5.GetValue())
            di5 = float(self.tDividenval5.GetValue())
            if Te5 >= Ts5 :
                trange5 = np.arange(Ts5,Te5+0.01,di5)
            elif Te5 < Ts5:
                trange5 = np.arange(Ts5,Te5-0.01,-di5)
    
        ## Generating T sequence        
        trange = np.concatenate([trange1,trange2,trange3,trange4,trange5])

        ## Get data file's name and directory
        directory = self.txtDic.GetValue()
        filename = self.txtFil.GetValue()
        
        filedic=directory+'\\'+filename
                
        ## Use SR850LTC21_measrue for performing measruements, used threading
        MEAsure.sr850ltc21(filename = filedic,
                           trange=trange,
                           SR850scanlength = float(self.sr850control1input.GetValue()),
                           SR850SinRMS = float(self.sr850control2input.GetValue()),
                           CurrentResistance = float(self.sr850control3input.GetValue())*1000.0,
                           GainRatio =  float(self.sr850control6input.GetValue()),
                           dT = float(self.sr850control4input.GetValue()),
                           dTfluc = float(self.sr850control5input.GetValue()),
                           description = self.description.GetValue(),
                           WaitTimeForT = float(self.sr850control7input.GetValue()))
               

        btn = event.GetEventObject()
        btn.Disable()
    

    #----------------------------------------------------------------------
    def updateDisplay(self, msg):
        """
        Receives data from thread and updates the display
        """
        t = msg
        if t == "Measurement finished!":
            self.bottonMeasure.Enable() 
            self.statusMeasureinput.SetValue(t)
        elif t == "A":
            self.statusMeasureinput.SetValue("Attempting to stablize T")
        elif t == "M":
            self.statusMeasureinput.SetValue("Measuring R and T")
        elif t == "S":
            self.statusMeasureinput.SetValue("Setting up SR850 and LTC21")
               
               
    def stopbutton(self,event):
        """
        Setting the stopFlag for stopping for loop in the running thread
        """
        GlobalFlag.stopFlag = False
        self.statusMeasureinput.SetValue("Stopping! Could be a minute!")
      
         
class FileInputStream(wx.InputStream):
    def __init__(self, name):
        self.f=open(name, "rb")
        wx.InputStream.__init__(self,self.f)

     
# Every wxWidgets application must have a class derived from wx.App
class MyApp(wx.App):

    # wxWindows calls this method to initialize the application
    def OnInit(self):

        # Create an instance of our customized Frame class
        frame = MyFrame(None, -1, "Resistivity App")
        frame.Show(True)

        # Tell wxWindows that this is our main window
        self.SetTopWindow(frame)
        # Return a success flag
        return True



app = MyApp(0)     # Create an instance of the application class
app.MainLoop()     # Tell it to start processing events    