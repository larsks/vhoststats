#!/usr/bin/python -u

import os
import sys
import time
import curses
import optparse
import signal
import errno

import pqs

global opts

class Normalizer (object):
    '''A class to normalize values against a target range (0, t_max).  The
    highest value seen will always == t_max, and other values will be
    adjusted accordingly.  The following example illustrates this
    behavior::

        >>> N = Normalizer()
        >>> N(100)
        100
        >>> N(50)
        50
        >>> N(200)
        100
        >>> N(50)
        25

    Note that the default configuration uses t_max=100, but you can change
    this when you create a Normalizer object.'''

    def __init__ (self, t_max=100, v_max=0):
        '''Parameters:
        
        - t_max -- maximum value of target range.
        - v_max -- initialize largest input value.

        The value of v_max will change if you call the object with v >
        v_max.'''

        self.t_max = t_max
        self.v_max = float(v_max)

    def __call__(self, v):
        '''Normalize a value v.'''
        if v > self.v_max:
            self.v_max = float(v)

        return int((v/self.v_max) * self.t_max)

class Hoststats (object):
    def __init__ (self,
            src=sys.stdin,
            vhost_field=0,
            time_field=4,
            size_field=7,
            window_size=300,
            maxhostlen=0,
            maxcountlen=10,
            sortkey='b'):

        if hasattr(src, 'readline'):
            self.src = src
        else:
            self.src = open(src)

        self.vhost_field= int(vhost_field)
        self.time_field = int(time_field)
        self.size_field = int(size_field)
        self.window_size = int(window_size)
        self.maxhostlen= int(maxhostlen)
        self.maxcountlen=10
        self.sortkey = sortkey.lower()

        self.parser = pqs.Parser()
        self.parser.addchars(('[',']'))

    def curses_entry(self, stdscr):
        self.stdscr = stdscr
        self._init_curses()

        self._loop()

    def _sigwinch_handler(self, sig, frame):
        curses.endwin()
        self.stdscr.refresh()
        self._init_curses()

    def _init_curses(self):
        self.winY, self.winX = self.stdscr.getmaxyx()
        self.centerY = int(float(self.winY)/2)
        self._init_colors()

    def _init_colors(self):
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)

    def _init_loop_vars(self):
        self.stack = []
        self.requests = 0
        self.hosts = set()
        self.sorted_hosts = []
        self.curmaxhostlen = 0

        self.bnorm = Normalizer()
        self.rnorm = Normalizer()

    def _init_signals(self):
        signal.signal(signal.SIGWINCH, self._sigwinch_handler)

    def _loop(self):
        self._init_loop_vars()
        self._init_signals()

        while True:
            try:
                line = self.src.readline()
                if not line:
                    break
            except IOError, detail:
                if detail.errno == errno.EINTR:
                    continue
                raise

            try:
                self._load(line)
            except (IndexError, ValueError), detail:
                self.errmsg = str(detail)
                continue

            self._update_totals()
            self._limit_hosts()
            self._update_screen()

    def _limit_hosts(self):
        self.sorted_hosts = list(reversed(sorted(self.hosts,
            cmp=lambda x,y: cmp(self.totals.get(x, {'r':0,'b':0})[self.sortkey],
                self.totals.get(y, {'r':0,'b':0})[self.sortkey]))))

        if len(self.sorted_hosts) >= self.centerY:
            self.sorted_hosts = self.sorted_hosts[:self.centerY-3]

    def _update_screen(self):
        hlen = self.maxhostlen and self.maxhostlen or self.curmaxhostlen
        clen = self.maxcountlen

        label = '%%-%ds' % hlen
        counter = '[%%s:%%-%dd] ' % clen
        labellen = len(label % (' '*hlen))
        counterlen = len(counter % ('B', 0))

        self.bnorm.t_max = self.winX - labellen - counterlen - 4
        self.rnorm.t_max = self.winX - labellen - counterlen - 4

        self.stdscr.erase()
        self.stdscr.addstr(0,0,'[%s] Hosts: %d [Displayed: %d] Requests: %d' %
                (time.strftime('%Y/%m/%d %H:%M:%S',
                    time.localtime(self.now)),
                    len(self.hosts), len(self.sorted_hosts), self.requests))

        hosty = self.centerY + len(self.sorted_hosts) - 1

        for host in self.sorted_hosts:
            bytes = self.totals.get(host, {'b':0,'r':0})['b']
            requests = self.totals.get(host, {'b':0,'r':0})['r']

            self.stdscr.addstr(hosty-1,0,
                    label % ((host + ' '*hlen)[:hlen]),
                    curses.color_pair(3))
            self.stdscr.addstr(hosty-1,labellen+1,
                    counter % ('R', requests))
            self.stdscr.addstr(hosty-1, labellen+counterlen+2,
                    '#'*self.rnorm(requests),
                    curses.color_pair(1))

            self.stdscr.addstr(hosty,0,
                    label % (' '*hlen))
            self.stdscr.addstr(hosty,labellen+1,
                    counter % ('B', bytes))
            self.stdscr.addstr(hosty, labellen+counterlen+2,
                    '#'*self.bnorm(bytes),
                    curses.color_pair(2))

            hosty -= 2

        self.stdscr.refresh()

    def _load(self, line):
        entry = [x[1] for x in self.parser.parse(line)]

        self.now = time.mktime(time.strptime(
                entry[self.time_field].split()[0],'%d/%b/%Y:%H:%M:%S'))

        self.curmaxhostlen = max(self.curmaxhostlen,
                len(entry[self.vhost_field]))

        self.stack.append((self.now,
            entry[self.vhost_field],
            int(entry[self.size_field])))

        self.requests += 1

    def _update_totals(self):
        newstack = []
        self.totals = {}

        for when, vhost, bytes in self.stack:
            self.hosts.add(vhost)
            if (self.now-when) < self.window_size:
                self.totals.setdefault(vhost, { 'r': 0, 'b': 0 })
                self.totals[vhost]['r'] += 1
                self.totals[vhost]['b'] += bytes
                newstack.append((when, vhost, bytes))

        self.stack = newstack

def parse_args():
    p = optparse.OptionParser()
    p.add_option('-v', '--vhost-field', default='0')
    p.add_option('-t', '--time-field',  default='4')
    p.add_option('-s', '--size-field',  default='7')
    p.add_option('-w', '--window-size', default='300')
    p.add_option('-B', '--bytes', action='store_const', const='b',
            dest='sortkey')
    p.add_option('-R', '--requests', action='store_const', const='r',
            dest='sortkey')

    p.set_defaults(sortkey='b')

    return p.parse_args()

def genplot(stdscr):
    totals = {}
    stack = []
    wsize       = int(opts.win_size)
    maxhostlen  = 20
    numlen      = 10
    padding     = 6

    rnorm = Normalizer(t_max = (winX-maxhostlen-numlen-padding)-2)
    bnorm = Normalizer(t_max = (winX-maxhostlen-numlen-padding)-2)

    hosts = set()

    while True:
        line = sys.stdin.readline()
        if not line:
            break

        hosty = centerY + len(s_hosts) - 2

        try:
            stdscr.erase()
            for host in s_hosts:
                data = totals.get(host, {'b':0, 'r':0})
                stdscr.addstr(hosty, 0, (host + ' '*maxhostlen)[:maxhostlen],
                        curses.color_pair(2))

                # output labels
                stdscr.addstr(hosty,    maxhostlen+1,
                        '[B:%%-%dd]' % numlen % data['b'])
                stdscr.addstr(hosty+1,  maxhostlen+1,
                        '[R:%%-%dd]' % numlen % data['r'])

                # output bars
                stdscr.addstr(hosty,
                        maxhostlen + numlen + padding,
                        '#'*bnorm(data['b']),
                        curses.color_pair(1))
                stdscr.addstr(hosty+1,
                        maxhostlen + numlen + padding,
                        '#'*rnorm(data['r']))
                hosty -= 2
        except curses.error:
            pass

        stdscr.refresh()

def main():
    opts, args = parse_args()
    app = Hoststats(
            vhost_field = opts.vhost_field,
            time_field = opts.time_field,
            size_field = opts.size_field,
            window_size = opts.window_size,
            maxhostlen = 20,
            sortkey = opts.sortkey,
            )

    curses.wrapper(app.curses_entry)

if __name__ == '__main__':
    main()

