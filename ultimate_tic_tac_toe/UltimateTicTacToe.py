import numpy as np

class UltimateTicTacToe:
    def __init__(self):
        # Main board is 3x3 array of small boards
        # Each small board is 3x3 array with 0 (empty), 1 (X), 2 (O)
        self.main_board = np.zeros((3, 3, 3, 3), dtype=int)
        self.current_player = 1  # X starts first
        self.game_over = False
        self.winner = None
        # In this version, any board can be played next
        self.allowed_boards = [(i, j) for i in range(3) for j in range(3)]
        
    def print_board(self):
        symbols = {0: '.', 1: 'X', 2: 'O'}
        
        for big_row in range(3):
            for small_row in range(3):
                line = ""
                for big_col in range(3):
                    for small_col in range(3):
                        val = self.main_board[big_row][big_col][small_row][small_col]
                        line += symbols[val] + " "
                    line += "  "  # Space between small boards
                print(line)
            print()  # Space between big rows
    
    def make_move(self, board_pos, cell_pos):
        """Make a move on the specified board and cell"""
        if self.game_over:
            return False
            
        big_row, big_col = board_pos
        small_row, small_col = cell_pos
        
        # Check if move is valid
        if (big_row, big_col) not in self.allowed_boards:
            return False
        if self.main_board[big_row][big_col][small_row][small_col] != 0:
            return False
            
        # Make the move
        self.main_board[big_row][big_col][small_row][small_col] = self.current_player
        
        # Check if the small board is won
        if self.check_small_board_win(big_row, big_col):
            # Mark the entire small board as won
            for i in range(3):
                for j in range(3):
                    self.main_board[big_row][big_col][i][j] = self.current_player
        
        # Check if the game is won
        if self.check_main_board_win():
            self.game_over = True
            self.winner = self.current_player
            return True
            
        # Check for a draw
        if self.is_draw():
            self.game_over = True
            return True
            
        # Switch player
        self.current_player = 3 - self.current_player  # Switch between 1 and 2
        return True
    
    def check_small_board_win(self, big_row, big_col):
        """Check if the current player has won the specified small board"""
        board = self.main_board[big_row][big_col]
        
        # Check rows
        for row in range(3):
            if all(board[row][col] == self.current_player for col in range(3)):
                return True
                
        # Check columns
        for col in range(3):
            if all(board[row][col] == self.current_player for row in range(3)):
                return True
                
        # Check diagonals
        if board[0][0] == board[1][1] == board[2][2] == self.current_player:
            return True
        if board[0][2] == board[1][1] == board[2][0] == self.current_player:
            return True
            
        return False
    
    def check_main_board_win(self):
        """Check if the current player has won the main board"""
        # Create a simplified view of the main board (which small boards are won)
        simplified_board = np.zeros((3, 3), dtype=int)
        for i in range(3):
            for j in range(3):
                # Check if the small board is completely filled with the same player
                first_val = self.main_board[i][j][0][0]
                if first_val == 0:
                    continue
                board_won = True
                for x in range(3):
                    for y in range(3):
                        if self.main_board[i][j][x][y] != first_val:
                            board_won = False
                            break
                    if not board_won:
                        break
                if board_won:
                    simplified_board[i][j] = first_val
        
        # Now check for wins on the simplified board
        # Check rows
        for row in range(3):
            if all(simplified_board[row][col] == self.current_player for col in range(3)):
                return True
                
        # Check columns
        for col in range(3):
            if all(simplified_board[row][col] == self.current_player for row in range(3)):
                return True
                
        # Check diagonals
        if simplified_board[0][0] == simplified_board[1][1] == simplified_board[2][2] == self.current_player:
            return True
        if simplified_board[0][2] == simplified_board[1][1] == simplified_board[2][0] == self.current_player:
            return True
            
        return False
    
    def is_draw(self):
        """Check if the game is a draw (all small boards are full)"""
        for i in range(3):
            for j in range(3):
                for x in range(3):
                    for y in range(3):
                        if self.main_board[i][j][x][y] == 0:
                            return False
        return True
    
    def get_available_moves(self):
        """Get all available moves (board_pos, cell_pos)"""
        moves = []
        for big_row, big_col in self.allowed_boards:
            for small_row in range(3):
                for small_col in range(3):
                    if self.main_board[big_row][big_col][small_row][small_col] == 0:
                        moves.append(((big_row, big_col), (small_row, small_col)))
        return moves