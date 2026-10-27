"""Transpilador .gyu -> Python.

Pipeline: tokenizador -> parser -> semantica -> gerador
"""
from .erros import ErroGyu, FalhaTranspilacao
from .gerador import gerar
from .parser import parse
from .semantica import analisar
from .tokenizador import tokenizar


def transpilar(texto, origem="<entrada>"):
    """Roda o pipeline completo. Levanta FalhaTranspilacao se houver erros."""
    try:
        tokens = tokenizar(texto)
        programa = parse(tokens)
    except ErroGyu as erro:  # léxico/sintático: para no primeiro
        raise FalhaTranspilacao([erro]) from erro
    erros = analisar(programa)  # semântico: acumula todos
    if erros:
        raise FalhaTranspilacao(erros)
    return gerar(programa, origem)
