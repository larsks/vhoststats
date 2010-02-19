#!/usr/bin/python -u

import os
import sys
import time
import curses
import optparse

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
    def __init__ (self, opts):
        self.opts = opts
        self.parser = pqs.Parser()
        self.parser.addchars(('[',']'))

    def curses_entry(self, stdscr):
        self.winX, self.winY = stdscr.getmaxyx()
        self.centerY = int(float(winY)/2)

    def _init_colors(self):
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

def parse_args():
    p = optparse.OptionParser()
    p.add_option('-v', '--vhost-field', default='0')
    p.add_option('-t', '--time-field',  default='4')
    p.add_option('-s', '--size-field',  default='7')
    p.add_option('-w', '--win-size', default='300')
    return p.parse_args()

def genplot(stdscr):
    p = pqs.Parser()
    p.addchars(('[',']'))

    totals = {}
    stack = []
    wsize       = int(opts.win_size)
    maxhostlen  = 20
    numlen      = 10
    padding     = 6

    winY,winX = stdscr.getmaxyx()
    centerY = int(float(winY)/2)
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

    rnorm = Normalizer(t_max = (winX-maxhostlen-numlen-padding)-2)
    bnorm = Normalizer(t_max = (winX-maxhostlen-numlen-padding)-2)

    hosts = set()

    while True:
        line = sys.stdin.readline()
        if not line:
            break

        try:
            entry = [x[1] for x in p.parse(line)]

            f_vhost = int(opts.vhost_field)
            f_size = int(opts.size_field)
            f_time = int(opts.time_field)

            if not entry[f_size].isdigit():
                continue

            now = time.mktime(time.strptime(
                    entry[f_time].split()[0],'%d/%b/%Y:%H:%M:%S'))
            stack.append((now,
                entry[f_vhost],
                int(entry[f_size])))
        except IndexError:
            continue

        newstack = []
        totals = {}
        for when, vhost, bytes in stack:
            hosts.add(vhost)
            if (now-when) < wsize:
                totals.setdefault(vhost, { 'r': 0, 'b': 0 })
                totals[vhost]['r'] += 1
                totals[vhost]['b'] += bytes
                newstack.append((when, vhost, bytes))

        stack = newstack

        s_hosts = list(reversed(sorted(hosts,
            cmp=lambda x,y: cmp(totals.get(x, {'b':0})['b'],
                totals.get(y, {'b':0})['b']))))

        if len(s_hosts) >= centerY:
            s_hosts = s_hosts[:centerY-3]

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
    global opts
    opts, args = parse_args()

    curses.wrapper(genplot)

if __name__ == '__main__':
    main()

