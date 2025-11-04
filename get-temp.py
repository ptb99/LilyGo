##
## CircuitPython code to read an SHT41 temp sensor
## 

# code.py output:
# I2C addresses found: ['0x44']
# I2C addresses found: ['0x44']


import time
import board
import busio

import adafruit_sht4x
import adafruit_logging as logging


class temp_sensor_sht4x:
    """Reads multiple weather values (temp, humidity, pressure)"""

    def __init__(self, i2c):
        """Set up Temp sensor"""
        super().__init__()
        self.sensor = adafruit_sht4x.SHT4x(i2c)

        logger = logging.getLogger('temp')
        logger.setLevel(logging.INFO)
        logger.info(f"SHT4x serial num: {self.sensor.serial_number:#x}")
        logger.info(f'SHT4x default mode: {adafruit_sht4x.Mode.string[self.sensor.mode]}')

        ## We'll be sampling this infrequently, so use High repeatability
        ## and single shot mode to let the sensor do the averaging.
        # Note: this is the default anyway
        self.sensor.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION

    # could also do:
    # temperature, relative_humidity = sht.measurements

    def get_temp_F(self):
        # convert C to F
        return self.sensor.temperature * 9/5 + 32

    def get_humidity(self):
        return self.sensor.relative_humidity


## main program

i2c = busio.I2C(board.STEMMA_SCL, board.STEMMA_SDA)  # use STEMMA/QT plug
sensor = temp_sensor_sht4x(i2c)

try:
    while True:
        start = time.time()
        temp = sensor.get_temp_F()
        stop = time.time()
        print(f'Temp= {temp:.2f} F     ',
              f'Humidity= {sensor.get_humidity():.2f}     ',
              f'in {(stop-start)*1e6:.3f} usec' )
        time.sleep(5)

finally:  # unlock the i2c bus when ctrl-c'ing out of the loop
    i2c.unlock()
        
