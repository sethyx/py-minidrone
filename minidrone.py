#!/usr/bin/env python

import time
import pexpect
import threading
from Queue import Queue
import binascii
import os
import re
import struct
import droneconfig
import dronedict

# From https://standards.ieee.org/develop/regauth/oui/oui.txt
PARROT_OUIS = ['A0:14:3D', '00:12:1C', '00:26:7E', '90:03:B7']
P_MAC = '^([0-9A-F]{2}:){5}([0-9A-F]{2})$'
P_MAC_END = '(:[0-9A-F]{2}){3}'
P_OUIS = ['{0}{1}'.format(oui, P_MAC_END) for oui in PARROT_OUIS]


lock = threading.Lock() # need to add this to r/w

class S:
    Disconnected, Init, Connected, Error = range(4)
    
class Base:
    FlatTrim, TakeOff, Land = range(3)

class Cmd:
    def __init__(self, handle, value, response=False):
        self.handle = handle
        self.value = value
        self.response = response

class StoppableThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()

    def stop(self):
        if self.isAlive():
            self.stop_event.set()

class ReaderThread(StoppableThread):
    def __init__(self, drone, pexp):
        StoppableThread.__init__(self)
        self.drone = drone
        self.reader = pexp
        
    def run(self):
        patterns = self.reader.compile_pattern_list([dronedict.P_NOTIFICATION, dronedict.P_BATTERY, dronedict.P_CONNECTED, pexpect.TIMEOUT, pexpect.EOF])
        while True:
            if not self.stop_event.is_set():
                index = self.reader.expect_list(patterns, timeout=30)
                if index == 0:
                    self.drone.send(self.drone.send_ack, self.reader.after.split(' ')[3])
                    dronedict.process_notification(self.drone, self.reader.after)
                elif index == 1:
                    dronedict.process_battery(self.drone, self.reader.after)
                elif index == 2:
                    self.drone.cb(4, 'y')
                    self.drone.cb(3, str(self.drone.speed))
                elif index > 2:
                    self.drone.cb(4, 'n')
            else:
                self.reader.terminate(True)
                break

class WriterThread(StoppableThread):

    def __init__(self, drone):
        StoppableThread.__init__(self)
        self.drone = drone
        self.gatt = pexpect.spawn(drone.gatttool_path + ' -b ' + drone.mac + ' -I -t random', echo=False)
        self.t_reader = ReaderThread(drone, self.gatt)
        self.t_reader.daemon = True

    def run(self):
        self.t_reader.start()
        while True:
            if self.stop_event.is_set() and self.drone.q.empty():
                self.drone.q.join()
                self.gatt.sendeof()
                self.gatt.terminate(True)
                self.t_reader.stop()
                self.t_reader.join()
                break
            else:
                cmd = self.drone.q.get()
                if "connect" in cmd.handle:
                    self.gatt.sendline(cmd.handle)
                    self.drone.q.task_done()
                    continue
                if not cmd.response:
                    self.gatt.sendline(" ".join(["char-write-cmd", cmd.handle, cmd.value]))
                else:
                    self.gatt.sendline(" ".join(["char-write-req", cmd.handle, cmd.value]))
                self.drone.q.task_done()

class MiniDrone(object):

    def __init__(self, mac=None, callback=None):
        self.mac = mac
        self.callback = callback
        req_missing = self.req_check()
        if req_missing:
            self.cb(0, req_missing)
            return
        self.seq_joy = 1 # 0x0040
        self.seq_ref = 0 # 0x0043
        self.timer_t = 0.3
        self.settings = dict()
        self.speed = 30
        self.status = S.Disconnected
        self.q = Queue()
        self.t_writer = WriterThread(self)
        self.t_writer.daemon = True
        self.wd_timer = threading.Timer(self.timer_t, self.still)

    def cb(self, *args, **kwargs):
        if self.callback:
            self.callback(*args, **kwargs)

    def req_check(self):
        # check pexpect

        # check BlueZ
        self.gatttool_path = pexpect.which('gatttool')
        if not self.gatttool_path:
            return "Please install the BlueZ stack: 'apt-get install bluez'"

        # if there is no MAC set, try to search for a drone (requires root)
        if not self.mac:
            if os.geteuid() != 0:
                return "Drone MAC missing. Init with 'mac=' or run as root to scan."
            lescan = pexpect.spawn("hcitool lescan", echo=False)
            index = lescan.expect(P_OUIS, timeout=5)
            if index != 0:
                return "Couldn't find any drones nearby."
            self.mac = lescan.after
            self.cb(0, "Drone found! MAC: " + self.mac)

        elif not re.match(P_MAC, self.mac):
            return "Drone MAC format incorrect, please check it. Format: XX:XX:XX:XX:XX:XX"

        self.cb(0, "Everything seems to be alright, time to fly!")
        return None

    def die(self):
        self.wd_timer.cancel()
        self.disconnect()
        if self.t_writer.is_alive():
            self.t_writer.stop()
            self.t_writer.join()
        self.cb(0, "Connection closed.")
        self.status = S.Disconnected
    
    def connect(self):
        self.cb(0, "Connecting to drone...")
        self.t_writer.start()
        self.low_level('connect', '')
        time.sleep(1)
        self.status = S.Init
        self.send(self.send_init)
    
    def disconnect(self):
        self.cb(0, "Disconnecting...")
        self.low_level('disconnect', '')

    def ascend(self):
        self.send(self.send_joy, 0, 0, 0, self.speed)

    def descend(self):
        self.send(self.send_joy, 0, 0, 0, -self.speed)

    def turn_left(self):
        self.send(self.send_joy, 0, 0, -self.speed, 0)

    def turn_right(self):
        self.send(self.send_joy, 0, 0, self.speed, 0)

    def move_fw(self):
        self.send(self.send_joy, 0, self.speed, 0, 0)

    def move_bw(self):
        self.send(self.send_joy, 0, -self.speed, 0, 0)

    def move_right(self):
        self.send(self.send_joy, self.speed, 0, 0, 0)

    def move_left(self):
        self.send(self.send_joy, -self.speed, 0, 0, 0)

    def still(self):
        self.send(self.send_joy, 0, 0, 0, 0)

    def incr_speed(self):
        if self.speed < 100:
            self.speed += 10
        self.cb(3, str(self.speed))

    def decr_speed(self):
        if self.speed > 0:
            self.speed -= 10
        self.cb(3, str(self.speed))

    def takeoff(self):
        self.cb(0, "Taking off!")
        self.send(self.send_ref, Base.FlatTrim)
        time.sleep(0.5)
        self.send(self.send_ref, Base.TakeOff)
        self.cb(0, "Airborne!")

    def land(self):
        self.cb(0, "Landing!")
        self.send(self.send_ref, Base.Land)
        time.sleep(1)
        self.cb(0, "Back to the ground.")

    def emergency(self):
        self.cb(0, "Emergency signal sent!")
        self.send(self.send_ref, None, True)

    def setup_time(self):
        times = time_bin()
        for i in range(1, 3):
            self.send_ref('0004' + ('%02x' % i) + '00' + times[i-1] + '00')

    def wheels(self, wheels):
        self.send_ref('02010200' + ('01' if wheels else '00'))

    def cutout(self, cutout):
        self.send_ref('020a0000' + ('01' if cutout else '00'))

    def send_joy(self, hor_lr, hor_fb, rot, vert):
        handle = '0x0040'
        value = '02' + \
                sq2b(self.seq_joy) + \
                '02000200' + \
                merge_moves(hor_lr, hor_fb, rot, vert) + \
                '00000000'
        self.low_level(handle, value)
        self.seq_joy += 1

    def send_ref(self, t, emergency=False):
        if not emergency:
            handle = '0x0043'
            self.seq_ref += 1
        else:
            handle = '0x0046'
        value = '04' + ('%02x' % self.seq_ref)
        if t == Base.FlatTrim:
            value += '02000000'
        elif t == Base.TakeOff:
            value += '02000100'
        elif t == Base.Land:
            value += '02000300'
        elif emergency:
            value += '02000400'
        else:
            value += t
        self.low_level(handle, value)

    def send_init(self):
        self.cb(0, "Initializing...")
        switch = '0100'
        self.low_level('0x00c0', switch, True)
        self.low_level('0x00bd', switch, True)
        self.low_level('0x00e4', switch, True)
        self.low_level('0x00e7', switch, True)
        self.low_level('0x0116', switch)
        self.low_level('0x0126', switch)
        self.setup_time()
        time.sleep(1.2)
        self.send_ref('00020000')
        time.sleep(1.2)
        self.send_ref('00040000')
        time.sleep(2)
        self.wheels(True)
        self.cutout(True)

    def send_ack(self, seq):
        handle = '0x007c'
        value = '01' + seq + seq
        self.low_level(handle, value)

    def send(self, cmd, *args, **kwargs):
        self.wd_timer.cancel()
        cmd(*args, **kwargs)
        self.wd_timer = threading.Timer(self.timer_t, self.still)
        self.wd_timer.start()

    def low_level(self, handle, value, response=False):
        self.q.put(Cmd(handle, value, response))

def sq2b(seq): # we need the last 8 bits only
    return '%02x' % (seq & 0b0000000011111111)

def sp2b(speed): # 0-100
    return '%02x' % (speed & 0b11111111)

def time_bin():
    return [binascii.hexlify(t) for t in time.strftime("%Y-%m-%d|T%H%M%S%z", time.localtime()).split('|')]

def merge_moves(hor_lr, hor_fb, rot, vert):
    t = '01' if (hor_lr != 0 or hor_fb != 0) else '00'
    return t + sp2b(hor_lr) + sp2b(hor_fb) + sp2b(rot) + sp2b(vert)

def config_value(type, seq, value):
    result = "04" + seq
    if type == droneconfig.MAX_ALT:
        result += "02080000" + val2hexs(value)
    elif type == droneconfig.MAX_TILT:
        result += "02080100" + val2hexs(value)
    elif type == droneconfig.MAX_VERT_SPEED:
        result += "02010000" + val2hexs(value)
    elif type == droneconfig.MAX_ROT_SPEED:
        result += "02010100" + val2hexs(value)
    return result
