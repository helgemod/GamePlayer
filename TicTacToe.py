#!/usr/bin/env python

"""
# TicTacToe implements game with same name, based on algorithms of
#  choice.
#
# The purpose of this is:
#   1) Implement the game in a generic way.
#   2) For demo purpose and educational purpose. And perhaps some amusement.
#
# Usage:
#
#   Make an object of class TicTacToe and attach your own GUI to it. Two example
#   classes are attached that examplifies how to use class TicTacToe.
#
#   When creating object, try out other game algorithms than MinMax, by
#   attaching these to "computerAlgo".
#
"""

import MinMaxAlgorithm as mma
import StrideDimensions as sd
import time
import logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s=> %(message)s')
#logging.disable(logging.CRITICAL)

__author__ = "Helge Modén, www.github.com/helgemod"
__copyright__ = "Copyright 2020, Helge Modén"
__credits__ = None
__license__ = "MIT"
__version__ = "1.0.1"
__maintainer__ = "Helge Modén, https://github.com/helgemod/MinMaxAlgorithm"
__email__ = "helgemod@gmail.com"
__status__ = "https://github.com/helgemod/GamePlayer"
__date__ = "2020-11-20"

class TicTacToe:
    board = None
    X_TOKEN = 'X'
    O_TOKEN = 'O'
    NO_TOKEN = '-'
    size = 3
    MIN_EVAL = -100
    MAX_EVAL = 100
    whoHas = X_TOKEN
    playersToken = X_TOKEN

    # In future this can be able to point at different algorithms
    # to test them.
    computerAlgo = None

    def __init__(self):
        self.board = sd.StrideDimension((3,3))
        self.board.fillData(self.NO_TOKEN)
        self.computerAlgo = mma.GameAlgo(self.evalBoard,
                                           self.moveX, self.moveO,
                                           self.undoMove, self.undoMove,
                                           self.getPossibleMoves, self.getPossibleMoves,
                                           self.MIN_EVAL, self.MAX_EVAL)

    ########################################
    #
    #           Game interface
    #
    ########################################
    #Call this to get the board for print.
    def getBoard(self):
        return self.board.getDimensionalData((None, None))
    def makeMove(self, coordinates, token):
        try:
            self.__checkMove(coordinates, token)
        except Exception as err:
            print(str(err))
            return False
        self.board.setData(coordinates, token)
        self.__invertWhoHas()
        return True
    def getComputersMoveForCurrentPosition(self):
        #move = self.computerAlgo.calculateMove(mma.MINMAX_ALGO, self.whoHas == self.X_TOKEN)
        move = self.computerAlgo.calculateMove(mma.MINMAXALPHABETAPRUNING_ALGO, self.whoHas == self.X_TOKEN, 2)
        #move = self.computerAlgo.calculateMove(mma.MINMAX_ALGO_WITH_LOGGING, self.whoHas == self.X_TOKEN)
        return (self.board.dimCoordinateForIndex(move), self.whoHas)
    def getWinnerOfCurrentPosition(self):
        currentEvaluation = self.evalBoard()
        if currentEvaluation == self.MAX_EVAL:
            return self.X_TOKEN
        elif currentEvaluation == self.MIN_EVAL:
            return self.O_TOKEN
        elif self.__isBoardFull():
            return self.NO_TOKEN
        return None
    def resetGame(self):
        self.whoHas = self.X_TOKEN
        self.board.fillData(self.NO_TOKEN)#clearboard

    ###############################################
    #
    # Callback Interfaces for different algorithms
    #
    ###############################################
    # Callback functions used by computer algorithm
    def evalBoard(self):
        # First, check if someone has a won position
        winningToken = self.__checkThreeInARow()
        if winningToken == self.X_TOKEN:
            return self.MAX_EVAL
        elif winningToken == self.O_TOKEN:
            return self.MIN_EVAL

        # No winner. Evaluate current position.
        # To increase engines strength, then
        # improve the help-eval methods below.
        # Or try to change the weights.
        #
        # For example. __evalTwoInARow has weight 5,
        # since programmer thinks that is more important
        # than having center position.
        # Perhaps more help-eval methods are needed? More
        # positions to evaluate?
        addVal = 0
        addVal += self.__evalCenter(2) #Weight 2
        addVal += self.__evalTwoInARow(5) #Weight 5

        return addVal
    def moveX(self,move):
        self.board.setDataAtIndex(move,self.X_TOKEN)
    def moveO(self,move):
        self.board.setDataAtIndex(move,self.O_TOKEN)
    def undoMove(self,move):
        self.board.setDataAtIndex(move,self.NO_TOKEN)
    def getPossibleMoves(self):
        winnerOfCurrentPos = self.getWinnerOfCurrentPosition()
        if winnerOfCurrentPos is None:
            return self.board.getIndexListWhereDataIs(self.NO_TOKEN)
        else:
            return []  # If the game is over. No possible moves further can be done!


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

        if x < 1 or x > self.size or y < 1 or y > self.size:
            print("!!!! Coord min=1 max=3 !!!")
            raise Exception("!!!! Coord min=1 max=3 !!!")

        if not self.__isFree((x, y)):
            raise Exception("!!! OCCUPIED SQUARE !!!")
    def __checkForThree(self, ll):
        if self.NO_TOKEN in ll:
            return None
        if all([x==self.X_TOKEN for x in ll]):
            return self.X_TOKEN
        if all([o==self.O_TOKEN for o in ll]):
            return self.O_TOKEN
        return None
    def __checkThreeInARow(self):
        for x in range(self.size):
            row = self.board.getDimensionalData((None,x+1))
            token = self.__checkForThree(row)
            if not token == None:
                return token
            col = self.board.getDimensionalData((x+1,None))
            token = self.__checkForThree(col)
            if not token == None:
                return token

        #Lets make own loop for diagonal
        #Begin with the most likely diagonals
        # (1,1) and upward
        # (1,size) and downward
        dia = self.board.getDimensionalDataWithDirection((1,1),(1,1))
        token = self.__checkForThree(dia)
        if not token == None:
            return token
        dia = self.board.getDimensionalDataWithDirection((1,3),(1,-1))
        token = self.__checkForThree(dia)
        if not token == None:
            return token

        return None
    def __isBoardFull(self):
        if self.NO_TOKEN in self.board.getAllData():
            return False
        return True
    def __isFree(self,coordinate):
        return self.board.getData(coordinate)==self.NO_TOKEN


    ################################
    #
    # Help functions for evaluator
    # - Change these to increase
    #   engines strength.
    #
    ################################
    def __evalCenter(self, eval):
        centerToken = self.board.getData((2,2))
        if centerToken == self.X_TOKEN:
            return eval
        elif centerToken == self.O_TOKEN:
            return -eval
        return 0
    def __evalTwoInARow(self, eval):
        addEval = 0
        for x in range(self.size):
            row = self.board.getDimensionalData((None,x+1))
            if row.count(self.NO_TOKEN)==1 and row.count(self.X_TOKEN)==2:
                addEval +=eval
            elif row.count(self.NO_TOKEN) == 1 and row.count(self.O_TOKEN) == 2:
                addEval -= eval

            col = self.board.getDimensionalData((x+1,None))
            if col.count(self.NO_TOKEN)==1 and col.count(self.X_TOKEN)==2:
                addEval +=eval
            elif col.count(self.NO_TOKEN) == 1 and col.count(self.O_TOKEN) == 2:
                addEval -= eval

        dia1 = self.board.getDimensionalDataWithDirection((1, 1), (1, 1))
        if dia1.count(self.NO_TOKEN) == 1 and dia1.count(self.X_TOKEN) == 2:
            addEval +=eval
        elif dia1.count(self.NO_TOKEN) == 1 and dia1.count(self.O_TOKEN) == 2:
            addEval -= eval

        dia2 = self.board.getDimensionalDataWithDirection((1, 3), (1, -1))
        if dia2.count(self.NO_TOKEN) == 1 and dia2.count(self.X_TOKEN) == 2:
            addEval += eval
        elif dia2.count(self.NO_TOKEN) == 1 and dia2.count(self.O_TOKEN) == 2:
            addEval -= eval

        return addEval

"""
Example how to use TicTacToe-class to play.
"""
class TextBasedTicTacToeGame:
    def __init__(self):
        self.game = TicTacToe()

    def play(self):
        print("*" * 11)
        print("TIC TAC TOE")
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
                    playersmove = self.__askPlayerForMove()
                    self.game.makeMove(playersmove, self.playersToken)
                except Exception as err:
                    logging.DEBUG(str(err))
            else:
                move = self.game.getComputersMoveForCurrentPosition()
                self.game.makeMove(move[0],move[1])
                print("Computer moves: ", move[0])

            askAgain = False
            if self.game.getWinnerOfCurrentPosition() == self.playersToken:
                self.printBoard()
                print("You win! Congrats!")
                askAgain = True
            elif self.game.getWinnerOfCurrentPosition() == self.computersToken:
                self.printBoard()
                print("You loose...sorry.")
                askAgain = True
            elif self.game.getWinnerOfCurrentPosition() == self.game.NO_TOKEN:
                self.printBoard()
                print("It's a draw!")
                askAgain = True

            if askAgain:
                print("Another game? (Y/n)")
                ans=input()
                if ans=='n':
                    print("Ok! Thank's for the game!")
                    break
                self.game.resetGame()
                self.__swapToken()

    def printBoard(self):
        list = self.game.getBoard()
        for x in range(len(list) - 1, -1, -1):
            for y in range(len(list)):
                print(list[x][y], end=' ')
            print("")
    def __swapToken(self):
        tmpToken = self.playersToken
        self.playersToken = self.computersToken
        self.computersToken=tmpToken
    def __askPlayerForMove(self):
        while True:
            print("Your move(" + self.playersToken + ")>")
            move = input()
            coord = move.split(",")
            if len(coord) < 2 or len(coord) > 2:
                print("!!! Give coord eg. 3,2 !!!")
                continue
            try:
                x = int(coord[0])
                y = int(coord[1])
                if x < 1 or x > self.game.size or y < 1 or y > self.game.size:
                    print("!!!! Coord min=1 max=3 !!!")
                    continue
            except:
                print("!!! Give numbers for coords !!!")
                continue
            break

        return (x, y)

class computerVsComputerGame:

    def __init__(self):
        self.game = TicTacToe()

    def play(self):
        print("*" * 11)
        print("TIC TAC TOE")
        print("*" * 11)
        while True:
            self.printBoard()
            time.sleep(1)
            move = self.game.getComputersMoveForCurrentPosition()
            print("Computer moves:",move)
            self.game.makeMove(move[0],move[1])

            askAgain = False
            winResult = self.game.getWinnerOfCurrentPosition()
            if winResult == self.game.X_TOKEN or winResult == self.game.O_TOKEN:
                self.printBoard()
                print("WINNER: ",winResult)
                askAgain = True
            elif winResult == self.game.NO_TOKEN:
                self.printBoard()
                print("It's a draw!")
                askAgain = True

            if askAgain:
                print("Another game? (Y/n)")
                ans = input()
                if ans == 'n':
                    print("Ok! Thank's for watching!")
                    break
                self.game.resetGame()
    def printBoard(self):
        list = self.game.getBoard()
        for x in range(len(list) - 1, -1, -1):
            for y in range(len(list)):
                print(list[x][y], end=' ')
            print("")
