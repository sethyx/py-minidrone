#!/usr/bin/env python
# -*- coding: utf-8 -*-

import binascii
import re
import struct

#### INCOMING NOTIFICATIONS

P_BATTERY = '0x00bf value:[0-9a-f ]+\r\n'
P_NOTIFICATION = '0x00bc value:[0-9a-f ]+\r\n'
P_CONNECTED = 'Connection successful'

P_NAME = '04 .. 00 03 02 00 [0-9a-f ]+ 00'
P_SERIALP1 = '04 .. 00 03 04 00 [0-9a-f ]+ 00'
P_SERIALP2 = '04 .. 00 03 05 00 [0-9a-f ]+ 00'
P_FW_HW = '04 .. 00 03 03 00 [0-9a-f ]+ 00 [0-9a-f ]+ 00'

P_PILOT_WHEELS_IN = '04 .. 02 05 02 00 [0-9a-f ]+'
P_PILOT_CUTOUT_IN = '04 .. 02 0b 02 00 [0-9a-f ]+'
P_PILOT_MAXVERT_IN = '04 .. 02 05 00 00 [0-9a-f ]+'
P_PILOT_MAXROT_IN = '04 .. 02 05 01 00 [0-9a-f ]+'
P_PILOT_MAXALT_IN = '04 .. 02 09 00 00 [0-9a-f ]+'
P_PILOT_MAXTILT_IN = '04 .. 02 09 01 00 [0-9a-f ]+'

#### OUTGOING MESSAGES

#### OTHER CONSTANTS, UNITS
S_NAME = 'name'
S_SERIAL = 'serial'
S_FW = 'fw'
S_HW = 'hw'
S_MAX_VERT = 'max_vert'
S_MAX_ROT = 'max_rot'
S_MAX_ALT = 'max_alt'
S_MAX_TILT = 'max_tilt'
S_WHEELS = 'wheels'
S_CUTOUT = 'cutout'

C_ON = 'On'
C_OFF = 'Off'
C_CONN_OK = 'Connection estabilished. Have fun!'

UNITS = {S_MAX_VERT:'m/s', S_MAX_ROT:'°/s', S_MAX_ALT:'m', S_MAX_TILT:'°'}

def process_battery(drone, value):
    drone.battery = str(int(value.split(' ')[-2], 16))
    drone.cb(1, drone.battery)

def process_notification(drone, value):
    ## Process drone information
    if re.search(P_NAME, value):
        drone.settings[S_NAME] = get_init_info(value)
    elif re.search(P_SERIALP1, value):
        drone.settings[S_SERIAL] = get_init_info(value)
    elif re.search(P_SERIALP2, value):
        drone.settings[S_SERIAL] = drone.settings[S_SERIAL] + get_init_info(value)
    elif re.search(P_FW_HW, value):
        (drone.settings[S_FW], drone.settings[S_HW]) = get_init_info(value.replace('00', '7c')).split('|')
        drone.cb(0, C_CONN_OK)
    ## Process piloting settings
    elif re.search(P_PILOT_MAXVERT_IN, value):
        drone.settings[S_MAX_VERT] = get_current_setting(value)
    elif re.search(P_PILOT_MAXROT_IN, value):
        drone.settings[S_MAX_ROT] = get_current_setting(value)
    elif re.search(P_PILOT_MAXALT_IN, value):
        drone.settings[S_MAX_ALT] = get_current_setting(value)
    elif re.search(P_PILOT_MAXTILT_IN, value):
        drone.settings[S_MAX_TILT] = get_current_setting(value)
    elif re.search(P_PILOT_WHEELS_IN, value):
        drone.settings[S_WHEELS] = get_misc(value)
    elif re.search(P_PILOT_CUTOUT_IN, value):
        drone.settings[S_CUTOUT] = get_misc(value)
    drone.cb(2, drone.settings)


def get_init_info(pattern):
    return binascii.unhexlify(''.join(pattern.split(' ')[8:][:-2]))

def get_current_setting(pattern):
    return hex2vals(''.join(pattern.split(' ')[9:12]))

# We don't use the minimum or maximum values currently, these can be implemented for safety checks though.
# def get_min_setting(pattern):
#     return hex2vals(''.join(pattern.split(' ')[13:16]))
#
# def get_max_setting(pattern):
#     return hex2vals(''.join(pattern.split(' ')[17:20]))

def get_misc(pattern):
    return True if pattern.split(' ')[-2] == '01' else False

def val2hexs(f_val):
   return format(struct.unpack('<I', struct.pack('!f', f_val))[0], '08x')

def hex2vals(x_val):
   return format(struct.unpack('!f', struct.pack('<I', int(x_val, 16)))[0], '.2f')

def onoff(b):
    return C_ON if b else C_OFF

def get_pretty(conf, setting):
    if setting == S_WHEELS or setting == S_CUTOUT:
        return onoff(conf[setting])
    else:
        return conf[setting] + ' ' + UNITS[setting]