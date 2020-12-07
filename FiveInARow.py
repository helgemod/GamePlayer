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
import threading
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

    START_WITH_NO_OF_COLUMNS = 10
    START_WITH_NO_OF_ROWS = 10
    DYNAMIC_BOARD = True

    MIN_EVAL = -1000
    MAX_EVAL = 1000

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


    def __init__(self):
        self.whoHas = self.X_TOKEN
        self.playersToken = self.X_TOKEN
        self.board = sd.StrideDimension((self.START_WITH_NO_OF_COLUMNS, self.START_WITH_NO_OF_ROWS))
        self.analyzeBoard = sd.StrideDimension((6, 6))
        self.board.fillData(self.NO_TOKEN)
        self.analyzeBoard.fillData(self.NO_TOKEN)
        self.computerAlgo = mma.GameAlgo(self.evalBoard,
                                           self.moveX, self.moveO,
                                           self.undoMove, self.undoMove,
                                           self.getPossibleMovesMaximizer, self.getPossibleMovesMinimizer,
                                           self.MIN_EVAL, self.MAX_EVAL)


        self.board_scanner = BoardScanner()

        self.moveChangeCallbacks = []

        self.analyzeDaemon = None

    ########################################
    #
    #           Game interface
    #
    ########################################
    #Call this to get the board for print.
    def getGameBoardsAllDimensions(self):
        return self.board.getDimensionalData((None, None))

    def getAnalyzeBoard(self):
        return self.analyzeBoard.getDimensionalData((None, None))

    def setAnalyzeBoardAsGameBoard(self):
        self.analyzeBoard.setUpWithData(self.board.getDataForSave())

    # Makes an actual move and do all administrations. Return True if move could be made. Else False.
    def makeMove(self, coordinates, token):
        try:
            self.__checkMove(coordinates, token)
        except Exception as err:
            print(str(err))
            return False
        self.board.setData(coordinates, token)
        self.__invertWhoHas()

        # If some analyze object is interested in that a move is made in the "main game".
        try:
            for obj in self.moveChangeCallbacks:
                obj.moveMade(coordinates, token)
        except Exception as err:
            pass

        if self.DYNAMIC_BOARD:
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
        self.board = sd.StrideDimension((self.START_WITH_NO_OF_COLUMNS, self.START_WITH_NO_OF_ROWS))
        self.board.fillData(self.NO_TOKEN)
        self.analyzeBoard = sd.StrideDimension((6, 6))
        self.analyzeBoard.fillData(self.NO_TOKEN)

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
        return self.__boardEvaluator(self.board)

    def moveX(self, move):
        self.board.setDataAtIndex(move, self.X_TOKEN)

    def moveO(self, move):
        self.board.setDataAtIndex(move, self.O_TOKEN)

    def undoMove(self, move):
        self.board.setDataAtIndex(move, self.NO_TOKEN)

    def getPossibleMovesMaximizer(self):
        return self.getMovesSorted(True, self.board)

    def getPossibleMovesMinimizer(self):
        return self.getMovesSorted(False, self.board)




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

    def __boardEvaluator(self, boardToEvaluate):
        evalFunc = lambda d: self.evaluateList(d[BoardScanner.KEY_BOARD_LIST_DATA])
        return self.board_scanner.scanBoardForEvaluation(boardToEvaluate, evalFunc)

    def getMovesSorted(self, regardingMaximizer, whichBoard):
        scanDict = self.board_scanner.scanBoardForPositions(whichBoard)

        # 1 - Is there a winner on board. No more moves are possible
        if len(scanDict[self.board_scanner.KEY_LIST_OF_WINNERS_X]) > 0 or len(scanDict[self.board_scanner.KEY_LIST_OF_WINNERS_O]) > 0:
            return []

        # 2) One move away from a win
        if regardingMaximizer:
            # 2) If I (as X) have at least one winning move. Return the first.
            if len(scanDict[self.board_scanner.KEY_LIST_OF_WINNING_MOVES_FOR_X]) > 0:
                return [whichBoard.indexForDimCoordinate(scanDict[self.board_scanner.KEY_LIST_OF_WINNING_MOVES_FOR_X][0])]
            # 3) If opponent (as O) have at least one winning move. Return first move, to stop him.
            elif len(scanDict[self.board_scanner.KEY_LIST_OF_WINNING_MOVES_FOR_O]) > 0:
                return [whichBoard.indexForDimCoordinate(scanDict[self.board_scanner.KEY_LIST_OF_WINNING_MOVES_FOR_O][0])]
        else:
            # 2) If I (as O) have at least one winning move. Return the first.
            if len(scanDict[self.board_scanner.KEY_LIST_OF_WINNING_MOVES_FOR_O]) > 0:
                return [whichBoard.indexForDimCoordinate(scanDict[self.board_scanner.KEY_LIST_OF_WINNING_MOVES_FOR_O][0])]
            # 3) If opponent (as X) have at least one winning move. Return first move, to stop him.
            elif len(scanDict[self.board_scanner.KEY_LIST_OF_WINNING_MOVES_FOR_X]) > 0:
                return [whichBoard.indexForDimCoordinate(scanDict[self.board_scanner.KEY_LIST_OF_WINNING_MOVES_FOR_X][0])]

        # 3) Potential winners.
        if regardingMaximizer:
            # 2) If I (as X) have potential winning moves. Return them.
            if len(scanDict[self.board_scanner.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_X]) > 0:
                return [whichBoard.indexForDimCoordinate(x) for x in scanDict[self.board_scanner.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_X]]
            # 3) If opponent (as O) have potential winning moves. Return them.
            elif len(scanDict[self.board_scanner.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_O]) > 0:
                return [whichBoard.indexForDimCoordinate(x) for x in scanDict[self.board_scanner.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_O]]
        else:
            # 2) If I (as O) have potential winning moves. Return them.
            if len(scanDict[self.board_scanner.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_O]) > 0:
                return [whichBoard.indexForDimCoordinate(x) for x in scanDict[self.board_scanner.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_O]]
            # 3) If opponent (as X) have potential winning moves. Return them.
            elif len(scanDict[self.board_scanner.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_X]) > 0:
                return [whichBoard.indexForDimCoordinate(x) for x in scanDict[self.board_scanner.KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_X]]

        # 5) If we come down here. There are no obvious winning move. Pick out a list of suggestions.

        # Ask board for all empty squares.
        readList = whichBoard.getIndexListWhereDataIs(self.NO_TOKEN)

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
            moveCoords = tuple(whichBoard.dimCoordinateForIndex(move))

            preEval = self.evaluateList(self.getColForCoord(moveCoords, whichBoard))
            preEval += self.evaluateList(self.getRowForCoord(moveCoords, whichBoard))
            preEval += self.evaluateList(self.getDiagonalForCoordUp(moveCoords, whichBoard))
            preEval += self.evaluateList(self.getDiagonalForCoordDown(moveCoords, whichBoard))

            # 2) Try the move
            if regardingMaximizer:
                self.moveX(move)
            else:
                self.moveO(move)

            # 3) Evaluate after the move try
            postEval = self.evaluateList(self.getColForCoord(moveCoords, whichBoard))
            postEval += self.evaluateList(self.getRowForCoord(moveCoords, whichBoard))
            postEval += self.evaluateList(self.getDiagonalForCoordUp(moveCoords, whichBoard))
            postEval += self.evaluateList(self.getDiagonalForCoordDown(moveCoords, whichBoard))

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

    def getColForCoord(self, coord, whichBoard):
        col = whichBoard.getDimensionalData((coord[0], None))
        return col

    def getRowForCoord(self, coord, whichBoard):
        row = whichBoard.getDimensionalData((None, coord[1]))
        return row

    def getDiagonalForCoordDown(self, coord, whichBoard):
        r = coord[0]+coord[1]-1
        c = 1
        if r > self.getNumberOfRows():
            r = self.getNumberOfRows()
            c = self.getNumberOfColumns() - (self.getNumberOfRows() - coord[1])

        dia = whichBoard.getDimensionalDataWithDirection((c, r), (1, -1))

        return dia

    def getDiagonalForCoordUp(self, coord, whichBoard):
        c = coord[0]-coord[1]+1
        r = 1
        if c < 1:
            c = 1
            r = coord[1] - coord[0] + 1

        dia = whichBoard.getDimensionalDataWithDirection((c, r), (1, 1))
        return dia

    ### Callbacks for analyzor algo
    def applyForMoveChange(self, applier):
        self.moveChangeCallbacks.append(applier)


    def tbd(self, d):
        if BoardScanner.KEY_BOARD_SCANNER_COLUMN in d:
            print("Ja")
        else:
            print("Nej")

    def debug(self):
        forEachList = lambda d: self.evaluateList(d[BoardScanner.KEY_BOARD_LIST_DATA])
        result = self.board_scanner.scanBoardForEvaluation(self.board, forEachList)
        print(result)
####### END CLASS FIVE IN A ROW #########









####### CLASS BOARD SCANNER #########

class BoardScanner:
    """
    Scans the board and calls a function of choice for each scanned row.
    """

    # So far, these are not used...
    KEY_BOARD_SCANNER_COLUMN = "keyBoardScannerColumn"
    KEY_BOARD_SCANNER_ROW = "keyBoardScannerRow"
    KEY_BOARD_SCANNER_DIAGONAL_UP_FROM_LEFT_SIDE_ROW_NUMBER = "keyBoardScannerDiagonalUpFromLeftSideWithRowNumber"
    KEY_BOARD_SCANNER_DIAGONAL_UP_FROM_BOTTOM_SIDE_COL_NUMBER = "keyBoardScannerDiagonalUpFromBottomSideWithColumnNumber"
    KEY_BOARD_SCANNER_DIAGONAL_DOWN_FROM_LEFT_SIDE_ROW_NUMBER = "keyBoardScannerDiagonalDownFromLeftSideWithRowNumber"
    KEY_BOARD_SCANNER_DIAGONAL_DOWN_FROM_TOP_SIDE_COL_NUMBER = "keyBoardScannerDiagonalDownFromTopSideWithColumnNumber"

    KEY_BOARD_LIST_DATA = "keyBoardListData"

    KEY_LIST_OF_WINNING_MOVES_FOR_X = 'keyListOfWinningMovesForX'
    KEY_LIST_OF_WINNING_MOVES_FOR_O = 'keyListOfWinningMovesForO'
    KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_X = 'keyListOfPotentialWinningMovesForX'
    KEY_LIST_OF_POTENTIAL_WINNING_MOVES_FOR_O = 'keyListOfPotentialWinningMovesForO'
    KEY_LIST_OF_WINNERS_X = 'keyListOfWinnersX'
    KEY_LIST_OF_WINNERS_O = 'keyListOfWinnersO'

    potentialWinnersX = [
        ['-XXX-', [0, 4]],
        ['-X-XX-', [2]],
        ['-XX-X-', [3]],
    ]
    potentialWinnersO = [
        ['-OOO-', [0, 4]],
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

    # "functionToCallForEachList" takes dict as argument. Keys in dict is as of above
    def scanBoardForEvaluation(self, boardToScan, functionToCallForEachList):
        numberOfCols = boardToScan.dimensions[0]
        numberOfRows = boardToScan.dimensions[1]

        summator = 0

        ################################################
        #           Scanning columns
        ################################################
        for columnNumber in range(1, numberOfCols + 1):
            colDict = {self.KEY_BOARD_SCANNER_COLUMN: columnNumber,
                       self.KEY_BOARD_LIST_DATA: boardToScan.getDimensionalData((columnNumber, None))}
            summator += functionToCallForEachList(colDict)

        ################################################
        #           Scanning rows
        ################################################
        for rowNumber in range(1, numberOfRows + 1):
            rowDict = {self.KEY_BOARD_SCANNER_ROW: rowNumber,
                       self.KEY_BOARD_LIST_DATA: boardToScan.getDimensionalData((None, rowNumber))}
            summator += functionToCallForEachList(rowDict)

        ################################################
        #           Scanning diagonal up
        ################################################
        for rdu in range(numberOfRows, 0, -1):
            rduDict = {self.KEY_BOARD_SCANNER_DIAGONAL_UP_FROM_LEFT_SIDE_ROW_NUMBER: rdu,
                       self.KEY_BOARD_LIST_DATA: boardToScan.getDimensionalDataWithDirection((1, rdu), (1, 1))}
            summator += functionToCallForEachList(rduDict)

        for cdu in range(2, numberOfCols + 1):
            cduDict = {self.KEY_BOARD_SCANNER_DIAGONAL_UP_FROM_BOTTOM_SIDE_COL_NUMBER: cdu,
                       self.KEY_BOARD_LIST_DATA: boardToScan.getDimensionalDataWithDirection((cdu, 1), (1, 1))}
            summator += functionToCallForEachList(cduDict)

        ################################################
        #       Scanning diagonal down
        ################################################
        for rdd in range(1, numberOfRows + 1):
            rddDict = {self.KEY_BOARD_SCANNER_DIAGONAL_DOWN_FROM_LEFT_SIDE_ROW_NUMBER: rdd,
                       self.KEY_BOARD_LIST_DATA: boardToScan.getDimensionalDataWithDirection((1, rdd), (1, -1))}
            summator += functionToCallForEachList(rddDict)

        for cdd in range(2, numberOfCols + 1):
            cddDict = {self.KEY_BOARD_SCANNER_DIAGONAL_DOWN_FROM_TOP_SIDE_COL_NUMBER: cdd,
                       self.KEY_BOARD_LIST_DATA: boardToScan.getDimensionalDataWithDirection((cdd, numberOfRows), (1, -1))}
            summator += functionToCallForEachList(cddDict)

        return summator

    def scanBoardForPositions(self, boardToScan):
        numberOfCols = boardToScan.dimensions[0]
        numberOfRows = boardToScan.dimensions[1]

        listOfWinningMovesForX = []
        listOfWinningMovesForO = []
        listOfPotentialWinningMovesForX = []
        listOfPotentialWinningMovesForO = []
        listOfWinningCombosX = []
        listOfWinningCombosO = []

        ################################################
        #           Scanning columns
        ################################################
        ma = lambda move, numberToAdd: (move[0][0], move[0][1] + numberToAdd)  # Move Appending function
        cm = lambda colNr, span: ((colNr, span[0] + 1), (colNr, span[1]))  # Coord matching function
        for columnNumber in range(1, numberOfCols+1):
            columnsAsString = ''.join(boardToScan.getDimensionalData((columnNumber, None)))
            listOfPotentialWinningMovesForX += self.__extractMovesFromMatchingPattern(self.potentialWinnersX, columnNumber, columnsAsString, cm, ma)
            listOfPotentialWinningMovesForO += self.__extractMovesFromMatchingPattern(self.potentialWinnersO, columnNumber, columnsAsString, cm, ma)
            listOfWinningMovesForX += self.__extractMovesFromMatchingPattern(self.definitivWinnersX, columnNumber, columnsAsString, cm, ma)
            listOfWinningMovesForO += self.__extractMovesFromMatchingPattern(self.definitivWinnersO, columnNumber, columnsAsString, cm, ma)
            listOfWinningCombosX += (self.__extractMovesFromMatchingPattern(self.winnersX, columnNumber, columnsAsString, cm, ma))
            listOfWinningCombosO += (self.__extractMovesFromMatchingPattern(self.winnersO, columnNumber, columnsAsString, cm, ma))

        ################################################
        #           Scanning rows
        ################################################
        ma = lambda move, numberToAdd: (move[0][0] + numberToAdd, move[0][1])
        cm = lambda rowNr, span: ((span[0] + 1, rowNr), (span[1], rowNr))
        for rowNumber in range(1, numberOfRows+1):
            rowAsString = ''.join(boardToScan.getDimensionalData((None, rowNumber)))
            listOfPotentialWinningMovesForX += self.__extractMovesFromMatchingPattern(self.potentialWinnersX, rowNumber, rowAsString, cm, ma)
            listOfPotentialWinningMovesForO += self.__extractMovesFromMatchingPattern(self.potentialWinnersO, rowNumber, rowAsString, cm, ma)
            listOfWinningMovesForX += self.__extractMovesFromMatchingPattern(self.definitivWinnersX, rowNumber, rowAsString, cm, ma)
            listOfWinningMovesForO += self.__extractMovesFromMatchingPattern(self.definitivWinnersO, rowNumber, rowAsString, cm, ma)
            listOfWinningCombosX += self.__extractMovesFromMatchingPattern(self.winnersX, rowNumber, rowAsString, cm, ma)
            listOfWinningCombosO += self.__extractMovesFromMatchingPattern(self.winnersO, rowNumber, rowAsString, cm, ma)

        ################################################
        #           Scanning diagonal up
        ################################################
        ma = lambda move, numberToAdd: (move[0][0] + numberToAdd, move[0][1] + numberToAdd)
        cm = lambda diagonalNr, span: ((1 + span[0], diagonalNr + span[0]), (1 + span[1] - 1, diagonalNr + span[1] - 1))
        for rdu in range(numberOfRows, 0, -1):
            diaupL = ''.join(boardToScan.getDimensionalDataWithDirection((1, rdu), (1, 1)))
            listOfPotentialWinningMovesForX += self.__extractMovesFromMatchingPattern(self.potentialWinnersX, rdu, diaupL, cm, ma)
            listOfPotentialWinningMovesForO += self.__extractMovesFromMatchingPattern(self.potentialWinnersO, rdu, diaupL, cm, ma)
            listOfWinningMovesForX += self.__extractMovesFromMatchingPattern(self.definitivWinnersX, rdu, diaupL, cm, ma)
            listOfWinningMovesForO += self.__extractMovesFromMatchingPattern(self.definitivWinnersO, rdu, diaupL, cm, ma)
            listOfWinningCombosX += self.__extractMovesFromMatchingPattern(self.winnersX, rdu, diaupL, cm, ma)
            listOfWinningCombosO += self.__extractMovesFromMatchingPattern(self.winnersO, rdu, diaupL, cm, ma)

        ma = lambda move, numberToAdd: (move[0][0] + numberToAdd, move[0][1] + numberToAdd)
        cm = lambda diagonalNr, span: ((diagonalNr + span[0], 1 + span[0]), (diagonalNr + span[1] - 1, 1 + span[1] - 1))
        for cdu in range(2, numberOfCols+1):
            diaupB = ''.join(boardToScan.getDimensionalDataWithDirection((cdu, 1), (1, 1)))
            listOfPotentialWinningMovesForX += self.__extractMovesFromMatchingPattern(self.potentialWinnersX, cdu, diaupB, cm, ma)
            listOfPotentialWinningMovesForO += self.__extractMovesFromMatchingPattern(self.potentialWinnersO, cdu, diaupB, cm, ma)
            listOfWinningMovesForX += self.__extractMovesFromMatchingPattern(self.definitivWinnersX, cdu, diaupB, cm, ma)
            listOfWinningMovesForO += self.__extractMovesFromMatchingPattern(self.definitivWinnersO, cdu, diaupB, cm, ma)
            listOfWinningCombosX += self.__extractMovesFromMatchingPattern(self.winnersX, cdu, diaupB, cm, ma)
            listOfWinningCombosO += self.__extractMovesFromMatchingPattern(self.winnersO, cdu, diaupB, cm, ma)

        ################################################
        #       Scanning diagonal down
        ################################################
        ma = lambda move, numberToAdd: (move[0][0] + numberToAdd, move[0][1] - numberToAdd)
        cm = lambda diagonalNr, span: ((1 + span[0], diagonalNr - span[0]), (span[1], diagonalNr - span[1] + 1))
        for rdd in range(1, numberOfRows+1):
            diadwL = ''.join(boardToScan.getDimensionalDataWithDirection((1, rdd), (1, -1)))
            listOfPotentialWinningMovesForX += self.__extractMovesFromMatchingPattern(self.potentialWinnersX, rdd, diadwL, cm, ma)
            listOfPotentialWinningMovesForO += self.__extractMovesFromMatchingPattern(self.potentialWinnersO, rdd, diadwL, cm, ma)
            listOfWinningMovesForX += self.__extractMovesFromMatchingPattern(self.definitivWinnersX, rdd, diadwL, cm, ma)
            listOfWinningMovesForO += self.__extractMovesFromMatchingPattern(self.definitivWinnersO, rdd, diadwL, cm, ma)
            listOfWinningCombosX += self.__extractMovesFromMatchingPattern(self.winnersX, rdd, diadwL, cm, ma)
            listOfWinningCombosO += self.__extractMovesFromMatchingPattern(self.winnersO, rdd, diadwL, cm, ma)

        ma = lambda move, numberToAdd: (move[0][0] + numberToAdd, move[0][1] - numberToAdd)
        cm = lambda diagonalNr, span: ((diagonalNr + span[0], numberOfRows - span[0]), (diagonalNr + span[1] - 1, numberOfRows - span[1] + 1))
        for cdd in range(2, numberOfCols+1):
            diadwU = ''.join(boardToScan.getDimensionalDataWithDirection((cdd, numberOfRows), (1, -1)))

            listOfPotentialWinningMovesForX += self.__extractMovesFromMatchingPattern(self.potentialWinnersX, cdd, diadwU, cm, ma)
            listOfPotentialWinningMovesForO += self.__extractMovesFromMatchingPattern(self.potentialWinnersO, cdd, diadwU, cm, ma)
            listOfWinningMovesForX += self.__extractMovesFromMatchingPattern(self.definitivWinnersX, cdd, diadwU, cm, ma)
            listOfWinningMovesForO += self.__extractMovesFromMatchingPattern(self.definitivWinnersO, cdd, diadwU, cm, ma)
            listOfWinningCombosX += self.__extractMovesFromMatchingPattern(self.winnersX, cdd, diadwU, cm, ma)
            listOfWinningCombosO += self.__extractMovesFromMatchingPattern(self.winnersO, cdd, diadwU, cm, ma)

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


    # INTERNAL HELPER METHODS
    def __extractMovesFromMatchingPattern(self, patternList, listNumber, listString, coordMatchingFunction, patternMoveAppender):
        retList = []
        for pattern in patternList:
            regCol = re.compile(pattern[0])
            for m in regCol.finditer(listString):
                for numbers in pattern[1]:
                    move = coordMatchingFunction(listNumber, m.span())
                    retList.append(patternMoveAppender(move, numbers))

        return retList

####### END CLASS BOARD SCANNER #########







class TextBasedFiveInARowGame:
    def __init__(self):
        self.game = FiveInARow()
        #self.analyzer = GameAnalyzer(self.game)

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
        list = self.game.getGameBoardsAllDimensions()
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

    def printAnalyzeBoard(self):
        list = self.game.getAnalyzeBoard()
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
            if move == 'h':
                print("HINT:", self.game.analyzeGame())
            if move == 's':
                print("Starting daemon")
                self.game.startDaemon()
            if move == 't':
                print("STOP analysing called from down here.")
                #self.game.stopAnalyze()

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

class GameAnalyzer:
    pass
    """
    def __init__(self, game):
        self.game = game
        self.analyzeBoard = sd.StrideDimension((self.game.START_WITH_NO_OF_COLUMNS, self.game.START_WITH_NO_OF_ROWS))
        self.game.applyForMoveChange(self)
        self.analyzeAlgo = mma.GameAnalyzerAlgo(self.analyze_evaluate,
                                        self.analyze_move_x, self.analyze_move_o,
                                        self.analyze_undo_move, self.analyze_undo_move,
                                        self.analyze_getPossibleMovesMaximizer, self.analyze_getPossibleMovesMinimizer,
                                        self.MIN_EVAL, self.MAX_EVAL)

    def moveMade(self, coordinate, token):
        print("Game Analyzer Object called> ", coordinate, token)

    def analyze_evaluate(self):
        return self.__boardEvaluator(self.analyzeBoard)

    def analyze_move_x(self, move):
        self.analyzeBoard.setDataAtIndex(move, self.X_TOKEN)

    def analyze_move_o(self, move):
        self.analyzeBoard.setDataAtIndex(move, self.O_TOKEN)

    def analyze_undo_move(self, move):
        self.analyzeBoard.setDataAtIndex(move, self.NO_TOKEN)

    def analyze_getPossibleMovesMaximizer(self):
        return self.getMovesSorted(True, self.analyzeBoard)

    def analyze_getPossibleMovesMinimizer(self):
        return self.getMovesSorted(False, self.analyzeBoard)

    newMove = False
    def stopAnalyze(self):
        print("Stop analyze called...")
        self.newMove = True
        self.analyzeAlgo.interruptAnalyze()

    def analyzeGame(self):
        cntr = 0
        print("Starting analyze of game")
        while True:
            time.sleep(3)
            cntr += 1
            if cntr % 3 == 0:
                print("tick")

        bestMoveSoFar = None
        self.setAnalyzeBoardAsGameBoard()
        currentDepth = 2

        while True:
            if self.newMove:
                time.sleep(3)
                print("Oh...new move...reset analyse info and restart.")
                bestMoveSoFar = None
                self.setAnalyzeBoardAsGameBoard()
                currentDepth = 2
                self.newMove = False

            move = self.analyzeAlgo.calculateMove(mma.MINMAXALPHABETAPRUNING_ALGO, self.whoHas == self.X_TOKEN, currentDepth)
            moveWithCoords = self.board.dimCoordinateForIndex(move)
            if not moveWithCoords == bestMoveSoFar:
                bestMoveSoFar = moveWithCoords
                print("New best move: (depth)", bestMoveSoFar, currentDepth)
            currentDepth += 1
            time.sleep(2)


        #return (self.board.dimCoordinateForIndex(move), self.whoHas)


    def startDaemon(self):
        self.analyzeDaemon = threading.Thread(target=self.analyzeGame())
        print("startDaemon CALLED")
        self.analyzeDaemon.start()
        return
    """