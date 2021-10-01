#!/usr/bin/env python

# This program creates and monitors a dBus service to trigger a system shutdown
# The com.victronenergy.shutdown service is created and contains one parameter: /Shutdown
# /Shutdown is normally 0 but if this program detects a value other than 0,
# the system shutdown -h now call is made

import platform
import argparse
import logging
import sys
import os
import time
import dbus

# accommodate both Python 2 and 3
# if the Python 3 GLib import fails, import the Python 2 gobject
try:
    from gi.repository import GLib # for Python 3
except ImportError:
    import gobject as GLib # for Python 2

# add the path to our own packages for import
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext', 'velib_python'))
from vedbus import VeDbusService


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

    def __init__(self):

    # set up unique dBus connection and dBus service
        self.DbusBus = dbusconnection()
        self._createDbusService()

        GLib.timeout_add (1000, self._background)
        return None

    # flag value change from external source

    def _handlechangedvalue (self, path, value):
        if value == 1:
            logging.info ("User shutdown received - shutting down system")
            os.system ("shutdown -h now")
        return True

    def _background (self):
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
     
        self.DbusService.add_path ('/Shutdown', 0, writeable = True, onchangecallback = self._handlechangedvalue)

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
