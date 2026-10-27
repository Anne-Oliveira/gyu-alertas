"""Etapa 5 - Geração de código: AST validada -> texto Python.

O Python gerado é autocontido (não depende do transpilador), pode ser importado
(`from alertas import ALERTAS`) e é determinístico (mesma entrada = mesma saída).

Semântica de `disparou(valor)`: True quando o valor está FORA da faixa permitida,
isto é, valor < min ou valor > max. Estar exatamente no limite NÃO dispara.
"""

_CABECALHO = '''\
# ----------------------------------------------------------------------
# ARQUIVO GERADO AUTOMATICAMENTE por gyu.py a partir de "{origem}".
# NÃO EDITE À MÃO: altere o .gyu e gere de novo.
# ----------------------------------------------------------------------
from dataclasses import dataclass
from typing import Optional, Union

Numero = Union[int, float]

__all__ = ["Alerta", "ALERTAS"]


@dataclass(frozen=True)
class Alerta:
    nome: str
    minimo: Optional[Numero] = None
    maximo: Optional[Numero] = None

    def disparou(self, valor: Numero) -> bool:
        """True se o valor saiu da faixa [minimo, maximo]."""
        if self.minimo is not None and valor < self.minimo:
            return True
        if self.maximo is not None and valor > self.maximo:
            return True
        return False


ALERTAS = [
'''


def gerar(programa, origem="<entrada>"):
    linhas = [_CABECALHO.format(origem=origem.replace('"', "'"))]
    for alerta in programa.alertas:
        argumentos = [f"nome={alerta.nome!r}"]
        for prop in alerta.propriedades:
            campo = "minimo" if prop.chave == "min" else "maximo"
            argumentos.append(f"{campo}={prop.valor!r}")
        linhas.append(f"    Alerta({', '.join(argumentos)}),\n")
    linhas.append("]\n")
    return "".join(linhas)
