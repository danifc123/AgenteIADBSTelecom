"""Carregamento do catálogo estático de planos — camada integrations.

Regra de negócio: a IXC guarda o plano contratado por cliente, mas não um
catálogo de marketing com descrições/condições comerciais — por isso o
catálogo do fluxo Comercial vem de um arquivo estático (`data/plans.json`),
não de uma consulta à IXC.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_PLANS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "plans.json"

# region Loader


@lru_cache
def load_plans() -> dict:
    """Carrega e cacheia o catálogo de planos a partir de `data/plans.json`. Retorna o dicionário do catálogo."""
    with _PLANS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


# endregion
