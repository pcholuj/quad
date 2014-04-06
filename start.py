#!/usr/bin/env python
import signal
import sys
import argparse
import time
import ctypes
import logging
import RPIO
import math

from config import config
from RPIO import PWM
from libs.ESC import ESC
from libs.Sensors import Accelerometr
from libs.ServerApi import Api
from ctypes.util import find_library
from libs.Server import Server

from socketio.server import SocketIOServer

#-------------------------------------------------------------------------------------------
# Set up the global constants
#-------------------------------------------------------------------------------------------

MCL_CURRENT = 1
MCL_FUTURE  = 2

class Quad:
    def __init__(self, api, options=False):
        self.esc_list = []

        self.libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
        signal.signal(signal.SIGINT, self.signalHandler)

        self.initLogger()
        self.mlockall()
        # self.initEsc()
        # self.initSensors()
        self.api = api(self)

        if options.command == 'start':
            print 1
            SocketIOServer(('0.0.0.0', 3000), Server(), policy_server=False,transports=['websocket']).serve_forever()
            self.logger.info('Listening on port http://127.0.0.1:3000 and on port 843 (flash policy server)')
        elif options.command == 'calibrate':
            self.calibrateEsc()


        while True:
            # fax_average = 0.0
            # fay_average = 0.0
            # faz_average = 0.0
            # for loop_count in range(0, 50, 1):
            #     [fax, fay, faz, fgx, fgy, fgz] = self.sensors.readSensors()
            #     fax_average += fax
            #     fay_average += fay
            #     faz_average += faz
            #     time.sleep(0.05)
            # fax = fax_average / 50.0
            # fay = fay_average / 50.0
            # faz = faz_average / 50.0
            [fax, fay, faz, fgx, fgy, fgz] = self.sensors.readSensors()
            prev_c_pitch, prev_c_roll, prev_c_tilt  =  self.sensors.getEulerAngles(fax, fay, faz)
            self.logger.info("Platform tilt: pitch %f, roll %f", prev_c_pitch * 180 / math.pi, prev_c_roll * 180 / math.pi)
            time.sleep(1)

    def printStartMessage(self):
        sys.stderr.write("\x1b[2J\x1b[H")
        print('************************************************************************')
        print('*******************RaspberyPi Quad initialized**************************')
        print('***************************Version: 1.0*********************************')
        print('************************************************************************')
        print('\n')

    def initLogger(self):
        configLogger = config['logger']
        #-------------------------------------------------------------------------------------------
        # Set up the base logging
        #-------------------------------------------------------------------------------------------
        self.logger = logging.getLogger(configLogger['name'])
        self.logger.setLevel(logging.INFO)

        #---------------------------------------------------------------------------------------
        # Create file and console logger handlers
        #-------------------------------------------------------------------------------------------
        file_handler = logging.FileHandler(configLogger['file'], 'w')
        file_handler.setLevel(configLogger['levelFile'])

        console_handler = logging.StreamHandler()
        console_handler.setLevel(configLogger['levelConsole'])

        #-------------------------------------------------------------------------------------------
        # Create a formatter and add it to both handlers
        #-------------------------------------------------------------------------------------------
        console_handler.setFormatter(logging.Formatter(configLogger['formatterConsole']))
        file_handler.setFormatter(logging.Formatter(configLogger['formatterFile']))

        #-------------------------------------------------------------------------------------------
        # Add both handlers to the logger
        #-------------------------------------------------------------------------------------------
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def initSensors (self):
        self.sensors = Accelerometr()
        self.sensors.calibrateGyros()
        # self.sensors.calibrateGravity('./qcgravity.cfg')
        # self.sensors.readGravity('./qcgravity.cfg')


    def initEsc(self):
        for esc_index in config['motors']:
            self.esc_list.append(ESC(esc_index['pin'], esc_index['name'], esc_index['dma']))

    def getEscList(self):
        return self.esc_list

    def handleServerResponse(self, response):
        try:
            func = getattr(self.api, response['action'])
        except AttributeError:
             self.logger.exception('function not found "%s" (%s)', response['action'], response['value'])
        else:
            func(response['value'])

    # Calibrate Esc At command line
    def calibrateEsc(self):

        self.logger.info('Turn OFF Esc power and press ENTER')
        raw_input()
        for esc in self.esc_list:
            esc.update(2000)

        self.logger.info('Turn ON Esc power and press ENTER')
        raw_input()

        for esc in self.esc_list:
            esc.update(1000)

        self.logger.info('After Esc beeep press ENTER')
        raw_input()

        self.logger.info('Calibration ESC done! Shutting down')
        self.cleanShutdown()

    def mlockall(self, flags = MCL_CURRENT| MCL_FUTURE):
        result = self.libc.mlockall(flags)

        if result != 0:
            raise Exception("cannot lock memmory, errno=%s" % ctypes.get_errno())

    def munlockall(self):
        result = self.libc.munlockall()
        if result != 0:
            raise Exception("cannot lock memmory, errno=%s" % ctypes.get_errno())

    def signalHandler(self, signal, frame):
        self.cleanShutdown()
        self.server.close()

    def cleanShutdown(self):
        #-----------------------------------------------------------------------------------
        # Time for teddy bye byes
        #-----------------------------------------------------------------------------------
        for esc in self.esc_list:
            esc.update(0)
            self.logger.info('Stoping blade "%s"', esc.name)

        #-----------------------------------------------------------------------------------
        # Clean up PWM / GPIO
        #-----------------------------------------------------------------------------------
        PWM.cleanup()
        RPIO.cleanup()

        self.munlockall()
        sys.exit(0)

parser = argparse.ArgumentParser(description='Quad Copter Lib')
parser.add_argument('-c','--command', help='Command [start,calibrate]',required=False, default='start')
args = parser.parse_args()

Quad(Api, args)
