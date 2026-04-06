import time
import importlib.util
import subprocess
import sys
import os

def ensure_installed(package_name):
    if importlib.util.find_spec(package_name) is None:
        print(f"'{package_name}' not found — installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"'{package_name}' installed successfully.")

ensure_installed("pandas")
ensure_installed("stockfish")
ensure_installed("pygame")
ensure_installed("requests")
ensure_installed("torch")

import pandas as pd
import torch
import torch.nn as nn
import numpy as np

import pygame as p
from requests import head
import sys
sys.path.append('Chess')
import ChessEngine as ce
import random
from stockfish import Stockfish


# Define ChessVGG model architecture
class ChessVGG(nn.Module):
    def __init__(self, dropout_rate=0.35):
        super(ChessVGG, self).__init__()

        self.block1 = nn.Sequential(
            nn.Conv2d(12, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.GELU(),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.GELU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        self.block2 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.GELU(),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.GELU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        self.block3 = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.GELU(),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.GELU(),
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256 * 2 * 2, 1024),
            nn.LayerNorm(1024),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(1024, 512),
            nn.LayerNorm(512),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(512, 1)
        )

    def forward(self, x):
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.classifier(x)
        return x.squeeze()


def fen_to_tensor(fen):
    """Convert FEN string to 12x8x8 tensor"""
    piece_to_idx = {
        'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
        'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
    }
    
    board_part = fen.split(' ')[0]
    tensor = np.zeros((12, 8, 8), dtype=np.float32)
    
    row = 0
    col = 0
    for char in board_part:
        if char == '/':
            row += 1
            col = 0
        elif char.isdigit():
            col += int(char)
        else:
            if char in piece_to_idx:
                tensor[piece_to_idx[char], row, col] = 1.0
            col += 1
    
    return torch.from_numpy(tensor)


# Load the trained chess model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = ChessVGG().to(device)

# Initialize optimizer for real-time learning
optimizer = torch.optim.Adam(model.parameters(), lr=0.0001)  # Small learning rate for stability
criterion = nn.MSELoss()

try:
    _model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chess_vgg_model_final.pth')
    checkpoint = torch.load(_model_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    # Load optimizer state if available
    if 'optimizer_state_dict' in checkpoint:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    model.train()  # Set to training mode for real-time learning
    print(f"Chess VGG model loaded successfully on {device}!")
    print("Real-time learning ENABLED - model will learn from each game")
except FileNotFoundError:
    print("ERROR: chess_vgg_model_final.pth not found! Please train the model first.")
    sys.exit(1)


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

# Real-time learning variables
experience_buffer = []  # Stores (fen, tensor) for each white move in current game
training_stats = {
    'games_played': 0,
    'white_wins': 0,
    'white_losses': 0,
    'draws': 0,
    'total_training_updates': 0,
    'avg_loss': []
}

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


def train_on_game_outcome(outcome):
    """
    Train the model based on game outcome.
    outcome: 'win', 'loss', or 'draw'
    Uses reward signal: Win = +1000, Draw = 0, Loss = -1000
    """
    if len(experience_buffer) == 0:
        return 0.0
    
    # Assign reward based on outcome
    if outcome == 'win':
        target_value = 1000.0  # High positive value for winning positions
        print("\n✓ WHITE WON! Reinforcing winning strategy...")
    elif outcome == 'loss':
        target_value = -1000.0  # Negative value - learn to avoid these positions
        print("\n✗ WHITE LOST! Learning from mistakes...")
    else:  # draw
        target_value = 0.0
        print("\n= DRAW. Neutral learning...")
    
    model.train()
    total_loss = 0.0
    batch_size = min(32, len(experience_buffer))
    
    # Train on all positions from this game
    for i in range(0, len(experience_buffer), batch_size):
        batch = experience_buffer[i:i+batch_size]
        
        # Stack tensors into batch
        batch_tensors = torch.stack([item[1] for item in batch]).to(device)
        targets = torch.full((len(batch),), target_value, dtype=torch.float32).to(device)
        
        # Forward pass
        optimizer.zero_grad()
        predictions = model(batch_tensors)
        
        # Compute loss and backpropagate
        loss = criterion(predictions, targets)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    
    avg_loss = total_loss / max(1, len(experience_buffer) // batch_size)
    training_stats['total_training_updates'] += 1
    training_stats['avg_loss'].append(avg_loss)
    
    print(f"  Training loss: {avg_loss:.4f}")
    print(f"  Positions learned from: {len(experience_buffer)}")
    print(f"  Total training updates: {training_stats['total_training_updates']}")
    
    # Clear buffer for next game
    experience_buffer.clear()
    
    return avg_loss


def move_vgg_model(board_state):
    """Get best move for white using chess VGG model (highest evaluation)"""
    possible_moves = gs.lenValidMoves(board_state)
    
    if not possible_moves or possible_moves == ['Nothing']:
        return None
    
    best_move = None
    best_eval = float('-inf')
    best_fen = None
    best_tensor = None
    
    # Save current game state
    saved_board = [row[:] for row in gs.board]
    saved_white_to_move = gs.whiteToMove
    
    # Evaluate each possible move
    for move in possible_moves:
        try:
            # Restore game state
            gs.board = [row[:] for row in saved_board]
            gs.whiteToMove = saved_white_to_move
            
            # Make the move
            start_pos = move[1][0]
            end_pos = move[1][1]
            gs.makeMove(start_pos, end_pos)
            
            # Get FEN and evaluate
            fen = gs.generateFen(gs.board)
            tensor = fen_to_tensor(fen)
            
            with torch.no_grad():
                evaluation = model(tensor.unsqueeze(0).to(device)).item()
            
            # White wants highest evaluation
            if evaluation > best_eval:
                best_eval = evaluation
                best_move = move[1]  # [(start_row, start_col), (end_row, end_col)]
                best_fen = fen
                best_tensor = tensor
        except Exception as e:
            # Skip invalid moves
            print(f"Warning: Skipping invalid move: {e}")
            continue
    
    # Restore original game state
    gs.board = [row[:] for row in saved_board]
    gs.whiteToMove = saved_white_to_move
    
    # Store the chosen position in experience buffer for learning
    if best_fen and best_tensor is not None:
        experience_buffer.append((best_fen, best_tensor))
    
    print(f"Model evaluation: {best_eval:.2f}")
    return best_move

            

load_images()  # Load images once before the loop

induce_randomness = 0
first_move = True


while running and game_number <= 1000:
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
                        # White uses VGG model - best move (highest eval)
                        print('White (VGG Model) thinking...')
                        best_move_coords = move_vgg_model(gs.board)
                        
                        if best_move_coords:
                            gs.makeMove(best_move_coords[0], best_move_coords[1])
                            
                            # Increment move number after each move
                            move_number += 1
                            print('move number:', move_number)
                            print('game number:', game_number)
                            
                            var_level = random.randint(1, 20)
                            var_elo = random.randint(500, 2500)
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
                        # Black uses Stockfish with randomness
                        var_level = random.randint(1, 20)
                        var_elo = random.randint(500, 2500)
                        print('Black (Stockfish) elo:', var_elo)
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
            game_outcome = 'win'
        elif gs.blackWon:
            text = 'BLACK WINS!'
            game_outcome = 'loss'
        else:
            text = 'STALEMATE!'
            game_outcome = 'draw'
        text_surface = my_font.render(text, False, (255, 0, 0))
        screen.blit(text_surface, (250, 400))
        
        # Train model based on game outcome (only once per game)
        if game_end_timer == 0:
            # Update training statistics
            training_stats['games_played'] += 1
            if gs.whiteWon:
                training_stats['white_wins'] += 1
            elif gs.blackWon:
                training_stats['white_losses'] += 1
            else:
                training_stats['draws'] += 1
            
            # Train on this game's experience
            print(f"\n{'='*60}")
            print(f"Game {game_number} ended.")
            training_loss = train_on_game_outcome(game_outcome)
            
            # Print training statistics
            print(f"\n--- Training Statistics ---")
            print(f"Games played: {training_stats['games_played']}")
            print(f"White wins: {training_stats['white_wins']} ({training_stats['white_wins']/training_stats['games_played']*100:.1f}%)")
            print(f"White losses: {training_stats['white_losses']} ({training_stats['white_losses']/training_stats['games_played']*100:.1f}%)")
            print(f"Draws: {training_stats['draws']} ({training_stats['draws']/training_stats['games_played']*100:.1f}%)")
            
            # Save model every 500 games
            if game_number % 500 == 0:
                model_save_path = f'chess_vgg_model_online_game_{game_number}.pth'
                torch.save({
                    'epoch': game_number,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'training_stats': training_stats,
                }, model_save_path)
                print(f"\n✓ Model checkpoint saved: {model_save_path}")
            
            print(f"{'='*60}\n")
            
            # Save game data
            df.to_csv('chess_games_final_2.csv', index=False)
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
df.to_csv('AI_chess_games_final_2.csv', index=False)
print(f"Data exported successfully! Total rows: {len(df)}")
print(df.head(20))