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
                    '-XXXX-': 50,
                    '-XXXXO': 30,
                    'OXXXX-': 30,
                    '-OOOO-': -50,
                    'XOOOO-': -30,
                    '-OOOOX': -30,
                    '-X-XXX-': 50,
                    '-XXX-X-': 50,
                    '-O-OOO-': -50,
                    '-OOO-O-': -50,

                   'XXXXX': MAX_EVAL,
                   'OOOOO': MIN_EVAL,
                }



    potentialWinnersX = {
                '-XXX-',
                '-X-XX-',
                '-XX-X-',
                'XXXX-',
                '-XXXX',
                'XX-XX',
                'X-XXX',
                'XXX-X',
            }
    potentialWinnersO = {
                '-OOO-',
                '-O-OO-',
                '-OO-O-',
                'OOOO-',
                '-OOOO',
                'OO-OO',
                'O-OOO',
                'OOO-O',
    }


    # In future this can be able to point at different algorithms
    # to test them.
    computerAlgo = None

    def __init__(self):
        #self.cols = 6
        #self.rows = 3
        self.whoHas = self.X_TOKEN
        self.playersToken = self.X_TOKEN
        self.board = sd.StrideDimension((6, 6)) #cols=6 rows=3
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

        ocoord = self.isFirstMoveForO()
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
        self.board = sd.StrideDimension((6, 6))  # cols=6 rows=3
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
    def isFirstMoveForO(self):
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

        #print("Regarding: "+what+" "+str(startCoordDic))
        dataStr = ''.join(dataList)
        for pattern in self.evaluations:
            result = re.search(pattern, dataStr)
            if result is not None:
                print(what, pattern, self.evaluations[pattern])
                self.evalRes += self.evaluations[pattern]
                #print("Found "+pattern+" in "+dataStr+" at " + str(result.span()) + " for a val of: " + str(evaluations[pattern]))
        return True # True => Continue scan

    def isThereAPotentialWinnerInThisList(self, dataList, regardingMaximizer):
        dataStr = ''.join(dataList)
        if regardingMaximizer:
            for pattern in self.potentialWinnersX:
                result = re.search(pattern, dataStr)
                if result is not None:
                    return True
        else:
            for pattern in self.potentialWinnersO:
                result = re.search(pattern, dataStr)
                if result is not None:
                    return True



    def evaluateList(self, dataList):
        dataStr = ''.join(dataList)
        addVal = 0
        for pattern in self.evaluations:
            result = re.search(pattern, dataStr)
            if result is not None:
                addVal += self.evaluations[pattern]
        return addVal

    def getMovesSorted(self, regardingMaximizer):

        winnerOfCurrentPos = self.getWinnerOfCurrentPosition()
        if winnerOfCurrentPos is not None:
            print("Current position is won for !", winnerOfCurrentPos)
            return []

        readList = self.board.getIndexListWhereDataIs(self.NO_TOKEN)

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
        """
        for i in range(len(moveList)):
            print(self.board.dimCoordinateForIndex(moveList[i]), end=' ')
        print("")
        """

        listOfPotentialWinnerMoves = []

        moveEvalDict = {}
        bestDiffMax = self.MIN_EVAL
        bestDiffMin = self.MAX_EVAL
        for move in moveList:

            moveCoords = tuple(self.board.dimCoordinateForIndex(move))
            #print("Trying move", moveCoords, move)
            # 1) Evaluate col, row, diagonals BEFORE move
            preColEval = self.getColForCoord(moveCoords)
            preRowEval = self.getRowForCoord(moveCoords)
            preDiaUpEval = self.getDiagonalForCoordUp(moveCoords)
            preDiaDwEval = self.getDiagonalForCoordDown(moveCoords)

            # First check if that move will defeat a potential winner for opponent.
            if self.isThereAPotentialWinnerInThisList(preColEval, not regardingMaximizer):
                #print("POTENTIAL WINNER OPPONENT COL and Coord:", preColEval, moveCoords)
                # 2) Try the move
                if regardingMaximizer:
                    self.moveX(move)
                else:
                    self.moveO(move)
                post = self.getColForCoord(moveCoords)
                if not self.isThereAPotentialWinnerInThisList(post, not regardingMaximizer):
                    #print("NO LONGER a potential win in this COL for OPPONENT APPEND IT", post)
                    listOfPotentialWinnerMoves.append(move)
                self.undoMove(move)

            if self.isThereAPotentialWinnerInThisList(preColEval, regardingMaximizer):
                #print("POTENTIAL WINNER FOR ME COL and Coord:", preColEval, moveCoords)
                # 2) Try the move
                if not regardingMaximizer:
                    self.moveX(move)
                else:
                    self.moveO(move)
                post = self.getColForCoord(moveCoords)
                if not self.isThereAPotentialWinnerInThisList(post, regardingMaximizer):
                    #print("NO LONGER a potential win in this COL for ME APPEND IT", post)
                    listOfPotentialWinnerMoves.append(move)
                self.undoMove(move)

            if self.isThereAPotentialWinnerInThisList(preRowEval, not regardingMaximizer):
                #print("POTENTIAL WINNER OPPONENT ROW and Coord:", preColEval, moveCoords)
                # 2) Try the move
                if regardingMaximizer:
                    self.moveX(move)
                else:
                    self.moveO(move)
                post = self.getRowForCoord(moveCoords)
                if not self.isThereAPotentialWinnerInThisList(post, not regardingMaximizer):
                    #print("NO LONGER a potential win in this ROW for OPPONENT APPEND IT", post)
                    listOfPotentialWinnerMoves.append(move)
                self.undoMove(move)

            if self.isThereAPotentialWinnerInThisList(preRowEval, regardingMaximizer):
                #print("POTENTIAL WINNER FOR ME  ROW and Coord:", preColEval, moveCoords)
                # 2) Try the move
                if not regardingMaximizer:
                    self.moveX(move)
                else:
                    self.moveO(move)
                post = self.getRowForCoord(moveCoords)
                if not self.isThereAPotentialWinnerInThisList(post, regardingMaximizer):
                    #print("NO LONGER a potential win in this ROW for ME APPEND IT", post)
                    listOfPotentialWinnerMoves.append(move)
                self.undoMove(move)



            if self.isThereAPotentialWinnerInThisList(preDiaUpEval, not regardingMaximizer):
                #print("POTENTIAL WINNER OPPONENT DIA UP and Coord:", preColEval, moveCoords)
                # 2) Try the move
                if regardingMaximizer:
                    self.moveX(move)
                else:
                    self.moveO(move)
                post = self.getDiagonalForCoordUp(moveCoords)
                if not self.isThereAPotentialWinnerInThisList(post, not regardingMaximizer):
                    #print("NO LONGER a potential win in this DIA UP for OPPONENT APPEND IT", post)
                    listOfPotentialWinnerMoves.append(move)
                self.undoMove(move)

            if self.isThereAPotentialWinnerInThisList(preDiaUpEval, regardingMaximizer):
                #print("POTENTIAL WINNER FOR ME DIA UP and Coord:", preColEval, moveCoords)
                # 2) Try the move
                if not regardingMaximizer:
                    self.moveX(move)
                else:
                    self.moveO(move)
                post = self.getDiagonalForCoordUp(moveCoords)
                if not self.isThereAPotentialWinnerInThisList(post, regardingMaximizer):
                    #print("NO LONGER a potential win in this DIA UP for ME APPEND IT", post)
                    listOfPotentialWinnerMoves.append(move)
                self.undoMove(move)

            if self.isThereAPotentialWinnerInThisList(preDiaDwEval, not regardingMaximizer):
                #print("POTENTIAL WINNER OPPONENT DIA DWN and Coord:", preColEval, moveCoords)
                # 2) Try the move
                if regardingMaximizer:
                    self.moveX(move)
                else:
                    self.moveO(move)
                post = self.getDiagonalForCoordDown(moveCoords)
                if not self.isThereAPotentialWinnerInThisList(post, not regardingMaximizer):
                    #print("NO LONGER a potential win in this DIA DWN for OPPONENT APPEND IT", post)
                    listOfPotentialWinnerMoves.append(move)
                self.undoMove(move)

            if self.isThereAPotentialWinnerInThisList(preDiaDwEval, regardingMaximizer):
                #print("POTENTIAL WINNER FOR ME DIA DWN and Coord:", preColEval, moveCoords)
                # 2) Try the move
                if not regardingMaximizer:
                    self.moveX(move)
                else:
                    self.moveO(move)
                post = self.getDiagonalForCoordDown(moveCoords)
                if not self.isThereAPotentialWinnerInThisList(post, regardingMaximizer):
                    #print("NO LONGER a potential win in this DIA DWN for ME APPEND IT", post)
                    listOfPotentialWinnerMoves.append(move)
                self.undoMove(move)

            #print("----->", listOfPotentialWinnerMoves,len(listOfPotentialWinnerMoves))
            if len(listOfPotentialWinnerMoves) > 0:
                #print("got move that is filled..no loger go on...")
                continue


            preEval = self.evaluateList(preColEval)
            preEval += self.evaluateList(preRowEval)
            preEval += self.evaluateList(preDiaUpEval)
            preEval += self.evaluateList(preDiaDwEval)

            # 2) Try the move
            if regardingMaximizer:
                self.moveX(move)
            else:
                self.moveO(move)

            # 3) Evaluate after the move try
            postColEval = self.getColForCoord(moveCoords)
            postRowEval = self.getRowForCoord(moveCoords)
            postDiaUpEval = self.getDiagonalForCoordUp(moveCoords)
            postDiaDwEval = self.getDiagonalForCoordDown(moveCoords)
            postEval = self.evaluateList(postColEval)
            postEval += self.evaluateList(postRowEval)
            postEval += self.evaluateList(postDiaUpEval)
            postEval += self.evaluateList(postDiaDwEval)

            # 4) Undo the move try
            self.undoMove(move)

            evalDiff = postEval - preEval

            if regardingMaximizer:
                bestDiffMax = max(bestDiffMax, evalDiff)
                #print("X> Move, evalDiff, best", self.board.dimCoordinateForIndex(move), evalDiff, bestDiffMax, end=' ')
                if evalDiff > (bestDiffMax - 10):
                    #print("Within 10 from max...so add")
                    moveEvalDict[move] = evalDiff
                else:
                    pass
                    #print("---so bad move for X...dont add")

            else:
                bestDiffMin = min(bestDiffMin, evalDiff)
                #print("O> Move, evalDiff, best", self.board.dimCoordinateForIndex(move), evalDiff, bestDiffMin, end=' ')
                if evalDiff < (bestDiffMin + 10):
                    #print("Within 10 from best so add..")
                    moveEvalDict[move] = evalDiff
                else:
                    pass
                    #print("----so bad move for O. Dont add")

        if len(listOfPotentialWinnerMoves) > 0:
            #print("RETURINGG!!! ----->", listOfPotentialWinnerMoves)
            """
            for c in listOfPotentialWinnerMoves:
                print(self.board.dimCoordinateForIndex(c),end='')
            print("")
            """
            return listOfPotentialWinnerMoves

        ## REMOVE DEBUG FROM HERE
        #tmpList = [self.board.dimCoordinateForIndex(x) for x in moveEvalDict.keys()]
        #print("Moves that are ok...", tmpList)
        ## REMOVE DEBUG TO HERE

        # So far all sensible moves are evaluated and placed into a dictionary.
        # Keys are moves. Value are the "evalDiff" (how much difference that move makes).
        sorted_values = sorted(moveEvalDict.values(), reverse=regardingMaximizer)
        sortedDict = {}
        for i in sorted_values:
            for k in moveEvalDict.keys():
                if moveEvalDict[k] == i:
                    sortedDict[k] = moveEvalDict[k]



        sortedMoveList = list(sortedDict.keys())
        #print("And list of only the moves...(can be returned?):", sortedMoveList)

        bestEval = sorted_values[0]

        """
        print("Sorted dict with moves and their values:")
        for key in sortedDict.keys():
            print("%s-%s"%(str(self.board.dimCoordinateForIndex(key)),str(sortedDict[key])), end=' ')
        print("")
        """

        bestOfDic = {}
        cntr = 0
        for key in sortedDict.keys():
            if sortedDict[key] > bestEval - 15:
                bestOfDic[key] = sortedDict[key]
            cntr += 1
            if cntr == 6:
                break
        """
        print("Best of dict with moves and their values:")
        for key in bestOfDic.keys():
            print("%s-%s" % (str(self.board.dimCoordinateForIndex(key)), str(bestOfDic[key])), end=' ')
        print("")
        """

        listToReturn = list(bestOfDic.keys())
        """
        for i in listToReturn:
            print(self.board.dimCoordinateForIndex(i),end='')
        print("")
        """

        return listToReturn



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

                #self.game.getMovesSorted(False)
                #playersmove = self.__askPlayerForMove()
                #self.game.makeMove(playersmove, self.computersToken)


            #continue
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