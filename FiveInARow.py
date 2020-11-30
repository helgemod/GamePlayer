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

    # In future this can be able to point at different algorithms
    # to test them.
    computerAlgo = None

    def __init__(self):
        #self.cols = 6
        #self.rows = 3
        self.whoHas = self.X_TOKEN
        self.playersToken = self.X_TOKEN
        self.board = sd.StrideDimension((9, 9)) #cols=6 rows=3
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
        #self.__extendBoardIfCloseToEdge()
        return True
    def getComputersMoveForCurrentPosition(self):
        #move = self.computerAlgo.calculateMove(mma.MINMAX_ALGO, self.whoHas == self.X_TOKEN, 4)
        #move = self.computerAlgo.calculateMove(mma.MINMAXALPHABETAPRUNING_ALGO, self.whoHas == self.X_TOKEN, 4)
        move = self.computerAlgo.calculateMove(mma.MINMAX_ALGO_WITH_LOGGING, self.whoHas == self.X_TOKEN, 4)
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
        self.board = sd.StrideDimension((1, 1))  # cols=6 rows=3
        self.board.fillData(self.NO_TOKEN)
        #self.board.fillData(self.NO_TOKEN)#clearboard
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
            if tmpEval1 <= self.MIN_EVAL + 200 or tmpEval1 >= self.MAX_EVAL - 200:
                return tmpEval2
            addEval += tmpEval2


        # Now check diagonals UPWARDS /
        for dcu in range(self.getNumberOfColumns()):
            diaUpCol = self.board.getDimensionalDataWithDirection((dcu + 1, 1), (1, 1))
            tmpEval3 = self.evaluateList(diaUpCol)
            if tmpEval1 <= self.MIN_EVAL + 200 or tmpEval1 >= self.MAX_EVAL - 200:
                return tmpEval3
            addEval += tmpEval3

        for dru in range(self.getNumberOfRows()-1):
            diaUpRow = self.board.getDimensionalDataWithDirection((1, dru + 2), (1, 1))
            tmpEval4 = self.evaluateList(diaUpRow)
            if tmpEval1 <= self.MIN_EVAL + 200 or tmpEval1 >= self.MAX_EVAL - 200:
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
            if tmpEval1 <= self.MIN_EVAL + 200 or tmpEval1 >= self.MAX_EVAL - 200:
                return tmpEval5
            addEval += tmpEval5

        # 2) Start in upper-left corner and go right in upper row
        #    and pick out the downward diagonal.
        for drd in range(noOfRows-1):
            diaDownRow = self.board.getDimensionalDataWithDirection((drd + 2, noOfRows), (1, -1))
            tmpEval6 = self.evaluateList(diaDownRow)
            if tmpEval1 <= self.MIN_EVAL + 200 or tmpEval1 >= self.MAX_EVAL - 200:
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


    # Scans the whole board and uses help methods above to look for 'howMany' in a row.
    # analyzeFunc shall take argument: (whatIsScanned, {startCoord}, [dataAsList])
    #
    def __scanBoard(self, howMany, analyzeFunc):
        for r in range(self.getNumberOfRows()):
            row = self.board.getDimensionalData((None, r+1))
            if len(row) < howMany:
                break
            if not analyzeFunc(self.ANALYZE_ROW, {self.KEY_COORD_COL: 1, self.KEY_COORD_ROW: r+1}, row):
                return

        for c in range(self.getNumberOfColumns()):
            col = self.board.getDimensionalData((c+1, None))
            if len(col) < howMany:
                break
            if not analyzeFunc(self.ANALYZE_COL, {self.KEY_COORD_COL: c+1, self.KEY_COORD_ROW: 1}, col):
                return

        # Now check diagonals UPWARDS /
        for dcu in range(self.getNumberOfColumns()):
            diaUpCol = self.board.getDimensionalDataWithDirection((dcu + 1, 1), (1, 1))
            if len(diaUpCol) < howMany:
                break
            if not analyzeFunc(self.ANALYZE_DIAUP, {self.KEY_COORD_COL: dcu + 1, self.KEY_COORD_ROW: 1}, diaUpCol):
                return

        for dru in range(self.getNumberOfRows()-1):
            diaUpRow = self.board.getDimensionalDataWithDirection((1, dru + 2), (1, 1))
            if len(diaUpRow) < howMany:
                break
            if not analyzeFunc(self.ANALYZE_DIAUP, {self.KEY_COORD_COL: 1, self.KEY_COORD_ROW: dru + 2}, diaUpRow):
                return

        # Now check diagonals DOWNWARDS \
        #
        # 1) Start in upper-left corner and go downward in first col
        #    and pick out the downward diagonal.
        noOfCol = self.getNumberOfColumns()
        noOfRows = self.getNumberOfRows()
        for dcd in range(noOfCol):
            diaDownCol = self.board.getDimensionalDataWithDirection((1, noOfRows - dcd), (1, -1))
            if len(diaDownCol) < howMany:
                break
            if not analyzeFunc(self.ANALYZE_DIADW, {self.KEY_COORD_COL: 1, self.KEY_COORD_ROW: noOfRows - dcd}, diaDownCol):
                return

        # 2) Start in upper-left corner and go right in upper row
        #    and pick out the downward diagonal.
        for drd in range(noOfRows-1):
            diaDownRow = self.board.getDimensionalDataWithDirection((drd + 2, noOfRows), (1, -1))
            if len(diaDownRow) < howMany:
                break
            if not analyzeFunc(self.ANALYZE_DIADW, {self.KEY_COORD_COL: drd + 2, self.KEY_COORD_ROW: noOfRows}, diaDownRow):
                return
        return None

    def __isBoardFull(self):
        if self.NO_TOKEN in self.board.getAllData():
            return False
        return True
    def __isFree(self,coordinate):
        return self.board.getData(coordinate)==self.NO_TOKEN
    def __isBoardEmpty(self):
        return all(x == self.NO_TOKEN or x is None for x in self.board.getAllData())


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




    # Takes a list and checks if there are five in a row of either X or O. If not: return None
    def __checkInARowInList(self, listToCheck, howMany):
        if len(listToCheck) < howMany:
            return None
        if listToCheck.count(self.X_TOKEN) < howMany and listToCheck.count(self.O_TOKEN) < howMany:
            return None
        for i in range(len(listToCheck)):
            listCutOut = listToCheck[i:i + howMany]
            if len(listCutOut) < howMany:
                break
            token = self.__checkIfAllArePlayerTokens(listCutOut)
            if token is not None:
                return token
        return

    # Takes a list and check if there are 'howMany' in a row with NO_TOKEN before and after.
    def __checkFreeInARow(self, listToCheck, howMany):
        if len(listToCheck) < howMany:
            return None
        if listToCheck.count(self.X_TOKEN) < howMany and listToCheck.count(self.O_TOKEN) < howMany:
            return None
        for i in range(len(listToCheck)):
            listCutOut = listToCheck[i:i + howMany + 2]
            if len(listToCheck) < howMany + 2:
                break
            if listCutOut[0] == self.NO_TOKEN and listCutOut[-1] == self.NO_TOKEN and listCutOut[
                                                                                      1:-2] == self.X_TOKEN:
                return self.X_TOKEN
            elif listCutOut[0] == self.NO_TOKEN and listCutOut[-1] == self.NO_TOKEN and listCutOut[
                                                                                        1:-2] == self.O_TOKEN:
                return self.O_TOKEN
        return None

    def __checkOneOfAKind(self, listToCheck, howMany, inRange):
        if len(listToCheck) < howMany:
            return None
        if listToCheck.count(self.X_TOKEN) < howMany and listToCheck.count(self.O_TOKEN) < howMany:
            return None
        for i in range(len(listToCheck)):
            listCutOut = listToCheck[i:i + inRange]
            if len(listCutOut) < howMany or len(listCutOut) < inRange:
                break
            if listCutOut.count(self.X_TOKEN) == howMany and listCutOut.count(self.NO_TOKEN) == len(
                    listCutOut) - howMany:
                return self.X_TOKEN
            elif listCutOut.count(self.O_TOKEN) == howMany and listCutOut.count(self.NO_TOKEN) == len(
                    listCutOut) - howMany:
                return self.O_TOKEN
        return None

    def help(self, what, startCoordDic, dataList):

        evaluations = {'XXXXX': self.MAX_EVAL,
                       '-XXXX': 10,
                       'XXXX-': 10,
                       'X-XXX': 10,
                       'XXX-X': 10,
                       'OXXX--': 3,
                       '-XXX-': 5,
                       '--XXXO': 5,
                       'XX-X-': 5,
                       '-XX-X': 5,
                       'X-XX-': 5,
                       '-X-XX': 5,
                       '-XX-': 3,
                       '-X-': 1,
                       'OOOOO': self.MIN_EVAL,
                       '-OOOO': -10,
                       'OOOO-': -10,
                       'OOO-O': -10,
                       'O-OOO': -10,
                       'XOOO--': -3,
                       '-OOO-': -5,
                       '--OOOX': -3,
                       'OO-O-': -5,
                       '-OO-O': -5,
                       'O-OO-': -5,
                       '-O-OO': -5,
                       '-OO-': -3,
                       '-O-': -1
                       }

        #print("Regarding: "+what+" "+str(startCoordDic))
        dataStr = ''.join(dataList)
        for pattern in evaluations:
            result = re.search(pattern, dataStr)
            if result is not None:
                print(what, pattern, evaluations[pattern])
                self.evalRes += evaluations[pattern]
                #print("Found "+pattern+" in "+dataStr+" at " + str(result.span()) + " for a val of: " + str(evaluations[pattern]))
        return True # True => Continue scan

    def evaluateList(self, dataList):

        evaluations = {'XXXXX': self.MAX_EVAL,
                       '-XXXX': 50,
                       'XXXX-': 50,
                       'X-XXX': 50,
                       'XXX-X': 50,
                       'OXXX--': 7,
                       '-XXX-': 25,
                       '--XXXO': 3,
                       'XX-X-': 25,
                       '-XX-X': 25,
                       'X-XX-': 25,
                       '-X-XX': 25,
                       '-X-X-': 5,
                       '-XX-': 5,
                       '---XX0': 2,
                       'OXX---': 2,
                       '-X-': 1,
                       'OOOOO': self.MIN_EVAL,
                       '-OOOO': -50,
                       'OOOO-': -50,
                       'OOO-O': -50,
                       'O-OOO': -50,
                       'XOOO--': -7,
                       '-OOO-': -25,
                       '--OOOX': -3,
                       'OO-O-': -25,
                       '-OO-O': -25,
                       'O-OO-': -25,
                       '-O-OO': -25,
                       '-O-O-': -5,
                       '-OO-': -5,
                       'XOO---': -2,
                       '---OOX': -2,
                       '-O-': -1
                       }

        #print("Regarding: "+what+" "+str(startCoordDic))
        dataStr = ''.join(dataList)
        for pattern in evaluations:
            result = re.search(pattern, dataStr)
            if result is not None:
                return evaluations[pattern]

        return 0

    def getMovesSorted(self, regardingMaximizer):

        winnerOfCurrentPos = self.getWinnerOfCurrentPosition()
        if winnerOfCurrentPos is not None:
            print("Current position is won for !", winnerOfCurrentPos)
            return []

        moveList = self.board.getIndexListWhereDataIs(self.NO_TOKEN)
        moveEvalDict = {}
        for move in moveList:
            moveCoords = tuple(self.board.dimCoordinateForIndex(move))
            # 1) Evaluate col, row, diagonals BEFORE move
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
            moveEvalDict[move] = evalDiff

        sorted_values = sorted(moveEvalDict.values(), reverse=regardingMaximizer)
        sortedDict = {}
        for i in sorted_values:
            for k in moveEvalDict.keys():
                if moveEvalDict[k] == i:
                    sortedDict[k] = moveEvalDict[k]

        sortedMoveList = list(sortedDict.keys())
        if len(sortedMoveList) > 3:
            dbgList = [self.board.dimCoordinateForIndex(x) for x in sortedMoveList[:3]]
            if regardingMaximizer:
                t='X'
            else:
                t = 'O'
            #print(t, dbgList)
            return sortedMoveList[:3]
        else:
            return sortedMoveList


    evalRes = 0
    def debug(self, regardingMaximizer):
        #print("*** DEBUG *** TBD")
        return




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
                    #self.game.debug(True)
                    #self.game.getMovesSorted(True)
                    playersmove = self.__askPlayerForMove()
                    self.game.makeMove(playersmove, self.playersToken)
                    """
                    c = self.game.getColForCoord(playersmove)
                    r = self.game.getRowForCoord(playersmove)
                    dd = self.game.getDiagonalForCoordDown(playersmove)
                    du = self.game.getDiagonalForCoordUp(playersmove)
                    print("Col:", str(c), self.game.evaluateList(c))
                    print("Row:", str(r), self.game.evaluateList(r))
                    print("DownDia:", str(dd), self.game.evaluateList(dd))
                    print("UpDia:", str(du), self.game.evaluateList(du))
                    """
                    #print("")
                    #self.printBoard()
                    #print("")
                except Exception as err:
                    print(str(err))
            else:
                move = self.game.getComputersMoveForCurrentPosition()
                self.game.makeMove(move[0], move[1])
                print("Computer moves: ", move[0])
                #self.game.debug(False)
                #self.game.getMovesSorted(False)
                #playersmove = self.__askPlayerForMove()
                #self.game.makeMove(playersmove, self.computersToken)

                #print("")
                #self.printBoard()
                #print("")


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
        self.computersToken=tmpToken
    def __askPlayerForMove(self):
        while True:
            print("Your move(" + self.playersToken + ")>")
            move = input()
            if move == 'e':
                eval = self.game.evalBoard()
                print("CurrentEval: ", eval)
                continue
            if move == 'd':
                self.game.debug()
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