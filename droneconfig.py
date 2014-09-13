#!/usr/bin/env python

import ConfigParser

CONFIG_FILE = 'drone.conf'
SECTION = 'drone'
SPEED = 'speed'
MAX_ALT = 'max_altitude'
MAX_ROT_SPEED = 'max_rotation_speed'
MAX_TILT = 'max_tilt'
MAX_VERT_SPEED = 'max_vertical_speed'
WHEELS = 'wheels'

class C(object):

	def __init__(self):
		self.config = ConfigParser.ConfigParser()
		self.config.readfp(open(CONFIG_FILE))

	def flush(self):
		self.config.write(open(CONFIG_FILE, 'w'))

	def get_speed(self):
		return self.config.getint(SECTION, SPEED)

	def get_max_alt(self):
		return self.config.getfloat(SECTION, MAX_ALT)

	def get_max_rot_speed(self):
		return self.config.getfloat(SECTION, MAX_ROT_SPEED)

	def get_max_tilt(self):
		return self.config.getfloat(SECTION, MAX_TILT)

	def get_max_vert_speed(self):
		return self.config.getfloat(SECTION, MAX_VERT_SPEED)

	def get_wheels(self):
		return self.config.getboolean(SECTION, WHEELS)

	def set_speed(self, value):
		self.config.set(SECTION, SPEED, value)
		self.flush()

	def set_max_alt(self, value):
		self.config.set(SECTION, MAX_ALT, value)
		self.flush()

	def set_max_rot_speed(self, value):
		self.config.set(SECTION, MAX_ROT_SPEED, value)
		self.flush()

	def set_max_tilt(self, value):
		self.config.set(SECTION, MAX_TILT, value)
		self.flush()

	def set_max_vert_speed(self, value):
		self.config.set(SECTION, MAX_VERT_SPEED, value)
		self.flush()

	def set_wheels(self, value):
		self.config.set(SECTION, WHEELS, value)
		self.flush()
