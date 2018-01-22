# -*- coding: utf-8 -*-
"""
Created on Fri Dec 16 17:11:09 2016

@author: drkiwi

Jeu de Go
"""
#
import sys
#
if __name__ == '__main__':
    import GoLib as gl
    gl.disp_info('Go Game')
#
    SIZE = int(raw_input('What Goban size do you wish to play on? '))
    while not 8 < SIZE < 20:
        print 'Board size has to be between 9 and 19.'
        SIZE = int(raw_input('What Goban size do you wish to play on? '))
#
    print 'Have a nice game'
    GOBAN = gl.Goban(SIZE)
#
    try:
        while True:
            print GOBAN
            GOBAN.play()
    except SystemExit:
        sys.exit(0)
    else:
        sys.exit(1)
#
