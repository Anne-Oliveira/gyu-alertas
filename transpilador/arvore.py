"""Nós da AST (árvore sintática abstrata) da linguagem .gyu."""
from dataclasses import dataclass, field
from typing import List, Union


@dataclass
class Propriedade:
    chave: str
    valor: Union[int, float]
    linha: int


@dataclass
class Alerta:
    nome: str
    linha: int
    propriedades: List[Propriedade] = field(default_factory=list)


@dataclass
class Programa:
    alertas: List[Alerta] = field(default_factory=list)


def descrever(programa):
    """Texto legível da AST (usado por `gyu.py --ast`)."""
    linhas = ["Programa"]
    for a in programa.alertas:
        linhas.append(f"  Alerta nome={a.nome!r} (linha {a.linha})")
        for p in a.propriedades:
            linhas.append(f"    Propriedade {p.chave} = {p.valor!r} (linha {p.linha})")
    return "\n".join(linhas)
