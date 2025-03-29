import random
import numpy as np

class RandomAgent:
    def __init__(self, player):
        self.player = player
    
    def get_move(self, game):
        available_moves = game.get_available_moves()
        return random.choice(available_moves) if available_moves else None

class SimpleStrategyAgent:
    def __init__(self, player):
        self.player = player
    
    def get_move(self, game):
        available_moves = game.get_available_moves()
        if not available_moves:
            return None
            
        # First, look for moves that win a small board
        for move in available_moves:
            board_pos, cell_pos = move
            if self.check_small_board_win_if_move(game, board_pos, cell_pos):
                return move
        
        # Then, look for moves that prevent opponent from winning a small board
        opponent = 3 - self.player
        for move in available_moves:
            board_pos, cell_pos = move
            if self.check_opponent_win_if_move(game, board_pos, cell_pos, opponent):
                return move
                
        # Then, prioritize center squares in small boards
        center_moves = [move for move in available_moves if move[1] == (1, 1)]
        if center_moves:
            return random.choice(center_moves)
            
        # Then, prioritize center small boards
        center_boards = [move for move in available_moves if move[0] == (1, 1)]
        if center_boards:
            return random.choice(center_boards)
            
        # Otherwise, choose randomly
        return random.choice(available_moves)
    
    def check_small_board_win_if_move(self, game, board_pos, cell_pos):
        """Check if making this move would win the small board"""
        big_row, big_col = board_pos
        small_row, small_col = cell_pos
        
        # Create a temporary copy of the board
        temp_board = np.copy(game.main_board)
        temp_board[big_row][big_col][small_row][small_col] = self.player
        
        # Check if this move wins the small board
        # Check rows
        for row in range(3):
            if all(temp_board[big_row][big_col][row][col] == self.player for col in range(3)):
                return True
                
        # Check columns
        for col in range(3):
            if all(temp_board[big_row][big_col][row][col] == self.player for row in range(3)):
                return True
                
        # Check diagonals
        if temp_board[big_row][big_col][0][0] == temp_board[big_row][big_col][1][1] == temp_board[big_row][big_col][2][2] == self.player:
            return True
        if temp_board[big_row][big_col][0][2] == temp_board[big_row][big_col][1][1] == temp_board[big_row][big_col][2][0] == self.player:
            return True
            
        return False
    
    def check_opponent_win_if_move(self, game, board_pos, cell_pos, opponent):
        """Check if opponent would win this small board if we don't block"""
        big_row, big_col = board_pos
        small_row, small_col = cell_pos
        
        # Create a temporary copy of the board
        temp_board = np.copy(game.main_board)
        temp_board[big_row][big_col][small_row][small_col] = opponent
        
        # Check if opponent would win
        # Check rows
        for row in range(3):
            if all(temp_board[big_row][big_col][row][col] == opponent for col in range(3)):
                return True
                
        # Check columns
        for col in range(3):
            if all(temp_board[big_row][big_col][row][col] == opponent for row in range(3)):
                return True
                
        # Check diagonals
        if temp_board[big_row][big_col][0][0] == temp_board[big_row][big_col][1][1] == temp_board[big_row][big_col][2][2] == opponent:
            return True
        if temp_board[big_row][big_col][0][2] == temp_board[big_row][big_col][1][1] == temp_board[big_row][big_col][2][0] == opponent:
            return True
            
        return False