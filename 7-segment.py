#! /usr/bin/python
##
## test program to develop a clock display emulating 7-segment LEDs
##

import pygame as pg
import time
#import datetime
import logging


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

    def __init__(self, surface, bg, **kwargs):
        super().__init__(**kwargs)
        self.surface = surface
        self.bg = bg
    
    def get_segments(self, digit):
        assert (type(digit) is int)
        assert (digit >= 0) and (digit < 10)
        return self.SEGMENT_MAP[digit]

    def draw_digit(self, digit, fg="white"):
        width, height = self.surface.get_size()
        SEGW = 6
        WD = SEGW/2
        self.surface.fill(self.bg)
        segments = self.get_segments(digit)
        for i, on in enumerate(segments):
            if on:
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

                pg.draw.rect(self.surface, fg, r, width=0)
                if True:
                    if i in [0, 3, 6]:
                        # horizontal
                        pts_l = [(r[0]-WD, r[1]+WD),
                                 (r[0], r[1]),
                                 (r[0], r[1]+r[3])]
                        pts_r = [(r[0]+r[2]+WD, r[1]+WD),
                                 (r[0]+r[2], r[1]),
                                 (r[0]+r[2], r[1]+r[3])]
                        # pg.draw.lines(self.surface, fg, True, pts_l, width=1)
                        # pg.draw.lines(self.surface, fg, True, pts_r, width=1)
                        pg.draw.polygon(self.surface, fg, pts_l, width=0)
                        pg.draw.polygon(self.surface, fg, pts_r, width=0)
                    else:
                        # vertical
                        pts_u = [(r[0]+WD, r[1]-WD),
                                 (r[0], r[1]),
                                 (r[0]+r[2], r[1])]
                        pts_l = [(r[0]+WD, r[1]+r[3]+WD),
                                 (r[0], r[1]+r[3]),
                                 (r[0]+r[2], r[1]+r[3])]
                        # pg.draw.lines(self.surface, fg, True, pts_u, width=1)
                        # pg.draw.lines(self.surface, fg, True, pts_l, width=1)
                        pg.draw.polygon(self.surface, fg, pts_u, width=0)
                        pg.draw.polygon(self.surface, fg, pts_l, width=0)

                    #pg.draw.polygon(self.surface, fg, pts, width=0)
        return self.surface


class App:
    WIDTH = 240
    HEIGHT = 135
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

        self.running = True
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

        # waiting too long hurts keypress latency
        pg.time.wait(500)       # in msec

    def do_update(self):
        self.logger.debug('do_update() called...')
        now = time.localtime()
        self.time_str = f'{now.tm_hour:02d}:{now.tm_min:02d}'

    def on_render(self):
        self.display.fill(self.BGCOLOR)
        if not self.digit_display:
            digit_size = (35, 50)
            surf = pg.Surface(digit_size, 0, self.display)
            self.digit_display =  DigitDisplay(surf, self.BGCOLOR)

        positions = [25, 70, 135, 180]
        digits = self.time_str.replace(':', '')
        #print('DBG: digits=', digits)
        assert len(digits) == 4

        for x,d in zip(positions,digits):
            r = self.digit_display.draw_digit(int(d), self.FGCOLOR)
            self.display.blit(r, (x, 40))
            if False:
                rect = [x, 40, 35, 50]
                pg.draw.rect(self.display, (255, 255, 0), rect, width=1)

        pg.draw.circle(self.display, self.FGCOLOR, (120,55), 3, width=0)
        pg.draw.circle(self.display, self.FGCOLOR, (120,75), 3, width=0)

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
        
