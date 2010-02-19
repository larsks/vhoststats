#!/usr/bin/python -u

import os
import sys
import time
import curses
import optparse

import pqs

global opts

class Normalizer (object):
    def __init__ (self, t_max=100, v_max=0):
        self.t_max = t_max
        self.v_max = float(v_max)

    def __call__(self, v):
        if v > self.v_max:
            self.v_max = float(v)

        return int((v/self.v_max) * self.t_max)

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

