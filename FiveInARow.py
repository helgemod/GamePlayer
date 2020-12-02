#!/usr/bin/env python

"""
# FiveInARow implements game with same name, based on algorithms of
#  choice.
#
# The purpose of this is:
#   1) Implement the game in a generic way.
#   2) For demo purpose and educational purpose. And perhaps some amusement.
#
# Usage:
#
#   Make an object of class FiveInARow and attach your own GUI to it. Two example
#   classes are attached that examplifies how to use class FiveInARow.
#
#   When creating object, try out other game algorithms than MinMax, by
#   attaching these to "computerAlgo".
#
"""

import MinMaxAlgorithm as mma
import StrideDimensions as sd
import re
import time
import random
import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s=> %(message)s')

__author__ = "Helge Modén, www.github.com/helgemod"
__copyright__ = "Copyright 2020, Helge Modén"
__credits__ = None
__license__ = "MIT"
__version__ = "1.0.1"
__maintainer__ = "Helge Modén, https://github.com/helgemod/MinMaxAlgorithm"
__email__ = "helgemod@gmail.com"
__status__ = "https://github.com/helgemod/GamePlayer"
__date__ = "2020-11-24"

class FiveInARow:

    X_TOKEN = 'X'
    O_TOKEN = 'O'
    NO_TOKEN = '-'

    MIN_EVAL = -1000
    MAX_EVAL = 1000

    ANALYZE_ROW = 'AnalyzeRow'
    ANALYZE_COL = 'AnalyzeCol'
    ANALYZE_DIAUP = 'AnalyzeDiagonalUp'
    ANALYZE_DIADW = 'AnalyzeDiagonalDown'
    KEY_COORD_COL = 'keyCoordColumn'
    KEY_COORD_ROW = 'keyCoordRow'

    KEY_LIST_OF_WINNING_MOVES_FOR_X = 'keyListOfWinningMovesForX'
    KEY_LIST_OF_WINNING_MOVES_FOR_O = 'keyListOfWinningMovesForO'
    KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_X = 'keyListOfPotentialWinningMovesForX'
    KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_O = 'keyListOfPotentialWinningMovesForO'
    KEY_LIST_OF_WINNERS_X = 'keyListOfWinnersX'
    KEY_LIST_OF_WINNERS_O = 'keyListOfWinnersO'

    # Change this for different weight of different positions
    evaluations = {#Combinations with one
                   '-X-': 2,
                   '-O-': -2,
                   # Combinations with two
                   '-XX-': 6,
                   '-OO-': -6,
                   '-X-X-': 5,
                   '-O-O-': -5,
                   '---XX0': 2,
                   'OXX---': 2,
                   '---OOX': -2,
                   'XOO---': -2,
                    # Combinaitons with three
                   '-XXX-': 20,
                   '-OOO-': -20,

                   'OXXX--': 10,
                   '--XXXO': 10,
                   'XOOO--': -10,
                   '--OOOX': -10,

                    '-XX-X-': 20,
                    '-X-XX-': 20,
                    'OXX-X-': 10,
                    '-X-XXO': 10,
                    'OX-XX-': 10,
                    '-XX-XO': 10,
                    'OXX-XO': 0,

                    '-OO-O-': -20,
                    '-O-OO-': -20,
                    'XOO-O-': -10,
                    '-O-OOX': -10,
                    'XO-OO-': -10,
                    '-OO-OX': -10,
                    'XOO-OX': 0,

                    # Combinations with four
                    '-XXXX-': 60,
                    '-XXXXO': 50,
                    'OXXXX-': 50,
                    '-OOOO-': -60,
                    'XOOOO-': -50,
                    '-OOOOX': -50,
                    '-X-XXX-': 60,
                    '-XXX-X-': 60,
                    '-O-OOO-': -60,
                    '-OOO-O-': -60,

                   'XXXXX': MAX_EVAL,
                   'OOOOO': MIN_EVAL,
                }



    potentialWinnersX = [
        ['-XXX-',  [0,4]],
        ['-X-XX-', [2]],
        ['-XX-X-', [3]],
    ]
    potentialWinnersO = [
        ['-OOO-',  [0,4]],
        ['-O-OO-', [2]],
        ['-OO-O-', [3]],
    ]
    definitivWinnersX = [
        ['-XXXX', [0]],
        ['X-XXX', [1]],
        ['XX-XX', [2]],
        ['XXX-X', [3]],
        ['XXXX-', [4]],
    ]
    definitivWinnersO = [
        ['-OOOO', [0]],
        ['O-OOO', [1]],
        ['OO-OO', [2]],
        ['OOO-O', [3]],
        ['OOOO-', [4]],
    ]
    winnersX = [
        ['XXXXX', [0, 4]],
    ]
    winnersO = [
        ['OOOOO', [0, 4]],
    ]


    # In future this can be able to point at different algorithms
    # to test them.
    computerAlgo = None

    def __init__(self):
        self.whoHas = self.X_TOKEN
        self.playersToken = self.X_TOKEN
        self.board = sd.StrideDimension((6, 6))
        self.board.fillData(self.NO_TOKEN)
        self.computerAlgo = mma.GameAlgo(self.evalBoard,
                                           self.moveX, self.moveO,
                                           self.undoMove, self.undoMove,
                                           self.getPossibleMovesMaximizer, self.getPossibleMovesMinimizer,
                                           self.MIN_EVAL, self.MAX_EVAL)

    ########################################
    #
    #           Game interface
    #
    ########################################
    #Call this to get the board for print.
    def getBoard(self):
        return self.board.getDimensionalData((None, None))

    # Makes an actual move and do all administrations. Return True if move could be made. Else False.
    def makeMove(self, coordinates, token):
        try:
            self.__checkMove(coordinates, token)
        except Exception as err:
            print(str(err))
            return False
        self.board.setData(coordinates, token)
        self.__invertWhoHas()
        self.__extendBoardIfCloseToEdge()
        return True

    def getComputersMoveForCurrentPosition(self):
        # Special case
        # 1) Is it the first move?
        if self.__isBoardEmpty():
            return ((self.getNumberOfColumns()//2, self.getNumberOfRows()//2), self.whoHas)

        ocoord = self.__isFirstMoveForO()
        if ocoord is not None:
            return (ocoord, self.whoHas)

        #move = self.computerAlgo.calculateMove(mma.MINMAX_ALGO, self.whoHas == self.X_TOKEN, 4)
        move = self.computerAlgo.calculateMove(mma.MINMAXALPHABETAPRUNING_ALGO, self.whoHas == self.X_TOKEN, 4)
        #move = self.computerAlgo.calculateMove(mma.MINMAX_ALGO_WITH_LOGGING, self.whoHas == self.X_TOKEN, 4)
        if move is None:
            print("\n\n**********MOVE IS NONE*********\n\n")
        return (self.board.dimCoordinateForIndex(move), self.whoHas)

    def getWinnerOfCurrentPosition(self):
        allBoardData = self.board.getAllData()
        if allBoardData.count(self.X_TOKEN) < 5 and allBoardData.count(self.O_TOKEN) < 5:
            return None

        currentEvaluation = self.evalBoard()
        if currentEvaluation >= self.MAX_EVAL-200:
            return self.X_TOKEN
        elif currentEvaluation <= self.MIN_EVAL+200:
            return self.O_TOKEN
        elif self.__isBoardFull():
            return self.NO_TOKEN
        return None

    def resetGame(self):
        self.whoHas = self.X_TOKEN
        self.board = sd.StrideDimension((6, 6))
        self.board.fillData(self.NO_TOKEN)

    def getNumberOfColumns(self):
        return self.board.dimensions[0]

    def getNumberOfRows(self):
        return self.board.dimensions[1]

    ###############################################
    #
    # Callback Interfaces for different algorithms
    #
    ###############################################
    # Callback functions used by computer algorithm
    def evalBoard(self):
        addEval = 0
        for r in range(self.getNumberOfRows()):
            row = self.board.getDimensionalData((None, r+1))
            tmpEval1 = self.evaluateList(row)
            if tmpEval1 <= self.MIN_EVAL + 200 or tmpEval1 >= self.MAX_EVAL - 200:
                return tmpEval1
            addEval += tmpEval1

        for c in range(self.getNumberOfColumns()):
            col = self.board.getDimensionalData((c+1, None))
            tmpEval2 = self.evaluateList(col)
            if tmpEval2 <= self.MIN_EVAL + 200 or tmpEval2 >= self.MAX_EVAL - 200:
                return tmpEval2
            addEval += tmpEval2


        # Now check diagonals UPWARDS /

        for dcu in range(self.getNumberOfColumns()):
            diaUpCol = self.board.getDimensionalDataWithDirection((dcu + 1, 1), (1, 1))
            tmpEval3 = self.evaluateList(diaUpCol)
            if tmpEval3 <= self.MIN_EVAL + 200 or tmpEval3 >= self.MAX_EVAL - 200:
                return tmpEval3
            addEval += tmpEval3

        for dru in range(self.getNumberOfRows()-1):
            diaUpRow = self.board.getDimensionalDataWithDirection((1, dru + 2), (1, 1))
            tmpEval4 = self.evaluateList(diaUpRow)
            if tmpEval4 <= self.MIN_EVAL + 200 or tmpEval4 >= self.MAX_EVAL - 200:
                return tmpEval4
            addEval += tmpEval4

        # Now check diagonals DOWNWARDS \
        #
        # 1) Start in upper-left corner and go downward in first col
        #    and pick out the downward diagonal.
        noOfCol = self.getNumberOfColumns()
        noOfRows = self.getNumberOfRows()
        for dcd in range(noOfCol):
            diaDownCol = self.board.getDimensionalDataWithDirection((1, noOfRows - dcd), (1, -1))
            tmpEval5 = self.evaluateList(diaDownCol)
            if tmpEval5 <= self.MIN_EVAL + 200 or tmpEval5 >= self.MAX_EVAL - 200:
                return tmpEval5
            addEval += tmpEval5

        # 2) Start in upper-left corner and go right in upper row
        #    and pick out the downward diagonal.
        for drd in range(noOfRows-1):
            diaDownRow = self.board.getDimensionalDataWithDirection((drd + 2, noOfRows), (1, -1))
            tmpEval6 = self.evaluateList(diaDownRow)
            if tmpEval6 <= self.MIN_EVAL + 200 or tmpEval6 >= self.MAX_EVAL - 200:
                return tmpEval6
            addEval += tmpEval6
        return addEval

    def moveX(self, move):
        self.board.setDataAtIndex(move, self.X_TOKEN)

    def moveO(self, move):
        self.board.setDataAtIndex(move, self.O_TOKEN)

    def undoMove(self, move):
        self.board.setDataAtIndex(move, self.NO_TOKEN)

    def getPossibleMovesMaximizer(self):
        return self.getMovesSorted(True)

    def getPossibleMovesMinimizer(self):
        return self.getMovesSorted(False)




    ########################
    #
    # Private help methods
    #
    ########################

    def __invertWhoHas(self):
        if self.whoHas==self.X_TOKEN:
            self.whoHas=self.O_TOKEN
        else:
            self.whoHas=self.X_TOKEN

    # Checks if the "token" is ok to place at "coordinate". Raises exception if not!
    def __checkMove(self, coordinate, token):
        if token not in (self.X_TOKEN, self.O_TOKEN):
            raise Exception("Only \'X\' or \'O\' is allowed as token!")

        if not self.whoHas == token:
            raise Exception("Wrong players move")
        try:
            x = int(coordinate[0])
            y = int(coordinate[1])
        except:
            raise Exception("Give tuple of integer as move! E.g. (1,1)")

        if x < 1 or x > self.board.dimensions[0] or y < 1 or y > self.board.dimensions[1]:
            raise Exception("!!!! Coords out of range !!!")

        if not self.__isFree((x, y)):
            raise Exception("!!! OCCUPIED SQUARE !!!")

    # Takes a list and returns X if all elements are X. Return o if all elements are O. Else return None.
    def __checkIfAllArePlayerTokens(self, ll):
        if self.NO_TOKEN in ll:
            return None
        if all([x == self.X_TOKEN for x in ll]):
            return self.X_TOKEN
        if all([o == self.O_TOKEN for o in ll]):
            return self.O_TOKEN
        return None

    def __isBoardFull(self):
        if self.NO_TOKEN in self.board.getAllData():
            return False
        return True

    def __isFree(self,coordinate):
        return self.board.getData(coordinate)==self.NO_TOKEN

    def __isBoardEmpty(self):
        return all(x == self.NO_TOKEN or x is None for x in self.board.getAllData())

    def __isFirstMoveForO(self):
        if self.board.getAllData().count(self.X_TOKEN) == 1:
            xind = self.board.getIndexAtFirstOccurrenceOfData(self.X_TOKEN)
            xcoord = self.board.dimCoordinateForIndex(xind)
            ocoord = [1, 1]
            while True:
                xadd = random.randint(-1, 1)
                yadd = random.randint(-1, 1)
                ocoord[0] = xcoord[0] + xadd
                ocoord[1] = xcoord[1] + yadd
                if not ocoord == xcoord:
                    break
            return ocoord
        else:
            return None

    # If it is a long game, the board may be extended during the game.
    def __extendBoardIfCloseToEdge(self):
        extends = self.__numberOfExtendsNeededToEdgeLow()
        if extends > 0:
            self.board.extendDimension(2, 1, True, self.NO_TOKEN)
        extends = self.__numberOfExtendsNeededToEdgeHigh()
        if extends > 0:
            self.board.extendDimension(2, 1, False, self.NO_TOKEN)
        extends = self.__numberOfExtendsNeededToEdgeLeft()
        if extends > 0:
            self.board.extendDimension(1, 1, True, self.NO_TOKEN)
        extends = self.__numberOfExtendsNeededToEdgeRight()
        if extends > 0:
            self.board.extendDimension(1, 1, False, self.NO_TOKEN)

    def __numberOfExtendsNeededToEdgeLow(self):
        extendsNeeded = 0
        ll = self.board.getDimensionalData((None, 1))
        if not all([x == self.NO_TOKEN for x in ll]):
            extendsNeeded = 2
        if extendsNeeded==0:
            ll = self.board.getDimensionalData((None, 2))
            if not all([x == self.NO_TOKEN for x in ll]):
                extendsNeeded = 1
        return extendsNeeded

    def __numberOfExtendsNeededToEdgeHigh(self):
        extendsNeeded = 0
        ll = self.board.getDimensionalData((None, self.getNumberOfRows()))
        if not all([x == self.NO_TOKEN for x in ll]):
            extendsNeeded = 2
        if extendsNeeded == 0:
            ll = self.board.getDimensionalData((None, self.getNumberOfRows()-1))
            if not all([x == self.NO_TOKEN for x in ll]):
                extendsNeeded = 1
        return extendsNeeded

    def __numberOfExtendsNeededToEdgeLeft(self):
        extendsNeeded = 0
        ll = self.board.getDimensionalData((1, None))
        if not all([x == self.NO_TOKEN for x in ll]):
            extendsNeeded = 2
        if extendsNeeded == 0:
            ll = self.board.getDimensionalData((2, None))
            if not all([x == self.NO_TOKEN for x in ll]):
                extendsNeeded = 1
        return extendsNeeded

    def __numberOfExtendsNeededToEdgeRight(self):
        extendsNeeded = 0
        ll = self.board.getDimensionalData((self.getNumberOfColumns(), None))
        if not all([x == self.NO_TOKEN for x in ll]):
            extendsNeeded = 2
        if extendsNeeded == 0:
            ll = self.board.getDimensionalData((self.getNumberOfColumns() - 1, None))
            if not all([x == self.NO_TOKEN for x in ll]):
                extendsNeeded = 1
        return extendsNeeded


    ################################
    #
    # Help functions for evaluator
    # - Change these to increase
    #   engines strength.
    #
    ################################

    # Help methods to pick out proper moves to feed MinMax-Algo
    def evaluateList(self, dataList):
        if len(dataList) == 0:
            return 0
        dataString = ''.join(dataList)
        if dataString[0] == self.NO_TOKEN and dataString.count(dataString[0]) == len(dataString):
            return 0
        addVal = 0
        for pattern in self.evaluations:
            result = re.search(pattern, dataString)
            if result is not None:
                addVal += self.evaluations[pattern]
        return addVal

    def getMovesSorted(self, regardingMaximizer):
        scanDict = self.scanBoard()

        # 1 - Is there a winner on board. No more moves are possible
        if len(scanDict[self.KEY_LIST_OF_WINNERS_X]) > 0 or len(scanDict[self.KEY_LIST_OF_WINNERS_O]) > 0:
            return []

        # 2) One move away from a win
        if regardingMaximizer:
            # 2) If I (as X) have at least one winning move. Return the first.
            if len(scanDict[self.KEY_LIST_OF_WINNING_MOVES_FOR_X]) > 0:
                return [self.board.indexForDimCoordinate(scanDict[self.KEY_LIST_OF_WINNING_MOVES_FOR_X][0])]
            # 3) If opponent (as O) have at least one winning move. Return first move, to stop him.
            elif len(scanDict[self.KEY_LIST_OF_WINNING_MOVES_FOR_O]) > 0:
                return [self.board.indexForDimCoordinate(scanDict[self.KEY_LIST_OF_WINNING_MOVES_FOR_O][0])]
        else:
            # 2) If I (as O) have at least one winning move. Return the first.
            if len(scanDict[self.KEY_LIST_OF_WINNING_MOVES_FOR_O]) > 0:
                return [self.board.indexForDimCoordinate(scanDict[self.KEY_LIST_OF_WINNING_MOVES_FOR_O][0])]
            # 3) If opponent (as X) have at least one winning move. Return first move, to stop him.
            elif len(scanDict[self.KEY_LIST_OF_WINNING_MOVES_FOR_X]) > 0:
                return [self.board.indexForDimCoordinate(scanDict[self.KEY_LIST_OF_WINNING_MOVES_FOR_X][0])]

        # 3) Potential winners.
        if regardingMaximizer:
            # 2) If I (as X) have potential winning moves. Return them.
            if len(scanDict[self.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_X]) > 0:
                return [self.board.indexForDimCoordinate(x) for x in scanDict[self.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_X]]
            # 3) If opponent (as O) have potential winning moves. Return them.
            elif len(scanDict[self.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_O]) > 0:
                return [self.board.indexForDimCoordinate(x) for x in scanDict[self.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_O]]
        else:
            # 2) If I (as O) have potential winning moves. Return them.
            if len(scanDict[self.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_O]) > 0:
                return [self.board.indexForDimCoordinate(x) for x in scanDict[self.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_O]]
            # 3) If opponent (as X) have potential winning moves. Return them.
            elif len(scanDict[self.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_X]) > 0:
                return [self.board.indexForDimCoordinate(x) for x in scanDict[self.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_X]]

        # 5) If we come down here. There are no obvious winning move. Pick out a list of suggestions.

        # Ask board for all empty squares.
        readList = self.board.getIndexListWhereDataIs(self.NO_TOKEN)

        # Resort the list of moves, to make the ones in "the middle" of board be evaluated first.
        moveList = []
        middleIndex = len(readList) // 2
        loops = len(readList)//2
        moveList.append(readList[middleIndex])
        for i in range(1, loops+1):
            itoadd = middleIndex - i
            if 0 <= itoadd < len(readList):
                moveList.append(readList[itoadd])
            itoadd = middleIndex + i
            if 0 <= itoadd < len(readList):
                moveList.append(readList[itoadd])

        moveEvalDict = {}
        bestDiffMax = self.MIN_EVAL
        bestDiffMin = self.MAX_EVAL

        for move in moveList:
            moveCoords = tuple(self.board.dimCoordinateForIndex(move))

            preEval = self.evaluateList(self.getColForCoord(moveCoords))
            preEval += self.evaluateList(self.getRowForCoord(moveCoords))
            preEval += self.evaluateList(self.getDiagonalForCoordUp(moveCoords))
            preEval += self.evaluateList(self.getDiagonalForCoordDown(moveCoords))

            # 2) Try the move
            if regardingMaximizer:
                self.moveX(move)
            else:
                self.moveO(move)

            # 3) Evaluate after the move try
            postEval = self.evaluateList(self.getColForCoord(moveCoords))
            postEval += self.evaluateList(self.getRowForCoord(moveCoords))
            postEval += self.evaluateList(self.getDiagonalForCoordUp(moveCoords))
            postEval += self.evaluateList(self.getDiagonalForCoordDown(moveCoords))

            # 4) Undo the move try
            self.undoMove(move)

            evalDiff = postEval - preEval

            if regardingMaximizer:
                bestDiffMax = max(bestDiffMax, evalDiff)
                if evalDiff > (bestDiffMax - 10):
                    moveEvalDict[move] = evalDiff
            else:
                bestDiffMin = min(bestDiffMin, evalDiff)
                if evalDiff < (bestDiffMin + 10):
                    moveEvalDict[move] = evalDiff

        # So far all sensible moves are evaluated and placed into a dictionary.
        # Keys are moves. Value are the "evalDiff" (how much difference that move makes).
        sorted_values = sorted(moveEvalDict.values(), reverse=regardingMaximizer)
        sortedDict = {}
        for i in sorted_values:
            for k in moveEvalDict.keys():
                if moveEvalDict[k] == i:
                    sortedDict[k] = moveEvalDict[k]

        bestEval = sorted_values[0]

        bestOfDic = {}
        cntr = 0
        for key in sortedDict.keys():
            if sortedDict[key] > bestEval - 15:
                bestOfDic[key] = sortedDict[key]
            cntr += 1
            if cntr == 3:
                break

        listToReturn = list(bestOfDic.keys())
        return listToReturn

    def __startAndEndCoordForMatchInCol(self, colNr, span):
        coordStart = []
        coordEnd = []
        coordStart += [colNr]
        coordEnd += [colNr]
        coordStart += [span[0] + 1]
        coordEnd += [span[1]]
        return (tuple(coordStart), tuple(coordEnd))

    def __startAndEndCoordForMatchInRow(self, rowNr, span):
        coordStart = []
        coordEnd = []
        coordStart += [span[0] + 1]
        coordEnd += [span[1]]
        coordStart += [rowNr]
        coordEnd += [rowNr]
        return (tuple(coordStart), tuple(coordEnd))

    def __startAndEndCoordForMatchInDiagonalUpLeftSide(self, diagonalNr, span):
        coordStart = []
        coordEnd = []

        coordStart += [1 + span[0]]
        coordStart += [diagonalNr + span[0]]

        coordEnd += [1 + span[1] - 1]
        coordEnd += [diagonalNr + span[1] - 1]

        return (tuple(coordStart), tuple(coordEnd))

    def __startAndEndCoordForMatchInDiagonalUpBottom(self, diagonalNr, span):
        coordStart = []
        coordEnd = []

        coordStart += [diagonalNr + span[0]]
        coordStart += [1 + span[0]]

        coordEnd += [diagonalNr + span[1] - 1]
        coordEnd += [1 + span[1] - 1]

        return (tuple(coordStart), tuple(coordEnd))

    def __startAndEndCoordForMatchInDiagonalDownLeftSide(self, diagonalNr, span):
        coordStart = []
        coordEnd = []

        coordStart += [1 + span[0]]
        coordStart += [diagonalNr - span[0]]

        coordEnd += [span[1]]
        coordEnd += [diagonalNr - span[1] + 1]

        return (tuple(coordStart), tuple(coordEnd))

    def __startAndEndCoordForMatchInDiagonalDownUpper(self, diagonalNr, span):
        coordStart = []
        coordEnd = []

        coordStart += [diagonalNr + span[0]]
        coordStart += [self.getNumberOfRows() - span[0]]

        coordEnd += [diagonalNr + span[1] - 1]
        coordEnd += [self.getNumberOfRows() - span[1] + 1]

        return (tuple(coordStart), tuple(coordEnd))

    def __extractMovesFromMatchingPattern(self, patternList, listNumber, listString, coordMatchingFunction, patternMoveAppender):
        retList = []
        for pattern in patternList:
            regCol = re.compile(pattern[0])
            for m in regCol.finditer(listString):
                for numbers in pattern[1]:
                    move = coordMatchingFunction(listNumber, m.span())
                    retList.append(patternMoveAppender(move, numbers))

        return retList

    def scanBoard(self):
        numberOfCols = self.getNumberOfColumns()
        numberOfRows = self.getNumberOfRows()

        listOfWinningMovesForX = []
        listOfWinningMovesForO = []
        listOfPotentialWinningMovesForX = []
        listOfPotentialWinningMovesForO = []
        listOfWinningCombosX = []
        listOfWinningCombosO = []

        ################################################
        #           Scanning columns
        ################################################
        for columnNumber in range(1, numberOfCols+1):
            columnsAsString = ''.join(self.getColForCoord((columnNumber, 1)))
            ma = lambda move, numberToAdd: (move[0][0], move[0][1] + numberToAdd)
            listOfPotentialWinningMovesForX += self.__extractMovesFromMatchingPattern(self.potentialWinnersX, columnNumber, columnsAsString, self.__startAndEndCoordForMatchInCol, ma)
            listOfPotentialWinningMovesForO += self.__extractMovesFromMatchingPattern(self.potentialWinnersO, columnNumber, columnsAsString, self.__startAndEndCoordForMatchInCol, ma)
            listOfWinningMovesForX += self.__extractMovesFromMatchingPattern(self.definitivWinnersX, columnNumber, columnsAsString, self.__startAndEndCoordForMatchInCol, ma)
            listOfWinningMovesForO += self.__extractMovesFromMatchingPattern(self.definitivWinnersO, columnNumber, columnsAsString, self.__startAndEndCoordForMatchInCol, ma)
            listOfWinningCombosX += (self.__extractMovesFromMatchingPattern(self.winnersX, columnNumber, columnsAsString, self.__startAndEndCoordForMatchInCol, ma))
            listOfWinningCombosO += (self.__extractMovesFromMatchingPattern(self.winnersO, columnNumber, columnsAsString, self.__startAndEndCoordForMatchInCol, ma))

        ################################################
        #           Scanning rows
        ################################################
        for rowNumber in range(1, numberOfRows+1):
            rowAsString = ''.join(self.getRowForCoord((1, rowNumber)))
            ma = lambda move, numberToAdd: (move[0][0] + numberToAdd, move[0][1])
            listOfPotentialWinningMovesForX += self.__extractMovesFromMatchingPattern(self.potentialWinnersX, rowNumber, rowAsString, self.__startAndEndCoordForMatchInRow, ma)
            listOfPotentialWinningMovesForO += self.__extractMovesFromMatchingPattern(self.potentialWinnersO, rowNumber, rowAsString, self.__startAndEndCoordForMatchInRow, ma)
            listOfWinningMovesForX += self.__extractMovesFromMatchingPattern(self.definitivWinnersX, rowNumber, rowAsString, self.__startAndEndCoordForMatchInRow, ma)
            listOfWinningMovesForO += self.__extractMovesFromMatchingPattern(self.definitivWinnersO, rowNumber, rowAsString, self.__startAndEndCoordForMatchInRow, ma)
            listOfWinningCombosX += self.__extractMovesFromMatchingPattern(self.winnersX, rowNumber, rowAsString, self.__startAndEndCoordForMatchInRow, ma)
            listOfWinningCombosO += self.__extractMovesFromMatchingPattern(self.winnersO, rowNumber, rowAsString, self.__startAndEndCoordForMatchInRow, ma)

        ################################################
        #           Scanning diagonal up
        ################################################
        for rdu in range(numberOfRows, 0, -1):
            diaupL = ''.join(self.board.getDimensionalDataWithDirection((1, rdu), (1, 1)))
            ma = lambda move, numberToAdd: (move[0][0] + numberToAdd, move[0][1] + numberToAdd)
            listOfPotentialWinningMovesForX += self.__extractMovesFromMatchingPattern(self.potentialWinnersX, rdu, diaupL, self.__startAndEndCoordForMatchInDiagonalUpLeftSide, ma)
            listOfPotentialWinningMovesForO += self.__extractMovesFromMatchingPattern(self.potentialWinnersO, rdu, diaupL, self.__startAndEndCoordForMatchInDiagonalUpLeftSide, ma)
            listOfWinningMovesForX += self.__extractMovesFromMatchingPattern(self.definitivWinnersX, rdu, diaupL, self.__startAndEndCoordForMatchInDiagonalUpLeftSide, ma)
            listOfWinningMovesForO += self.__extractMovesFromMatchingPattern(self.definitivWinnersO, rdu, diaupL, self.__startAndEndCoordForMatchInDiagonalUpLeftSide, ma)
            listOfWinningCombosX += self.__extractMovesFromMatchingPattern(self.winnersX, rdu, diaupL, self.__startAndEndCoordForMatchInDiagonalUpLeftSide, ma)
            listOfWinningCombosO += self.__extractMovesFromMatchingPattern(self.winnersO, rdu, diaupL, self.__startAndEndCoordForMatchInDiagonalUpLeftSide, ma)

        for cdu in range(2, numberOfCols+1):
            diaupB = ''.join(self.board.getDimensionalDataWithDirection((cdu, 1), (1, 1)))
            ma = lambda move, numberToAdd: (move[0][0] + numberToAdd, move[0][1] + numberToAdd)
            listOfPotentialWinningMovesForX += self.__extractMovesFromMatchingPattern(self.potentialWinnersX, cdu, diaupB, self.__startAndEndCoordForMatchInDiagonalUpBottom, ma)
            listOfPotentialWinningMovesForO += self.__extractMovesFromMatchingPattern(self.potentialWinnersO, cdu, diaupB, self.__startAndEndCoordForMatchInDiagonalUpBottom, ma)
            listOfWinningMovesForX += self.__extractMovesFromMatchingPattern(self.definitivWinnersX, cdu, diaupB, self.__startAndEndCoordForMatchInDiagonalUpBottom, ma)
            listOfWinningMovesForO += self.__extractMovesFromMatchingPattern(self.definitivWinnersO, cdu, diaupB, self.__startAndEndCoordForMatchInDiagonalUpBottom, ma)
            listOfWinningCombosX += self.__extractMovesFromMatchingPattern(self.winnersX, cdu, diaupB, self.__startAndEndCoordForMatchInDiagonalUpBottom, ma)
            listOfWinningCombosO += self.__extractMovesFromMatchingPattern(self.winnersO, cdu, diaupB, self.__startAndEndCoordForMatchInDiagonalUpBottom, ma)

        ################################################
        #       Scanning diagonal down
        ################################################
        for rdd in range(1, numberOfRows+1):
            diadwL = ''.join(self.board.getDimensionalDataWithDirection((1, rdd), (1, -1)))
            ma = lambda move, numberToAdd: (move[0][0] + numberToAdd, move[0][1] - numberToAdd)
            listOfPotentialWinningMovesForX += self.__extractMovesFromMatchingPattern(self.potentialWinnersX, rdd, diadwL, self.__startAndEndCoordForMatchInDiagonalDownLeftSide, ma)
            listOfPotentialWinningMovesForO += self.__extractMovesFromMatchingPattern(self.potentialWinnersO, rdd, diadwL, self.__startAndEndCoordForMatchInDiagonalDownLeftSide, ma)
            listOfWinningMovesForX += self.__extractMovesFromMatchingPattern(self.definitivWinnersX, rdd, diadwL, self.__startAndEndCoordForMatchInDiagonalDownLeftSide, ma)
            listOfWinningMovesForO += self.__extractMovesFromMatchingPattern(self.definitivWinnersO, rdd, diadwL, self.__startAndEndCoordForMatchInDiagonalDownLeftSide, ma)
            listOfWinningCombosX += self.__extractMovesFromMatchingPattern(self.winnersX, rdd, diadwL, self.__startAndEndCoordForMatchInDiagonalDownLeftSide, ma)
            listOfWinningCombosO += self.__extractMovesFromMatchingPattern(self.winnersO, rdd, diadwL, self.__startAndEndCoordForMatchInDiagonalDownLeftSide, ma)

        for cdd in range(2, numberOfCols+1):
            diadwU = ''.join(self.board.getDimensionalDataWithDirection((cdd, numberOfRows), (1, -1)))
            ma = lambda move, numberToAdd: (move[0][0] + numberToAdd, move[0][1] - numberToAdd)
            listOfPotentialWinningMovesForX += self.__extractMovesFromMatchingPattern(self.potentialWinnersX, cdd, diadwU, self.__startAndEndCoordForMatchInDiagonalDownUpper, ma)
            listOfPotentialWinningMovesForO += self.__extractMovesFromMatchingPattern(self.potentialWinnersO, cdd, diadwU, self.__startAndEndCoordForMatchInDiagonalDownUpper, ma)
            listOfWinningMovesForX += self.__extractMovesFromMatchingPattern(self.definitivWinnersX, cdd, diadwU, self.__startAndEndCoordForMatchInDiagonalDownUpper, ma)
            listOfWinningMovesForO += self.__extractMovesFromMatchingPattern(self.definitivWinnersO, cdd, diadwU, self.__startAndEndCoordForMatchInDiagonalDownUpper, ma)
            listOfWinningCombosX += self.__extractMovesFromMatchingPattern(self.winnersX, cdd, diadwU, self.__startAndEndCoordForMatchInDiagonalDownUpper, ma)
            listOfWinningCombosO += self.__extractMovesFromMatchingPattern(self.winnersO, cdd, diadwU, self.__startAndEndCoordForMatchInDiagonalDownUpper, ma)

        # Remove doublets
        listOfWinningMovesForX = list(set(listOfWinningMovesForX))
        listOfWinningMovesForO = list(set(listOfWinningMovesForO))
        listOfPotentialWinningMovesForX = list(set(listOfPotentialWinningMovesForX))
        listOfPotentialWinningMovesForO = list(set(listOfPotentialWinningMovesForO))
        listOfWinningCombosX = list(set(listOfWinningCombosX))
        listOfWinningCombosO = list(set(listOfWinningCombosO))

        return {self.KEY_LIST_OF_WINNING_MOVES_FOR_X: listOfWinningMovesForX,
                self.KEY_LIST_OF_WINNING_MOVES_FOR_O: listOfWinningMovesForO,
                self.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_X: listOfPotentialWinningMovesForX,
                self.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_O: listOfPotentialWinningMovesForO,
                self.KEY_LIST_OF_WINNERS_X: listOfWinningCombosX,
                self.KEY_LIST_OF_WINNERS_O: listOfWinningCombosO
                }

    def getColForCoord(self, coord):
        col = self.board.getDimensionalData((coord[0], None))
        return col

    def getRowForCoord(self, coord):
        row = self.board.getDimensionalData((None, coord[1]))
        return row

    def getDiagonalForCoordDown(self, coord):
        r = coord[0]+coord[1]-1
        c = 1
        if r > self.getNumberOfRows():
            r = self.getNumberOfRows()
            c = self.getNumberOfColumns() - (self.getNumberOfRows() - coord[1])

        dia = self.board.getDimensionalDataWithDirection((c, r), (1, -1))

        return dia

    def getDiagonalForCoordUp(self, coord):
        c = coord[0]-coord[1]+1
        r = 1
        if c < 1:
            c = 1
            r = coord[1] - coord[0] + 1

        dia = self.board.getDimensionalDataWithDirection((c, r), (1, 1))
        return dia



####### END CLASS FIVE IN A ROW #########

class TextBasedFiveInARowGame:
    def __init__(self):
        self.game = FiveInARow()

    def debugGame(self):
        self.game.debugMakeSetup()
        self.printBoard()
        self.game.debug()

    def play(self):
        print("*" * 11)
        print("FIVE IN A ROW")
        print("*" * 11)
        print("Play X or O? (X)>")
        self.playersToken = self.game.X_TOKEN
        self.computersToken = self.game.O_TOKEN
        if input() == self.game.O_TOKEN:
            self.playersToken = self.game.O_TOKEN
            self.computersToken = self.game.X_TOKEN

        while True:
            self.printBoard()
            if self.game.whoHas == self.playersToken:
                try:
                    #self.game.getMovesSorted(True)
                    playersmove = self.__askPlayerForMove()
                    self.game.makeMove(playersmove, self.playersToken)
                except Exception as err:
                    print(str(err))
            else:
                move = self.game.getComputersMoveForCurrentPosition()
                self.game.makeMove(move[0], move[1])
                print("Computer moves: ", move[0])

                #self.game.getMovesSorted(False)
                #playersmove = self.__askPlayerForMove()
                #self.game.makeMove(playersmove, self.computersToken)


            winnerOfCurrentPos = self.game.getWinnerOfCurrentPosition()
            if winnerOfCurrentPos is None:
                continue

            if winnerOfCurrentPos == self.playersToken:
                self.printBoard()
                print("You win! Congrats!")
            elif winnerOfCurrentPos == self.computersToken:
                self.printBoard()
                print("You loose...sorry.")
            elif winnerOfCurrentPos == self.game.NO_TOKEN:
                self.printBoard()
                print("It's a draw!")

            print("Another game? (Y/n)")
            ans = input()
            if ans == 'n':
                print("Ok! Thank's for the game!")
                break
            self.game.resetGame()
            self.__swapToken()


    def printBoard(self):
        list = self.game.getBoard()
        spaces = 3
        for x in range(len(list) - 1, -1, -1):
            if x + 1 < 10:
                spaces = 3
            else:
                spaces = 2
            print(x + 1, end=' ' * spaces)
            for y in range(len(list[x])):
                if list[x][y] == None:
                    print('-', end='   ')
                else:
                    print(list[x][y], end='   ')
            print("")
        print("",end=' '*(spaces+1))
        for i in range(self.game.getNumberOfColumns()):
            if i+1 < 10:
                print(i+1, end='   ')
            else:
                print(i + 1, end='  ')
        print("")

    def __swapToken(self):
        tmpToken = self.playersToken
        self.playersToken = self.computersToken
        self.computersToken = tmpToken

    def __askPlayerForMove(self):
        x = 1
        y = 1
        while True:
            print("Your move(" + self.playersToken + ")>")
            move = input()
            if move == 'e':
                eval = self.game.evalBoard()
                print("CurrentEval: ", eval)
                continue
            if move == 'd':
                self.game.debug()
            if move == 'p':
                self.printBoard()

            coord = move.split(",")
            if len(coord) < 2 or len(coord) > 2:
                print("!!! Give coord eg. 3,2 !!!")
                continue
            try:
                x = int(coord[0])
                y = int(coord[1])
                if x < 1 or x > self.game.getNumberOfColumns() or y < 1 or y > self.game.getNumberOfRows():
                    print("!!!! Coords out of range!!!")
                    continue
            except:
                print("!!! Give numbers for coords !!!")
                continue
            break

        return (x, y)