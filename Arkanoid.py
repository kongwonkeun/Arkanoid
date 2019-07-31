#
#
#

import argparse

from arkanoid.game import Arkanoid
from arkanoid.sensor import SensorThread

if __name__ == '__main__':
    com_port = 'COM1'
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p',
        '--port',
        default = com_port,
        help = 'serial communication port, default is %s' % com_port
    )
    args = parser.parse_args()
    print(args.port)
    sensor = SensorThread(args.port)
    if  sensor.serial.is_open:
        sensor.start()

    arkanoid = Arkanoid(sensor)
    arkanoid.main_loop()

#
#
#
