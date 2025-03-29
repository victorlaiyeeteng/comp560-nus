# COMP560 Project Abstract

### Project Group
1. Lai Yee Teng, Victor (730841980)
2. Cao Duy Nguyen (730842001)
3. Cheng Zhi Sheng (730842247)
4. Xiaoxiao Ma (730841676)


### Problem Statement
https://www.codingame.com/multiplayer/bot-programming/tic-tac-toe

Our problem will be based on this game, 'Ultimate Tic Tac Toe'. The game consists of 3x3 grid of standard Tic-Tac-Toe boards. The game starts on any small board. In each move, a player can play in any board. A board is won when a player wins three in a row, column or diagonal in a local 3x3 board. The game is won by securing three local boards in a row, column or diagonal. We aim to build a bot to play this game as optimal as possible against an agent (random moves / optimal moves).

### Implementation Plan
- Represent the 9x9 tic-tac-toe game state.
- Set up a “random” agent that chooses moves randomly.
- Set up an evaluation function for the board state:
    - Weighted scoring system based on possible criteria:
        - Winning a local board.
        - Threatening a win in a local board.
        - Securing a global board win.
        - Preventing the opponent’s win in a local board.
        - Number of occupied spaces.
- Implement a depth-limited minimax algorithm using the evaluation function:
    - Check for terminal states.
    - Evaluate heuristic if the depth limit is reached.
    - Recursively simulate all legal moves and maximize/minimize scores.
    - Use alpha-beta pruning to cut off unneeded branches.
- Play the minimax agent against a random agent.
- Play the minimax agent against another minimax agent.

