#!/usr/bin/env python

import curses
import time
import threading
import minidrone
import dronedict

right_events = [curses.KEY_RIGHT, curses.KEY_LEFT, curses.KEY_UP, curses.KEY_DOWN]
left_events = [ord('d'), ord('a'), ord('w'), ord('s')]

S_DISCONNECTED = 0
S_CONNECTING = 1
S_CONNECTED = 2

DRONEMAC = 'A0:14:3D:28:D6:A9'
CB_MSG = 0
CB_BATTERY = 1
CB_DATA_UPDATE = 2
CB_SPEED = 3
CB_STATE = 4

mutex = threading.Lock()

def refresh_data(t, data):
    global message, config, battery, speed, state
    if t == CB_MSG:
        mutex.acquire()
        message = data
        mutex.release()
    elif t == CB_BATTERY:
        mutex.acquire()
        battery = data
        mutex.release()
    elif t == CB_SPEED:
        mutex.acquire()
        speed = data
        mutex.release()
    elif t == CB_DATA_UPDATE:
        mutex.acquire()
        config = data
        mutex.release()
    elif t == CB_STATE:
        mutex.acquire()
        state = S_CONNECTED if data == 'y' else S_DISCONNECTED
        mutex.release()

def draw_joy(win):
    win.erase()
    for i in range(0, 5):
        win.addch(i, 5, '|')
    win.addstr(2, 0, '---- o ----')
    win.refresh()

def hl_dir(win, dir):
    if dir in [curses.KEY_UP, ord('w')]:
        for i in range(0, 2):
            win.chgat(i, 5, 1, curses.color_pair(1))
    elif dir in [curses.KEY_DOWN, ord('s')]:
        for i in range(3, 5):
            win.chgat(i, 5, 1, curses.color_pair(1))
    elif dir in [curses.KEY_LEFT, ord('a')]:
        win.chgat(2, 0, 4, curses.color_pair(1))
    elif dir in [curses.KEY_RIGHT, ord('d')]:
        win.chgat(2, 7, 4, curses.color_pair(1))
    win.chgat(2, 5, 1, curses.color_pair(2))
    win.refresh()

def move_drone(event):
    if event == ord(' '):
        drone.takeoff()
    elif event in [13, curses.KEY_ENTER]:
        drone.land()
    elif event == 27: # ESC
        drone.emergency()
    elif event == curses.KEY_UP:
        drone.ascend()
    elif event == curses.KEY_DOWN:
        drone.descend()
    elif event == curses.KEY_RIGHT:
        drone.turn_right()
    elif event == curses.KEY_LEFT:
        drone.turn_left()
    elif event == ord('w'):
        drone.move_fw()
    elif event == ord('s'):
        drone.move_bw()
    elif event == ord('d'):
        drone.move_right()
    elif event == ord('a'):
        drone.move_left()
    elif event == ord('+'):
        drone.incr_speed()
    elif event == ord('-'):
        drone.decr_speed()
    elif event == ord('x'):
        drone.disconnect()

def main_loop(stdscr):
    screen = curses.initscr()
    showing_info = False
    screen.timeout(100)
    win = screen.subwin(24, 80, 0, 0)
    curses.curs_set(0)
    curses.nonl()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    w_status = win.subwin(9, 80, 0, 0)
    w_help = win.subwin(6, 80, 18, 0)
    w_leftjoy = win.subwin(5, 11, 11, 13)
    w_rightjoy = win.subwin(5, 11, 11, 55)
    w_status.box()
    w_help.box()
    w_help.vline(1, 39, '|', 4)
    w_help.vline(1, 59, '|', 4)
    w_help.addstr(1, 2, "w-a-s-d: Move horizontally")
    w_help.addstr(1, 41, "Space: Take off")
    w_help.addstr(2, 41, "Enter: Land")
    w_help.addstr(1, 61, "Esc: Emergency")
    w_help.addstr(3, 2, "+/-: Incr/decr speed")
    w_help.addstr(2, 2, "Arrows: Move vertically & rotate")
    w_help.addstr(2, 61, "c: Connect")
    w_help.addstr(3, 61, "x: Disconnect")
    w_help.addstr(4, 61, "q: Quit")
    w_help.addstr(4, 2, "u: Update config")
    w_help.addstr(3, 41, "i: Toggle Wheels")
    w_help.addstr(4, 41, "o: Toggle CutOut")
    win.box()
    win.addstr(0, 25, " MiniDrone remote controller ")
    w_status.vline(1, 39, '|', 5)
    w_status.hline(6, 1, '-', 78)
    w_status.addstr(2, 2, "Battery: ")
    w_status.addstr(1, 2, "ID: ")
    w_status.addstr(1, 41, "Serial: ")
    w_status.addstr(2, 41, "FW/HW ver: ")
    w_status.addstr(3, 2, "Speed: ")
    w_status.addstr(3, 41, "Wheels/CutOut: ")
    w_status.addstr(4, 2, "MaxAlt: ")
    w_status.addstr(4, 41, "MaxTilt: ")
    w_status.addstr(5, 2, "MaxVert: ")
    w_status.addstr(5, 41, "MaxRot: ")
    w_status.addstr(7, 2, "Status: ")
    win.refresh()
    global state
    while True:
        mutex.acquire()
        s = state
        w_status.addstr(7, 10, message + (68-len(message))*' ')
        mutex.release()
        w_status.refresh()
        if s == S_DISCONNECTED:
            event = screen.getch()
            if event == ord('q'):
                break
            elif event == ord('c'):
                mutex.acquire()
                state = S_CONNECTING
                mutex.release()
                drone.connect()
        elif s == S_CONNECTING:
            curses.napms(50)
        elif s == S_CONNECTED:
            draw_joy(w_leftjoy)
            draw_joy(w_rightjoy)
            win.chgat(0, 26, 27, curses.color_pair(1))
            mutex.acquire()
            if len(config) >= 10:
                w_status.addstr(2, 11, battery + '%  ')
                w_status.addstr(3, 9, speed + '%  ')
                w_status.addstr(3, 56, dronedict.onoff(config['wheels']) + '/' + dronedict.onoff(config['cutout']) + '  ')
                w_status.addstr(1, 6, config['name'])
                w_status.addstr(1, 49, config['serial'])
                w_status.addstr(2, 52, config['fw'] + ', ' + config['hw'])
                w_status.addstr(4, 10, dronedict.get_pretty(config, dronedict.S_MAX_ALT) + '  ')
                w_status.addstr(4, 50, dronedict.get_pretty(config, dronedict.S_MAX_TILT) + '  ')
                w_status.addstr(5, 11, dronedict.get_pretty(config, dronedict.S_MAX_VERT) + '  ')
                w_status.addstr(5, 49, dronedict.get_pretty(config, dronedict.S_MAX_ROT) + '  ')
            mutex.release()
            w_status.refresh()
            event = screen.getch()
            if event == ord('q'):
                break
            move_drone(event)
            if event in right_events:
                hl_dir(w_rightjoy, event)
            elif event in left_events:
                hl_dir(w_leftjoy, event)
            elif event == ord('o'):
                drone.cutout(not config['cutout'])
            elif event == ord('i'):
                drone.wheels(not config['wheels'])
            curses.napms(70)

if __name__ == '__main__':
    global drone, state, message, config, speed, battery
    state = S_DISCONNECTED
    message = speed = battery = ''
    config = dict()
    drone = minidrone.MiniDrone(mac=DRONEMAC, callback=refresh_data)
    curses.wrapper(main_loop)
    drone.die()
    curses.curs_set(1)
    curses.nl()

