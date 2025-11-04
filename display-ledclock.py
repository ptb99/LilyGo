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
#from adafruit_bitmap_font import bitmap_font
#from adafruit_display_text.bitmap_label import Label

import displayio
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.triangle import Triangle



## config knobs;
#TZ_OFFSET = -7 # for DST
TZ_OFFSET = -8 # for winter time
BG_COLOR = 0x000000
FG_COLOR = 0x0000FF
#FG_COLOR = 0x00ebf2
#FG_COLOR = 0xFF0000


## the LilyGo T-Display S3 board has a 320x170 screen
## the Feather S2 Reverse-TFT has 240x135


class DigitDisplay:
    """Wrapper for GPIO pins driving 7-segment LED digit display."""
    SEGMENT_MAP = [
        # vectors represent the segments [A,B,C,D,E,F,G]
        [1,1,1,1,1,1,0], # 0
        [0,1,1,0,0,0,0], # 1
        [1,1,0,1,1,0,1], # 2
        [1,1,1,1,0,0,1], # 3
        [0,1,1,0,0,1,1], # 4
        [1,0,1,1,0,1,1], # 5
        [1,0,1,1,1,1,1], # 6
        [1,1,1,0,0,0,0], # 7
        [1,1,1,1,1,1,1], # 8
        [1,1,1,1,0,1,1], # 9
    ]

    def __init__(self, group, size, bgcolor, **kwargs):
        super().__init__(**kwargs)
        self.root_group = group
        self.size = size
        self.bg = bgcolor
        self.segm_map = {}
        self.fill_bg(bgcolor)

    def get_segments(self, digit):
        assert (type(digit) is int)
        assert (digit >= 0) and (digit < 10)
        return self.SEGMENT_MAP[digit]

    def fill_bg(self, bgcolor="black"):
        # Make a background color fill
        width, height = self.size
        color_bitmap = displayio.Bitmap(width, height, 1)
        color_palette = displayio.Palette(1)
        color_palette[0] = bgcolor
        bg_sprite = displayio.TileGrid(color_bitmap, x=0, y=0,
                                       pixel_shader=color_palette)
        # clear out old group ??
        self.root_group.insert(0, bg_sprite)

    def draw_digit(self, digit, fgcolor="white"):
        width, height = self.size
        SEGW = 6
        WD = int(SEGW/2)
        # clear out old surface ??
        #self.fill_bg(self.bg)
        segments = self.get_segments(digit)
        for i, on in enumerate(segments):
            if i in self.segm_map:
                g = self.segm_map[i]
                g.hidden = not on
            else:
                if on:
                    g = displayio.Group()
                    self.segm_map[i] = g
                    if i == 0:
                        r = [SEGW+1, 0, width-2*SEGW-2, SEGW]
                    elif i == 1:
                        r = [width-SEGW, SEGW+1, SEGW, height/2-1.5*SEGW-2]
                    elif i == 2:
                        r = [width-SEGW, (height+SEGW)/2+1, SEGW, height/2-1.5*SEGW-2]
                    elif i == 3:
                        r = [SEGW+1, height-SEGW, width-2*SEGW-2, SEGW]
                    elif i == 4:
                        r = [0, (height+SEGW)/2+1, SEGW, height/2-1.5*SEGW-2]
                    elif i == 5:
                        r = [0, SEGW+1, SEGW, height/2-1.5*SEGW-2]
                    elif i == 6:
                        r = [SEGW+1, (height-SEGW)/2, width-2*SEGW-2, SEGW]
                        
                    try:
                        r = [int(x) for x in r]
                        rect = Rect(r[0], r[1], r[2], r[3], fill=fgcolor)
                        g.append(rect)
                    except TypeError as e:
                        print(e)
                        print(f'EXCEPT1: i={i} r= {r[0]}, {r[1]}, {r[2]}, {r[3]} fill={fgcolor}')

                    if True:
                        if i in [0, 3, 6]:
                            # horizontal
                            try:
                                pts_l = [(r[0]-WD, r[1]+WD),
                                         (r[0], r[1]),
                                         (r[0], r[1]+r[3])]
                                pts_r = [(r[0]+r[2]+WD, r[1]+WD),
                                         (r[0]+r[2], r[1]),
                                         (r[0]+r[2], r[1]+r[3])]
                                tri1 = Triangle(pts_l[0][0], pts_l[0][1], 
                                                pts_l[1][0], pts_l[1][1], 
                                                pts_l[2][0], pts_l[2][1], fill=fgcolor)
                                g.append(tri1)
                                tri2 = Triangle(pts_r[0][0], pts_r[0][1], 
                                                pts_r[1][0], pts_r[1][1], 
                                                pts_r[2][0], pts_r[2][1], fill=fgcolor)
                                g.append(tri2)
                            except TypeError as e:
                                print(e)
                                print(f'EXCEPT2: i={i} r= {r[0]}, {r[1]}, {r[2]}, {r[3]} fill={fgcolor}')
                                print('EXCEPT2:', pts_l)
                        else:
                            # vertical
                            pts_u = [(r[0]+WD, r[1]-WD),
                                     (r[0], r[1]),
                                     (r[0]+r[2], r[1])]
                            pts_l = [(r[0]+WD, r[1]+r[3]+WD),
                                     (r[0], r[1]+r[3]),
                                     (r[0]+r[2], r[1]+r[3])]
                            tri1 = Triangle(pts_u[0][0], pts_u[0][1], 
                                            pts_u[1][0], pts_u[1][1], 
                                            pts_u[2][0], pts_u[2][1], fill=fgcolor)
                            g.append(tri1)
                            tri2 = Triangle(pts_l[0][0], pts_l[0][1], 
                                            pts_l[1][0], pts_l[1][1], 
                                            pts_l[2][0], pts_l[2][1], fill=fgcolor)
                            g.append(tri2)
                    self.root_group.append(g)
                    g.hidden = False

        return self.root_group


def get_time_string(ts):
    return f'{ts.tm_hour:02d}:{ts.tm_min:02d}:{ts.tm_sec:02d}'
    #return f'{ts.tm_hour:02d}:{ts.tm_min:02d}'



## Network setup and ntp object
# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

wifi.radio.connect(secrets["ssid"], secrets["password"])
pool = socketpool.SocketPool(wifi.radio)
ntp = adafruit_ntp.NTP(pool, tz_offset=TZ_OFFSET, socket_timeout=30)
      # default server = "0.adafruit.pool.ntp.org"


display = board.DISPLAY
time_text = '00:00:00'
digit_size = (35, 70)

# display.show() is now replaced by setting .root_group
display.root_group = displayio.Group()

## set up the display tree
digit_disps = [DigitDisplay(displayio.Group(), digit_size, BG_COLOR) 
               for i in range(6)]
positions = [10, 55, 120, 165, 230, 275]
for x,dsp in zip(positions, digit_disps):
    g = dsp.draw_digit(0, FG_COLOR)
    g.x = x
    g.y = 50
    display.root_group.append(g)

dot1 = Circle(105, 75, 3, fill=FG_COLOR)
dot2 = Circle(105, 95, 3, fill=FG_COLOR)
display.root_group.append(dot1)
display.root_group.append(dot2)

dot1 = Circle(215, 75, 3, fill=FG_COLOR)
dot2 = Circle(215, 95, 3, fill=FG_COLOR)
display.root_group.append(dot1)
display.root_group.append(dot2)

# pad = 10
# r = Rectangle (pad, pad, self.WIDTH-2*pad, self.HEIGHT-2*pad, outline=FG_COLOR)
# display.root_group.append(r)


while True:
    try:
        #now = time.localtime()
        now = ntp.datetime

        time_text = get_time_string(now)
        #print('Time = ', time_text)

        digits = time_text.replace(':', '')
        #print('DBG: digits=', digits)
        assert len(digits) == 6

        for i,d in enumerate(digits):
            digit_disps[i].draw_digit(int(d), FG_COLOR)

    except OSError as e:
        print('EXCEPTION:', e)

    display.refresh()
    time.sleep(1)
