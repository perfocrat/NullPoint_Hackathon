"""
train_market_engine.py  --  CareerLens AI neural matrix training agent
======================================================================
Trains the ConditionalEmployabilityVAE on the real Kaggle resume corpus
(ResumeRishi, saved locally as data/market_jds.csv) and writes
'market_latent_space.pth'.

Run:  python train_market_engine.py            (25 epochs)
      python train_market_engine.py --epochs 40 --batch-size 128
"""
from __future__ import annotations

import argparse
import math
import os
import time
from typing import List, Tuple

import numpy as np
import pandas as pd
import torch

from core_model import (COND_DIM, LATENT_DIM, MAX_LEN, PAD_ID, ConditionalEmployabilityVAE,
                        SkillTokenizer, save_checkpoint)
from portfolio_analyzer import SKILLS, compute_text_properties

CSV_PATH = os.path.join("data", "market_jds.csv")
OUT_PATH = "market_latent_space.pth"
RESUME_COLUMN_CANDIDATES = ("Resume_text", "Resume", "Resume_str", "resume_text", "resume", "Text")


def _pick_resume_column(df: pd.DataFrame) -> str:
    lowered = {c.lower(): c for c in df.columns}
    for candidate in RESUME_COLUMN_CANDIDATES:
        if candidate in df.columns:
            return candidate
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    # Fallback: the text column with the longest average content
    text_cols = [c for c in df.columns if df[c].dtype == object or str(df[c].dtype).startswith("str")]
    if not text_cols:
        raise ValueError(f"No text column found in {list(df.columns)}")
    return max(text_cols, key=lambda c: df[c].astype(str).str.len().mean())


def load_genuine_kaggle_dataset(max_seq_len: int = MAX_LEN, csv_path: str = CSV_PATH,
                                max_vocab: int = 8000) -> Tuple[torch.Tensor, torch.Tensor, SkillTokenizer]:
    """
    Loads the physical Kaggle file, tokenizes every resume into a [N, max_seq_len]
    LongTensor and computes the matching [N, 12] float property matrix.
    Returns CPU tensors (they are moved to the GPU once, in train()).
    """
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(
            f"'{csv_path}' not found. Download the ResumeRishi dataset from Kaggle and save it as {csv_path}.")
    try:
        df = pd.read_csv(csv_path, encoding="utf-8", on_bad_lines="skip")
    except UnicodeDecodeError:  # a few Kaggle exports are latin-1
        df = pd.read_csv(csv_path, encoding="latin-1", on_bad_lines="skip")

    column = _pick_resume_column(df)
    texts = (df[column].dropna().astype(str).str.strip())
    texts = texts[texts.str.len() > 50].drop_duplicates().tolist()
    if len(texts) < 32:
        raise ValueError(f"Only {len(texts)} usable resumes found in column '{column}'.")
    print(f"[data] {len(texts)} resumes loaded from column '{column}'")

    seed = [tok for skill in SKILLS for tok in SkillTokenizer.tokenize(skill.replace("_", " "))]
    tokenizer = SkillTokenizer.build(texts, max_vocab=max_vocab, min_freq=3, seed_tokens=seed)
    print(f"[data] vocabulary size: {len(tokenizer)}")

    token_matrix = np.asarray([tokenizer.encode(t, max_seq_len) for t in texts], dtype=np.int64)
    prop_matrix = np.asarray([compute_text_properties(t) for t in texts], dtype=np.float32)
    assert prop_matrix.shape[1] == COND_DIM
    return torch.from_numpy(token_matrix), torch.from_numpy(prop_matrix), tokenizer


def train(epochs: int = 25, batch_size: int = 64, lr: float = 1e-3, seed: int = 42,
          csv_path: str = CSV_PATH, out_path: str = OUT_PATH) -> None:
    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        torch.backends.cudnn.benchmark = True
    print(f"[init] device = {device}" + (f" ({torch.cuda.get_device_name(0)})" if device.type == "cuda" else ""))

    data_cpu, prop_cpu, tokenizer = load_genuine_kaggle_dataset(MAX_LEN, csv_path)

    # Everything lives on the training device from this line on -> no device mismatches
    data_tensor = data_cpu.to(device)
    prop_tensor = prop_cpu.to(device)

    model = ConditionalEmployabilityVAE(vocab_size=len(tokenizer)).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    print(f"[init] parameters: {sum(p.numel() for p in model.parameters()):,} | latent={LATENT_DIM} | cond=+{COND_DIM}")

    n = data_tensor.size(0)
    split = torch.randperm(n, device=device)  # permutation compiled natively on the GPU
    n_val = max(16, int(0.1 * n))
    val_idx, train_idx = split[:n_val], split[n_val:]

    beta_max, kl_warmup_epochs, word_dropout = 0.5, 10, 0.3
    history: List[dict] = []

    for epoch in range(1, epochs + 1):
        model.train()
        t0 = time.time()
        beta = beta_max * min(1.0, epoch / kl_warmup_epochs)
        order = train_idx[torch.randperm(train_idx.numel(), device=device)]  # scramble on GPU
        tot = rec = kld = 0.0
        batches = 0
        for start in range(0, order.numel(), batch_size):
            idx = order[start:start + batch_size]
            xb, cb = data_tensor[idx], prop_tensor[idx]
            optimizer.zero_grad(set_to_none=True)
            logits, mu, logvar = model(xb, cb, word_dropout=word_dropout)
            loss, recon, kl = ConditionalEmployabilityVAE.loss_function(logits, xb, mu, logvar, beta, PAD_ID)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            tot, rec, kld, batches = tot + loss.item(), rec + recon.item(), kld + kl.item(), batches + 1
        scheduler.step()

        model.eval()
        with torch.no_grad():
            xv, cv = data_tensor[val_idx], prop_tensor[val_idx]
            lv, mv, lvv = model(xv, cv)
            val_loss, val_recon, _ = ConditionalEmployabilityVAE.loss_function(lv, xv, mv, lvv, beta, PAD_ID)
        row = {"epoch": epoch, "loss": tot / batches, "recon": rec / batches, "kl": kld / batches,
               "val_loss": val_loss.item(), "val_recon": val_recon.item()}
        history.append(row)
        print(f"[epoch {epoch:02d}/{epochs}] loss {row['loss']:.2f} | recon {row['recon']:.2f} | "
              f"kl {row['kl']:.2f} | val {row['val_loss']:.2f} | beta {beta:.2f} | {time.time() - t0:.1f}s")

    # Market statistics in latent space (used by the app for the 'market typicality' readout)
    model.eval()
    with torch.no_grad():
        mus = torch.cat([model.embed(data_tensor[i:i + 256], prop_tensor[i:i + 256])
                         for i in range(0, n, 256)], dim=0)
        centroid = mus.mean(dim=0)
        distances = torch.linalg.norm(mus - centroid, dim=1)
        quantiles = torch.quantile(distances, torch.linspace(0, 1, 101, device=device))

    extras = {
        "centroid": centroid.cpu().tolist(),
        "dist_quantiles": quantiles.cpu().tolist(),
        "prop_mean": prop_tensor.mean(dim=0).cpu().tolist(),
        "prop_std": prop_tensor.std(dim=0).cpu().tolist(),
        "epochs": epochs,
        "n_resumes": int(n),
        "final_val_loss": history[-1]["val_loss"],
    }
    save_checkpoint(out_path, model, tokenizer, extras)
    print(f"[done] saved '{out_path}' ({os.path.getsize(out_path) / 1e6:.1f} MB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train the CareerLens market latent space.")
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--csv", type=str, default=CSV_PATH)
    parser.add_argument("--out", type=str, default=OUT_PATH)
    args = parser.parse_args()
    train(epochs=args.epochs, batch_size=args.batch_size, lr=args.lr, csv_path=args.csv, out_path=args.out)
