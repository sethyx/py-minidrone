#!/usr/bin/env python

import binascii
import re

P_BATTERY = '0x00bf value:[0-9a-f ]+\r\n'
P_NOTIFICATION = '0x00bc value:[0-9a-f ]+\r\n'
P_CONNECTED = 'Connection successful'

P_ID = '04 03 00 03 02 00 [0-9a-f ]+ 00'
P_SERIALP1 = '04 04 00 03 04 00 [0-9a-f ]+ 00'
P_SERIALP2 = '04 05 00 03 05 00 [0-9a-f ]+ 00'
P_FW_HW = '04 06 00 03 03 00 [0-9a-f ]+ 00 [0-9a-f ]+ 00'

P_WHEELS = '04 ..'
P_PILOT_SETTINGS = ''

def process_battery(drone, value):
    drone.battery = str(int(value.split(' ')[-2], 16))
    drone.cb(1, drone.battery)

def process_notification(drone, value):
    if re.search(P_ID, value):
        drone.settings['name'] = get_init_info(value)
    elif re.search(P_SERIALP1, value):
        drone.settings['serial'] = get_init_info(value)
    elif re.search(P_SERIALP2, value):
        drone.settings['serial'] = drone.settings['serial'] + get_init_info(value)
    elif re.search(P_FW_HW, value):
        (drone.settings['fw'], drone.settings['hw']) = get_init_info(value.replace('00', '7c')).split('|')
        drone.cb(0, "Connection estabilished. Have fun!")
    drone.cb(2, drone.settings)
        
def get_init_info(pattern):
    return binascii.unhexlify(''.join(pattern.split(' ')[8:][:-2]))