#!/bin/env python3
# -*- coding: utf-8 -*-


from libsimp import SIMPS


# Functions that are exposed to LabVIEW.

# How long to wait for a FTDI driver lock.
CONNECT_TIMEOUT = 5

# Get the mode.
def get_mode():
    with SIMPS(connect_timeout=CONNECT_TIMEOUT) as device:
        mode = device.get_mode()
    return mode

# Program the device.
def program(ps_voltage, frequency, waveform_table, _range):
    with SIMPS(connect_timeout=CONNECT_TIMEOUT) as device:
        device.program(ps_voltage, frequency, waveform_table, _range)

def start_measurement():
    with SIMPS(connect_timeout=CONNECT_TIMEOUT) as device:
        fg_measurements, dut_measurements, ps_voltage = device.measurement()
    return (fg_measurements, dut_measurements, ps_voltage)

# Disable the Power Supply
def disable_ps():
    with SIMPS(connect_timeout=CONNECT_TIMEOUT) as device:
        device.disable_ps()

# Enable the Power Supply
def enable_ps():
    with SIMPS(connect_timeout=CONNECT_TIMEOUT) as device:
        device.enable_ps()

# Disable the Function Generator
def disable_fg():
    with SIMPS(connect_timeout=CONNECT_TIMEOUT) as device:
        device.disable_fg()

# Enable the Function Generator
def enable_fg():
    with SIMPS(connect_timeout=CONNECT_TIMEOUT) as device:
        device.enable_fg()

# Set the Power Supplys Value
def set_ps(ps_voltage):
    with SIMPS(connect_timeout=CONNECT_TIMEOUT) as device:
        device.set_ps(ps_voltage)

#def get_ps():
#    with SIMPS(connect_timeout=CONNECT_TIMEOUT) as device:
#        device.get_ps()

# Get the devices current Range.
def get_range():
    with SIMPS(connect_timeout=CONNECT_TIMEOUT) as device:
        range = device.get_range()
    return range

# Set the Measurement Range
def set_range(_range):
    with SIMPS(connect_timeout=CONNECT_TIMEOUT) as device:
        device.set_range(_range)

#def get_updated_values():
#    with SIMPS(connect_timeout=CONNECT_TIMEOUT) as device:
#        mode = device.get_mode()
#        #ps_voltage = device.get_ps()
#        range = device.get_range()
#    return mode, range # ps_voltage)