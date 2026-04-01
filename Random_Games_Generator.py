import time
import importlib.util
import subprocess
import sys

def ensure_installed(package_name):
    if importlib.util.find_spec(package_name) is None:
        print(f"'{package_name}' not found — installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"'{package_name}' installed successfully.")

ensure_installed("pandas")
ensure_installed("stockfish")
ensure_installed("pygame")
ensure_installed("requests")

import pandas as pd

import pygame as p
from requests import head
import ChessEngine as ce
import random
from stockfish import Stockfish
import random




WIDTH = 800
HEIGHT = 800
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15

# pygame setup
p.init()
screen = p.display.set_mode((WIDTH, HEIGHT))
clock = p.time.Clock()
running = True
gs = ce.gameState()
IMAGES = {}
moveSet = []
auto_play = False  # Autoplay starts after first click
move_delay = 0
MOVE_INTERVAL = 50  # milliseconds between auto moves (1 second)
game_number = 1
move_number = 0
game_end_timer = 0
GAME_END_DELAY = 2000  # 2 seconds delay before restarting after game ends


df = pd.DataFrame(columns=['Game_No', 'FEN', 'Eval_cp', 'Eval_mate', 'stat_win', 'stat_draw', 'stat_loss', 'white_won', 
                           'black_won', 'stalemate', 'move_no'])




def load_images():
    pieces = ['wP', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bP', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load(f"Chess/Images/{piece}.png"), (SQ_SIZE, SQ_SIZE))

def makeSquares():
    for r in range(0, WIDTH, 10):
        for c in range(0, HEIGHT, 100):
            val = (((r+c)//100 ) % 2)
            if val == 0:
                color = p.Color('White')
            else:
                color = p.Color('Gray')
            p.draw.rect(screen, color, p.Rect(r, c, 100, 100))
        
def drawPieces():
    for r in range(0, WIDTH//100):
        for c in range(0, HEIGHT//100):
            if gs.board[r][c] != '--':
                piece = gs.board[r][c]
                screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))

def eval_stockfish(var_fen, var_level, var_elo):

    stockfish = Stockfish(path="C:/Users/anchi/GitHub/Repos/Chess_Game/stockfish/stockfish-windows-x86-64-avx2.exe")

    {
        "Debug Log File": "",
        "Contempt": 0,
        "Min Split Depth": 0,
        "Threads": 1, # More threads will make the engine stronger, but should be kept at less than the number of logical processors on your computer.
        "Ponder": "false",
        "Hash": 16, # Default size is 16 MB. It's recommended that you increase this value, but keep it as some power of 2. E.g., if you're fine using 2 GB of RAM, set Hash to 2048 (11th power of 2).
        "MultiPV": 1,
        "Skill Level": var_level,
        "Move Overhead": 10,
        "Minimum Thinking Time": 20,
        "Slow Mover": 100,
        "UCI_Chess960": "false",
        "UCI_LimitStrength": "false",
        "UCI_Elo": var_elo
    }

    stockfish.set_fen_position(var_fen)
    evaluation = stockfish.get_evaluation()
    wdl_stats = stockfish.get_wdl_stats()

    return evaluation, wdl_stats



def move_stockfish(var_fen, var_level, var_elo):

    stockfish = Stockfish(path="C:/Users/anchi/GitHub/Repos/Chess_Game/stockfish/stockfish-windows-x86-64-avx2.exe")

    {
        "Debug Log File": "",
        "Contempt": 0,
        "Min Split Depth": 0,
        "Threads": 1, # More threads will make the engine stronger, but should be kept at less than the number of logical processors on your computer.
        "Ponder": "false",
        "Hash": 16, # Default size is 16 MB. It's recommended that you increase this value, but keep it as some power of 2. E.g., if you're fine using 2 GB of RAM, set Hash to 2048 (11th power of 2).
        "MultiPV": 1,
        "Skill Level": var_level,
        "Move Overhead": 10,
        "Minimum Thinking Time": 20,
        "Slow Mover": 100,
        "UCI_Chess960": "false",
        "UCI_LimitStrength": "false",
        "UCI_Elo": var_elo
    }

    stockfish.set_fen_position(var_fen)
    best_move = stockfish.get_best_move()
    print("Best move:", best_move)


    column_convert = {
        'a': 0, 'b': 1, 'c': 2, 'd': 3,
        'e': 4, 'f': 5, 'g': 6, 'h': 7
    }
    row_convert = {'8': 0, '7': 1, '6': 2, '5': 3, '4': 4, '3': 5, '2': 6, '1': 7}

    moveSet = []

    startRow = row_convert[best_move[1]]
    startCol = column_convert[best_move[0]]
    startSq = (startRow, startCol)
    moveSet.append(startSq)
    endRow = row_convert[best_move[3]]
    endCol = column_convert[best_move[2]]
    endSq = (endRow, endCol)
    moveSet.append(endSq)
    return moveSet

            

load_images()  # Load images once before the loop

induce_randomness = 0
first_move = True


while running and game_number <= 100:
    screen.fill("White")
    makeSquares()
    drawPieces()
    
    for event in p.event.get():
        if event.type == p.QUIT:
            running = False
        elif event.type == p.MOUSEBUTTONDOWN:
            if not auto_play:
                auto_play = True
                print("Auto-play started! Game will play itself.")
            else:
                auto_play = False
                print("Auto-play paused.")


    
    # Auto-play logic: make moves automatically
    if auto_play and not (gs.whiteWon or gs.blackWon or gs.staleMate):
        current_time = p.time.get_ticks()
        if current_time - move_delay > MOVE_INTERVAL:
            if first_move:
                var_level = random.randint(1, 20)
                var_elo = random.randint(100, 2500)
                evaluation, wdl_stats = eval_stockfish(gs.generateFen(gs.board), var_level, var_elo)
                new_row = pd.DataFrame([{
                                                'Game_No': game_number,
                                                'FEN': gs.generateFen(gs.board),
                                                'Eval_cp': evaluation.get('value') if evaluation['type'] == 'cp' else None,
                                                'Eval_mate': evaluation.get('value') if evaluation['type'] == 'mate' else None,
                                                'stat_win': wdl_stats[0] if wdl_stats else None,
                                                'stat_draw': wdl_stats[1] if wdl_stats else None,
                                                'stat_loss': wdl_stats[2] if wdl_stats else None,
                                                'white_won': 1 if gs.whiteWon else 0,
                                                'black_won': 1 if gs.blackWon else 0,
                                                'stalemate': 1 if gs.staleMate else 0,
                                                'move_no': move_number
                                            }])
                df = pd.concat([df, new_row], ignore_index=True)
                first_move = False
            else:
                induce_randomness = random.randint(1, 10)
                if induce_randomness % 4 == 0:
                    possible_moves = gs.lenValidMoves(gs.board)
                    if possible_moves and possible_moves != ['Nothing']:
                        var_level = random.randint(1, 20)
                        var_elo = random.randint(100, 2500)
                        select_move = random.choice(possible_moves)
                        row = select_move[1][0][0]
                        col = select_move[1][0][1]
                        sqSelected = (row, col)
                        moveSet.append(sqSelected)
                        
                        row = select_move[1][1][0]
                        col = select_move[1][1][1]
                        sqSelected = (row, col)
                        moveSet.append(sqSelected)
                        gs.makeMove(moveSet[0], moveSet[1])
                        
                        # Increment move number after each move
                        move_number += 1
                        print('move number:', move_number)
                        print('game number:', game_number)
                        
                        evaluation, wdl_stats = eval_stockfish(gs.generateFen(gs.board), var_level, var_elo)
                        
                        # Append data to DataFrame
                        new_row = pd.DataFrame([{
                                                'Game_No': game_number,
                                                'FEN': gs.generateFen(gs.board),
                                                'Eval_cp': evaluation.get('value') if evaluation['type'] == 'cp' else None,
                                                'Eval_mate': evaluation.get('value') if evaluation['type'] == 'mate' else None,
                                                'stat_win': wdl_stats[0] if wdl_stats else None,
                                                'stat_draw': wdl_stats[1] if wdl_stats else None,
                                                'stat_loss': wdl_stats[2] if wdl_stats else None,
                                                'white_won': 1 if gs.whiteWon else 0,
                                                'black_won': 1 if gs.blackWon else 0,
                                                'stalemate': 1 if gs.staleMate else 0,
                                                'move_no': move_number 
                                            }])
                        df = pd.concat([df, new_row], ignore_index=True)

                        moveSet = []
                        move_delay = current_time
                else:
                    if gs.whiteToMove:
                        var_level = random.randint(1, 20)
                        var_elo = random.randint(500, 2500)
                        print('white elo:', var_elo)
                        moveSet = move_stockfish(gs.generateFen(gs.board), var_level, var_elo)
                        gs.makeMove(moveSet[0], moveSet[1])
                        
                        # Increment move number after each move
                        move_number += 1
                        print('move number:', move_number)
                        print('game number:', game_number)
                        
                        evaluation, wdl_stats = eval_stockfish(gs.generateFen(gs.board), var_level, var_elo)
                        moveSet = []
                        move_delay = current_time
                        
                        # Append data to DataFrame
                        new_row = pd.DataFrame([{
                                                'Game_No': game_number,
                                                'FEN': gs.generateFen(gs.board),
                                                'Eval_cp': evaluation.get('value') if evaluation['type'] == 'cp' else None,
                                                'Eval_mate': evaluation.get('value') if evaluation['type'] == 'mate' else None,
                                                'stat_win': wdl_stats[0] if wdl_stats else None,
                                                'stat_draw': wdl_stats[1] if wdl_stats else None,
                                                'stat_loss': wdl_stats[2] if wdl_stats else None,
                                                'white_won': 1 if gs.whiteWon else 0,
                                                'black_won': 1 if gs.blackWon else 0,
                                                'stalemate': 1 if gs.staleMate else 0,
                                                'move_no': move_number
                                            }])
                        df = pd.concat([df, new_row], ignore_index=True)
                    else:
                        var_level = random.randint(1, 20)
                        var_elo = random.randint(500, 2500)
                        print('black elo:', var_elo)
                        moveSet = move_stockfish(gs.generateFen(gs.board), var_level, var_elo)
                        gs.makeMove(moveSet[0], moveSet[1])
                        
                        # Increment move number after each move
                        move_number += 1
                        print('move number:', move_number)
                        print('game number:', game_number)
                        
                        evaluation, wdl_stats = eval_stockfish(gs.generateFen(gs.board), var_level, var_elo)
                        moveSet = []
                        move_delay = current_time
                        
                        # Append data to DataFrame
                        new_row = pd.DataFrame([{
                                                'Game_No': game_number,
                                                'FEN': gs.generateFen(gs.board),
                                                'Eval_cp': evaluation.get('value') if evaluation['type'] == 'cp' else None,
                                                'Eval_mate': evaluation.get('value') if evaluation['type'] == 'mate' else None,
                                                'stat_win': wdl_stats[0] if wdl_stats else None,
                                                'stat_draw': wdl_stats[1] if wdl_stats else None,
                                                'stat_loss': wdl_stats[2] if wdl_stats else None,
                                                'white_won': 1 if gs.whiteWon else 0,
                                                'black_won': 1 if gs.blackWon else 0,
                                                'stalemate': 1 if gs.staleMate else 0,
                                                'move_no': move_number
                                            }])
                        df = pd.concat([df, new_row], ignore_index=True)
            
    # Check for game end
    if gs.whiteWon or gs.blackWon or gs.staleMate:
        my_font = p.font.SysFont('Comic Sans MS', 30)
        if gs.whiteWon:
            text = 'WHITE WINS!'
        elif gs.blackWon:
            text = 'BLACK WINS!'
        else:
            text = 'STALEMATE!'
        text_surface = my_font.render(text, False, (255, 0, 0))
        screen.blit(text_surface, (250, 400))
        
        # Save DataFrame when game ends (only once)
        if game_end_timer == 0:
            print(f"Game {game_number} ended. Saving data to chess_games_final.csv...")
            df.to_csv('chess_games_final_2.csv', index=False)
            print(f"Total games saved: {game_number}")
            game_end_timer = p.time.get_ticks()
        
        # Restart game after delay
        if p.time.get_ticks() - game_end_timer > GAME_END_DELAY:
            print(f"\nStarting new game {game_number + 1}...")
            gs = ce.gameState()  # Reset game state
            game_number += 1
            move_number = 0
            moveSet = []
            first_move = True
            game_end_timer = 0
            auto_play = True  # Continue auto-play for next game
    
    p.display.flip()
    clock.tick(15)  # Use MAX_FPS value for smoother animation


p.quit()

# Export final DataFrame
print("\nExporting final DataFrame...")
df.to_csv('chess_games_final_2.csv', index=False)
print(f"Data exported successfully! Total rows: {len(df)}")
print(df.head(20))




