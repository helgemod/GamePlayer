import MinMaxAlgorithm as mma
import StrideDimensions as sd

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
        self.computerAlgo = mma.MinMaxAlgo(self.evalBoard,\
                                           self.moveX,self.moveO,\
                                           self.undoMove,self.undoMove,\
                                           self.getPossibleMoves,self.getPossibleMoves,\
                                           self.MIN_EVAL,self.MAX_EVAL)

    ########################################
    #
    #           Game interface
    #
    ########################################

    # Just call this to play textbased against defined algo.
    def playTextbasedAgainstComputer(self):
        print("*"*11)
        print("TIC TAC TOE")
        print("*"*11)
        print("Play X or O? >")
        token = input()
        if token == self.O_TOKEN:
            self.playersToken = self.O_TOKEN
        self.whoHas = self.X_TOKEN

        while True:
            self.__printBoard()
            if self.whoHas==self.playersToken:
                moveCoordinates = self.__askPlayerForMove()
                self.board.setData(moveCoordinates,self.whoHas)
            else:
                move = self.computerAlgo.calculateMove(self.playersToken==self.O_TOKEN)
                print("My move: ",self.board.dimCoordinateForIndex(move))
                self.board.setDataAtIndex(move,self.whoHas)

            askPlayAgain = False
            if not self.__checkThreeInARow() == None:
                self.__printBoard()
                print("WINNER IS ",self.whoHas)
                askPlayAgain = True
            elif self.__isBoardFull():
                self.__printBoard()
                print("IT IS A TIE")
                askPlayAgain=True

            if askPlayAgain:
                print("Rematch? (Y/n)>")
                rematch=input()
                if not rematch=='n':
                    self.board.fillData(self.NO_TOKEN) #Clearboard:
                    self.__invertPlayersToken()
                    self.whoHas = self.X_TOKEN
                    continue
                else:
                    print("Thanks for playing!")
                    break

            if self.whoHas==self.X_TOKEN:
                self.whoHas=self.O_TOKEN
            else:
                self.whoHas=self.X_TOKEN

    # Call this if you want to build an external GUI that
    # plays against this engine.
    #
    #   callback_computersMove - a function that takes as
    #                            argument a tuple with
    #                            computers move as coordinates
    #                            (1,1)...(3,3)
    #   callback_messageHandler - A function that takes a string
    #                             as argument with a message to
    #                             a user.
    #   callback_askForUserMove - When this is call the engine
    #                             is waiting for at user to make
    #                             a move.
    #                             Call "userMove"-method below.
    #
    callback_computersMove = None
    callback_messageHandler = None
    callback_askForUserMove = None
    def playGenericGame(self,callback_computersMove,\
                        callback_messageHandler,\
                        callback_askForUserMove,
                        playersToken):
        return #To be continued implementation
        self.playersToken = playersToken
        self.callback_computersMove = callback_computersMove
        self.callback_messageHandler = callback_messageHandler
        self.callback_askForUserMove = callback_askForUserMove

        self.callback_messageHandler("Game starting!")
        if self.whoHas == self.playersToken:
            self.callback_askForUserMove()

        #TO BE CONTINUED...

    #Takes a users move as a tuple (1,1) - (3,3)
    def userMove(self,coords):
        try:
            self.__checkMove(coords,self.playersToken)
        except Exception as err:
            self.callback_messageHandler(str(err))

        print("Come here?")
        self.board.setData(coords,self.playersToken)

        move = self.computerAlgo.calculateMove(self.playersToken == self.O_TOKEN)
        self.board.setDataAtIndex(move, self.whoHas)
        self.callback_computersMove(tuple(self.board.dimCoordinateForIndex(move)))

    #Call this to get the board for print.
    def getBoard(self):
        return self.board.getDimensionalData((None, None))

    def makeMove(self,coordinates,token):
        try:
            self.__checkMove(coordinates,token)
        except Exception as err:
            print(str(err))
            return
        self.board.setData(coordinates,token)
        self.__invertWhoHas()

    def getComputersMoveForCurrentPosition(self):
        move = self.computerAlgo.calculateMove(self.whoHas == self.X_TOKEN) #Move as Maximizer or Minimizer.
        return (self.board.dimCoordinateForIndex(move),self.whoHas)

    def getWinnerOfCurrentPosition(self):
        if self.evalBoard() == self.MAX_EVAL:
            return self.X_TOKEN
        elif self.evalBoard() == self.MIN_EVAL:
            return self.O_TOKEN
        return None

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
        return self.board.getIndexListWhereDataIs(self.NO_TOKEN)


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

    def __invertPlayersToken(self):
        if self.playersToken==self.X_TOKEN:
            self.playersToken=self.O_TOKEN
        else:
            self.playersToken=self.X_TOKEN
    def __checkMove(self,coordinate,token):
        if not token in (self.X_TOKEN,self.O_TOKEN):
            raise Exception("Only \'X\' or \'O\' is allowed as token!")
            return

        if not self.whoHas == token:
            raise Exception("Wrong players move")
            return
        try:
            x = int(coordinate[0])
            y = int(coordinate[1])
        except:
            raise Exception("Give tuple of integer as move! E.g. (1,1)")
            return

        if x < 1 or x > self.size or y < 1 or y > self.size:
            print("!!!! Coord min=1 max=3 !!!")
            raise Exception("!!!! Coord min=1 max=3 !!!")
            return

        if not self.__isFree((x, y)):
            raise Exception("!!! OCCUPIED SQUARE !!!")
            return



    def __askPlayerForMove(self):
        while True:
            print("Your move(" + self.whoHas + ")>")
            move = input()
            coord = move.split(",")
            if len(coord) < 2 or len(coord) > 2:
                print("!!! Give coord eg. 3,2 !!!")
                continue
            try:
                x = int(coord[0])
                y = int(coord[1])
                if x < 1 or x > self.size or y < 1 or y > self.size:
                    print("!!!! Coord min=1 max=3 !!!")
                    continue
                else:
                    if not self.__isFree((x, y)):
                        print("!!! OCCUPIED SQUARE !!!")
                        continue
                    else:
                        break
            except:
                print("!!! Give numbers for coords !!!")
                continue

        return (x, y)
    def __checkWin(self,ll):
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
            token = self.__checkWin(row)
            if not token == None:
                return token
            col = self.board.getDimensionalData((x+1,None))
            token = self.__checkWin(col)
            if not token == None:
                return token

        #Lets make own loop for diagonal
        #Begin with the most likely diagonals
        # (1,1) and upward
        # (1,size) and downward
        dia = self.board.getDimensionalDataWithDirection((1,1),(1,1))
        token = self.__checkWin(dia)
        if not token == None:
            return token
        dia = self.board.getDimensionalDataWithDirection((1,3),(1,-1))
        token = self.__checkWin(dia)
        if not token == None:
            return token

        return None
    def __isBoardFull(self):
        if self.NO_TOKEN in self.board.getAllData():
            return False
        return True
    def __isFree(self,coordinate):
        return self.board.getData(coordinate)==self.NO_TOKEN:

    def __printBoard(self):
        list = self.board.getDimensionalData((None, None))
        for x in range(len(list) - 1, -1, -1):
            for y in range(len(list)):
                print(list[x][y], end=' ')
            print("")

    ################################
    #
    # Help functions for evaluator
    # - Change these to increase
    #   engines strength.
    #
    ################################
    def __evalCenter(self,eval):
        centerToken = self.board.getData((2,2))
        if centerToken == self.X_TOKEN:
            return eval
        elif centerToken == self.O_TOKEN:
            return -eval
        return 0
    def __evalTwoInARow(self,eval):
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

class TextBasedTicTacToeGame:
    pass

