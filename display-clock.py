##
## CircuitPython code for a basic clock on TFT display
##

import time
import board

import socketpool
import wifi
import adafruit_ntp

#import terminalio
#from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.bitmap_label import Label


## config knobs;
#TZ_OFFSET = -7 # for DST
TZ_OFFSET = -8 # for winter time
LARGE_FONT =  "fonts/DejaVuSans-Bold24.pcf"
FG_COLOR = 0x0000FF


def get_time_string(ts):
    return f'{ts.tm_hour:02d}:{ts.tm_min:02d}:{ts.tm_sec:02d}'


## Network setup and ntp object
# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

wifi.radio.connect(secrets["ssid"], secrets["password"])
pool = socketpool.SocketPool(wifi.radio)
ntp = adafruit_ntp.NTP(pool, tz_offset=TZ_OFFSET)
      # default server = "0.adafruit.pool.ntp.org"


display = board.DISPLAY
time_text = '00:00:00'


# Create the text label
#font = terminalio.FONT
# Alternate font:
large_font = bitmap_font.load_font(LARGE_FONT)
text_area = Label(large_font, text=time_text, color=FG_COLOR)

# Set the location
text_area.x = 60
text_area.y = 70

# display.show() is now replaced by setting .root_group
display.root_group = text_area


while True:
    #now = time.localtime()
    now = ntp.datetime

    time_text = get_time_string(now)
    #print('Time = ', time_text)
    text_area.text = time_text
    display.refresh()
    time.sleep(1)
