
import importlib.util
import subprocess
import sys

def ensure_installed(package_name, import_name=None):
    """Install package if not found. 
    package_name: name to install via pip
    import_name: name to import (if different from package_name)
    """
    check_name = import_name if import_name else package_name
    if importlib.util.find_spec(check_name) is None:
        print(f"'{check_name}' not found — installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"'{package_name}' installed successfully.")

ensure_installed("torch")
ensure_installed('tabulate')
ensure_installed('scikit-learn', 'sklearn')
ensure_installed('matplotlib')
ensure_installed('pandas')

import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from tabulate import tabulate
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# Reproducibility: set global seed for PyTorch and NumPy
# Change `SEED` value if you want a different deterministic run
SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)


# Load data
df = pd.read_csv('C:/Users/anchi/GitHub/Repos/Chess_Game/chess_games_final.csv')
chess_df = df[['Game_No', 'move_no', 'FEN', 'Eval_cp']]
chess_df = chess_df[chess_df['Eval_cp'].notnull()].reset_index(drop=True)
print(f"Dataset size: {len(chess_df)} positions")

# Normalize evaluation scores to [-1, 1] range for better training
eval_min = chess_df['Eval_cp'].min()
eval_max = chess_df['Eval_cp'].max()
print(f"Eval range: [{eval_min:.2f}, {eval_max:.2f}]")
chess_df['Eval_cp_normalized'] = 2 * (chess_df['Eval_cp'] - eval_min) / (eval_max - eval_min) - 1

def points_of_material(fen):
    white_material = 0
    black_material = 0

    point_to_piece = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 11,
        'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 11
    }

    board_part = fen.split(' ')[0]

    for char in board_part:
        if char in ['p','r','n','b','q','k']:
            black_material += point_to_piece[char]
        elif char in ['P','R','N','B','Q','K']:
            white_material += point_to_piece[char]
        else:
            continue
    return white_material, black_material

chess_df[['white_material', 'black_material']] = chess_df['FEN'].apply(points_of_material).apply(pd.Series)



# FEN to tensor conversion
def fen_to_tensor(fen):
    """
    Convert FEN string to 12x8x8 tensor (12 piece types x 8x8 board)
    Piece mapping: P=0, N=1, B=2, R=3, Q=4, K=5 (white)
                   p=6, n=7, b=8, r=9, q=10, k=11 (black)
    """
    piece_to_idx = {
        'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
        'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
    }
    
    board_part = fen.split(' ')[0]  # Get board position part
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

# VGG-style model for chess evaluation
'''class ChessVGG(nn.Module):
    def __init__(self):
        super(ChessVGG, self).__init__()
        
        # VGG-style convolutional blocks
        self.features = nn.Sequential(
            # Block 1
            nn.Conv2d(12, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            
            # Block 2
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),

            # Block 3
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            
            # Block 4
            nn.Conv2d(256, 512, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
        )
        
        # Fully connected layers
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(512 * 8 * 8, 8192),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(8192, 4096),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(4096, 2048),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(2048, 1)
        )
    
    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x.squeeze()'''

# Improved VGG-style model with batch norm, GELU, pooling, and material inputs
class ChessVGG(nn.Module):
    def __init__(self, dropout_rate=0.35):
        super(ChessVGG, self).__init__()

        # VGG-style convolutional blocks with batch normalization and max pooling
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

        # Small MLP to process [white_material, black_material]
        self.material_head = nn.Sequential(
            nn.Linear(2, 32),
            nn.GELU(),
            nn.Linear(32, 32),
            nn.GELU(),
        )

        # Fused classifier: CNN features (1024) + material features (32)
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256 * 2 * 2 + 32, 1024),
            nn.LayerNorm(1024),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(1024, 512),
            nn.LayerNorm(512),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(512, 1)  # Output: normalized eval_cp
        )

    def forward(self, x, material):
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x_flat = torch.flatten(x, start_dim=1)       # (B, 256*2*2)
        m = self.material_head(material)              # (B, 32)
        fused = torch.cat([x_flat, m], dim=1)         # (B, 1024+32)
        return self.classifier(fused).squeeze()

# Train-test split
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

train_df, test_df = train_test_split(chess_df, test_size=0.2, random_state=42)
print(f"Train size: {len(train_df)}, Test size: {len(test_df)}")

# Create custom dataset
class ChessDataset(torch.utils.data.Dataset):
    def __init__(self, dataframe, use_normalized=True):
        self.dataframe = dataframe.reset_index(drop=True)
        self.use_normalized = use_normalized

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, idx):
        row = self.dataframe.iloc[idx]
        fen = row['FEN']
        if self.use_normalized:
            eval_cp = float(row['Eval_cp_normalized'])
        else:
            eval_cp = float(row['Eval_cp'])
        tensor = fen_to_tensor(fen)
        material = torch.tensor([float(row['white_material']), float(row['black_material'])], dtype=torch.float32)
        return tensor, material, torch.tensor(eval_cp, dtype=torch.float32)

# Create dataloaders
train_dataset = ChessDataset(train_df, use_normalized=True)
test_dataset = ChessDataset(test_df, use_normalized=True)

batch_size = 64  # Increased batch size for better gradient estimates
train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

torch.cuda.empty_cache()


# Initialize model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = ChessVGG(dropout_rate=0.35).to(device)
print(f"Training on: {device}")
print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

# Loss and optimizer with weight decay (L2 regularization)
criterion = nn.MSELoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-5)

# Learning rate scheduler - reduce LR when validation loss plateaus
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='min', factor=0.5, patience=3, min_lr=1e-6
)

# Training loop with early stopping and learning rate scheduling
num_epochs = 50
patience = 8
best_val_loss = float('inf')
patience_counter = 0
train_losses = []
test_losses = []
train_metrics = {'mae': [], 'r2': []}
test_metrics = {'mae': [], 'r2': []}

print("\nTraining started...")
print("=" * 80)

for epoch in range(num_epochs):
    # Training
    model.train()
    train_loss = 0.0
    train_preds = []
    train_targets = []
    
    print(f"\n[EPOCH {epoch+1}/{num_epochs}]")
    print("-" * 80)
    
    for batch_idx, (inputs, material, targets) in enumerate(train_loader):
        inputs, material, targets = inputs.to(device), material.to(device), targets.to(device)

        optimizer.zero_grad()
        outputs = model(inputs, material)
        loss = criterion(outputs, targets)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        
        train_loss += loss.item()
        train_preds.extend(outputs.detach().cpu().numpy())
        train_targets.extend(targets.detach().cpu().numpy())
        
        # Verbose output every 10 batches
        if (batch_idx + 1) % 10 == 0:
            progress = (batch_idx + 1) / len(train_loader) * 100
            avg_loss = train_loss / (batch_idx + 1)
            print(f"  Batch [{batch_idx+1:4d}/{len(train_loader)}] ({progress:5.1f}%) | "
                  f"Loss: {loss.item():8.4f} | Avg: {avg_loss:8.4f}")
    
    train_loss /= len(train_loader)
    train_mae = mean_absolute_error(train_targets, train_preds)
    train_r2 = r2_score(train_targets, train_preds)
    
    train_losses.append(train_loss)
    train_metrics['mae'].append(train_mae)
    train_metrics['r2'].append(train_r2)
    
    print(f"\n  TRAIN LOSS: {train_loss:.4f} | MAE: {train_mae:.4f} | R² Score: {train_r2:.4f}")
    
    # Validation
    model.eval()
    test_loss = 0.0
    test_preds = []
    test_targets = []
    
    with torch.no_grad():
        for batch_idx, (inputs, material, targets) in enumerate(test_loader):
            inputs, material, targets = inputs.to(device), material.to(device), targets.to(device)
            outputs = model(inputs, material)
            loss = criterion(outputs, targets)
            test_loss += loss.item()
            test_preds.extend(outputs.detach().cpu().numpy())
            test_targets.extend(targets.detach().cpu().numpy())
    
    test_loss /= len(test_loader)
    test_mae = mean_absolute_error(test_targets, test_preds)
    test_r2 = r2_score(test_targets, test_preds)
    
    test_losses.append(test_loss)
    test_metrics['mae'].append(test_mae)
    test_metrics['r2'].append(test_r2)
    
    print(f"  TEST LOSS:  {test_loss:.4f} | MAE: {test_mae:.4f} | R² Score: {test_r2:.4f}")
    print(f"  GAP: {(train_loss - test_loss):+.4f}")
    
    # Learning rate scheduler step
    scheduler.step(test_loss)
    
    # Early stopping check
    if test_loss < best_val_loss:
        best_val_loss = test_loss
        patience_counter = 0
        # Save best model
        import os
        model_path = os.path.join(os.path.dirname(__file__), 'chess_vgg_best_model.pth')
        torch.save({
            'epoch': epoch + 1,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'test_loss': test_loss,
        }, model_path)
        print(f"  ✓ Best model saved (loss: {test_loss:.4f})")
    else:
        patience_counter += 1
        if patience_counter >= patience:
            print(f"\n  ⚠ Early stopping triggered after {epoch + 1} epochs")
            break
    
    print("=" * 80)

# Save final model
import os
model_path = os.path.join(os.path.dirname(__file__), 'chess_vgg_model_final.pth')
torch.save({
    'epoch': epoch + 1,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'train_losses': train_losses,
    'test_losses': test_losses,
    'train_metrics': train_metrics,
    'test_metrics': test_metrics,
    'eval_min': eval_min,
    'eval_max': eval_max,
}, model_path)
print(f"Model saved to '{model_path}'")

print("\nTraining completed!")

# Plot training metrics
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

epochs_range = range(1, len(train_losses) + 1)

# Loss plot
axes[0].plot(epochs_range, train_losses, label='Train Loss', marker='o', linewidth=2)
axes[0].plot(epochs_range, test_losses, label='Test Loss', marker='s', linewidth=2)
axes[0].set_xlabel('Epoch', fontsize=12)
axes[0].set_ylabel('MSE Loss', fontsize=12)
axes[0].set_title('Training & Test Loss', fontsize=14, fontweight='bold')
axes[0].legend(fontsize=11)
axes[0].grid(True, alpha=0.3)

# MAE plot
axes[1].plot(epochs_range, train_metrics['mae'], label='Train MAE', marker='o', linewidth=2)
axes[1].plot(epochs_range, test_metrics['mae'], label='Test MAE', marker='s', linewidth=2)
axes[1].set_xlabel('Epoch', fontsize=12)
axes[1].set_ylabel('MAE', fontsize=12)
axes[1].set_title('Mean Absolute Error', fontsize=14, fontweight='bold')
axes[1].legend(fontsize=11)
axes[1].grid(True, alpha=0.3)

# R² plot
axes[2].plot(epochs_range, train_metrics['r2'], label='Train R²', marker='o', linewidth=2)
axes[2].plot(epochs_range, test_metrics['r2'], label='Test R²', marker='s', linewidth=2)
axes[2].set_xlabel('Epoch', fontsize=12)
axes[2].set_ylabel('R² Score', fontsize=12)
axes[2].set_title('R² Score', fontsize=14, fontweight='bold')
axes[2].legend(fontsize=11)
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('training_metrics.png', dpi=300)
print("Training metrics plot saved as 'training_metrics.png'")
plt.show()

# Test predictions with denormalization
model.eval()
sample_indices = [0, 1, 2, 3, 4]
print("\n" + "=" * 80)
print("Sample Predictions (Denormalized):")
print("=" * 80)
with torch.no_grad():
    for idx in sample_indices:
        fen = test_df.iloc[idx]['FEN']
        actual_norm = test_df.iloc[idx]['Eval_cp_normalized']
        actual = test_df.iloc[idx]['Eval_cp']
        tensor = fen_to_tensor(fen).unsqueeze(0).to(device)
        wm = float(test_df.iloc[idx]['white_material'])
        bm = float(test_df.iloc[idx]['black_material'])
        material = torch.tensor([[wm, bm]], dtype=torch.float32).to(device)
        predicted_norm = model(tensor, material).item()
        # Denormalize predictions
        predicted = (predicted_norm + 1) / 2 * (eval_max - eval_min) + eval_min
        print(f"Actual: {actual:8.2f} | Predicted: {predicted:8.2f} | Error: {abs(actual - predicted):8.2f}")

# Create new dataframe with predictions for all positions
print("\n" + "=" * 80)
print("Generating predictions for all positions...")
print("=" * 80)
chess_df_with_predictions = chess_df.copy()
predictions = []

model.eval()
with torch.no_grad():
    for idx in range(len(chess_df)):
        row = chess_df.iloc[idx]
        fen = row['FEN']
        tensor = fen_to_tensor(fen).unsqueeze(0).to(device)
        material = torch.tensor([[float(row['white_material']), float(row['black_material'])]], dtype=torch.float32).to(device)
        predicted_norm = model(tensor, material).item()
        # Denormalize prediction
        predicted = (predicted_norm + 1) / 2 * (eval_max - eval_min) + eval_min
        predictions.append(predicted)
        
        # Progress indicator
        if (idx + 1) % 1000 == 0:
            print(f"  Processed {idx + 1}/{len(chess_df)} positions ({(idx+1)/len(chess_df)*100:.1f}%)")

chess_df_with_predictions['Predicted_Eval_cp'] = predictions
print(f"Predictions completed for all {len(chess_df)} positions!")

# Save the dataframe with predictions
output_file = 'chess_predictions_improved.csv'
chess_df_with_predictions.to_csv(output_file, index=False)
print(f"Dataframe with predictions saved to '{output_file}'")

# Show comprehensive statistics
print("\n" + "=" * 80)
print("Prediction Statistics:")
print("=" * 80)
errors = chess_df_with_predictions['Eval_cp'] - chess_df_with_predictions['Predicted_Eval_cp']
mae = errors.abs().mean()
rmse = (errors**2).mean()**0.5
r2 = r2_score(chess_df_with_predictions['Eval_cp'], chess_df_with_predictions['Predicted_Eval_cp'])
median_ae = errors.abs().median()

print(f"Mean Absolute Error (MAE):     {mae:.4f}")
print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")
print(f"Median Absolute Error:          {median_ae:.4f}")
print(f"R² Score:                       {r2:.4f}")
print(f"\nError Statistics:")
print(f"  Min Error:  {errors.min():.4f}")
print(f"  Max Error:  {errors.max():.4f}")
print(f"  Std Dev:    {errors.std():.4f}")

print(f"\nFirst 10 predictions:")
print(chess_df_with_predictions[['Game_No', 'move_no', 'Eval_cp', 'Predicted_Eval_cp']].head(10).to_string())
print("=" * 80)



