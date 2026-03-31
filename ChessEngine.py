class gameState():
    def __init__(self):
        self.board = [
                    ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
                    ['bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP'],
                    ['--', '--', '--', '--', '--', '--', '--', '--'],
                    ['--', '--', '--', '--', '--', '--', '--', '--'],
                    ['--', '--', '--', '--', '--', '--', '--', '--'],
                    ['--', '--', '--', '--', '--', '--', '--', '--'],
                    ['wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP'],
                    ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']
                ]
        

        self.whiteToMove = True
        inCheck = False
        self.whiteWon = False
        self.blackWon = False
        self.staleMate = False

        self.whiteInCheck = False
        self.blackInCheck = False


        self.castleRights = {'wKs' : True, 'wQs' : True, 'bKs' : True, 'bQs' : True}

        self.whiteenpassantMoves = []
        self.blackenpassantMoves = []

        self.enpassantMove = False




    def makeMove(self, startSq, endSq):

        print('*****************************************************************************************************************************************************')

        self.move_complete = 0

        
        self.enpassantMove = False
        self.temp_board = self.board


        self.whitePawnPromotion = False
        self.blackPawnPromotion = False

        self.whiteCastleMove_Ks = False
        self.whiteCastleMove_Qs = False
        self.blackCastleMove_Ks = False
        self.blackCastleMove_Qs = False

        
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.main_pieceMoved = self.board[self.startRow][self.startCol]
        self.main_pieceCaptured = self.board[self.endRow][self.endCol]
        if self.main_pieceMoved[0] == 'w' and self.whiteToMove:
            if self.validMove(self.temp_board, self.main_pieceMoved, self.startRow, self.startCol, self.endRow, self.endCol) and self.whitePawnPromotion:
                self.board[self.startRow][self.startCol] = '--'
                self.board[self.endRow][self.endCol] = 'wQ' 
                self.move_complete = 1
                self.whiteToMove = not self.whiteToMove    
            elif self.validMove(self.temp_board, self.main_pieceMoved, self.startRow, self.startCol, self.endRow, self.endCol) and not self.whitePawnPromotion:
                if self.whiteCastleMove_Ks and self.main_pieceMoved == 'wK':
                    self.board[self.startRow][self.startCol] = '--'
                    self.board[self.endRow][self.endCol] = 'wK'
                    self.board[7][7] = '--'
                    self.board[7][5] = 'wR'
                    self.castleRights['wKs'] = self.castleRights['wQs'] = False
                    self.move_complete = 1
                    self.whiteToMove = not self.whiteToMove  
                elif self.whiteCastleMove_Qs and self.main_pieceMoved == 'wK':
                    self.board[self.startRow][self.startCol] = '--'
                    self.board[self.endRow][self.endCol] = 'wK'
                    self.board[7][0] = '--'
                    self.board[7][3] = 'wR'
                    self.castleRights['wKs'] = self.castleRights['wQs'] = False
                    self.move_complete = 1
                    self.whiteToMove = not self.whiteToMove  
                elif self.enpassantMove:
                    self.board[self.startRow][self.startCol] = '--'
                    self.board[self.endRow][self.endCol] = self.main_pieceMoved
                    self.board[self.endRow + 1][self.endCol] = '--'
                    self.move_complete = 1
                    self.blackenpassantMoves.remove((self.endRow, self.endCol))
                    self.whiteToMove = not self.whiteToMove
                else:
                    self.board[self.startRow][self.startCol] = '--'
                    self.board[self.endRow][self.endCol] = self.main_pieceMoved 
                    self.move_complete = 1
                    self.whiteToMove = not self.whiteToMove    
        elif self.main_pieceMoved[0] == 'b' and not self.whiteToMove:
            if self.validMove(self.temp_board, self.main_pieceMoved, self.startRow, self.startCol, self.endRow, self.endCol) and self.blackPawnPromotion:
                self.board[self.startRow][self.startCol] = '--'
                self.board[self.endRow][self.endCol] = 'bQ'
                self.move_complete = 1
                self.whiteToMove = not self.whiteToMove
            elif self.validMove(self.temp_board, self.main_pieceMoved, self.startRow, self.startCol, self.endRow, self.endCol) and not self.blackPawnPromotion:
                if self.blackCastleMove_Ks and self.main_pieceMoved == 'bK':
                    self.board[self.startRow][self.startCol] = '--'
                    self.board[self.endRow][self.endCol] = 'bK'
                    self.board[0][7] = '--'
                    self.board[0][5] = 'bR'
                    self.castleRights['bKs'] = self.castleRights['bQs'] = False
                    self.move_complete = 1
                    self.whiteToMove = not self.whiteToMove  
                elif self.blackCastleMove_Qs and self.main_pieceMoved == 'bK':
                    self.board[self.startRow][self.startCol] = '--'
                    self.board[self.endRow][self.endCol] = 'bK'
                    self.board[0][0] = '--'
                    self.board[0][3] = 'bR'
                    self.castleRights['bKs'] = self.castleRights['bQs'] = False
                    self.move_complete = 1
                    self.whiteToMove = not self.whiteToMove  
                elif self.enpassantMove:
                    self.board[self.startRow][self.startCol] = '--'
                    self.board[self.endRow][self.endCol] = self.main_pieceMoved
                    self.board[self.endRow - 1][self.endCol] = '--'
                    self.move_complete = 1
                    self.whiteenpassantMoves.remove((self.endRow, self.endCol))
                    self.whiteToMove = not self.whiteToMove
                else:
                    self.board[self.startRow][self.startCol] = '--'
                    self.board[self.endRow][self.endCol] = self.main_pieceMoved 
                    self.move_complete = 1
                    self.whiteToMove = not self.whiteToMove 
        
        self.whiteCastleMove_Ks = False
        self.whiteCastleMove_Qs = False
        self.blackCastleMove_Ks = False
        self.blackCastleMove_Qs = False

        self.firstMove = False


        self.temp_board = self.board


        if self.main_pieceMoved[1] == 'P' and self.move_complete == 1:
            self.calculateEnpassantMoves(self.temp_board,  self.main_pieceMoved, self.startRow, self.startCol, self.endRow, self.endCol)
 
        self.inCheck(self.temp_board)

        self.prev_whiteInCheck = self.whiteInCheck
        self.prev_blackInCheck = self.blackInCheck

        self.temp_castleRights_wKs = self.castleRights['wKs']
        self.temp_castleRights_wQs = self.castleRights['wQs']
        self.temp_castleRights_bKs = self.castleRights['bKs']
        self.temp_castleRights_bQs = self.castleRights['bQs']

        if len(self.lenValidMoves(self.temp_board)) == 0 and self.whiteInCheck == True:
            self.blackWon = True
        elif len(self.lenValidMoves(self.temp_board)) == 0 and self.blackInCheck == True:
            self.whiteWon = True
        elif len(self.lenValidMoves(self.temp_board)) == 0 and self.blackInCheck == False and self.whiteInCheck == False:
            self.staleMate = True
        elif len(self.getPositionSets(self.temp_board)['bP']) == 0 and len(self.getPositionSets(self.temp_board)['wP']) == 0 and len(self.getPositionSets(self.temp_board)['bB']) == 0 and len(self.getPositionSets(self.temp_board)['wB']) == 0 and len(self.getPositionSets(self.temp_board)['bN']) == 0 and len(self.getPositionSets(self.temp_board)['wN']) == 0 and len(self.getPositionSets(self.temp_board)['bR']) == 0 and len(self.getPositionSets(self.temp_board)['wR']) == 0 and len(self.getPositionSets(self.temp_board)['bQ']) == 0 and len(self.getPositionSets(self.temp_board)['wQ']) == 0 and len(self.getPositionSets(self.temp_board)['bK']) != 0 and len(self.getPositionSets(self.temp_board)['wK']) != 0:
            self.staleMate = True
        

        #print(self.lenValidMoves(self.temp_board))

        self.castleRights['wKs'] = self.temp_castleRights_wKs
        self.castleRights['wQs'] = self.temp_castleRights_wQs
        self.castleRights['bKs'] = self.temp_castleRights_bKs
        self.castleRights['bQs'] = self.temp_castleRights_bQs
        #print(self.castleRights)

        

    def validMove(self, var_board, var_pieceMoved, var_startRow, var_startCol, var_endRow, var_endCol):
        if var_pieceMoved[1] == 'P':
            if self.validPawnMoves(var_board, var_pieceMoved, var_startRow, var_startCol, var_endRow, var_endCol):   
                if self.enpassantMove:
                    var_pieceMoved = var_board[var_startRow][var_startCol]
                    var_pieceCaptured = var_board[var_endRow + (1 if var_pieceMoved[0] == 'w' else -1)][var_endCol]
                    var_board[var_startRow][var_startCol] = '--'
                    var_board[var_endRow][var_endCol] = var_pieceMoved
                    var_board[var_endRow + (1 if var_pieceMoved[0] == 'w' else -1)][var_endCol] = '--'
                    if self.inCheck(var_board):
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = '--'
                        var_board[var_endRow + (1 if var_pieceMoved[0] == 'w' else -1)][var_endCol] = var_pieceCaptured
                        return False
                    else:
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = '--'
                        var_board[var_endRow + (1 if var_pieceMoved[0] == 'w' else -1)][var_endCol] = var_pieceCaptured
                        return True
                else:
                    var_pieceMoved = var_board[var_startRow][var_startCol]
                    var_pieceCaptured = var_board[var_endRow][var_endCol]
                    var_board[var_startRow][var_startCol] = '--'
                    var_board[var_endRow][var_endCol] = var_pieceMoved
                    if self.inCheck(var_board):
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        return False
                    else:
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        if var_pieceMoved[0] == 'w' and var_endRow == 0:
                            self.whitePawnPromotion = True
                            return True
                        elif var_pieceMoved[0] == 'b' and var_endRow == 7:
                            self.blackPawnPromotion = True
                            return True
                        else:
                            return True
        if var_pieceMoved[1] == 'B':
            if self.validBishopMoves(var_board, var_pieceMoved, var_startRow, var_startCol, var_endRow, var_endCol):
                var_pieceMoved = var_board[var_startRow][var_startCol]
                var_pieceCaptured = var_board[var_endRow][var_endCol]
                var_board[var_startRow][var_startCol] = '--'
                var_board[var_endRow][var_endCol] = var_pieceMoved
                if self.inCheck(var_board):
                    var_board[var_startRow][var_startCol] = var_pieceMoved
                    var_board[var_endRow][var_endCol] = var_pieceCaptured
                    return False
                else:
                    var_board[var_startRow][var_startCol] = var_pieceMoved
                    var_board[var_endRow][var_endCol] = var_pieceCaptured
                    return True
        if var_pieceMoved[1] == 'N':
            if self.validKnightMoves(var_board, var_pieceMoved, var_startRow, var_startCol, var_endRow, var_endCol):
                var_pieceMoved = var_board[var_startRow][var_startCol]
                var_pieceCaptured = var_board[var_endRow][var_endCol]
                var_board[var_startRow][var_startCol] = '--'
                var_board[var_endRow][var_endCol] = var_pieceMoved
                if self.inCheck(var_board):
                    var_board[var_startRow][var_startCol] = var_pieceMoved
                    var_board[var_endRow][var_endCol] = var_pieceCaptured
                    return False
                else:
                    var_board[var_startRow][var_startCol] = var_pieceMoved
                    var_board[var_endRow][var_endCol] = var_pieceCaptured
                    return True
        if var_pieceMoved[1] == 'R':
            if self.validRookMoves(var_board, var_pieceMoved, var_startRow, var_startCol, var_endRow, var_endCol):
                var_pieceMoved = var_board[var_startRow][var_startCol]
                var_pieceCaptured = var_board[var_endRow][var_endCol]
                var_board[var_startRow][var_startCol] = '--'
                var_board[var_endRow][var_endCol] = var_pieceMoved
                if self.inCheck(var_board):
                    var_board[var_startRow][var_startCol] = var_pieceMoved
                    var_board[var_endRow][var_endCol] = var_pieceCaptured
                    return False
                else:
                    if var_pieceMoved[0] == 'w' and var_startCol == 0 and var_startRow == 7:
                        self.castleRights['wQs'] = False
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        return True
                    elif var_pieceMoved[0] == 'w' and var_startCol == 7 and var_startRow == 7:
                        self.castleRights['wKs'] = False
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        return True
                    elif var_pieceMoved[0] == 'b' and var_startCol == 7 and var_startRow == 0:
                        self.castleRights['bKs'] = False
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        return True
                    elif var_pieceMoved[0] == 'b' and var_startCol == 0 and var_startRow == 0:
                        self.castleRights['bQs'] = False
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        return True
                    else:
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        return True                  
        if var_pieceMoved[1] == 'Q':
            if self.validQueenMoves(var_board, var_pieceMoved, var_startRow, var_startCol, var_endRow, var_endCol):
                var_pieceMoved = var_board[var_startRow][var_startCol]
                var_pieceCaptured = var_board[var_endRow][var_endCol]
                var_board[var_startRow][var_startCol] = '--'
                var_board[var_endRow][var_endCol] = var_pieceMoved
                if self.inCheck(var_board):
                    var_board[var_startRow][var_startCol] = var_pieceMoved
                    var_board[var_endRow][var_endCol] = var_pieceCaptured
                    return False
                else:
                    var_board[var_startRow][var_startCol] = var_pieceMoved
                    var_board[var_endRow][var_endCol] = var_pieceCaptured
                    return True
        if var_pieceMoved[1] == 'K':
            if self.validKingMoves(var_board, var_pieceMoved, var_startRow, var_startCol, var_endRow, var_endCol):  
                if var_pieceMoved[0] == 'w' and self.whiteCastleMove_Ks and var_endCol > var_startCol:
                    var_pieceMoved = var_board[var_startRow][var_startCol]
                    var_pieceCaptured = var_board[var_endRow][var_endCol]      
                    var_board[var_startRow][var_startCol] = '--'
                    var_board[var_endRow][var_endCol] = var_pieceMoved
                    var_board[7][7] = '--'
                    var_board[7][5] = 'wR'
                    if self.inCheck(var_board):
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        var_board[7][7] = 'wR'
                        var_board[7][5] = '--'
                        return False
                    else:
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        var_board[7][7] = 'wR'
                        var_board[7][5] = '--'
                        return True
                elif var_pieceMoved[0] == 'w' and self.whiteCastleMove_Qs and var_endCol < var_startCol:
                    var_pieceMoved = var_board[var_startRow][var_startCol]
                    var_pieceCaptured = var_board[var_endRow][var_endCol]      
                    var_board[var_startRow][var_startCol] = '--'
                    var_board[var_endRow][var_endCol] = var_pieceMoved
                    var_board[7][0] = '--'
                    var_board[7][3] = 'wR'
                    if self.inCheck(var_board):
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        var_board[7][0] = 'wR'
                        var_board[7][3] = '--'
                        return False
                    else:
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        var_board[7][0] = 'wR'
                        var_board[7][3] = '--'
                        return True
                elif var_pieceMoved[0] == 'b' and self.blackCastleMove_Ks and var_endCol > var_startCol:
                    var_pieceMoved = var_board[var_startRow][var_startCol]
                    var_pieceCaptured = var_board[var_endRow][var_endCol]      
                    var_board[var_startRow][var_startCol] = '--'
                    var_board[var_endRow][var_endCol] = var_pieceMoved
                    var_board[0][7] = '--'
                    var_board[0][5] = 'bR'
                    if self.inCheck(var_board):
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        var_board[0][7] = 'bR'
                        var_board[0][5] = '--'
                        return False
                    else:
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        var_board[0][7] = 'bR'
                        var_board[0][5] = '--'
                        return True
                elif var_pieceMoved[0] == 'b' and self.blackCastleMove_Qs and var_endCol < var_startCol:
                    var_pieceMoved = var_board[var_startRow][var_startCol]
                    var_pieceCaptured = var_board[var_endRow][var_endCol]      
                    var_board[var_startRow][var_startCol] = '--'
                    var_board[var_endRow][var_endCol] = var_pieceMoved
                    var_board[0][0] = '--'
                    var_board[0][3] = 'bR'
                    if self.inCheck(var_board):
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        var_board[0][0] = 'bR'
                        var_board[0][3] = '--'
                        return False
                    else:
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        var_board[0][0] = 'bR'
                        var_board[0][3] = '--'
                        return True
                else:
                    var_pieceMoved = var_board[var_startRow][var_startCol]
                    var_pieceCaptured = var_board[var_endRow][var_endCol]      
                    var_board[var_startRow][var_startCol] = '--'
                    var_board[var_endRow][var_endCol] = var_pieceMoved
                    if self.inCheck(var_board):
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        return False
                    else:
                        var_board[var_startRow][var_startCol] = var_pieceMoved
                        var_board[var_endRow][var_endCol] = var_pieceCaptured
                        return True


                


                
    
    def validPawnMoves(self, var_board,  var_pieceMoved, var_startRow, var_startCol, var_endRow, var_endCol):
        if var_pieceMoved[0] == 'w' and var_endRow < var_startRow:
            if var_startCol == var_endCol:
                if abs(var_endRow - var_startRow) == 2:
                    if var_startRow == 6 and var_board[var_startRow-1][var_endCol] == '--' and var_board[var_startRow-2][var_endCol] == '--':
                        return True
                elif abs(var_endRow - var_startRow) == 1:
                    if var_board[var_startRow-1][var_endCol] == '--':
                        return True
            elif abs(var_endCol - var_startCol) == 1 and abs(var_startRow - var_endRow) == 1 and var_endRow < var_startRow:
                if var_board[var_endRow][var_endCol][0] == 'b':
                    return True
                elif var_board[var_endRow][var_endCol] == '--':
                    if (var_endRow, var_endCol) in self.blackenpassantMoves:
                        self.enpassantMove = True
                        return True
                    else:
                        return False
                elif var_board[var_endRow][var_endCol][0] == 'w':
                    return False
                return True
        elif var_pieceMoved[0] == 'b' and var_endRow > var_startRow:
            if var_startCol == var_endCol:
                if abs(var_endRow - var_startRow) == 2:
                    if var_startRow == 1 and var_board[var_startRow+1][var_endCol] == '--' and var_board[var_startRow+2][var_endCol] == '--':
                        return True
                elif abs(var_endRow - var_startRow) == 1:
                    if var_board[var_startRow+1][var_endCol] == '--':
                        return True
            elif abs(var_endCol - var_startCol) == 1 and abs(var_startRow - var_endRow) == 1 and var_endRow > var_startRow:
                if var_board[var_endRow][var_endCol][0] == 'w':
                    return True
                elif var_board[var_endRow][var_endCol] == '--':
                    if (var_endRow, var_endCol) in self.whiteenpassantMoves:
                        self.enpassantMove = True
                        return True
                    else:
                        return False
                elif var_board[var_endRow][var_endCol][0] == 'b':
                    return False    
                return True
        else:
            return False
        
        
    def validBishopMoves(self, var_board, var_pieceMoved,  var_startRow, var_startCol, var_endRow, var_endCol):
        if var_pieceMoved[0] == 'w':
            if var_board[var_endRow][var_endCol][0] == 'w':
                return False 
            elif abs(var_startRow - var_endRow) == abs(var_startCol - var_endCol):
                if var_startRow > var_endRow and var_startCol > var_endCol:
                    for i in range(1, abs(var_startRow - var_endRow)):
                        if var_board[var_startRow - i][var_startCol - i] != '--':
                            return False
                            break      
                elif var_startRow > var_endRow and var_startCol < var_endCol:
                    for i in range(1, abs(var_startRow - var_endRow)):
                        if var_board[var_startRow - i][var_startCol + i] != '--':
                            return False
                            break  
                elif var_startRow < var_endRow and var_startCol > var_endCol:
                    for i in range(1, abs(var_startRow - var_endRow)):
                        if var_board[var_startRow + i][var_startCol - i] != '--':
                            return False
                            break 
                elif var_startRow < var_endRow and var_startCol < var_endCol:
                    for i in range(1, abs(var_startRow - var_endRow)):
                        if var_board[var_startRow + i][var_startCol + i] != '--':
                            return False
                            break 
                return True
        elif var_pieceMoved[0] == 'b':
            if var_board[var_endRow][var_endCol][0] == 'b':
                return False 
            elif abs(var_startRow - var_endRow) == abs(var_startCol - var_endCol):
                if var_startRow > var_endRow and var_startCol > var_endCol:
                    for i in range(1, abs(var_startRow - var_endRow)):
                        if var_board[var_startRow - i][var_startCol - i] != '--':
                            return False
                            break      
                elif var_startRow > var_endRow and var_startCol < var_endCol:
                    for i in range(1, abs(var_startRow - var_endRow)):
                        if var_board[var_startRow - i][var_startCol + i] != '--':
                            return False
                            break  
                elif var_startRow < var_endRow and var_startCol > var_endCol:
                    for i in range(1, abs(var_startRow - var_endRow)):
                        if var_board[var_startRow + i][var_startCol - i] != '--':
                            return False
                            break 
                elif var_startRow < var_endRow and var_startCol < var_endCol:
                    for i in range(1, abs(var_startRow - var_endRow)):
                        if var_board[var_startRow + i][var_startCol + i] != '--':
                            return False
                            break 
                return True
    
    def validKnightMoves(self, var_board, var_pieceMoved, var_startRow, var_startCol, var_endRow, var_endCol):
        if var_pieceMoved[0] == 'w':
            if var_board[var_endRow][var_endCol][0] == 'w':
                return False
            else:
                if abs(var_endRow - var_startRow) == 2 and abs(var_endCol - var_startCol) == 1:
                    return True
                elif abs(var_endRow - var_startRow) == 1 and abs(var_endCol - var_startCol) == 2:
                    return True
        if var_pieceMoved[0] == 'b':
            if var_board[var_endRow][var_endCol][0] == 'b':
                return False
            else:
                if abs(var_endRow - var_startRow) == 2 and abs(var_endCol - var_startCol) == 1:
                    return True
                elif abs(var_endRow - var_startRow) == 1 and abs(var_endCol - var_startCol) == 2:
                    return True
                
    def validRookMoves(self, var_board, var_pieceMoved, var_startRow, var_startCol, var_endRow, var_endCol):
        if var_pieceMoved[0] == 'w':
            if var_board[var_endRow][var_endCol][0] == 'w':
                return False
            elif var_endRow != var_startRow and var_endCol != var_startCol:
                return False
            elif var_endRow == var_startRow:
                if var_endCol > var_startCol:
                    for i in range(1, abs(var_endCol - var_startCol)):
                        if var_board[var_startRow][var_startCol + i] != '--':
                            return False
                            break 
                elif var_endCol < var_startCol:
                    for i in range(1, abs(var_endCol - var_startCol)):
                        if var_board[var_startRow][var_startCol - i] != '--':
                            return False
                            break
            elif var_endCol == var_startCol:
                if var_endRow > var_startRow:
                    for i in range(1, abs(var_endRow - var_startRow)):
                        if var_board[var_startRow + i][var_startCol] != '--':
                            return False
                            break 
                elif var_endRow < var_startRow:
                    for i in range(1, abs(var_endRow - var_startRow)):
                        if var_board[var_startRow - i][var_startCol] != '--':
                            return False
                            break
            return True
        elif var_pieceMoved[0] == 'b':
            if var_board[var_endRow][var_endCol][0] == 'b':
                return False
            elif var_endRow != var_startRow and var_endCol != var_startCol:
                return False
            elif var_endRow == var_startRow:
                if var_endCol > var_startCol:
                    for i in range(1, abs(var_endCol - var_startCol)):
                        if var_board[var_startRow][var_startCol + i] != '--':
                            return False
                            break 
                elif var_endCol < var_startCol:
                    for i in range(1, abs(var_endCol - var_startCol)):
                        if var_board[var_startRow][var_startCol - i] != '--':
                            return False
                            break
            elif var_endCol == var_startCol:
                if var_endRow > var_startRow:
                    for i in range(1, abs(var_endRow - var_startRow)):
                        if var_board[var_startRow + i][var_startCol] != '--':
                            return False
                            break 
                elif var_endRow < var_startRow:
                    for i in range(1, abs(var_endRow - var_startRow)):
                        if var_board[var_startRow - i][var_startCol] != '--':
                            return False
                            break
            return True
            

    def validQueenMoves(self, var_board,  var_pieceMoved, var_startRow, var_startCol, var_endRow, var_endCol):
        if self.validBishopMoves(var_board, var_pieceMoved, var_startRow, var_startCol, var_endRow, var_endCol) or self.validRookMoves(var_board, var_pieceMoved, var_startRow, var_startCol, var_endRow, var_endCol):
            return True
        
    def validKingMoves(self, var_board, var_pieceMoved, var_startRow, var_startCol, var_endRow, var_endCol):
        if var_pieceMoved[0] == 'w':
            if var_board[var_endRow][var_endCol][0] == 'w':
                return False
            elif var_endRow == var_startRow:
                if abs(var_endCol - var_startCol) == 1:
                    self.castleRights['wKs'] = False
                    self.castleRights['wQs'] = False
                    return True
                elif abs(var_endCol - var_startCol) == 2 and var_endRow == 7:
                    if var_endCol > var_startCol and var_board[var_startRow][var_endCol] == '--' and var_board[var_startRow][var_endCol-1] == '--' and self.castleRights['wKs'] and not self.prev_whiteInCheck:
                        self.whiteCastleMove_Ks = True
                        return True
                    elif var_endCol < var_startCol and var_board[var_startRow][var_endCol] == '--' and var_board[var_startRow][var_endCol+1] == '--' and var_board[var_startRow][var_endCol-1] == '--' and self.castleRights['wQs'] and not self.prev_whiteInCheck:
                        self.whiteCastleMove_Qs = True
                        return True
                    else:
                        return False            
            elif var_endCol == var_startCol and abs(var_endRow - var_startRow) == 1:
                self.castleRights['wKs'] = False
                self.castleRights['wQs'] = False
                return True
            elif abs(var_endCol - var_startCol) == 1 and abs(var_endRow - var_startRow) == 1:
                self.castleRights['wKs'] = False
                self.castleRights['wQs'] = False
                return True        
        elif var_pieceMoved[0] == 'b':
            if var_board[var_endRow][var_endCol][0] == 'b':
                return False
            elif var_endRow == var_startRow:
                if abs(var_endCol - var_startCol) == 1:
                    self.castleRights['bKs'] = False
                    self.castleRights['bQs'] = False
                    return True
                elif abs(var_endCol - var_startCol) == 2 and var_endRow == 0:
                    if var_endCol > var_startCol and var_board[var_startRow][var_endCol] == '--' and var_board[var_startRow][var_endCol-1] == '--' and self.castleRights['bKs'] and not self.prev_blackInCheck:
                        self.blackCastleMove_Ks = True
                        return True
                    elif var_endCol < var_startCol and var_board[var_startRow][var_endCol] == '--' and var_board[var_startRow][var_endCol+1] == '--' and var_board[var_startRow][var_endCol-1] == '--' and self.castleRights['bQs'] and not self.prev_blackInCheck:
                        self.blackCastleMove_Qs = True
                        return True 
                    else:
                        return False
            elif var_endCol == var_startCol and abs(var_endRow - var_startRow) == 1:
                self.castleRights['bKs'] = False
                self.castleRights['bQs'] = False
                return True
            elif abs(var_endCol - var_startCol) == 1 and abs(var_endRow - var_startRow) == 1:
                self.castleRights['bKs'] = False
                self.castleRights['bQs'] = False
                return True
            
            
    def getPositionSets(self, var_board):
        position_dict = {}
        self.b_pawnPositionSet = []
        self.w_pawnPositionSet = []
        self.b_bishopPositionSet = []
        self.w_bishopPositionSet = []
        self.b_knightPositionSet = []
        self.w_knightPositionSet = []
        self.b_rookPositionSet = []
        self.w_rookPositionSet = []
        self.b_queenPositionSet = []
        self.w_queenPositionSet = []
        self.b_kingPositionSet = []
        self.w_kingPositionSet = []
        for i in range(0,8):
            for j in range(0,8):
                if var_board[i][j] == 'bP':
                    position = (i, j)
                    self.b_pawnPositionSet.append(position)
                elif var_board[i][j] == 'wP':
                    position = (i, j)
                    self.w_pawnPositionSet.append(position)
                elif var_board[i][j] == 'bB':
                    position = (i, j)
                    self.b_bishopPositionSet.append(position) 
                elif var_board[i][j] == 'wB':
                    position = (i, j)
                    self.w_bishopPositionSet.append(position) 
                elif var_board[i][j] == 'bN':
                    position = (i, j)
                    self.b_knightPositionSet.append(position) 
                elif var_board[i][j] == 'wN':
                    position = (i, j)
                    self.w_knightPositionSet.append(position) 
                elif var_board[i][j] == 'bR':
                    position = (i, j)
                    self.b_rookPositionSet.append(position) 
                elif var_board[i][j] == 'wR':
                    position = (i, j)
                    self.w_rookPositionSet.append(position)  
                elif var_board[i][j] == 'bQ':
                    position = (i, j)
                    self.b_queenPositionSet.append(position)
                elif var_board[i][j] == 'wQ':
                    position = (i, j)
                    self.w_queenPositionSet.append(position)
                elif var_board[i][j] == 'bK':
                    position = (i, j)
                    self.b_kingPositionSet.append(position) 
                elif var_board[i][j] == 'wK':
                    position = (i, j)
                    self.w_kingPositionSet.append(position) 
        position_dict = {
            'bP': self.b_pawnPositionSet,
            'wP': self.w_pawnPositionSet,
            'bB': self.b_bishopPositionSet,
            'wB': self.w_bishopPositionSet,
            'bN': self.b_knightPositionSet,
            'wN': self.w_knightPositionSet,
            'bR': self.b_rookPositionSet,
            'wR': self.w_rookPositionSet,
            'bQ': self.b_queenPositionSet,
            'wQ': self.w_queenPositionSet,
            'bK': self.b_kingPositionSet,
            'wK': self.w_kingPositionSet
        }
        return position_dict

            
    def inCheck(self, var_board):
        self.getPositionSets(var_board)
        w_kingRow =  self.w_kingPositionSet[0][0]   
        w_kingCol =  self.w_kingPositionSet[0][1]
        b_kingRow =  self.b_kingPositionSet[0][0]
        b_kingCol =  self.b_kingPositionSet[0][1]

        self.whiteInCheck = False
        self.blackInCheck = False
        
        if self.whiteToMove:
            for coord in self.b_pawnPositionSet:
                if self.validPawnMoves(var_board, 'b', coord[0], coord[1], w_kingRow, w_kingCol):
                    self.whiteInCheck = True
                    return True
            for coord in self.b_bishopPositionSet:
                if self.validBishopMoves(var_board, 'b', coord[0], coord[1], w_kingRow, w_kingCol):
                    self.whiteInCheck = True
                    return True
            for coord in self.b_knightPositionSet:
                if self.validKnightMoves(var_board, 'b', coord[0], coord[1], w_kingRow, w_kingCol):
                    self.whiteInCheck = True
                    return True
            for coord in self.b_rookPositionSet:
                if self.validRookMoves(var_board, 'b', coord[0], coord[1], w_kingRow, w_kingCol):
                    self.whiteInCheck = True
                    return True
            for coord in self.b_queenPositionSet:
                if self.validQueenMoves(var_board, 'b', coord[0], coord[1], w_kingRow, w_kingCol):
                    self.whiteInCheck = True
                    return True
            for coord in self.b_kingPositionSet:
                if self.validKingMoves(var_board, 'b', coord[0], coord[1], w_kingRow, w_kingCol):
                    self.whiteInCheck = True
                    return True
        elif not self.whiteToMove:
            for coord in self.w_pawnPositionSet:
                if self.validPawnMoves(var_board, 'w', coord[0], coord[1], b_kingRow, b_kingCol):
                    self.blackInCheck = True
                    return True
            for coord in self.w_bishopPositionSet:
                if self.validBishopMoves(var_board, 'w', coord[0], coord[1], b_kingRow, b_kingCol):
                    self.blackInCheck = True
                    return True
            for coord in self.w_knightPositionSet:
                if self.validKnightMoves(var_board, 'w', coord[0], coord[1], b_kingRow, b_kingCol):
                    self.blackInCheck = True
                    return True
            for coord in self.w_rookPositionSet:
                if self.validRookMoves(var_board, 'w', coord[0], coord[1], b_kingRow, b_kingCol):
                    self.blackInCheck = True
                    return True
            for coord in self.w_queenPositionSet:
                if self.validQueenMoves(var_board, 'w', coord[0], coord[1], b_kingRow, b_kingCol):
                    self.blackInCheck = True
                    return True
            for coord in self.w_kingPositionSet:
                if self.validKingMoves(var_board, 'w', coord[0], coord[1], b_kingRow, b_kingCol):
                    self.blackInCheck = True
                    return True
        return False
    
    def lenValidMoves(self, var_board):        
        validMovesList = []
        self.getPositionSets(var_board)
        if self.whiteInCheck:
            for coord in self.w_pawnPositionSet:
                for i in range(0, 8):
                    for j in range(0, 8):  
                        #print('Checking pawn from:', coord, 'to:', (i, j))                   
                        if self.validMove(var_board, 'wP', coord[0], coord[1], i, j):
                            validMovesList.append(['P', (coord, (i, j))])
            for coord in self.w_bishopPositionSet:
                for i in range(0, 8):
                    for j in range(0, 8):
                        #print('Checking bishop from:', coord, 'to:', (i, j))                   
                        self.pieceCaptured = var_board[i][j]
                        if self.validMove(var_board, 'wB', coord[0], coord[1], i, j):
                            validMovesList.append(['B', (coord, (i, j))])
            for coord in self.w_knightPositionSet:
                for i in range(0, 8):
                    for j in range(0, 8):
                        #print('Checking knight from:', coord, 'to:', (i, j))                   
                        self.pieceCaptured = var_board[i][j]
                        if self.validMove(var_board, 'wN', coord[0], coord[1], i, j):
                            validMovesList.append(['N', (coord, (i, j))])
            for coord in self.w_rookPositionSet:
                for i in range(0, 8):
                    for j in range(0, 8):
                        #print('Checking rook from:', coord, 'to:', (i, j))
                        self.pieceCaptured = var_board[i][j]
                        if self.validMove(var_board, 'wR', coord[0], coord[1], i, j):
                            validMovesList.append(['R', (coord, (i, j))])
            for coord in self.w_queenPositionSet:
                for i in range(0, 8):
                    for j in range(0, 8):
                        #print('Checking queen from:', coord, 'to:', (i, j))
                        self.pieceCaptured = var_board[i][j]
                        if self.validMove(var_board, 'wQ', coord[0], coord[1], i, j):
                            validMovesList.append(['Q', (coord, (i, j))])
            for coord in self.w_kingPositionSet:
                for i in range(0, 8):
                    for j in range(0, 8):
                        #print('Checking king from:', coord, 'to:', (i, j))
                        self.pieceCaptured = var_board[i][j]
                        if self.validMove(var_board, 'wK', coord[0], coord[1], i, j):
                            validMovesList.append(['K', (coord, (i, j))])
        elif self.blackInCheck:
            for coord in self.b_pawnPositionSet:
                for i in range(0, 8):
                    for j in range(0, 8):
                        #print('Checking pawn from:', coord, 'to:', (i, j))
                        self.pieceCaptured = var_board[i][j]
                        if self.validMove(var_board, 'bP', coord[0], coord[1], i, j):
                            validMovesList.append(['P', (coord, (i, j))])
            for coord in self.b_bishopPositionSet:
                for i in range(0, 8):
                    for j in range(0, 8):
                        #print('Checking bishop from:', coord, 'to:', (i, j))
                        self.pieceCaptured = var_board[i][j]
                        if self.validMove(var_board, 'bB', coord[0], coord[1], i, j):
                            validMovesList.append(['B', (coord, (i, j))])
            for coord in self.b_knightPositionSet:
                for i in range(0, 8):
                    for j in range(0, 8):
                        #print('Checking knight from:', coord, 'to:', (i, j))
                        self.pieceCaptured = var_board[i][j]
                        if self.validMove(var_board, 'bN', coord[0], coord[1], i, j):
                            validMovesList.append(['N', (coord, (i, j))])
            for coord in self.b_rookPositionSet:
                for i in range(0, 8):
                    for j in range(0, 8):
                        #print('Checking rook from:', coord, 'to:', (i, j))
                        self.pieceCaptured = var_board[i][j]
                        if self.validMove(var_board, 'bR', coord[0], coord[1], i, j):
                            validMovesList.append(['R', (coord, (i, j))])
            for coord in self.b_queenPositionSet:
                for i in range(0, 8):
                    for j in range(0, 8):
                        #print('Checking queen from:', coord, 'to:', (i, j))
                        self.pieceCaptured = var_board[i][j]
                        if self.validMove(var_board, 'bQ', coord[0], coord[1], i, j):
                            validMovesList.append(['Q', (coord, (i, j))])
            for coord in self.b_kingPositionSet:
                for i in range(0, 8):
                    for j in range(0, 8):
                        #print('Checking king from:', coord, 'to:', (i, j))
                        self.pieceCaptured = var_board[i][j]
                        if self.validMove(var_board, 'bK', coord[0], coord[1], i, j):
                            validMovesList.append(['K', (coord, (i, j))])
        else:
            if self.whiteToMove:
                for coord in self.w_pawnPositionSet:
                    for i in range(0, 8):
                        for j in range(0, 8):   
                            #print('Checking pawn from:', coord, 'to:', (i, j))
                            self.pieceCaptured = var_board[i][j]                  
                            if self.validMove(var_board, 'wP', coord[0], coord[1], i, j):
                                validMovesList.append(['P', (coord, (i, j))])
                for coord in self.w_bishopPositionSet:
                    for i in range(0, 8):
                        for j in range(0, 8):
                            #print('Checking bishop from:', coord, 'to:', (i, j))
                            self.pieceCaptured = var_board[i][j]
                            if self.validMove(var_board, 'wB', coord[0], coord[1], i, j):
                                validMovesList.append(['B', (coord, (i, j))])
                for coord in self.w_knightPositionSet:
                    for i in range(0, 8):
                        for j in range(0, 8):
                            #print('Checking knight from:', coord, 'to:', (i, j))
                            self.pieceCaptured = var_board[i][j]
                            if self.validMove(var_board, 'wN', coord[0], coord[1], i, j):
                                validMovesList.append(['N', (coord, (i, j))])
                for coord in self.w_rookPositionSet:
                    for i in range(0, 8):
                        for j in range(0, 8):
                            #print('Checking rook from:', coord, 'to:', (i, j))
                            self.pieceCaptured = var_board[i][j]
                            if self.validMove(var_board, 'wR', coord[0], coord[1], i, j):
                                validMovesList.append(['R', (coord, (i, j))])
                for coord in self.w_queenPositionSet:
                    for i in range(0, 8):
                        for j in range(0, 8):
                            #print('Checking queen from:', coord, 'to:', (i, j))
                            self.pieceCaptured = var_board[i][j]
                            if self.validMove(var_board, 'wQ', coord[0], coord[1], i, j):
                                validMovesList.append(['Q', (coord, (i, j))])
                for coord in self.w_kingPositionSet:
                    for i in range(0, 8):
                        for j in range(0, 8):
                            #print('Checking king from:', coord, 'to:', (i, j))
                            self.pieceCaptured = var_board[i][j]
                            if self.validMove(var_board, 'wK', coord[0], coord[1], i, j):
                                validMovesList.append(['K', (coord, (i, j))])
            elif not self.whiteToMove:
                for coord in self.b_pawnPositionSet:
                    for i in range(0, 8):
                        for j in range(0, 8):
                            #print('Checking pawn from:', coord, 'to:', (i, j))
                            self.pieceCaptured = var_board[i][j]
                            if self.validMove(var_board, 'bP', coord[0], coord[1], i, j):
                                validMovesList.append(['P', (coord, (i, j))])
                for coord in self.b_bishopPositionSet:
                    for i in range(0, 8):
                        for j in range(0, 8):
                            #print('Checking bishop from:', coord, 'to:', (i, j))
                            self.pieceCaptured = var_board[i][j]
                            if self.validMove(var_board, 'bB', coord[0], coord[1], i, j):
                                validMovesList.append(['B', (coord, (i, j))])
                for coord in self.b_knightPositionSet:
                    for i in range(0, 8):
                        for j in range(0, 8):
                            #print('Checking knight from:', coord, 'to:', (i, j))
                            self.pieceCaptured = var_board[i][j]
                            if self.validMove(var_board, 'bN', coord[0], coord[1], i, j):
                                validMovesList.append(['N', (coord, (i, j))])
                for coord in self.b_rookPositionSet:
                    for i in range(0, 8):
                        for j in range(0, 8):
                            #print('Checking rook from:', coord, 'to:', (i, j))
                            self.pieceCaptured = var_board[i][j]
                            if self.validMove(var_board, 'bR', coord[0], coord[1], i, j):
                                validMovesList.append(['R', (coord, (i, j))])
                for coord in self.b_queenPositionSet:
                    for i in range(0, 8):
                        for j in range(0, 8):
                            #print('Checking queen from:', coord, 'to:', (i, j))
                            self.pieceCaptured = var_board[i][j]
                            if self.validMove(var_board, 'bQ', coord[0], coord[1], i, j):
                                validMovesList.append(['Q', (coord, (i, j))])
                for coord in self.b_kingPositionSet:
                    for i in range(0, 8):
                        for j in range(0, 8):
                            #print('Checking king from:', coord, 'to:', (i, j))
                            self.pieceCaptured = var_board[i][j]
                            if self.validMove(var_board, 'bK', coord[0], coord[1], i, j):
                                validMovesList.append(['K', (coord, (i, j))])
        return validMovesList
    
    def calculateEnpassantMoves(self, var_board,  var_pieceMoved, var_startRow, var_startCol, var_endRow, var_endCol):
        if var_pieceMoved[1] == 'P' and abs(var_startRow - var_endRow) == 2:
            if var_endCol != 0 and var_endCol != 7:
                if var_pieceMoved[0] == 'w' and (var_board[var_endRow][var_endCol - 1] == 'bP' or var_board[var_endRow][var_endCol + 1] == 'bP'):
                    self.enpassantPossible = ((var_endRow + 1), var_endCol)
                    self.whiteenpassantMoves.append(self.enpassantPossible)
                elif var_pieceMoved[0] == 'b' and (var_board[var_endRow][var_endCol - 1] == 'wP' or var_board[var_endRow][var_endCol + 1] == 'wP'):
                    self.enpassantPossible = ((var_endRow - 1), var_endCol) 
                    self.blackenpassantMoves.append(self.enpassantPossible)
            elif var_endCol == 0:
                if var_pieceMoved[0] == 'w' and var_board[var_endRow][var_endCol + 1] == 'bP':
                    self.enpassantPossible = ((var_endRow + 1), var_endCol)
                    self.whiteenpassantMoves.append(self.enpassantPossible)
                elif var_pieceMoved[0] == 'b' and var_board[var_endRow][var_endCol + 1] == 'wP':
                    self.enpassantPossible = ((var_endRow - 1), var_endCol) 
                    self.blackenpassantMoves.append(self.enpassantPossible)
            elif var_endCol == 7:
                if var_pieceMoved[0] == 'w' and var_board[var_endRow][var_endCol - 1] == 'bP':
                    self.enpassantPossible = ((var_endRow + 1), var_endCol)
                    self.whiteenpassantMoves.append(self.enpassantPossible)
                elif var_pieceMoved[0] == 'b' and var_board[var_endRow][var_endCol - 1] == 'wP':
                    self.enpassantPossible = ((var_endRow - 1), var_endCol) 
                    self.blackenpassantMoves.append(self.enpassantPossible)
        for coord in self.whiteenpassantMoves:
            if var_board[coord[0] - 1][coord[1]] != 'wP':
                self.whiteenpassantMoves.remove(coord)
        for coord in self.blackenpassantMoves:
            if var_board[coord[0] + 1][coord[1]] != 'bP':
                self.blackenpassantMoves.remove(coord)
        return self.whiteenpassantMoves, self.blackenpassantMoves
    
    def generateFen(self, var_board):
        fen = ''
        for row in var_board:
            emptyCount = 0
            for square in row:
                if square == '--':
                    emptyCount += 1
                else:
                    if emptyCount > 0:
                        fen += str(emptyCount)
                        emptyCount = 0
                    fen += square[1] if square[0] == 'w' else square[1].lower()
            if emptyCount > 0:
                fen += str(emptyCount)
            fen += '/'
        fen = fen[:-1]  # Remove the trailing '/'
        fen += ' ' + ('w' if self.whiteToMove else 'b') + ' '
        castlingRights = ''
        if self.castleRights['wKs']:
            castlingRights += 'K'
        if self.castleRights['wQs']:
            castlingRights += 'Q'
        if self.castleRights['bKs']:
            castlingRights += 'k'
        if self.castleRights['bQs']:
            castlingRights += 'q'
        fen += castlingRights if castlingRights else '-'
        fen += ' '

        if len(self.whiteenpassantMoves) > 0:
            fen += chr(self.whiteenpassantMoves[-1][1] + ord('a')) + str(8 - self.whiteenpassantMoves[-1][0])
        elif len(self.blackenpassantMoves) > 0:
            fen += chr(self.blackenpassantMoves[-1][1] + ord('a')) + str(8 - self.blackenpassantMoves[-1][0])
        else:
            fen += '-'
        fen += ' 0 1'  # Placeholder for halfmove clock and fullmove number
        return fen
                    
                    

        

                    

                
                 

    

    
            
    




           
            



        




