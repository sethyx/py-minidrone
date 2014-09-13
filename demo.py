#!/usr/bin/env python

import curses
import time
import threading
import minidrone

right_events = [curses.KEY_RIGHT, curses.KEY_LEFT, curses.KEY_UP, curses.KEY_DOWN]
left_events = [ord('d'), ord('a'), ord('w'), ord('s')]

S_DISCONNECTED = 0
S_CONNECTING = 1
S_CONNECTED = 2

DRONEMAC = 'A0:14:3D:28:D6:A9'
CB_MSG = 0
CB_BATTERY = 1
CB_ID = 2
CB_SERIAL = 3
CB_FW_HW = 4
CB_STATE = 5
CB_SPEED = 6
CB_WHEELS = 7

mutex = threading.Lock()

def refresh_data(t, msg):
    global message, battery, did, serial, fw, hw, state, speed, wheels
    if t == CB_MSG:
        mutex.acquire()
        message = msg
        mutex.release()
    elif t == CB_BATTERY:
        mutex.acquire()
        battery = msg
        mutex.release()
    elif t == CB_ID:
        mutex.acquire()
        did = msg
        mutex.release()
    elif t == CB_FW_HW:
        mutex.acquire()
        (fw, hw) = msg.split('|')
        mutex.release()
    elif t == CB_STATE:
        mutex.acquire()
        state = S_CONNECTED if msg == 'y' else S_DISCONNECTED
        mutex.release()
    elif t == CB_SERIAL:
        mutex.acquire()
        serial = msg
        mutex.release()
    elif t == CB_SPEED:
        mutex.acquire()
        speed = msg
        mutex.release()
    elif t == CB_WHEELS:
        mutex.acquire()
        wheels = msg
        mutex.release()

def draw_joy(win):
    win.erase()
    for i in range(0, 7):
        win.addch(i, 7, '|')
    win.addstr(3, 1, '----- o -----')
    win.refresh()

def hl_dir(win, dir):
    if dir in [curses.KEY_UP, ord('w')]:
        for i in range(0, 3):
            win.chgat(i, 7, 1, curses.color_pair(1))
    elif dir in [curses.KEY_DOWN, ord('s')]:
        for i in range(4, 7):
            win.chgat(i, 7, 1, curses.color_pair(1))
    elif dir in [curses.KEY_LEFT, ord('a')]:
        win.chgat(3, 1, 5, curses.color_pair(1))
    elif dir in [curses.KEY_RIGHT, ord('d')]:
        win.chgat(3, 9, 5, curses.color_pair(1))
    win.chgat(3, 7, 1, curses.color_pair(2))
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
    w_status = win.subwin(7, 80, 0, 0)
    w_help = win.subwin(5, 80, 19, 0)
    w_leftjoy = win.subwin(7, 15, 9, 12)
    w_rightjoy = win.subwin(7, 15, 9, 52)
    w_status.box()
    w_help.box()
    w_help.vline(1, 39, '|', 3)
    w_help.vline(1, 59, '|', 3)
    w_help.addstr(1, 2, "W-A-S-D: Move horizontally")
    w_help.addstr(1, 41, "Space: Take off")
    w_help.addstr(2, 41, "Enter: Land")
    w_help.addstr(3, 41, "Emergency: Esc")
    w_help.addstr(3, 2, "+/-: Incr/decr speed")
    w_help.addstr(2, 2, "Arrows: Move vertically & rotate")
    w_help.addstr(1, 61, "Connect: c")
    w_help.addstr(2, 61, "Disconnect: x")
    w_help.addstr(3, 61, "Quit: q")
    win.box()
    win.addstr(0, 25, " MiniDrone remote controller ")
    w_status.vline(1, 39, '|', 3)
    w_status.hline(4, 1, '-', 78)
    w_status.addstr(2, 2, "Battery: ")
    w_status.addstr(1, 2, "ID: ")
    w_status.addstr(1, 41, "Serial: ")
    w_status.addstr(2, 41, "FW/HW ver: ")
    w_status.addstr(3, 2, "Speed: ")
    w_status.addstr(3, 41, "Wheels: ")
    w_status.addstr(5, 2, "Status: ")
    win.refresh()
    global state
    while True:
        mutex.acquire()
        s = state
        w_status.addstr(5, 10, message + (68-len(message))*' ')
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
            w_status.addstr(2, 11, battery + '%  ')
            w_status.addstr(3, 9, speed + '%  ')
            w_status.addstr(3, 49, wheels + '  ')
            w_status.addstr(1, 6, did)
            w_status.addstr(1, 49, serial)
            w_status.addstr(2, 52, fw + ', ' + hw)
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
            curses.napms(70)

if __name__ == '__main__':
    global state, message, battery, drone, did, fw, hw, serial
    state = S_DISCONNECTED
    battery = did = fw = hw = serial = message = ''
    drone = minidrone.MiniDrone(mac=DRONEMAC, callback=refresh_data)
    curses.wrapper(main_loop)
    drone.die()
    curses.curs_set(1)
    curses.nl()

