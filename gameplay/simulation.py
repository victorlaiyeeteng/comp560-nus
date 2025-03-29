from ultimate_tic_tac_toe import UltimateTicTacToe, RandomAgent, SimpleStrategyAgent

def simulate_game(agent1, agent2, print_game=False):
    game = UltimateTicTacToe()
    agents = {1: agent1, 2: agent2}
    
    if print_game:
        print("Initial board:")
        game.print_board()
    
    while not game.game_over:
        current_agent = agents[game.current_player]
        move = current_agent.get_move(game)
        
        if not move:
            break  # No moves left
            
        board_pos, cell_pos = move
        if print_game:
            player_symbol = 'X' if game.current_player == 1 else 'O'
            print(f"Player {player_symbol} plays at board {board_pos}, cell {cell_pos}")
        
        game.make_move(board_pos, cell_pos)
        
        if print_game:
            game.print_board()
    
    if print_game:
        if game.winner:
            winner_symbol = 'X' if game.winner == 1 else 'O'
            print(f"Player {winner_symbol} wins!")
        else:
            print("The game is a draw!")
    
    return game.winner

if __name__ == "__main__":
    # Run a single game with printing
    print("Starting a single game with printing...")
    agent1 = SimpleStrategyAgent(1)  # X
    agent2 = RandomAgent(2)          # O
    simulate_game(agent1, agent2, print_game=True)

    # Run multiple games to see statistics
    print("\nRunning 100 games to see statistics...")
    results = {1: 0, 2: 0, None: 0}
    for _ in range(100):
        winner = simulate_game(agent1, agent2, print_game=False)
        results[winner] += 1

    print(f"Results after 100 games:")
    print(f"SimpleStrategyAgent (X) wins: {results[1]}")
    print(f"RandomAgent (O) wins: {results[2]}")
    print(f"Draws: {results[None]}")