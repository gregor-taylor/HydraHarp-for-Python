#Python wrappings for HydraHarp C functions
#
#Requirements:
#-Python3
#-Hydraharp HHLibV30 (See Picoquant website)

#Data holders are of the form 'aCamelType'
#functions are as per documentation for HHLib but 'pythonised' ie 'HH_GetContModeBlock' becomed 'get_cont_mode_block'



#===============================
#IMPORTS
#===============================

import ctypes as ct

#===============================
#Main Class
#===============================

class HydraHarp():
    def __init__(self, devid):
        #From hhdefin.h
        self.TTREADMAX = 131072
        self.MAXCONTMODEBUFLEN = 62272

        #Set up buffers for variables from DLL
        self.buffer = (ct.c_uint * self.TTREADMAX)()
        self.contBuffer = (ct.c_uint * self.MAXCONTMODEBUFLEN)()
        self.hwSerial = ct.create_string_buffer(b"", 8)
        self.hwPartno = ct.create_string_buffer(b"", 8)
        self.hwModel = ct.create_string_buffer(b"", 16)
        self.numChannels = ct.c_int()
        self.numModules = ct.c_int()
        self.mod_id = ct.c_int()
        self.modelCode = ct.c_int()
        self.versionCode = ct.c_int()
        self.baseResolution=ct.c_double()
        self.resolution = ct.c_double()
        self.elapsedTime=ct.c_double()
        self.binSteps = ct.c_int()
        self.syncRate = ct.c_int()
        self.syncPeriod = ct.c_double()
        self.countRate = ct.c_int()
        self.flags = ct.c_int()
        self.features = ct.c_int()
        self.nRecords = ct.c_int()
        self.ctcStatus = ct.c_int()
        self.warnings = ct.c_int()
        self.histoLen = ct.c_int()
        self.warningsText = ct.create_string_buffer(b"", 16384)
        self.debugInfo = ct.create_string_buffer(b"", 65536)
        self.nActual = ct.c_int()
        self.nBytesReceived = ct.c_int()
        self.errorString = ct.create_string_buffer(b"", 40)
        #Some dicts to hold measurement info for reference
        Ch_1_parameters={}
        Ch_2_parameters={}
        Ch_3_parameters={}
        Ch_4_parameters={}
        Sync_ch_parameters={}
        #Setup some parameter defaults
        self._dev_id = ct.c_int(devid) 
        self.measurement_running = False
        
        #
        self.hhlib = ct.CDLL("hhlib64.dll") 
        open_device(devid)

    def execute_func(self, retcode, func_name): #Obtains readable error strings from the error code if a func fails.
        if retcode < 0: #Error codes are less than zero
            self.hhlib.HH_GetErrorString(self.errorString, ct.c_int(retcode))
            print("HH_%s error %d (%s). Aborted." % (func_name, retcode, self.errorString.value.decode("utf-8")))
            #self.close_device()


    def initialise(self, mode, clk_source): #This routine must be called before any of the other routines below can be used. Note that some of them depend on the
                                           #measurement mode you select here. See the HydraHarp manual for more information on the measurement modes.
                                           #devidx: device index 0..7
                                           #mode: measurement mode
                                           #0 = histogramming mode
                                           #2 = T2 mode
                                           #3 = T3 mode
                                           #8 = continuous mode
                                           #clk_source: reference clock to use
                                           #0 = internal
                                           #1 = external
        self.execute_func(self.hhlib.HH_Initialize(self._dev_id, ct.c_int(mode), ct.c_int(clk_source)), 'intialise')

    def close_device(self): #Closes and releases the device for use by other programs.
        self.execute_func(self.hhlib.HH_CloseDevice(self._dev_id), 'close_device')

#=====================
#Below functions once intialised
#=====================

    def get_hardware_info(self):
        self.execute_func(self.hhlib.HH_GetHardwareInfo(self._dev_id, self.hwModel, self.hwPartno), 'get_hardware_info')

    def get_features(self):
        self.execute_func(self.hhlib.HH_GetFeatures(self._dev_id, ct.byref(self.features)), 'get_features')

    def get_serial_number(self):
        self.execute_func(self.hhlib.HH_GetSerialNumber(self._dev_id, self.hwSerial),'get_serial_number')

    def get_base_resolution(self): #Use the value returned in binsteps as maximum value for the HH_SetBinning function.
        self.execute_func(self.hhlib.HH_GetBaseResolution(self._dev_id, ct.byref(self.baseResolution), ct.byref(self.binSteps)), 'get_base_resolution')

    def get_num_of_input_channels(self):
        self.execute_func(self.hhlib.HH_GetNumOfInputChannels(self._dev_id, ct.byref(self.numChannels)), 'get_num_of_input_channels')

    def get_num_of_modules(self):
        self.execute_func(self.hhlib.HH_GetNumOfModules(self._dev_id, ct.byref(self.numModules)), 'get_num_of_modules')

    def get_module_info(self, mod_id):
        self.execute_func(self.hhlib.HH_GetModuleInfo(self._dev_id, mod_id, ct.byref(self.modelCode), ct.byref(self.versionCode)), 'get_module_info')

    def get_module_index(self, channel_id):
        self.execute_func(self.hhlib.HH_GetModuleIndex(self._dev_id, ct.c_int(channel_id), ct.byref(self.mod_id)), 'get_module_index')

    def get_hardware_debug_info(self):
        self.execute_func(self.hhlib.HH_GetHardwareDebugInfo(self._dev_id, self.debugInfo), 'get_hardware_debug_info')

    def calibrate(self):
        self.execute_func(self.hhlib.HH_Calibrate(self._dev_id), 'calibrate')

    def set_sync_divider(self, SRD): #The sync divider must be used to keep the effective sync rate at values ≤ 12.5 MHz. It should only be used with sync sources
                                     #of stable period. Using a larger divider than strictly necessary does not do great harm but it may result in slightly larger timing
                                     #jitter. The readings obtained with HH_GetCountRate are internally corrected for the divider setting and deliver the external
                                     #(undivided) rate. The sync divider should not be changes whilee a measurement is running.
        self.execute_func(self.hhlib.HH_SetSyncDiv(self._dev_id, ct.c_int(SRD)), 'set_sync_divider')

    def set_sync_cfd(self, level, zero_cross): #Value is given as a positive number although the electrical signals are actually negative.
        self.Sync_ch_parameters['Level']=level
        self.Sync_ch_parameters['Zero X']=zero_cross
        self.execute_func(self.hhlib.HH_SetSyncCFD(self._dev_id, ct.c_int(level), ct.c_int(zero_cross)), 'set_sync_cfd')

    def set_sync_channel_offset(self, value): #sync ch offset in ps
        self.Sync_ch_parameters['Offset']=value
        self.execute_func(self.hhlib.HH_SetSyncChannelOffset(self._dev_id, ct.c_int(value)), 'set_sync_channel_offset')

    def set_input_cfd(self, channel, level, zero_cross): #Value is given as a positive number although the electrical signals are actually negative.
        if channel == 1:
            current_dict=Ch_1_parameters
        elif channel == 2:
            current_dict=Ch_2_parameters
        elif channel == 3:
            current_dict=Ch_3_parameters
        elif channel == 4:
            current_dict=Ch_4_parameters
        current_dict['Level']=level
        current_dict['Zero X']=zero_cross
        self.execute_func(self.hhlib.HH_SetInputCFD(self._dev_id, ct.c_int(channel), ct.c_int(level), ct.c_int(zero_cross)), 'set_input_cfd')

    def set_input_channel_offset(self, channel, value): #ch timing offset in ps
        if channel == 1:
            current_dict=Ch_1_parameters
        elif channel == 2:
            current_dict=Ch_2_parameters
        elif channel == 3:
            current_dict=Ch_3_parameters
        elif channel == 4:
            current_dict=Ch_4_parameters
        current_dict['Offset']=value
        self.execute_func(self.hhlib.HH_SetInputChannelOffset(self._dev_id, ct.c_int(channel), ct.c_int(value)), 'set_input_channel_offset')

    def set_input_channel_enable(self, channel, enable): #enable=0 disabled, enable=1 enabled.
        self.execute_func(self.hhlib.HH_SetInputChannelEnable(self._dev_id, ct.c_int(channel), ct.c_int(enable)), 'set_input_channel_enable')

    def set_stop_overflow(self, stop_ovfl, stopcount): #This setting determines if a measurement run will stop if any channel reaches the maximum set by stopcount. If stop_ofl
                                                       #is 0 the measurement will continue but counts above STOPCNTMAX in any bin will be clipped.
        self.execute_func(self.hhlib.HH_SetStopOverflow(self._dev_id, ct.c_int(stop_ovfl), ct.c_uint(stopcount)), 'set_stop_overflow')

    def set_binning(self, binning):#binning code works to the power of 2, i.e.
                                   #0 = 1x base resolution,
                                   #1 = 2x base resolution,
                                   #2 = 4x base resolution,
                                   #3 = 8x base resolution, and so on.
        self.execute_func(self.hhlib.HH_SetBinning(self._dev_id, ct.c_int(binning)), 'set_binning')

    def set_offset(self, offset): #histogram time offset in ns
        self.execute_func(self.hhlib.HH_SetOffset(self._dev_id, ct.c_int(offset)), 'set_offset')

    def set_histo_length(self, lencode): #histo length code 0-6. Actual len is 1024*lencode^2.
        self.execute_func(self.hhlib.HH_SetHistoLen(self._dev_id, ct.c_int(lencode), ct.byref(self.histoLen)), 'set_histo_length')

    def clear_hist_memory(self):
        self.execute_func(self.hhlib.HH_ClearHistMem(self._dev_id), 'clear_hist_memory')

    def set_meas_control(self, meascontrol, startedge, stopedge): #meascontrol: measurement control code
                                                                         #0 = MEASCTRL_SINGLESHOT_CTC
                                                                         #1 = MEASCTRL_C1_GATED
                                                                         #2 = MEASCTRL_C1_START_CTC_STOP
                                                                         #3 = MEASCTRL_C1_START_C2_STOP
                                                                         #5 = MEASCTRL_CONT_C1_START_CTC_STOP
                                                                         #6 = MEASCTRL_CONT_CTC_RESTART
                                                                         #startedge: edge selection code
                                                                         #0 = falling
                                                                         #1 = rising
                                                                         #stopedge: edge selection code
                                                                         #0 = falling
                                                                         #1 = rising
        self.execute_func(self.hhlib.HH_SetMeasControl(self._dev_id, ct.c_int(meascontrol), ct.c_int(startedge), ct.c_int(stopedge)), 'set_meas_control')

    def start_meas(self, acq_time): #acq_time in ms
        self.execute_func(self.hhlib.HH_StartMeas(self._dev_id, ct.c_int(acq_time)), 'start_meas')

    def stop_meas(self):
        self.execute_func(self.hhlib.HH_StopMeas(self._dev_id), 'stop_meas')

    def CTC_status(self):
        self.execute_func(self.hhlib.HH_CTCStatus(self._dev_id, ct.byref(self.ctcStatus)), 'CTC_status')

    def get_histogram(self, channel, clear): #The histogram buffer size actuallen must correspond to the value obtained through HH_SetHistoLen().
                              #The maximum input channel index must correspond to nchannels-1 as obtained through HH_GetNumOfInputChannels().
                              #channel: input channel index 0..nchannels-1
                              #clear denotes the action upon completing the reading process
                              #0 = keeps the histogram in the acquisition buffer
                              #1 = clears the acquisition buffer
        self.histoBuffer = (ct.c_uint*self.histoLen)()
        self.execute_func(self.hhlib.HH_GetHistogram(self._dev_id, ct.byref(self.histoBuffer), ct.c_int(channel), ct.c_int(clear)), 'get_histogram') 

    def get_resolution(self):
        self.execute_func(self.hhlib.HH_GetResolution(self._dev_id, ct.byref(self.resolution)), 'get_resolution')

    def get_sync_rate(self):
        self.execute_func(self.hhlib.HH_GetSyncRate(self._dev_id, ct.byref(self.syncRate)), 'get_sync_rate')

    def get_count_rate(self, channel): #Allow at least 100 ms after HH_Initialize or HH_SetSyncDivider to get a stable rate meter reading.
                                       #Similarly, wait at least 100 ms to get a new reading. This is the gate time of the counters.
                                       #The maximum input channel index must correspond to nchannels-1 as obtained through HH_GetNumOfInputChannels().
        self.execute_func(self.hhlib.HH_GetCountRate(self._dev_id, ct.c_int(channel), ct.byref(self.countRate)), 'get_count_rate')

    def get_flags(self):
        self.execute_func(self.hhlib.HH_GetFlags(self._dev_id, ct.byref(self.flags)), 'get_flags')

    def get_elapsed_meas_time(self):
        self.execute_func(self.hhlib.HH_GetElapsedMeasTime(self._dev_id, ct.byref(self.elapsedTime)), 'get_elapsed_meas_time')

    def get_warnings(self):
        self.execute_func(self.hhlib.HH_GetWarnings(self._dev_id, ct.byref(self.warnings)), 'get_warnings')

    def get_warnings_text(self):
        self.execute_func(self.hhlib.HH_GetWarningsText(self._dev_id, self.warningsText, ct.byref(self.warnings)), 'get_warnings_text')

    def get_sync_period(self):
        self.execute_func(self.hhlib.HH_GetSyncPeriod(self._dev_id, ct.byref(self.syncPeriod)), 'get_sync_period')

#=====================
#Special TTTR Mode Functions
#=====================

    def read_FiFo(self, count): #CPU time during wait for completion will be yielded to other processes / threads. Function will return after a timeout period of
                                #~10 ms, if not all data could be fetched. Buffer must not be accessed until the function returns.
        self.execute_func(self.hhlib.HH_ReadFiFo(self._dev_id, ct.byref(self.buffer), ct.c_int(count), ct.byref(self.nActual)), 'read_FiFo')

    def set_marker_edges(self,me0,me1,me2,me3): #active edge of marker signal <n>,
                                                #0 = falling,
                                                #1 = rising
        self.execute_func(self.hhlib.HH_SetMarkerEdges(self._dev_id, ct.c_int(me0),ct.c_int(me1),ct.c_int(me2),ct.c_int(me3)), 'set_marker_edges')

    def set_marker_enable(self, en0, en1, en2, en3): #desired enable state of marker signal <n>,
                                                     #0 = disabled,
                                                     #1 = enabled
        self.execute_func(self.hhlib.HH_SetMarkerEnable(self._dev_id, ct.c_int(en0),ct.c_int(en1),ct.c_int(en2),ct.c_int(en3)),'set_marker_enable')

    def set_marker_holdoff_time(self, holdofftime): #holdoff time in ns
        self.execute_func(self.hhlib.HH_SetMarkerHoldoffTime(self._dev_id, ct.c_int(holdofftime)), 'set_marker_holdoff_time')

#=====================
#Special Continuous Mode Functions
#=====================    

    def get_cont_mode_block(self):
        self.execute_func(self.hhlib.HH_GetContModeBlock(self._dev_id, ct.byref(self.contBuffer), ct.byref(self.nBytesReceived)), 'get_cont_mode_block')

#=====================
#Non PicoQuant functions for class
#=====================
    def get_hw_config(self):
        self.hw_config = {}
        self.get_hardware_info()
        self.hw_config['Model']=self.hwModel.value.decode("utf-8")
        self.hw_config['Part No']=self.hwPartno.value.decode("utf-8")
        self.get_features()
        self.hw_config['Features']=self.features.value
        self.get_serial_number()
        self.hw_config['Serial']=self.hwSerial.value.decode("utf-8")
        self.get_base_resolution()
        self.hw_config['Base Resolution']=self.baseResolution.value
        self.hw_config['Bin Steps']=self.binSteps.value
        self.get_num_of_input_channels()
        self.hw_config['Number of Channels']=self.numChannels.value
        self.get_num_of_modules()
        self.hw_config['Number of Modules']=self.numModules.value
        self.get_hardware_debug_info()
        self.hw_config['Debug Info']=self.debugInfo.value.decode("utf-8")
        for k,v in self.hw_config.items():
            print(str(k)+' = '+str(v))

    def get_current_meas_config(self):
        self.meas_config = {}
        self.get_resolution()
        self.meas_config['Resolution']=self.resolution.value
        self.get_sync_rate()
        self.meas_config['Sync Rate']=self.syncRate.value
        self.get_flags()
        self.meas_config['Flags']=self.flags.value
        self.get_sync_period()
        self.meas_config['Sync Period']=self.syncPeriod.value
        self.get_warnings()
        self.get_warnings_text()
        self.meas_config['Warnings']=self.warningsText.value.decode("utf-8")
        for k,v in self.meas_config.items():
            print(str(k)+' = '+str(v))


#==============================================================================================================================================
#==============================================================================================================================================

#======================
#Non instance specific functions to work out ids, lib details and close instances etc - does not need to be intialised to run these.
#======================
        
def get_library_version(): #Gets lib version. 
    LibVersion = ct.create_string_buffer(b"", 8)
    hhlib = ct.CDLL("hhlib64.dll")
    hhlib.HH_GetLibraryVersion(LibVersion)
    return LibVersion.value.decode("utf-8")

def open_device(dev_id): #Opens Device and returns it's serial number
    hhlib = ct.CDLL("hhlib64.dll")
    hwSerial = ct.create_string_buffer(b"", 8)
    retcode = hhlib.HH_OpenDevice(ct.c_int(dev_id), hwSerial)
    if retcode < 0:
        print('Error - dev %d not found' % dev_id)
        return False
    else:
        return hwSerial.value.decode("utf-8")

def close_device(dev_id): #Closes and releases the device for use by other programs. Left here for completeness - call .close_device() on the instance in reality. 
    hhlib = ct.CDLL("hhlib64.dll")
    hhlib.HH_CloseDevice(ct.c_int(dev_id))

#======================
#Non PicoQuant funcs
#======================

def list_devs(MAXDEVNUM):
    for i in range(0,MAXDEVNUM):
        dev = open_device(i)
        if dev == False:
            pass
        else:
            print('Device %d - '%i + dev)



if __name__ == '__main__':
        pass






