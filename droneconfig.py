#!/usr/bin/env python

import ConfigParser
import dronedict

CONFIG_FILE = 'drone.conf'
SECTION = 'drone'

class C(object):

	def __init__(self):
		self.config = ConfigParser.ConfigParser()
		self.config.readfp(open(CONFIG_FILE))

	def flush(self):
		self.config.write(open(CONFIG_FILE, 'w'))

	def get_max_alt(self):
		return self.config.getfloat(SECTION, dronedict.S_MAX_ALT)

	def get_max_rot_speed(self):
		return self.config.getfloat(SECTION, dronedict.S_MAX_ROT)

	def get_max_tilt(self):
		return self.config.getfloat(SECTION, dronedict.S_MAX_TILT)

	def get_max_vert_speed(self):
		return self.config.getfloat(SECTION, dronedict.S_MAX_VERT)

	def get_wheels(self):
		return self.config.getboolean(SECTION, dronedict.S_WHEELS)

	def get_cutoff(self):
		return self.config.getboolean(SECTION, dronedict.S_CUTOUT)

	def set_max_alt(self, value):
		self.config.set(SECTION, dronedict.S_MAX_ALT, value)
		self.flush()

	def set_max_rot_speed(self, value):
		self.config.set(SECTION, dronedict.S_MAX_ROT_SPEED, value)
		self.flush()

	def set_max_tilt(self, value):
		self.config.set(SECTION, dronedict.S_MAX_TILT, value)
		self.flush()

	def set_max_vert_speed(self, value):
		self.config.set(SECTION, dronedict.S_MAX_VERT_SPEED, value)
		self.flush()

	def set_wheels(self, value):
		self.config.set(SECTION, dronedict.S_WHEELS, value)
		self.flush()

	def set_cutoff(self, value):
		self.config.set(SECTION, dronedict.S_CUTOUT, value)
		self.flush()
