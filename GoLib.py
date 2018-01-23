# -*- coding: utf-8 -*-
"""
Created on Fri Dec 16 17:14:45 2016

@author: drkiwi
"""
#
import numpy
#
DISPFORMAT = '{:^60}'
DISPSEP = '-' * 60
DEBUG = False
#
class Goban(object):
    """Goban (go gameboard) instance"""
#
    def __init__(self, size=19):
        self.size = size
#       1 means black stone, 2 means white stone
        self.map = numpy.zeros((size, size), dtype=numpy.int)
        self.chainmap = numpy.zeros((size, size), dtype=numpy.int)
        self.chainlist = list()
#       creates a chain zero out of the board so that the first chain is indexed at 1
        self.chainlist.append(Chain(self, size, size, 0))
#       false means black turn, true means white turn
        self.turn = bool(0)
        self.disp = Gbview(size)
        self.game = Gosequence(self)
#
    def __str__(self):
        """represent an ASCII view of the goban"""
        print DISPFORMAT.format(self.disp.xlegend2)
        print DISPFORMAT.format(self.disp.xlegend1)
        print DISPFORMAT.format("_" * (self.size * 2 + 3))
        for i in xrange(self.size):
            line = "{:2d} | ".format(i)
            for j in xrange(self.size):
                if self.map[i][j] == 1 and not DEBUG:
                    line += 'o '
                elif self.map[i][j] == 2 and not DEBUG:
                    line += 'x '
#               (debug) to display chains on Goban
                elif self.chainmap[i][j] != 0 and DEBUG:
                    line += str(self.chainmap[i][j]) + ' '
                else:
                    line += '. '
            print DISPFORMAT.format(line+"| {:<2d}".format(i))
        print DISPFORMAT.format("|"+"_" * (self.size * 2 + 1)+"|")
        print DISPFORMAT.format(self.disp.xlegend1)
        print DISPFORMAT.format(self.disp.xlegend2)
        print DISPSEP
        if DEBUG:
            self.disp_liberties()
        return 'Black turn:' if self.turn == 0 else 'White turn:'
#
    def play(self):
        """ execute the action of placing a stone """
        try:
            entry_row, entry_col = raw_input('Enter line coordinate '), \
                                   raw_input('Enter column coordinate ')
            i, j = int(entry_row), int(entry_col)
        except ValueError:
            if entry_row == "pass" or entry_row == "Pass" or entry_row == "PASS":
                color = "White " if self.turn else "Black "
                disp_info(color + "player has passed")
                if self.game.is_passed():
                    end()
                else:
                    self.game.toggle_passed()
                    self.turn = not self.turn
#       EOFError occurs when the program is run with a text file into the standard input
        except EOFError:
            end()
        else:
            if self.game.is_passed():
                self.game.toggle_passed()
            if self.check_possible(i, j):
                try:
                    self.chain_stone(i, j)
                except GoLibError as err:
                    print "\n"
                    disp_info(err)
                else:
                    self.map[i][j] = 1 if not self.turn else 2
                    self.turn = not self.turn
                    self.update_score()
                    disp_info("Score: Black " + str(self.game.scoring[1]) + \
                    " White " + str(self.game.scoring[2]))
            else:
                pass
#
    def check_possible(self, i, j):
        """ check if the move is allowed """
        if not isinstance(i, int):
            disp_info("line coordinate has to be an integer")
            return False
        elif not isinstance(j, int):
            disp_info("column coordinate has to be an integer")
            return False
        elif i < 0 or i > self.size:
            disp_info("line coordinate out of range")
            return False
        elif j < 0 or j > self.size:
            disp_info("column coordinate out of range")
            return False
        elif not self.map[i][j] == 0:
            disp_info("it appears you can't play here")
            return False
        else:
            return True
#
    def chain_stone(self, i, j):
        """ create new chain or connect the last stone to existing ones """
        neighbor_chains, enemy_chains, surrounded = self.check_neighbors(i, j, \
        1 if not self.turn else 2)
#       check if the move is allowed in terms of liberties to come
        if surrounded:
            if not self.does_it_capture(enemy_chains):
                raise SurroundedError("Impossible to play a stone without any liberty")
            elif self.game.does_it_ko(enemy_chains, (i, j)):
                raise KoError("Ko situation: you can't play a stone that would \
recreate the board that followed your previous move")
#       remove a liberty to the neighboring enemies and capture them if able to
        if len(enemy_chains):
            for k in enemy_chains:
                self.chainlist[k].dellib(i, j)
#       add a stone to neighboring friends and merge them if possible
        if len(neighbor_chains):
            for k in neighbor_chains[1:]:
                self.chainlist[neighbor_chains[0]].merge(k)
            self.chainlist[neighbor_chains[0]].add(i, j)
            self.chainmap_update(neighbor_chains[0])
#       create a new chain
        else:
            self.chainlist.append(Chain(self, i, j, len(self.chainlist)))
#            if self.chainlist[len(self.chainlist)-1].getlib() == 0:
#                print 'noooooooooo'
            self.chainmap_update(len(self.chainlist)-1)
        self.game.reset_ko((i, j))
#
    def check_neighbors(self, i, j, player):
        """ check for existing neighboring chains and return idn lists"""
        enemy = 1 if player == 2 else 2
        neighbors_list = list()
        enemies_list = list()
        surrounded = True
        test = [i > 0, i < self.size-1, j > 0, j < self.size-1]
        coord = [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]
        for k, cond in enumerate(test):
            if cond:
                if self.map[coord[k][0]][coord[k][1]] == player:
                    neighbors_list.append(self.chainmap[coord[k][0]][coord[k][1]])
                    if self.chainlist[self.chainmap[coord[k][0]][coord[k][1]]].getlib() > 1:
                        surrounded = False
                elif self.map[coord[k][0]][coord[k][1]] == enemy:
                    enemies_list.append(self.chainmap[coord[k][0]][coord[k][1]])
                else:
                    surrounded = False
        return neighbors_list, set(enemies_list), surrounded
#
    def does_it_capture(self, enemies):
        """ check wether a move will capture any enemy or not """
        for k in enemies:
            if self.chainlist[k].getlib() == 1:
                return True
        return False
#
    def chainmap_update(self, idn):
        """ update chainmap attribute after a stone move """
        for coord_tupl in self.chainlist[idn].coords:
            self.chainmap[coord_tupl[0]][coord_tupl[1]] = idn
#
    def disp_liberties(self):
        """ debug purposes: print the details of all chains """
        for i, chain in enumerate(self.chainlist):
            print 'chainlist[{}]: {} stones, {} liberties'.format(i, \
            chain.stones, chain.getlib())
            print DISPSEP
#
    def update_score(self):
        """ update the current game score """
#       livestones[0] is not used, [1] is for black, [2] is for white
        livestones = [0, 0, 0]
        for chain in self.chainlist:
            if chain.is_alive():
                livestones[chain.player] += chain.stones
        self.game.set_score(livestones)
#
class Gbview(object):
    """ class used in Goban objects to store variables relative to the display """
#
    def __init__(self, size):
        """ Gbview constructor """
        self.xlegend2 = ' ' * 20
        self.xlegend2 += ' '.join([str(i)[1] for i in range(size) \
                                             if len(str(i)) > 1])
        self.xlegend1 = ' '.join([str(i)[0] for i in range(size)])
#
def disp_info(line):
    "Display game information"
    print DISPSEP
    print line
    print DISPSEP
#
def end():
    """ end of game launcher """
    print "\n"
    print "The game has ended"
    raise SystemExit()
#
class Chain(object):
    """ stone chain instance """
#
    def __init__(self, goban_obj, i, j, counter):
        """ create new chain """
        self.goban_father = goban_obj
        if hasattr(goban_obj, 'turn'):
            self.player = 1 if not goban_obj.turn else 2
        else:
#           concerns the chain-zero, when game has not begun
            self.player = 0
        self.idn = counter
        self.stones = 1
        self.alive = True
        self.coords = [(i, j),]
#       determine where the liberties are if not chain-zero
        if self.player:
            self.setlib()
        else:
            self.liberties = list()
#
    def is_alive(self):
        """ return the chain status (score related)  """
        return self.alive
#
    def getlib(self):
        """ return the number of liberties """
        return len(self.liberties)
#
    def getlen(self):
        """ return the number of stones """
        return self.stones
#
    def dellib(self, i, j):
        """ delete a specific liberty """
        self.liberties.remove((i, j))
        if not len(self.liberties):
            disp_info('{} player has captured {} stone(s)'.format( \
            'White' if self.player == 1 else 'Black', self.stones))
            self.captured()
            self.empty()
#
    def captured(self):
        """ remove the chain from the goban """
#        enemy_chains = set()
        for coord in self.coords:
            self.goban_father.map[coord[0]][coord[1]] = 0
            self.goban_father.chainmap[coord[0]][coord[1]] = 0
            enemy_chains = self.goban_father.check_neighbors(coord[0], \
            coord[1], 1 if self.goban_father.turn else 2)[1]
            for k in enemy_chains:
#                if coord not in self.goban_father.chainlist[k].liberties:
                self.goban_father.chainlist[k].liberties.append(coord)
#
    def setlib(self):
        """ update the liberties from scratch """
        self.liberties = list()
        for (i, j) in self.coords:
            if i > 0 and self.goban_father.map[i-1][j] == 0:
                if not (i-1, j) in self.liberties:
                    self.liberties.append((i-1, j))
            if i < self.goban_father.size-1 and self.goban_father.map[i+1][j] == 0:
                if not (i+1, j) in self.liberties:
                    self.liberties.append((i+1, j))
            if j > 0 and self.goban_father.map[i][j-1] == 0:
                if not (i, j-1) in self.liberties:
                    self.liberties.append((i, j-1))
            if j < self.goban_father.size-1 and self.goban_father.map[i][j+1] == 0:
                if not (i, j+1) in self.liberties:
                    self.liberties.append((i, j+1))
#
    def add(self, i, j):
        """ add a stone to an existing chain """
        self.stones += 1
        self.coords.append((i, j))
        self.liberties.remove((i, j))
        test = [i > 0, i < self.goban_father.size-1, j > 0, \
        j < self.goban_father.size-1]
        coord = [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]
        for k, cond in enumerate(test):
            if cond and self.goban_father.map[coord[k][0]][coord[k][1]] == 0:
                if not coord[k] in self.liberties:
                    self.liberties.append(coord[k])
#        self.goban_father.chainmap_update(self.idn)
#
    def merge(self, other_idn):
        """ merge two chains (one will remain empty) """
        self.stones += self.goban_father.chainlist[other_idn].stones
        self.coords.extend(self.goban_father.chainlist[other_idn].coords)
        self.liberties.extend(self.goban_father.chainlist[other_idn].liberties)
#       remove duplicates
        self.liberties = list(set(self.liberties))
        self.goban_father.chainlist[other_idn].empty()
#        self.goban_father.chainmap_update(self.idn)
#
    def empty(self):
        """ empty an existing chain """
        self.stones = 0
        self.coords = list()
#
class Gosequence(object):
    """ class used in Goban objects to store the sequence of some events """
    def __init__(self, goban_obj):
        """ sequence constructor """
        self.goban_father = goban_obj
        self.passed = bool(0)
        self.singlecaptured = None
        self.lastplayed = None
        self.scoring = [0, 0, 0]
#
    def is_passed(self):
        """ check on the "passed" attribute """
        return self.passed
#
    def toggle_passed(self):
        """ toggle the boolean "passed" attribute """
        self.passed = not self.passed
#
    def does_it_ko(self, enemies, currentmove):
        """ test ensuring the played move is not restricted by a ko situation """
        captured = 0
        for k in enemies:
            if self.goban_father.chainlist[k].getlib() == 1:
                if not captured and self.goban_father.chainlist[k].getlen() == 1:
                    captured = k
#               the capture is bigger than one stone or one chain
                else:
                    return False
        if self.lastplayed == self.goban_father.chainlist[captured].coords[0] and \
        currentmove == self.singlecaptured:
            return True
        else:
            self.singlecaptured = self.goban_father.chainlist[captured].coords[0]
            self.lastplayed = currentmove
            return False
#
    def reset_ko(self, currentmove):
        """ reset the ko history if it has not been updated by the current move """
        if self.lastplayed != currentmove:
            self.singlecaptured = None
            self.lastplayed = None
#
    def set_score(self, livestones):
        """ set the score of both players on the current goban """
        self.scoring = livestones
#
class GoLibError(Exception):
    """ specific errors to be raised within the lib """
    pass
#
class SurroundedError(GoLibError, ValueError):
    """ error to be raised when a player attempts to play in a surrounded location """
    pass
#
class KoError(GoLibError, ValueError):
    """ error to be raised when a player attempts a ko situation """
    pass
#
    