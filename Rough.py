import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from tabulate import tabulate
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import warnings

if torch.cuda.is_available():
    device = torch.device("cuda")
    gpu_count = torch.cuda.device_count()
    print(f"GPU is available: {torch.cuda.get_device_name(0)}")
    print(f"Number of GPUs: {gpu_count}")
    for i in range(gpu_count):
        props = torch.cuda.get_device_properties(i)
        total_mem = props.total_memory / (1024 ** 3)
        print(f"  GPU {i}: {props.name} | VRAM: {total_mem:.2f} GB | "
              f"Compute Capability: {props.major}.{props.minor}")
    print(f"Current GPU: {torch.cuda.current_device()}")
    print(f"CUDA Version: {torch.version.cuda}")
else:
    device = torch.device("cpu")
    print("GPU is NOT available. Using CPU.")

print(f"\nUsing device: {device}")