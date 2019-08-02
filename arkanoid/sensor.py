#
#
#

import sys
import time
import serial
import threading

class SensorThread(threading.Thread):

    def __init__(self, port):
        super(SensorThread, self).__init__()
        self.serial = serial.Serial(port, 9600, timeout = 0.03) # timeout unit is sec --> 30ms
        self.run_flag = True
        self.s = 0 # state
        self.v = 0 # velocity
        self.d = 0 # distance
        self.d_last = 0 # last distance

    def run(self):
        while (self.run_flag):
            b = self.serial.read()
            self.readStateMachine(int.from_bytes(b, byteorder='big'))

    def readStateMachine(self, b):
        global G_speed
        global G_direction
        if   b == 86: self.s = 1; self.v = 0 # 86 = 'V' of 'VNNNNN'
        elif b == 68: self.s = 7; self.d = 0 # 68 = 'D' of 'DNNN'
        else:
            if    self.s == 1: self.s = 2;  self.v = (b - 48)
            elif  self.s == 2: self.s = 3;  self.v = (self.v * 10) + (b - 48)
            elif  self.s == 3: self.s = 4;  self.v = (self.v * 10) + (b - 48)
            elif  self.s == 4: self.s = 5;  self.v = (self.v * 10) + (b - 48)
            elif  self.s == 5: self.s = 6;  self.v = (self.v * 10) + (b - 48)
            elif  self.s == 7: self.s = 8;  self.d = (b - 48)
            elif  self.s == 8: self.s = 9;  self.d = (self.d * 10) + (b - 48)
            elif  self.s == 9: self.s = 10; self.d = (self.d * 10) + (b - 48)
            else: pass
        if  self.s == 6:
            G_speed = self.v
            return
        if  self.s == 10:
            if  self.d == self.d_last:
                if    self.d > 17: G_direction = -1
                elif  self.d < 15: G_direction = 1
                else: G_direction = 0
                return

    def stop(self):
        self.run_flag = False
        if  self.serial.is_open:
            self.serial.close()

G_speed = 0
G_direction = 0

#
#
#
