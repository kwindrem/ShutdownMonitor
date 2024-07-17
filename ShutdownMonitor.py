#!/usr/bin/env python

# This program creates and monitors a dBus service to trigger a system shutdown
# The com.victronenergy.shutdown service is created and contains one parameter: /Shutdown
# /Shutdown is normally 0 but if this program detects a value other than 0,
# the system shutdown -h now call is made

# it also reads a GPIO pin on Raspberry Pi platforms
#	if that pin goes low the system is a shutdown
#	a switch in Settings enables this input so it doesn't cause unintended shutdowns
#	

import platform
import argparse
import logging
import sys
import os
import time
import re
import dbus
from gi.repository import GLib
# add the path to our own packages for import
sys.path.insert(1, "/data/SetupHelper/velib_python")
from vedbus import VeDbusService
from settingsdevice import SettingsDevice

ShutdownServiceName = 'com.victronenergy.shutdown'

# These methods permit creation of a separate connection for each Repeater
# overcoming the one service per process limitation
# requires updated vedbus, originally obtained from https://github.com/victronenergy/dbus-digitalinputs
# updates are incorporated in the ext directory of this package

class SystemBus(dbus.bus.BusConnection):
	def __new__(cls):
		return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SYSTEM)

class SessionBus(dbus.bus.BusConnection):
	def __new__(cls):
		return dbus.bus.BusConnection.__new__(cls, dbus.bus.BusConnection.TYPE_SESSION)

def dbusconnection():
	return SessionBus() if 'DBUS_SESSION_BUS_ADDRESS' in os.environ else SystemBus()


class Monitor:

	DbusService = None

	DbusBus = None

	# read the GPIO pin and detect tansition to active
	# only the TRANSITION causes action

	def detectPinActiveTransition (self):
		transitionDetected = False
		if self.ShutdownPinPresent:
			pinFile = "/sys/class/gpio/gpio16/value"
			if os.path.isfile (pinFile):
				file = open (pinFile, 'r')
				state = file.readline ().strip()
				state = int (state)
				if state == 0:
					# log pin stuck warning after 2 minutes in active state
					if self.externalPinActiveCount == 120:
						logging.warning ("external shutdown pin appars to be stuck active low")
					if self.externalPinActiveCount <= 120:
						self.externalPinActiveCount += 1
				else:
					self.externalPinActiveCount = 0
				# pint must be active for 3 passes (3 seconds)
				if self.externalPinActiveCount == 3:
					return True
		else:
			return False

	def __init__(self):

		# if this is a Raspberry PI, enable the shutdown pin
		platformFile = "/etc/venus/machine"
		try:
			file = open (platformFile, 'r')
		except:
			self.ShutdownPinPresent = False
		else:
			Platform = file.readline().strip()
			if Platform[0:4] == 'rasp':
				self.ShutdownPinPresent = True
			else:
				self.ShutdownPinPresent = False
			file.close()

		# set up unique dBus connection and dBus service
		self.DbusBus = dbusconnection()
		self._createDbusService()

		# initialize active pin count to one more than the treshold
		# so a stuck pin doesn't immediately trigger shutdown
		# a stuck pin warning is output after 2 minutes
		# then the counter is never incremented again
		# once the pin returns to inactive, normal behavior returns
		self.externalPinActiveCount = 4

		GLib.timeout_add (1000, self._background)
		return None

	# flag value change from external source
	def _handlechangedvalue (self, path, value):
		if value == 1:
			logging.info ("User shutdown received from GUI - shutting down system")
			os.system ("shutdown -h now")
		return True

	def _background (self):
 
		# if shutdown pin was enabled in the GUI

		# always read the pin so we have the correct state when
		# the external switch is enabled
		transition = self.detectPinActiveTransition ()

		# if shutdown pin is enabled in the GUI and a transition to active just occurred, trigger shutdown
		if self.DbusSettings['externalSwitch'] == 1 and transition:
			logging.critical ("User shutdown received from GPIO 16 (pin 36) - shutting down system")
			os.system ("shutdown -h now")
 
		self.DbusService['/Shutdown'] = 0
		return True

	def _createDbusService (self):

		# updated version of VeDbusService (in ext directory) -- see https://github.com/victronenergy/dbus-digitalinputs for new imports
		self.DbusService = VeDbusService (ShutdownServiceName, bus = self.DbusBus)

		# Create the objects

		self.DbusService.add_path ('/Mgmt/ProcessName', __file__)
		self.DbusService.add_path ('/Mgmt/ProcessVersion', '1.0')
		self.DbusService.add_path ('/Mgmt/Connection', 'dBus')

		self.DbusService.add_path ('/DeviceInstance', 0)
		self.DbusService.add_path ('/ProductName', "ShutdownMonitor")
		self.DbusService.add_path ('/ProductId', 0)
		self.DbusService.add_path ('/FirmwareVersion', 0)
		self.DbusService.add_path ('/HardwareVersion', 0)
		self.DbusService.add_path ('/Serial', '')
		# use numeric values (1/0) not True/False for /Connected to make GUI display correct state
		self.DbusService.add_path ('/Connected', 1)
		# indicates to the GUI that it can show the RPI shutdown pin control
		self.DbusService.add_path ('/ExtShutdownPresent', 0)

		# GUI sets this to initialte shutdown
		self.DbusService.add_path ('/Shutdown', 0, writeable = True, onchangecallback = self._handlechangedvalue)

		# create the setting that allows enabling the RPI shutdown pin
		settingsList = {'externalSwitch': [ '/Settings/ShutdownMonitor/ExternalSwitch', 0, 0, 0 ],
						}
		self.DbusSettings = SettingsDevice(bus=dbus.SystemBus(), supportedSettings=settingsList,
								timeout = 10, eventCallback=None )

		# enable the shutdown pin only if on a Raspberry PI
		if self.ShutdownPinPresent:
			self.DbusService['/ExtShutdownPresent'] = 1

		return


def main():

	from dbus.mainloop.glib import DBusGMainLoop

	global TheBus

	# set logging level to include info level entries
	logging.basicConfig(level=logging.INFO)

	# Have a mainloop, so we can send/receive asynchronous calls to and from dbus
	DBusGMainLoop(set_as_default=True)

	logging.info (">>>>>>>>>>>>>>>> Shutdown Monitor Starting <<<<<<<<<<<<<<<<")

	Monitor ()

	mainloop = GLib.MainLoop()
	mainloop.run()

# Always run our main loop so we can process updates
main()
