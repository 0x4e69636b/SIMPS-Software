#!/bin/env python3
# -*- coding: utf-8 -*-

import argparse

from libsimp import SIMPS, WAVEFORM_SAMPLES_PER_PERIOD, POWERSUPPLY_MIN, POWERSUPPLY_MAX, MEASUREMENT_SAMPLES, MEASUREMENT_PERIODS


def cli():
    #from pyfiglet import Figlet
    #fig = Figlet(font='slant')
    #header = fig.renderText('SIMPS ATE')
    
    header = ('   _____ ______  _______  _____    ___  ____________\n'
    + '  / ___//  _/  |/  / __ \\/ ___/   /   |/_  __/ ____/\n'
    + '  \\__ \\ / // /|_/ / /_/ /\\__ \\   / /| | / / / __/   \n'
    + ' ___/ // // /  / / ____/___/ /  / ___ |/ / / /___   \n'
    + '/____/___/_/  /_/_/    /____/  /_/  |_/_/ /_____/   \n')
    
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='Command line interface for the\n'+header)
    subparsers = parser.add_subparsers(help='sub-command help', dest='action')
    
    sub_program = subparsers.add_parser('program', help='program the device')
    sub_program.add_argument('-p', '--ps_voltage', type=int, help='powersupply voltage; 0-60V', required=True)
    sub_program.add_argument('-w', '--waveform', type=int, nargs=WAVEFORM_SAMPLES_PER_PERIOD, metavar='P', help='waveform period values', required=True)
    sub_program.add_argument('-f', '--frequency', type=int, help='waveform frequency; 1-2,000,000Hz', required=True)
    sub_program.add_argument('-r', '--range', type=int, choices=range(1,5), help='measurement voltage range; 1:0-4V, 2:4-10V, 3:10-20V, 4:20-60V', required=True)
    sub_program.set_defaults(func=device_action)
    
    sub_ps = subparsers.add_parser('ps', help='powersupply options')
    group_ps = sub_ps.add_mutually_exclusive_group(required=True)
    group_ps.add_argument('--enable', action='store_true', help='enable the powersupply')
    group_ps.add_argument('--disable', action='store_true', help='disable the powersupply')
    group_ps.add_argument('-s', '--set_voltage', metavar='voltage', type=lambda x: restricted_float(x, POWERSUPPLY_MIN, POWERSUPPLY_MAX), help='set power supply; %r-%rV' % (POWERSUPPLY_MIN, POWERSUPPLY_MAX))
    sub_ps.set_defaults(func=device_action)
    
    sub_fg = subparsers.add_parser('fg', help='function generator options')
    group_fg = sub_fg.add_mutually_exclusive_group(required=True)
    group_fg.add_argument('--enable', action='store_true', help='enable the function generator')
    group_fg.add_argument('--disable', action='store_true', help='disable the function generator')
    sub_fg.set_defaults(func=device_action)
    
    sub_me = subparsers.add_parser('measurement', help='measurement options')
    group_me = sub_me.add_mutually_exclusive_group(required=True)
    group_me.add_argument('-g', '--get_range', action='store_true', help='get the devices current range')
    group_me.add_argument('-r', '--range', type=int, choices=range(1,5), help='set measurement range; 1:0-4V, 2:4-10V, 3:10-20V, 4:20-60V')
    group_me.add_argument('-t', '--take_measurement', action='store_true', help='take a measurement')
    sub_me.set_defaults(func=device_action)
    
    sub_mo = subparsers.add_parser('mode', help='mode options')
    sub_mo.add_argument('-g', '--get-mode', action='store_true', help='get the devices current mode of operation', required=True)
    sub_mo.set_defaults(func=device_action)
    
    sub_verification = subparsers.add_parser('debug', help='debug the device')
    group_verification = sub_verification.add_mutually_exclusive_group(required=True)
    group_verification.add_argument('-v', '--validate_communications', action='store_true', help='validate communications with the FPGA')
    sub_verification.set_defaults(func=device_action)
    
    #parser.add_argument('waveform_values', metavar='V', type=int, nargs='+', help='an integer for the accumulator')
    #parser.add_argument('--sum', dest='accumulate', action='store_const', const=sum, default=max, help='sum the integers (default: find the max)')
    
    args = parser.parse_args()
    if args.action: args.func(args)
    else: parser.print_help()

def restricted_float(x, min, max):
    try:
        x = float(x)
    except ValueError:
        raise argparse.ArgumentTypeError('%r not a floating-point literal' % (x,))
    if (x < float(min)) or (x > float(max)):
        raise argparse.ArgumentTypeError('%r not in range [%r, %r]' % (x, min, max))
    return x

def device_action(args):
    with SIMPS() as device:
        if (args.action == 'ps') and (args.enable == True):
            device.enable_ps()
        elif (args.action == 'ps') and (args.disable == True):
            device.disable_ps()
        elif (args.action == 'fg') and (args.enable == True):
            device.enable_fg()
        elif (args.action == 'fg') and (args.disable == True):
            device.disable_fg()
        elif (args.action == 'measurement') and (args.range != None):
            device.set_range(args.range)
        elif (args.action == 'measurement') and (args.get_range == True):
            print('The SIMPS ATE device is in measurement range %i.' % device.get_range())
        elif (args.action == 'debug') and (args.validate_communications == True):
            device.validate_communications()
        elif (args.action == 'mode'):
            print('The SIMPS ATE device is operating in the %s mode.' % device.get_mode())
        elif (args.action == 'ps') and (args.set_voltage != None):
            device.set_ps(args.set_voltage)
        elif (args.action == 'program'):
            device.program(args.ps_voltage, args.frequency, args.waveform, args.range)
        elif (args.action == 'measurement') and (args.take_measurement == True):
            fg_measurements, dut_measurements, ps_voltage = device.measurement()
            print('\n----- Current power supply voltage: %r' % ps_voltage)
            print('\n----- DUT measurements:')
            for i in range(MEASUREMENT_SAMPLES*MEASUREMENT_PERIODS):
                print('\t%i: %r' % (i, round(dut_measurements[i], 4)))
            print('\n----- Function generator measurements:')
            for i in range(MEASUREMENT_SAMPLES*MEASUREMENT_PERIODS):
                print('\t%i: %r' % (i, round(fg_measurements[i], 4)))

if (__name__ == '__main__'):
    cli()