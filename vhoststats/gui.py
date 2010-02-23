#!/usr/bin/python

import curses
import time
import subprocess
import optparse

status_size = 1
log_size = 5

class Window(object):
    registry = []

    def __init__ (self, ncols, nrows,
            begin_x=None,begin_y=None):
        self.win = curses.newwin(ncols, nrows, begin_x, begin_y)
        self.size = self.win.getmaxyx()
        self.registry.append(self)

    def refresh(self):
        return self.win.nooutrefresh()

    def __getattr__(self, k):
        return getattr(self.win, k)

    @classmethod
    def refresh_all(cls):
        for w in cls.registry:
            w.refresh()

        curses.doupdate()

class BoxWindow(Window):
    def refresh(self):
        self.win.box()
        super(BoxWindow, self).refresh()

class StatusWindow(BoxWindow):
    def update(self, str):
        self.erase()
        self.addstr(1,1, str)

class ScrollWindow(BoxWindow):
    def __init__(self, *args, **kwargs):
        self.lines = []
        super(ScrollWindow, self).__init__(*args, **kwargs)

    def update(self, str):
        self.erase()
        str = ' '.join(str.split('\n'))
        self.lines.append(str)
        if len(self.lines) > (self.size[0]-2):
            self.lines.pop(0)

        for i,line in enumerate(self.lines):
            if len(line) > self.size[1]-2:
                line = line[:self.size[1]-5] + '...'
            self.addstr(i+1, 1, line)

def app(stdscr):
    maxY,maxX = stdscr.getmaxyx()

    w_stat = StatusWindow(status_size+2, maxX-2, 0, 0)
    w_log = ScrollWindow(log_size+2, maxX-2, maxY - log_size - 2, 0)
    w_main = BoxWindow(maxY - log_size - status_size - 4,
            maxX-2, status_size+2, 0)

    w_stat.update('Welcome to the program!')
    Window.refresh_all()
    while True:
        ch = w_main.getkey()
        if ch == 'q':
            break
        elif ch == 'c':
            w_log.erase()

        w_log.update('You typed: %s' % ch)
        w_log.update('''Lorem ipsum dolor sit amet, consectetur adipiscing
        elit. Aliquam ultricies, lorem eget hendrerit semper, enim urna
        tempor velit, non consectetur nibh arcu et tortor. Integer pretium
        blandit felis sit amet lacinia. Integer imperdiet feugiat magna id
        congue. Suspendisse at purus eget nulla vehicula hendrerit.
        Pellentesque varius, erat vitae congue tristique, nulla quam mattis
        libero, et consequat dui metus ut lectus. Phasellus mauris purus,
        consectetur eget dictum ut, varius non ante.''')

        Window.refresh_all()

if __name__ == '__main__':
    try:
        curses.wrapper(app)
    except:
        subprocess.call(['stty', 'sane'])
        raise

