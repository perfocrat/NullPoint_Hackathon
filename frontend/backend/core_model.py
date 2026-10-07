"""
core_model.py  --  CareerLens AI latent market model
====================================================
12-Dimensional Skill-Conditional Recurrent Autoencoder (a conditional VAE).

  tokens --embedding--> [E] --concat 12 market params--> [E + 12]
        --BiLSTM encoder--> (mu, logvar) in R^128
  z (128) + 12 market params --> initial decoder state
        --forward LSTM decoder (input = [E + 12] per step)--> token logits

The "conditioning gate" widens the recurrent input channel dimension by
exactly +12 (COND_DIM) so the 12 market parameters ride along inside the
LSTM at every time-step, both in the encoder and in the decoder.

Also contains the tokenizer and checkpoint helpers, so training and the
Streamlit app are guaranteed to use identical vocabularies.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence

LATENT_DIM = 128
MAX_LEN = 100
COND_DIM = 12

PAD_TOKEN, UNK_TOKEN, BOS_TOKEN, EOS_TOKEN = "<pad>", "<unk>", "<bos>", "<eos>"
PAD_ID, UNK_ID, BOS_ID, EOS_ID = 0, 1, 2, 3


# --------------------------------------------------------------------------- #
# Tokenizer (engineering-competency vocabulary)
# --------------------------------------------------------------------------- #
_TOKEN_RE = re.compile(r"c\+\+|c#|[a-z][a-z0-9]*(?:[.+#][a-z0-9]+)*")
STOPWORDS = frozenset("""
a an the and or of to in on at for with by from as is are was were be been being this that these those
it its i me my we our you your he she they them their his her not no yes but if then than so such also
can could should would will may might must do does did done have has had having into over under about
across per via using used use within between during after before while through etc eg ie
""".split())


class SkillTokenizer:
    """Word-level tokenizer that keeps content words (stop-words are removed so the
    100 available slots are spent on competencies, not filler)."""

    def __init__(self, itos: Optional[Sequence[str]] = None) -> None:
        self.itos: List[str] = list(itos) if itos else [PAD_TOKEN, UNK_TOKEN, BOS_TOKEN, EOS_TOKEN]
        self.stoi: Dict[str, int] = {t: i for i, t in enumerate(self.itos)}

    def __len__(self) -> int:
        return len(self.itos)

    def _add(self, token: str) -> None:
        if token not in self.stoi:
            self.stoi[token] = len(self.itos)
            self.itos.append(token)

    @staticmethod
    def tokenize(text: str) -> List[str]:
        tokens = _TOKEN_RE.findall((text or "").lower())
        return [t for t in tokens if t not in STOPWORDS and len(t) > 1]

    @classmethod
    def build(cls, texts: Iterable[str], max_vocab: int = 8000, min_freq: int = 3,
              seed_tokens: Iterable[str] = ()) -> "SkillTokenizer":
        counter: Counter = Counter()
        for text in texts:
            counter.update(cls.tokenize(text))
        tokenizer = cls()
        for token in seed_tokens:  # guarantee that the 21 master skills are in-vocabulary
            tokenizer._add(token.lower())
        for token, count in counter.most_common():
            if len(tokenizer.itos) >= max_vocab or count < min_freq:
                break
            tokenizer._add(token)
        return tokenizer

    def encode(self, text: str, max_len: int = MAX_LEN) -> List[int]:
        ids = [self.stoi.get(t, UNK_ID) for t in self.tokenize(text)]
        ids = [BOS_ID] + ids[: max_len - 2] + [EOS_ID]
        return ids + [PAD_ID] * (max_len - len(ids))

    def decode(self, ids: Iterable[int]) -> str:
        words = []
        for i in ids:
            i = int(i)
            if i == EOS_ID:
                break
            if i in (PAD_ID, BOS_ID):
                continue
            words.append(self.itos[i] if 0 <= i < len(self.itos) else UNK_TOKEN)
        return " ".join(words)


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
class ConditionalEmployabilityVAE(nn.Module):
    def __init__(self, vocab_size: int, embed_dim: int = 128, hidden_dim: int = 256,
                 latent_dim: int = LATENT_DIM, cond_dim: int = COND_DIM, max_len: int = MAX_LEN,
                 num_layers: int = 1, dropout: float = 0.2, pad_id: int = PAD_ID) -> None:
        super().__init__()
        self.vocab_size, self.embed_dim, self.hidden_dim = vocab_size, embed_dim, hidden_dim
        self.latent_dim, self.cond_dim, self.max_len = latent_dim, cond_dim, max_len
        self.num_layers, self.pad_id = num_layers, pad_id

        # Conditioning gate: recurrent input channels = embed_dim + 12
        self.gated_input_dim = embed_dim + cond_dim

        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_id)
        self.embed_dropout = nn.Dropout(dropout)

        # Bidirectional LSTM encoder
        self.encoder = nn.LSTM(self.gated_input_dim, hidden_dim, num_layers=num_layers,
                               batch_first=True, bidirectional=True)
        # Linear Gaussian bottleneck
        self.fc_mu = nn.Linear(hidden_dim * 2, latent_dim)
        self.fc_logvar = nn.Linear(hidden_dim * 2, latent_dim)

        # Latent (+ conditions) -> initial decoder state
        self.latent_to_h = nn.Linear(latent_dim + cond_dim, hidden_dim * num_layers)
        self.latent_to_c = nn.Linear(latent_dim + cond_dim, hidden_dim * num_layers)

        # Forward LSTM decoder
        self.decoder = nn.LSTM(self.gated_input_dim, hidden_dim, num_layers=num_layers, batch_first=True)
        self.out = nn.Linear(hidden_dim, vocab_size)

    # -- helpers ------------------------------------------------------------ #
    def _condition(self, emb: torch.Tensor, cond: torch.Tensor) -> torch.Tensor:
        """Concatenate the 12 market parameters to every time-step: [B,T,E] -> [B,T,E+12]."""
        cond_seq = cond.unsqueeze(1).expand(-1, emb.size(1), -1)
        return torch.cat([emb, cond_seq], dim=-1)

    def _init_state(self, z: torch.Tensor, cond: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        zc = torch.cat([z, cond], dim=-1)
        b = zc.size(0)
        h0 = torch.tanh(self.latent_to_h(zc)).view(b, self.num_layers, self.hidden_dim).transpose(0, 1).contiguous()
        c0 = torch.tanh(self.latent_to_c(zc)).view(b, self.num_layers, self.hidden_dim).transpose(0, 1).contiguous()
        return h0, c0

    # -- encoder / decoder -------------------------------------------------- #
    def encode(self, x: torch.Tensor, cond: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        emb = self.embed_dropout(self.embedding(x))
        enc_in = self._condition(emb, cond)
        lengths = (x != self.pad_id).sum(dim=1).clamp(min=1).cpu()
        packed = pack_padded_sequence(enc_in, lengths, batch_first=True, enforce_sorted=False)
        _, (h_n, _) = self.encoder(packed)
        h = torch.cat([h_n[-2], h_n[-1]], dim=1)  # last layer: forward + backward
        return self.fc_mu(h), self.fc_logvar(h)

    @staticmethod
    def reparameterize(mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        std = torch.exp(0.5 * logvar)
        return mu + torch.randn_like(std) * std

    def decode(self, z: torch.Tensor, cond: torch.Tensor, dec_in: torch.Tensor) -> torch.Tensor:
        emb = self.embed_dropout(self.embedding(dec_in))
        out, _ = self.decoder(self._condition(emb, cond), self._init_state(z, cond))
        return self.out(out)

    def forward(self, x: torch.Tensor, cond: torch.Tensor, word_dropout: float = 0.0):
        mu, logvar = self.encode(x, cond)
        z = self.reparameterize(mu, logvar)
        dec_in = x[:, :-1]
        if self.training and word_dropout > 0.0:  # weakens the decoder -> avoids posterior collapse
            drop = (torch.rand_like(dec_in, dtype=torch.float32) < word_dropout) & (dec_in != self.pad_id) & (dec_in != BOS_ID)
            dec_in = torch.where(drop, torch.full_like(dec_in, UNK_ID), dec_in)
        logits = self.decode(z, cond, dec_in)
        return logits, mu, logvar

    @staticmethod
    def loss_function(logits: torch.Tensor, x: torch.Tensor, mu: torch.Tensor, logvar: torch.Tensor,
                      beta: float = 1.0, pad_id: int = PAD_ID):
        targets = x[:, 1:]
        batch = x.size(0)
        recon = F.cross_entropy(logits.reshape(-1, logits.size(-1)), targets.reshape(-1),
                                ignore_index=pad_id, reduction="sum") / batch
        kl = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp()) / batch
        return recon + beta * kl, recon, kl

    @torch.no_grad()
    def embed(self, x: torch.Tensor, cond: torch.Tensor) -> torch.Tensor:
        """Deterministic latent code (the posterior mean)."""
        self.eval()
        return self.encode(x, cond)[0]

    @torch.no_grad()
    def generate(self, z: torch.Tensor, cond: torch.Tensor, max_len: Optional[int] = None,
                 greedy: bool = True, temperature: float = 1.0) -> torch.Tensor:
        self.eval()
        max_len = max_len or self.max_len
        state = self._init_state(z, cond)
        tokens = torch.full((z.size(0), 1), BOS_ID, dtype=torch.long, device=z.device)
        for _ in range(max_len - 1):
            emb = self.embedding(tokens[:, -1:])
            out, state = self.decoder(self._condition(emb, cond), state)
            logits = self.out(out[:, -1]) / max(temperature, 1e-6)
            nxt = logits.argmax(-1, keepdim=True) if greedy else torch.multinomial(F.softmax(logits, -1), 1)
            tokens = torch.cat([tokens, nxt], dim=1)
        return tokens


# --------------------------------------------------------------------------- #
# Checkpoint helpers (everything is stored as tensors / primitives so that
# torch.load(..., weights_only=True) works)
# --------------------------------------------------------------------------- #
def save_checkpoint(path: str, model: ConditionalEmployabilityVAE, tokenizer: SkillTokenizer,
                    extras: Dict[str, Any]) -> None:
    torch.save({
        "config": {
            "vocab_size": model.vocab_size, "embed_dim": model.embed_dim, "hidden_dim": model.hidden_dim,
            "latent_dim": model.latent_dim, "cond_dim": model.cond_dim, "max_len": model.max_len,
            "num_layers": model.num_layers,
        },
        "state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
        "vocab": list(tokenizer.itos),
        "extras": extras,
    }, path)


def load_checkpoint(path: str, device: torch.device):
    ckpt = torch.load(path, map_location=device, weights_only=True)
    model = ConditionalEmployabilityVAE(**ckpt["config"]).to(device)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    return model, SkillTokenizer(ckpt["vocab"]), ckpt.get("extras", {})


@torch.no_grad()
def latent_alignment(model: ConditionalEmployabilityVAE, tokenizer: SkillTokenizer, text: str,
                     cond_vec: Sequence[float], extras: Dict[str, Any], device: torch.device) -> Dict[str, float]:
    """Where does this resume sit in the learned market latent space?
    typicality_pct = % of the training corpus that lies FARTHER from the market
    centroid than this resume (higher = more typical of the market corpus)."""
    model.eval()
    x = torch.tensor([tokenizer.encode(text, model.max_len)], dtype=torch.long, device=device)
    c = torch.tensor([list(cond_vec)], dtype=torch.float32, device=device)
    mu = model.encode(x, c)[0][0]
    centroid = torch.tensor(extras["centroid"], dtype=torch.float32, device=device)
    distance = torch.linalg.norm(mu - centroid).item()
    quantiles = np.asarray(extras["dist_quantiles"], dtype=np.float64)
    rank = float(np.interp(distance, quantiles, np.linspace(0.0, 100.0, len(quantiles))))
    return {"distance": distance, "typicality_pct": 100.0 - rank,
            "median_distance": float(quantiles[len(quantiles) // 2])}
