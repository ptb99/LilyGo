#! /usr/bin/python
##
## test program for display on LilyGo CircuitPython device
##

import pygame as pg
import time
import datetime
import logging



def get_time_strings():
    """Wrapper function to convert current time/date into a pair of strings."""
    #USE_AMPM = True
    USE_AMPM = False
    now = datetime.datetime.now()
    if USE_AMPM:
        timestr = now.strftime('%l:%M %P')
    else:
        timestr = now.strftime('%H:%M:%S')
    datestr = now.strftime('%a, %b %e, %Y')
    # 'Tue, Dec 7, 2024'
    #datestr = now.strftime('%A, %B %e, %Y')
    # 'Tuesday, December 7, 2024'

    return timestr, datestr

def get_temp_string():
    """Wrapper function to get (dummy) temp sensor info in deg F"""
    temp = 74.159
    tstring = f'{temp:.1f} °F'
    return tstring

def get_status_string():
    """Wrapper function to get a dummy exception string"""
    #msg = 'Test Text'
    #msg = ''
    msg = 'MQTT.MQTTException'
    return msg


## the LilyGo T-Display S3 board has a 320x170 screen
## the Feather S2 Reverse-TFT has 240x135

class App:
    # WIDTH = 240
    # HEIGHT = 135
    WIDTH = 320
    HEIGHT = 170
    BGCOLOR = (30, 0, 40)    # dark purple
    #FGCOLOR = (178, 235, 242)  # light blue
    FGCOLOR = (0, 235, 242)  # light blue
    UPDATE_INTERVAL = 5

    def __init__(self):
        self.logger = logging.getLogger()
        self.running = True
        self.display = None
        self.size = (self.WIDTH, self.HEIGHT)
        self.next_update = 0
        self.time_str = '00:00'
        self.digit_display = None

    def on_init(self):
        pg.init()

        # print out some info
        fb_size = (pg.display.Info().current_w,
                   pg.display.Info().current_h)
        self.logger.info("Default Framebuffer size: %d x %d" %
                         (fb_size[0], fb_size[1]))
        self.logger.info(f'Chosen window size: {self.size}')

        self.display = pg.display.set_mode(self.size, pg.SHOWN)
        self.logger.info(f'PyGame driver = {pg.display.get_driver()}')

        # Initialise font support
        #pg.font.init()
        pg.freetype.init()
        self.fonts = {}
        #self.fonts['CLOCK'] = pg.font.SysFont('freesans', 60)
        #self.fonts['CLOCK'] = pg.freetype.Font('fonts/FreeSans-60.pcf')
        self.fonts['CLOCK'] = pg.freetype.Font('fonts/NimbusSansNarrow-Regular-60.pcf')
        #self.fonts['TEMP'] = pg.font.SysFont('freesans', 40)
        #self.fonts['TEMP'] = pg.freetype.Font('fonts/FreeSans-40.pcf')
        self.fonts['TEMP'] = pg.freetype.Font('fonts/NimbusSansNarrow-Regular-40.pcf')
        #self.fonts['SMALL'] = pg.font.SysFont('freesans', 16, bold=True)
        self.fonts['SMALL'] = pg.freetype.Font('fonts/NimbusSansNarrow-Regular-8.pcf')
        
        self.clock = pg.time.Clock()
        self.running = True
        #time.sleep(0.1)           # brief delay to let driver init settle
        return self.running

    def on_event(self, event):
        if event.type == pg.QUIT:
            self.running = False
        elif event.type == pg.KEYDOWN:
            keys = pg.key.get_pressed()
            if keys[pg.K_q]:
                self.running = False
        # Could maybe use mouse-presses for UI buttons (someday)...

    def on_loop(self):
        now = time.time()
        if now > self.next_update:
            self.do_update()
            self.next_update = now + self.UPDATE_INTERVAL

        # run any BG tasks
        #run_once(self.bgloop)

        # waiting too long hurts keypress latency
        self.clock.tick(1)
        #pg.time.wait(500)       # in msec


    def do_update(self):
        self.logger.debug('do_update() called...')

        # task = self.bgloop.create_task(self.update_start())
        # self.bgloop.create_task(self.update_end(task))
        
        # now = time.localtime()
        # self.time_str = f'{now.tm_hour:02d}:{now.tm_min:02d}:{now.tm_sec:02d}'

    def on_render(self):
        self.display.fill(self.BGCOLOR)

        # from LEDclock
        # positions = [25, 70, 135, 180]
        # y = 40

        timestr, datestr = get_time_strings()
        surface, _ = self.fonts['CLOCK'].render(
            timestr,
            self.FGCOLOR)
        self.display.blit(surface, (30, 30))
        
        surface, _ = self.fonts['TEMP'].render(
            get_temp_string(),
            self.FGCOLOR)
        self.display.blit(surface, (150, 110))

        surface, _ = self.fonts['SMALL'].render(
            get_status_string(),
            self.FGCOLOR)
        self.display.blit(surface, (35, 135))
        
        #fgcolor = (255, 0, 0)  # red
        fgcolor = (100, 255, 0)  # green
        pg.draw.circle(self.display, fgcolor, (45,120), 4, width=0)

        # The pg.font TrueType case
        # surface = self.fonts['TEMP'].render(
        #     get_temp_string(),
        #     True, # antialiasing
        #     self.FGCOLOR)
        # self.display.blit(surface, (130, 120))
        

        pad = 10
        rect = (pad, pad, self.WIDTH-2*pad, self.HEIGHT-2*pad)
        pg.draw.rect(self.display, self.FGCOLOR, rect, width=1)

        pg.display.update()


    def on_cleanup(self):
        pg.quit()

    def on_execute(self):
        if self.on_init() == False:
            self.running = False
 
        while( self.running ):
            for event in pg.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()

        self.on_cleanup()


def main():
    logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',
                        level=logging.INFO)

    theApp = App()
    theApp.on_execute()

    
if __name__ == "__main__" :
    # Any use for argv's?
    main()
        
