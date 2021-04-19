#!/bin/env python3
# -*- coding: utf-8 -*-


from time import sleep

import ftd2xx
from ftd2xx.defines import *


# Device operation code definitions.
OP_RESERVED = b'\x00'
OP_ECHO = b'\x10'
OP_ECHO_ALT = b'\x80'
OP_PROGRAM = b'\x20'
OP_DISABLE_PS = b'\x30'
OP_ENABLE_PS = b'\x40'
OP_TRIGGER_MEASUREMENT = b'\x50'
OP_SET_RANGE = b'\x60'
OP_GET_RANGE = b'\xb0'
OP_DISABLE_FG = b'\x70'
OP_ENABLE_FG = b'\xc0'
OP_GET_MODE = b'\x90'
OP_SET_PS = b'\xa0'

# Device mode definitions.
MODE_UNKNOWN = 'unknown'
MODE_RESET = 'reset'
MODE_PROGRAM = 'programming'
MODE_INACTIVE = 'inactive'
MODE_ACTIVE = 'active'
MODE_TABLE = {
    b'\x00': MODE_RESET,
    b'\x10': MODE_RESET,
    b'\x20': MODE_RESET,
    b'\x30': MODE_PROGRAM,
    b'\x40': MODE_PROGRAM,
    b'\x50': MODE_PROGRAM,
    b'\x60': MODE_INACTIVE,
    b'\x70': MODE_ACTIVE
}

# Power supply definitions.
POWERSUPPLY_VREF = 60
POWERSUPPLY_MIN = 1.6
POWERSUPPLY_MAX = 59.3

# Waveform table definitions.
WAVEFORM_SAMPLES_PER_PERIOD = 8
WAVEFORM_VREF = 10

# Measurement definitions.
MEASUREMENT_SAMPLES = 8
MEASUREMENT_PERIODS = 3
DUT_MEASUREMENT_VREF = 1
DUT_MEASUREMENT_RANGE_MULTIPLIERS = [1.1, 2.7, 5.5, 16.6] # Ranges 1, 2, 3, 4 respectively.
DUT_MEASUREMENT_RANGE_TABLE = {
    1: b'\x30', # Inverted in order for binary to match pin outputs.
    2: b'\x20',
    3: b'\x10',
    4: b'\x00'
}
FG_MEASURMENT_VREF = 2.5


class SIMPS(object):
    # Wrapper around SIMPSDevice to be able to use the 'with' style.
    def __enter__(self):
        self.device = SIMPSDevice()
        self.device.connect()
        return self.device
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.device.close()

class SIMPSDevice(object):
    def __init__(self, connect_timeout=None):
        self.device = None
        self.range = 1
        self.range_mult = 1.1
        self.connect_timeout = connect_timeout
    
    def connect(self):
        time = 0
        while True:
            try:
                # Is a simp present.
                # This takes too long...
                devices = self._find_some_simps()
                
                # Did I catch a simp?
                if (len(devices) == 0): raise Exception('Cound not find a SIMPS ATE device. Make sure the FTDI chip is programmed and the D2XX driver is installed.')
                
                # We are going to assume that there is only one simp per PC right now.
                if (len(devices) != 1): raise Exception('Too many simps for this software to handle.')
                
                # Lets make a connection to the simp.
                self.device = ftd2xx.open(devices[0]['index'])
                
                # Reset Device
                self.device.resetDevice()
                
                # Set Timeouts
                #self.device.setTimeouts(500, 500)
                
                # Set Latency Time - 2ms
                #self.device.setLatencyTimer(2)
                
                # Set USB Parameters - 
                #self.device.setUSBParameters(in_tx_size, out_tx_size=0)
                
                # If we wanted to so the synchronus interface,
                #self.device.setBitMode(mask, enable)
                
                # Set Flow Control - 0x0100, RTS-CTS
                #self.device.setFlowControl(FLOW_RTS_CTS)
                
                # Purge Buffers
                #self.device.purge(PURGE_RX + PURGE_TX)
                
                # FT_Set_DTR
                #self.device.setDtr()
                
                # FT_set_RTS
                #self.device.setRts()
            except:
                # We failed to connect to the device.
                if (self.connect_timeout == None):
                    # There is not connection timeout, so re-raise the exception.
                    raise
                else:
                    if (self.connect_timeout >= time):
                        # Re-raise the exception if we are over the allowed waiting time.
                        raise
                    else:
                        # Wait before retrying.
                        # Note: This will probably take longer than wanted.
                        #       Should probably change to time.now()
                        sleep(0.25)
                        time = time + 0.25
            else:
                # The connection was successful, so break the loop.
                break
                
    
    def close(self):
        if self.device: self.device.close()
    
    def _find_some_simps(self):
        # Determine the number of devices. This is a slow call.
        number_of_devices = ftd2xx.createDeviceInfoList()
        
        # For each FTDI device using the D2XX drivers, get and check the device description for a simp.
        devices = []
        for index in range(number_of_devices):
            try:
                # Update is false to prevent another slow createDeviceInfoList call.
                device_details = ftd2xx.getDeviceInfoDetail(index, update=False)
                if (device_details['description'] == b'SIMPS Device'):
                    devices.append(device_details)
                elif (device_details['description'] == b'SIMPS ATE'):
                    devices.append(device_details)
            except ftd2xx.ftd2xx.DeviceError:
                pass
        return devices
    
    def _try_read(self, bytes=1, all=False, timeout=None, wait=0.010):
        # How much data can we read?
        rx_queue, tx_queue, status = self.device.getStatus()
        
        # Return all bytes that are in the buffer.
        if (all == True) and (rx_queue >= 1):
            return self.device.read(rx_queue)
        
        # Otherwise return none if there is nothing in the buffer.
        elif (all == True):
            return
        
        # If there is no timeout try to read the correct amount of bytes.
        elif (timeout == None):
            if (rx_queue >= bytes):
                return self.device.read(bytes)
        # If timeout is true, wait until timeout to read specific number of bytes.
        elif (timeout != None):
            time = 0
            while True:
                if (time >= timeout):
                    return None
                
                if (rx_queue >= bytes):
                    return self.device.read(bytes)
                
                # Wait to read the buffer status.
                sleep(wait)
                time += wait
                
                # Check the buffers.
                rx_queue, tx_queue, status = self.device.getStatus()
    
    def validate_communications(self):
        # This function will be used to test and validate the interface.
        print('----- Detecting wiring errors')
        self.device.purge(PURGE_RX + PURGE_TX)
        self.device.write(b'\x10\xaa')
        a = self._try_read(1, timeout=2)
        self.device.purge(PURGE_RX + PURGE_TX)
        self.device.write(b'\x10\x55')
        b = self._try_read(1, timeout=2)
        
        if ((a == None) or (b == None)):
            # The first data line, D0, is required to trigger the echo function
            # in the FPGA. We can also use an alternate op code of 0x80 which uses
            # the last data line, D7.
            self.device.purge(PURGE_RX + PURGE_TX)
            self.device.write(b'\x80\xaa')
            a = self._try_read(1, timeout=2)
            self.device.purge(PURGE_RX + PURGE_TX)
            self.device.write(b'\x80\x55')
            b = self._try_read(1, timeout=2)
            
            if ((a == None) or (b == None)):
                print('Error detected. No data was successfully exchanged with the FPGA.')
                print('Possible causes/fixes:')
                print('\t- Check the data bus for continuity between the FTDI chip and FPGA.')
                print('\t- Check the control lines for continuirty. RXFn, TXEn, RDn, WRn, SIWUn')
                print('\t- The FPGA\'s firmware may not be flashed or correct.')
                print('\t- Any number of other things. ;)')
                exit(1)
        
        # XOR both a and b.
        xor = bytes([_a ^ _b for _a, _b in zip(a, b)])
        
        # Split the byte into a list of bits
        bits = list(bin(int.from_bytes(xor, byteorder='big')).lstrip('0b').zfill(8))
        
        # Detect bad datalines.
        error = False
        for i in range(8):
            if (bits[7-i] != '1'):
                print('Error detected with dataline, D%u' % i)
                error = True
        if error is True:
            exit(1)
        
        # Detect if the datalines are wired backwards.
        if (a == b'\x55') or (b == b'\xaa'):
            print('Error detected. Datalines are backwards. They can be flipped in the firmware pinout.')
            exit(1)
        
        # Success
        print('No errors were detected.')
        print('                                                                \n'
        + '    _/_/_/      _/_/      _/_/_/    _/_/_/  _/_/_/_/  _/_/_/    \n'
        + '   _/    _/  _/    _/  _/        _/        _/        _/    _/   \n'
        + '  _/_/_/    _/_/_/_/    _/_/      _/_/    _/_/_/    _/    _/    \n'
        + ' _/        _/    _/        _/        _/  _/        _/    _/     \n'
        + '_/        _/    _/  _/_/_/    _/_/_/    _/_/_/_/  _/_/_/        \n'
        + '                                                                \n')
    
    def test(self):
        print('----- Testing echo functionality')
        print('\tpurging buffers')
        self.device.purge(PURGE_RX + PURGE_TX)
        print('\techoing 05')
        self.device.write(b'\x10\x50')
        print('\twaiting for data')
        bytes = self._try_read(1, timeout=1)
        print(bytes)
        if (bytes == b'\x50'): print('SUCCESS')
        else:
            print('FAILURE')
            exit()
        print()
        
        print('----- Testing echo read anti-lockup functionality in fpga firmware')
        print('\tpurging buffers')
        self.device.purge(PURGE_RX + PURGE_TX)
        print('\techo without data leading to a lockup condition')
        self.device.write(b'\x10')
        print('\twaiting for FPGA timeout period to be over')
        sleep(0.5)
        print('\tstarting a new echo with data of 6')
        self.device.write(b'\x10\x60')
        bytes = self._try_read(1, timeout=1)
        print(bytes)
        if (bytes == b'\x60'): print('SUCCESS')
        else:
            print('FAILURE')
            exit()
    
    def program(self, ps_voltage, frequency, waveform_table, _range):
        # Make sure there are enough waveform table values.
        assert len(waveform_table) == WAVEFORM_SAMPLES_PER_PERIOD
        
        # Make sure the power supply value is in the right range.
        assert (ps_voltage >= POWERSUPPLY_MIN) and (ps_voltage <= POWERSUPPLY_MAX)
        
        # Check for the proper mode?
        
        data = b''
        #data += voltage_to_bytes(ps_voltage, POWERSUPPLY_VREF, 10)
        data += integer_to_bytes(int(ps_voltage), 10)
        data += integer_to_bytes(frequency, 24)
        for waveform_value in waveform_table:
            data += voltage_to_bytes(waveform_value, WAVEFORM_VREF, 12, True)
        data += self.range_byte(_range)
        
        # Send the assembled set of programming bytes.
        self.device.write(OP_PROGRAM + split_bytes(data))
    
    def get_mode(self):
        # Purge buffers
        self.device.purge(PURGE_RX + PURGE_TX)
        
        # Write op code 8'h09 to request the operational mode.
        self.device.write(OP_GET_MODE)
        
        # Read the mode back.
        response = self._try_read(bytes=1, timeout=1)
        
        try:
            return MODE_TABLE[cancel_ls_four_bits(response)]
        except:
            raise
            return MODE_UNKNOWN
    
    def set_ps(self, ps_voltage):
        # Make sure the power supply value is in the right range.
        assert (ps_voltage >= POWERSUPPLY_MIN) and (ps_voltage <= POWERSUPPLY_MAX)
        
        data = OP_SET_PS
        #data += fix_ps_bytes(voltage_to_bytes(ps_voltage, POWERSUPPLY_VREF, 10))
        data += fix_ps_bytes(integer_to_bytes(int(ps_voltage), 10))
        
        self.device.write(data)
    
    def disable_ps(self):
        # Write op code 8'h03 to disable the power supply.
        self.device.write(OP_DISABLE_PS)
    
    def enable_ps(self):
        # Write op code 8'h04 to enable the power supply.
        self.device.write(OP_ENABLE_PS)
    
    def disable_fg(self):
        # Write op code 8'h07 to disable the function generator.
        self.device.write(OP_DISABLE_FG)
    
    def enable_fg(self):
        # Write op code 8'h08 to enable the function generator.
        self.device.write(OP_ENABLE_FG)
    
    def get_range(self):
        # Purge buffers
        self.device.purge(PURGE_RX + PURGE_TX)
        
        # Write op code 8'h09 to request the operational mode.
        self.device.write(OP_GET_RANGE)
        
        # Read the mode back.
        range_byte = self._try_read(bytes=1, timeout=1)
        assert (range_byte != None)
        
        inv_mapping = {v: k for k, v in DUT_MEASUREMENT_RANGE_TABLE.items()}
        _range = inv_mapping[cancel_ls_four_bits(range_byte)]
        
        assert (_range > 0) and (_range < 5)
        self.range = _range
        
        self.range_mult = DUT_MEASUREMENT_RANGE_MULTIPLIERS[self.range-1]
        return self.range
    
    def range_byte(self, _range):
        # Check and generate the range byte. Also set the measurement multiplier.
        assert (_range > 0) and (_range < 5)
        self.range_mult = DUT_MEASUREMENT_RANGE_MULTIPLIERS[_range-1]
        return DUT_MEASUREMENT_RANGE_TABLE[_range]
    
    def set_range(self, _range):
        # Set the measurement range with the op code 8'h06.
        self.range = _range
        self.device.write(OP_SET_RANGE + self.range_byte(_range))
    
    def measurement(self):
        # Get the devices range
        self.get_range()
        
        # Purge Buffers
        self.device.purge(PURGE_RX + PURGE_TX)
        
        # Trigger the FPGA to send back measurement data with op code 8'b05.
        self.device.write(OP_TRIGGER_MEASUREMENT)
        
        # Get all the data back...
        length = (2*2*MEASUREMENT_SAMPLES*MEASUREMENT_PERIODS + 2) * 2
        response = combine_bytes(self._try_read(length, timeout=5))
        
        assert (response != None)
        
        # Function Generater Measurements
        fg_measurements = []
        for i in range(MEASUREMENT_SAMPLES*MEASUREMENT_PERIODS):
            start = i*2
            end = (i*2) + 2
            fg_measurements.append(bytes_to_voltage(response[start:end], FG_MEASURMENT_VREF, 12, bipolar=True))
        
        # DUT Output Measurements
        dut_measurements = []
        for i in range(MEASUREMENT_SAMPLES*MEASUREMENT_PERIODS):
            start = i*2 + 48
            end = (i*2) + 2 + 48
            dut_measurements.append((self.range_mult * bytes_to_voltage(response[start:end], DUT_MEASUREMENT_VREF, 12, bipolar=True)))
        
        # Power Supply Voltage Feedback
        ps_voltage = bytes_to_voltage(response[96:98], POWERSUPPLY_VREF, 12)
        
        return (fg_measurements, dut_measurements, ps_voltage)

def voltage_to_bytes(v, ref, n=12, bipolar=False):
    if (bipolar == True):
        # The input voltage value cannot be greater than the reference or less than the -reference.
        assert (v <= ref) or (v >= -ref)
        
        # Bipolar: Vout = (Vref x D/2^(n-1)) - Vref
        D = (2**(n-1)) * ((v/ref) + 1)
    else:
        # The input voltage value cannot be greater than the reference.
        assert (v <= ref)
    
        # Unipolar: Vout = Vref x D/2^n
        D = (2**n) * (v/ref)
    
    # Prevent binary overflow.
    if (D == 2**n): D -= 1
    
    # Convert to bytes. The output length is of 8-bit increments.
    length = int(n/8) + (n % 8 > 0)
    return int.to_bytes(int(D), length=length, byteorder='big', signed=False)

def bytes_to_voltage(b, ref, n=12, bipolar=False):
    # Convert the bytes to an integer value.
    D = int.from_bytes(b, byteorder='big', signed=False)
    
    if (bipolar == True):
        # Bipolar: Vout = (Vref x D/2^(n-1)) - Vref
        return (ref * D/(2 ** (n-1))) - ref
    else:
        # Unipolar: Vout = Vref x D/2^n
        return ref * D/(2 ** n)

def integer_to_bytes(i, n=12, signed=False):
    assert ((2**n) - 1) >= i
    length = int(n/8) + (n % 8 > 0)
    return int.to_bytes(int(i), length=length, byteorder='big', signed=signed)

def bytes_to_integer(b, n=12, signed=False):
    # Should cap the output to the number of bits... perhaps later.
    return int.from_bytes(b, byteorder='big', signed=signed)

# Functions to hack those bits inorder to get around that 3rd dataline being dead...
def fix_ps_bytes(bytes):
    # Make 0000.1111.1111.1111 into 1111.1000.1111.1011
    # The 3rd bit of each byte is passed by.
    msByte = bytes[0]
    lsByte = bytes[1]
    ms_bits = list(bin(msByte).lstrip('0b').zfill(8))
    ls_bits = list(bin(lsByte).lstrip('0b').zfill(8))
    #print(''.join(ms_bits))
    #print(''.join(ls_bits))
    ms_new = ''.join(ms_bits[4:] + [ls_bits[0]] + ['0', '0', '0']) # <- Fix
    ls_new = ''.join(ls_bits[1:6] + ['0'] + ls_bits[6:])
    #print(ms_new)
    #print(ls_new)
    new_bytes = b''
    new_bytes += int.to_bytes(int(ms_new, 2), length=1, byteorder='big', signed=False)
    new_bytes += int.to_bytes(int(ls_new, 2), length=1, byteorder='big', signed=False)
    #print(new_bytes)
    #exit()
    return new_bytes

def cancel_ls_four_bits(byte):
    # Make 1111xxxx into 11110000
    bits = list(bin(int.from_bytes(byte, byteorder='big')).lstrip('0b').zfill(8))
    new_byte = int.to_bytes(int(''.join(bits[:4] + ['0', '0', '0', '0']), 2), length=1, byteorder='big', signed=False)
    return new_byte

def split_bytes(bytes):
    # Split each byte into msb and lsb parts of 4-bits each.
    # Send msb parts first followed by lsb parts.
    msb_parts = b''
    lsb_parts = b''
    
    for byte in bytes:
        bits = list(bin(byte).lstrip('0b').zfill(8))
        msb_parts += int.to_bytes(int(''.join(bits[:4] + ['0', '0', '0', '0']), 2), length=1, byteorder='big', signed=False)
        lsb_parts += int.to_bytes(int(''.join(bits[4:] + ['0', '0', '0', '0']), 2), length=1, byteorder='big', signed=False)
    
    new_bytes = msb_parts + lsb_parts
    
    return new_bytes

def combine_bytes(bytes):
    length = len(bytes)
    # We need an even number of bytes for this operation.
    assert ((length % 2) == 0)
    actual_length = int(length / 2)
    
    new_bytes = b''
    for i in range(actual_length):
        new_bytes += int.to_bytes(int(''.join(list(bin(bytes[i]).lstrip('0b').zfill(8))[:4] + list(bin(bytes[i+actual_length]).lstrip('0b').zfill(8))[:4]), 2), length=1, byteorder='big', signed=False)
    
    return new_bytes

# If this is executed as a script.
if (__name__ == '__main__'):
    with SIMPS() as device:
        #device.test()
        device.validate_communications()
