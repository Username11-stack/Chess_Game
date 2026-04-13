
import time
import importlib.util
import subprocess
import sys
import os
import shutil

if os.getenv("HEADLESS", "0") == "1" or os.getenv("GITHUB_ACTIONS") == "true":
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

IS_HEADLESS = os.getenv("HEADLESS", "0") == "1" or os.getenv("GITHUB_ACTIONS") == "true"

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

        # Block 1: 8x8 -> 4x4  (18 input planes: pieces + side-to-move + castling + en passant)
        self.block1 = nn.Sequential(
            nn.Conv2d(18, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.GELU(),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.GELU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        # Block 2: stays at 4x4
        self.block2 = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.GELU(),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.GELU(),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.GELU(),
        )

        # Block 3: residual 256 -> 512
        self.block3_main = nn.Sequential(
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.GELU(),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
        )
        self.block3_skip = nn.Sequential(
            nn.Conv2d(256, 512, kernel_size=1),
            nn.BatchNorm2d(512),
        )

        # Block 4: residual 512 -> 512 (identity skip)
        self.block4 = nn.Sequential(
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
            nn.GELU(),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.BatchNorm2d(512),
        )

        self.adaptive_pool = nn.AdaptiveAvgPool2d((2, 2))

        self.material_head = nn.Sequential(
            nn.Linear(2, 64),
            nn.GELU(),
            nn.Linear(64, 64),
            nn.GELU(),
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(512 * 2 * 2 + 64, 2048),
            nn.LayerNorm(2048),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(2048, 1024),
            nn.LayerNorm(1024),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(1024, 512),
            nn.LayerNorm(512),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(512, 1)
        )

    def forward(self, x, material):
        x = self.block1(x)
        x = self.block2(x)
        x = torch.nn.functional.gelu(self.block3_main(x) + self.block3_skip(x))
        x = torch.nn.functional.gelu(self.block4(x) + x)
        x = self.adaptive_pool(x)
        x_flat = torch.flatten(x, start_dim=1)
        m = self.material_head(material)
        fused = torch.cat([x_flat, m], dim=1)
        return self.classifier(fused).squeeze()


def points_of_material(fen):
    white_material = 0
    black_material = 0
    point_to_piece = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 11,
        'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 11
    }
    board_part = fen.split(' ')[0]
    for char in board_part:
        if char in ['p', 'r', 'n', 'b', 'q', 'k']:
            black_material += point_to_piece[char]
        elif char in ['P', 'R', 'N', 'B', 'Q', 'K']:
            white_material += point_to_piece[char]
    return white_material, black_material


def fen_to_tensor(fen):
    """Convert FEN string to 18x8x8 tensor (pieces + side-to-move + castling + en passant)"""
    piece_to_idx = {
        'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
        'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
    }

    parts = fen.split(' ')
    board_part = parts[0]
    side_to_move = parts[1] if len(parts) > 1 else 'w'
    castling = parts[2] if len(parts) > 2 else '-'
    en_passant = parts[3] if len(parts) > 3 else '-'

    tensor = np.zeros((18, 8, 8), dtype=np.float32)

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

    if side_to_move == 'w':
        tensor[12, :, :] = 1.0
    if 'K' in castling:
        tensor[13, :, :] = 1.0
    if 'Q' in castling:
        tensor[14, :, :] = 1.0
    if 'k' in castling:
        tensor[15, :, :] = 1.0
    if 'q' in castling:
        tensor[16, :, :] = 1.0
    if en_passant != '-' and len(en_passant) == 2:
        ep_col = ord(en_passant[0]) - ord('a')
        ep_row = 8 - int(en_passant[1])
        if 0 <= ep_row < 8 and 0 <= ep_col < 8:
            tensor[17, ep_row, ep_col] = 1.0

    return torch.from_numpy(tensor)


# Load the trained chess model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = ChessVGG().to(device)

# Initialize optimizer for real-time learning
optimizer = torch.optim.Adam(model.parameters(), lr=0.0001)  # Small learning rate for stability
criterion = nn.MSELoss()

try:
    _model_dir = os.path.dirname(os.path.abspath(__file__))
    _model_path = os.path.join(_model_dir, 'chess_vgg_model_final_Test.pth')
    if not os.path.exists(_model_path):
        raise FileNotFoundError
    checkpoint = torch.load(_model_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    # Load optimizer state if available
    if 'optimizer_state_dict' in checkpoint:
        try:
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        except ValueError:
            print("Warning: Could not load optimizer state for current model configuration.")
    model.train()  # Set to training mode for real-time learning
    print(f"Chess VGG model loaded successfully on {device}!")
    print("Real-time learning ENABLED - model will learn from each game")
except FileNotFoundError:
    print("ERROR: chess_vgg_model_final_Test.pth not found.")
    sys.exit(1)


WIDTH = 800
HEIGHT = 800
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15

# pygame setup
if not IS_HEADLESS:
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
else:
    screen = None
    clock = None
running = True
gs = ce.gameState()
IMAGES = {}
moveSet = []
auto_play = os.getenv("AUTO_PLAY", "1") == "1"
move_delay = 0
MOVE_INTERVAL = 50  # milliseconds between auto moves (1 second)
move_number = 0
game_end_timer = 0
GAME_END_DELAY = 2000  # 2 seconds delay before restarting after game ends
MAX_GAMES = int(os.getenv("MAX_GAMES", "100"))

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

CSV_PATH = 'chess_games_final_2.csv'
CSV_COLUMNS = ['Game_No', 'FEN', 'Eval_cp', 'Eval_mate', 'stat_win', 'stat_draw', 'stat_loss', 'white_won',
               'black_won', 'stalemate', 'move_no']

if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
else:
    df = pd.DataFrame(columns=CSV_COLUMNS)

if not df.empty and 'Game_No' in df.columns and pd.notna(df['Game_No'].max()):
    game_number = int(df['Game_No'].max()) + 1
else:
    game_number = 1

end_game_number = game_number + MAX_GAMES - 1
print(f"Starting from game {game_number}. This run will finish at game {end_game_number}.")




def load_images():
    if IS_HEADLESS:
        return
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

def resolve_stockfish_path():
    env_path = os.getenv("STOCKFISH_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    repo_root = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(repo_root, "stockfish", "stockfish-windows-x86-64-avx2.exe"),
        os.path.join(repo_root, "stockfish", "stockfish-ubuntu-x86-64-avx2"),
        "/usr/games/stockfish",
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    path_candidate = shutil.which("stockfish")
    if path_candidate:
        return path_candidate

    raise FileNotFoundError("Stockfish binary not found. Set STOCKFISH_PATH or install stockfish.")

def eval_stockfish(var_fen, var_level, var_elo):

    stockfish = Stockfish(path=resolve_stockfish_path())

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

    stockfish = Stockfish(path=resolve_stockfish_path())

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
        batch_materials = torch.stack([item[2] for item in batch]).to(device)
        targets = torch.full((len(batch),), target_value, dtype=torch.float32).to(device)
        
        # Forward pass
        optimizer.zero_grad()
        predictions = model(batch_tensors, batch_materials)
        
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
    best_material = None
    
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
            wm, bm = points_of_material(fen)
            material_tensor = torch.tensor([wm / 50.0, bm / 50.0], dtype=torch.float32)
            
            with torch.no_grad():
                evaluation = model(tensor.unsqueeze(0).to(device), material_tensor.unsqueeze(0).to(device)).item()
            
            # White wants highest evaluation
            if evaluation > best_eval:
                best_eval = evaluation
                best_move = move[1]  # [(start_row, start_col), (end_row, end_col)]
                best_fen = fen
                best_tensor = tensor
                best_material = material_tensor
        except Exception as e:
            # Skip invalid moves
            print(f"Warning: Skipping invalid move: {e}")
            continue
    
    # Restore original game state
    gs.board = [row[:] for row in saved_board]
    gs.whiteToMove = saved_white_to_move
    
    # Store the chosen position in experience buffer for learning
    if best_fen and best_tensor is not None:
        experience_buffer.append((best_fen, best_tensor, best_material))
    
    print(f"Model evaluation: {best_eval:.2f}")
    return best_move

            

load_images()  # Load images once before the loop

induce_randomness = 0
first_move = True

def current_millis():
    if IS_HEADLESS:
        return int(time.time() * 1000)
    return p.time.get_ticks()


while running and game_number <= end_game_number:
    if not IS_HEADLESS:
        screen.fill("White")
        makeSquares()
        drawPieces()
    
    if not IS_HEADLESS:
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
        current_time = current_millis()
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
        if gs.whiteWon:
            text = 'WHITE WINS!'
            game_outcome = 'win'
        elif gs.blackWon:
            text = 'BLACK WINS!'
            game_outcome = 'loss'
        else:
            text = 'STALEMATE!'
            game_outcome = 'draw'
        if not IS_HEADLESS:
            my_font = p.font.SysFont('Comic Sans MS', 30)
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
            df.to_csv(CSV_PATH, index=False)
            game_end_timer = current_millis()
        
        # Restart game after delay
        if current_millis() - game_end_timer > GAME_END_DELAY:
            print(f"\nStarting new game {game_number + 1}...")
            gs = ce.gameState()  # Reset game state
            game_number += 1
            move_number = 0
            moveSet = []
            first_move = True
            game_end_timer = 0
            auto_play = True  # Continue auto-play for next game
    
    if not IS_HEADLESS:
        p.display.flip()
        clock.tick(15)  # Use MAX_FPS value for smoother animation


if not IS_HEADLESS:
    p.quit()

# Export final DataFrame
print("\nExporting final DataFrame...")
df.to_csv(CSV_PATH, index=False)
df.to_csv('AI_chess_games_final_2.csv', index=False)
print(f"Data exported successfully! Total rows: {len(df)}")
print(df.head(20))