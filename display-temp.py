##
## CircuitPython code for a basic clock on TFT display
##

import asyncio
import time
import board
import busio
import keypad

import adafruit_logging as logging
import traceback

import wifi
#import ssl
import socketpool

import adafruit_connection_manager
import adafruit_requests
import adafruit_ntp
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT
from adafruit_io.adafruit_io_errors import  AdafruitIO_MQTTError

import adafruit_sht4x

#import terminalio
import displayio
#from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.bitmap_label import Label
from adafruit_display_shapes.circle import Circle


## config knobs;
DEBUG = False
#DEBUG = True

TZ_OFFSET = 0 ## use AF service to get offset
#TZ_OFFSET = -7 # for PDT
#TZ_OFFSET = -8 # for PST

# with display of min (and not secs), only need to check NTP clock every 10 sec
UPDATE_INTERVAL = 10
# diff interval for publish to AdafruitIO
PUBLISH_INTERVAL = 60

## UI buttons
BUTTON_UP = board.IO14
BUTTON_DOWN = board.IO0
#BACKLIGHT = Pin(38, Pin.OUT)

CLOCK_FONT = 'fonts/NimbusSansNarrow-Regular-72.pcf'
MEDIUM_FONT = 'fonts/NimbusSansNarrow-Regular-60.pcf'
SMALL_FONT = 'fonts/NimbusSansNarrow-Regular-8.pcf'

FGCOLOR = 0x00ebf2              # cyan-ish
BGCOLOR = 0x1e0028              # dark purple
FG_COLORS = [0x00ebf2, 0x00d3d9, 0x00b0b4, 0x007478]

# drawing parameters
DISPLAY_WIDTH  = 320
DISPLAY_HEIGHT = 170



class ColorSelect():
    def __init__(self):
        # make a copy of list using [:]
        self.color_wheel = FG_COLORS[:]

    def get(self):
        return self.color_wheel[0]

    def rotate_left(self):
        self.color_wheel = self.color_wheel[1:] + [self.color_wheel[0]]

    def rotate_right(self):
        self.color_wheel = [self.color_wheel[-1]] + self.color_wheel[0:-1]


class temp_sensor_sht4x:
    """Reads multiple weather values (temp, humidity, pressure)"""

    def __init__(self, i2c):
        """Set up Temp sensor"""
        super().__init__()
        self.sensor = adafruit_sht4x.SHT4x(i2c)

        self.logger = logging.getLogger('main')
        self.logger.info(f"SHT4x serial num: {self.sensor.serial_number:#x}")
        default_mode = self.sensor.mode
        default_mode_string = adafruit_sht4x.Mode.string[default_mode]
        self.logger.info(f'SHT4x default mode: {default_mode_string}')

        ## We'll be sampling this infrequently, so use High repeatability
        ## and single shot mode to let the sensor do the averaging.
        # Note: this is the default anyway
        self.sensor.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION

    # could also do:
    # temperature, relative_humidity = sht.measurements

    def get_temp_C(self):
        return self.sensor.temperature

    def get_temp_F(self):
        # convert C to F
        return self.sensor.temperature * 9/5 + 32

    def get_humidity(self):
        return self.sensor.relative_humidity

    def get_temp_string(self):
        temp = self.get_temp_F()
        return f'{temp:.1f} °F'


class graphic_display:
    """Wrapper for CircuitPython displayio display"""
    def __init__(self, color_set, *, am_pm=True, celsius=False):
        self.logger = logging.getLogger('main')
        #self.logger.info('graphic_display() init called')

        self.display_group = None
        self.color_set = color_set

        self.am_pm = am_pm
        self.celsius = celsius

        self.clock_font = bitmap_font.load_font(CLOCK_FONT)
        self.temp_font = bitmap_font.load_font(MEDIUM_FONT)
        self.status_font = bitmap_font.load_font(SMALL_FONT)
        self._time_str = '00:00:00'
        self._temp_str = '00.0 F'
        self._status_str = ""

    def update_time(self, now):
        """Set the current time to the timespec passed as NOW"""
        # allow for current time to be passed in, otherwise use now()
        # if not now:
        #     ## CircuitPython doesn't have a time.now() method
        #     #now = time.now()
        # very hackish!  But no zoneinfo infrastructure in CircuitPython...
        #     now = time.localtime(now + tz_offset)
        ts = now
        hour = ts.tm_hour
        am_pm = ''
        if self.am_pm:
            am_pm = 'am'
            if hour >= 12:
                am_pm = 'pm'
                hour -= 12
            if hour == 0:
                hour = 12
            self._time_str = f'{hour:2d}:{ts.tm_min:02d}{am_pm}'
        else:
            self._time_str = f'{hour:2d}:{ts.tm_min:02d}:{ts.tm_sec:02d}'
        #self._time_str=now.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
        self.logger.debug(f'update_time() sets time_str={self._time_str}')

        self.clock_area.text = self._time_str

    def update_temp(self, sensor):
        deg = '\u00B0'
        if self.celsius:
            temp = sensor.get_temp_C()
            temp_label = 'C'
        else:
            temp = sensor.get_temp_F()
            temp_label = 'F'
        self._temp_str = f'{temp:.1f}{deg}{temp_label}'
        self.temp_area.text = self._temp_str
        self.logger.debug(f'update_temp() sets temp_str={self._temp_str}')
 
    def update_errstatus(self, e):
        if e is None:
            # leave the last exception string in there
            #self._status_str = ""
            self._status_val = True
        else:
            self._lasterr = str(e)
            self._status_val = False
        ## more stuff here...
        self.status_area.text = self._status_str
        self.logger.debug(f'update_errstatus() sets status_str={self._status_str}')

        red = 0xff0000
        green = 0x80ff00  # tweak to look better vs blue foreground
        if self._status_val:
            self.status_dot.fill = green
        else:
            self.status_dot.fill = red

    def update_colors(self):
        fgcolor = self.color_set.get()
        self.clock_area.color = fgcolor
        self.temp_area.color = fgcolor
        self.status_area.color = fgcolor

    def get_display_group(self, display_width, display_height):
        if not self.display_group:
            # First time through, create a group for all the labels
            bg_group = displayio.Group()

            self.display_group = bg_group
            self.disp_width = display_width
            self.disp_height = display_height
            
            bg_bitmap = displayio.Bitmap(display_width, display_height, 1)
            palette = displayio.Palette(1)
            palette[0] = BGCOLOR

            # Put the background into the display group
            bg_tile = displayio.TileGrid(bg_bitmap, pixel_shader=palette, 
                                         x=0, y=0)
            bg_group.append(bg_tile)
            
            # Time display
            self.clock_area = Label(self.clock_font,
                                    text=self._time_str,
                                    color=FGCOLOR)
            self.clock_area.x = 30
            self.clock_area.y = 50

            bg_group.append(self.clock_area)

            # Temp display
            self.temp_area = Label(self.temp_font,
                                   text=self._temp_str,
                                   color=FGCOLOR)
            self.temp_area.x = 140
            self.temp_area.y = 120

            bg_group.append(self.temp_area)

            # Last exception display
            self.status_area = Label(self.status_font,
                                     text=self._status_str,
                                     color=FGCOLOR)
            self.status_area.x = 30
            self.status_area.y = 140

            bg_group.append(self.status_area)

            # alternately, could use a Triangle if no .fill property for Circle
            self.status_dot = Circle(45, 120, 4, fill=FGCOLOR)
            bg_group.append(self.status_dot)

            # store our result here
            self.display_group = bg_group

        else:
            # don't create a new group, just update the labels
            self.clock_area.text = self._time_str
            self.temp_area.text = self._temp_str
            self.status_area.text = self._status_str
            self.logger.info(
                'get_display_group() unexpectedly called after init'
            )

        return self.display_group


class network_handles:
    """Wrapper for wifi and various network handles"""
    def __init__(self, *, dhcpname=None, tz_offset=0):
        self.logger = logging.getLogger('main')
        #self.logger.info('network_handle init() called')

        # Get wifi details and more from a secrets.py file
        try:
            from secrets import secrets
        except ImportError:
            self.logger.error("WiFi connect failed: no secrets.py file")
            # maybe flash LED with some pattern?
            raise

        mac = ':'.join(f'{i:02x}' for i in wifi.radio.mac_address)
        self.logger.info(f"My MAC addr: {mac}")

        if dhcpname:
            wifi.radio.hostname = dhcpname
        wifi.radio.connect(secrets["ssid"], secrets["password"])

        self.logger.info("Connected to %s!"%secrets["ssid"])
        self.logger.info(f"My IP address is {wifi.radio.ipv4_address}")

        # Create a socket pool
        self.pool = socketpool.SocketPool(wifi.radio)
        self.ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)

        # get DST-adjusted offset from Adafruit service
        if tz_offset == 0:
            requests = adafruit_requests.Session(self.pool, self.ssl_context)
            url = f'https://io.adafruit.com/api/v2/{secrets["aio_username"]}/' + \
                  f'integrations/time/strftime?x-aio-key={secrets["aio_key"]}&fmt=%25z'
            with requests.get(url) as response:
                self.logger.info(f"strftime call returned: {response.status_code}")
                # check status_code == 200??
                val = int(response.text)/100
                self.logger.info(f"tz_offset: {response.text} ->  {val}")
                tz_offset = val

        # NTP handle
        self.ntp = adafruit_ntp.NTP(self.pool, 
                                    tz_offset=tz_offset, 
                                    cache_seconds=600)
        # default server = "0.adafruit.pool.ntp.org"
        # cache_seconds = poll NTP no more often than (what is optimal?)

        # Initialize a new MQTT Client object
        self.mqtt_client = MQTT.MQTT(
            broker="io.adafruit.com",
            client_id='BRsensor',
            username=secrets["aio_username"],
            password=secrets["aio_key"],
            is_ssl=True,
            socket_pool=self.pool,
            ssl_context=self.ssl_context,
            keep_alive=120, #? - want this longer than 1min update intvl?
            connect_retries=7, # default = 5
        )
        # should we instead use port=8883 ??
        # port=1883,

        # Initialize an Adafruit IO MQTT Client
        self.io = IO_MQTT(self.mqtt_client)

    def get_ntp(self):
        return self.ntp

    def get_adafruit_io(self):
        return self.io
    

async def handle_buttons(pin_up, pin_down, graphic):
    """Handle buttons: up/down run through a set of FG colors (brightness)"""
    logger = logging.getLogger('main')
    color_set = graphic.color_set
    with keypad.Keys(
        (pin_down, pin_up), value_when_pressed=False, pull=True
    ) as keys:
        while True:
            event = keys.events.get()
            if event and event.pressed:
                if event.key_number == 0:
                    # rotate up
                    color_set.rotate_left()
                    fgcolor = color_set.get()
                    logger.info(f'key UP - rotate left - color {fgcolor:x}')
                    graphic.update_colors()
                else:
                    # key_number == 1
                    color_set.rotate_right()
                    fgcolor = color_set.get()
                    logger.info(f'key DOWN - rotate left - color {fgcolor:x}')
                    graphic.update_colors()
            # Let another task run.
            await asyncio.sleep(0)


## main program
async def main():
    logger = logging.getLogger('main')
    
    i2c = busio.I2C(board.STEMMA_SCL, board.STEMMA_SDA)  # use STEMMA/QT plug
    sensor = temp_sensor_sht4x(i2c)

    display = board.DISPLAY
    dhcpname='temp-display'
    network = network_handles(dhcpname=dhcpname, tz_offset=TZ_OFFSET)
    ntp = network.get_ntp()
    af_io = network.get_adafruit_io()

    # Connect the callback method defined above to Adafruit IO
    #af_io.on_message = recv_values
    af_io.connect()

    color_set = ColorSelect()
    graphic = graphic_display(color_set, am_pm=True, celsius=False)

    # display.show() is now replaced by setting .root_group
    display.root_group = graphic.get_display_group(DISPLAY_WIDTH,
                                                   DISPLAY_HEIGHT)

    button_task = asyncio.create_task(
        handle_buttons(BUTTON_UP, BUTTON_DOWN, graphic)
    )

    i = 0
    next_publish = 0

    while True:
        try:
            logger.info(f'main loop iter {i}')
            i += 1

            now = ntp.datetime  # this returns a timestruct
            graphic.update_time(now)
            #logger.debug(f'graphic.time_str = {graphic._time_str}')

            graphic.update_temp(sensor)
            #logger.debug(f'graphic.temp_str = {graphic._temp_str}')

            #publish data to AdafruitIO every so often:
            current_time = time.mktime(now)
            if current_time > next_publish:
                values = [
                    ('BR-Temp', sensor.get_temp_F()),
                    ('BR-Humidity', sensor.get_humidity())
                ]
                af_io.publish_multiple(values)
                logger.info(f'publ to AdafruitIO val= {values}')
                next_publish = current_time + PUBLISH_INTERVAL
                # if publish succeeds, then clear any prev exceptions
                graphic.update_errstatus(None)

            display.refresh()

        except OSError as e:
            # NTP error
            logger.error('OSError: %s', e)
            traceback.print_exception(e)
            graphic.update_errstatus(e)
            # prob a timeout to NTP server, just try again

        except MQTT.MMQTTException as e:
            ## apparently, protocol exceptions happen fairly frequently
            logger.error('MQTT exception: %s', e)
            graphic.update_errstatus(e)
            # Maybe need these?
            # if not wifi.radio.connected:
            #     wifi.reset()
            #     wifi.connect()
            af_io.reconnect()

        except AdafruitIO_MQTTError as e:
            ## apparently, protocol exceptions happen fairly frequently
            logger.error('MQTT exception: %s', e)
            graphic.update_errstatus(e)
            ## swallow this exception and try another round at main()
            # Maybe need these?
            #wifi.reset()
            #wifi.connect()
            af_io.reconnect()

        except Exception as e:
            # This works to print a stack trace
            logger.error('Unexpected exception: %s', e)
            graphic.update_errstatus(e)
            traceback.print_exception(e)
            # re-raise the error and hang the program
            raise

        # regardless of errors, wait the 10 sec before trying again
        await asyncio.sleep(UPDATE_INTERVAL)

    # Never actually reach this join as while loop is infinite
    await asyncio.gather(button_task)


## actual exec here:
if __name__ == '__main__':
    logger = logging.getLogger('main')
    if DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    #main()
    asyncio.run(main())

