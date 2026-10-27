"""Etapa 2 - Análise sintática: tokens -> AST (descida recursiva).

Gramática (EBNF):

    programa    = { alerta } FIM ;
    alerta      = ALERT nome ";" NOVA_LINHA { propriedade } ;
    propriedade = "-" chave ":" NUMERO ( NOVA_LINHA | FIM ) ;
    nome        = IDENT | NUMERO ;     (formato do nome é checado na semântica)
    chave       = IDENT ;              (min/max é checado na semântica)

O parser só olha a *forma* do arquivo e para no primeiro erro de sintaxe.
"""
import math

from .arvore import Alerta, Programa, Propriedade
from .erros import ErroSintatico
from .tokenizador import (ALERT, DOIS_PONTOS, FIM, IDENT, NOVA_LINHA, NUMERO,
                          PONTO_E_VIRGULA, TRACO)


def _descrever(token):
    if token.tipo == NOVA_LINHA:
        return "o fim da linha"
    if token.tipo == FIM:
        return "o fim do arquivo"
    return f"'{token.valor}'"


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    @property
    def atual(self):
        return self.tokens[self.i]

    def avancar(self):
        token = self.tokens[self.i]
        if token.tipo != FIM:
            self.i += 1
        return token

    def erro(self, mensagem, token=None):
        token = token or self.atual
        return ErroSintatico(mensagem, token.linha, token.coluna)

    # programa = { alerta } FIM
    def programa(self):
        alertas = []
        while self.atual.tipo != FIM:
            alertas.append(self.alerta())
        return Programa(alertas)

    # alerta = ALERT nome ";" NOVA_LINHA { propriedade }
    def alerta(self):
        inicio = self.atual
        if inicio.tipo == TRACO:
            raise self.erro("propriedade fora de um alerta: declare antes 'alert nome;'")
        if inicio.tipo != ALERT:
            raise self.erro(f"esperado 'alert', encontrado {_descrever(inicio)}")
        self.avancar()

        nome = self.atual
        if nome.tipo in (PONTO_E_VIRGULA, NOVA_LINHA, FIM):
            raise self.erro("'alert' precisa de um nome (ex.: alert temperatura_sensor;)")
        if nome.tipo not in (IDENT, NUMERO):
            raise self.erro(f"nome de alerta inesperado: {_descrever(nome)}")
        self.avancar()

        if self.atual.tipo != PONTO_E_VIRGULA:
            if self.atual.tipo in (IDENT, NUMERO, ALERT):
                raise self.erro(
                    f"nome de alerta não pode ter espaços "
                    f"(encontrado {_descrever(self.atual)} depois de '{nome.valor}'); use '_'"
                )
            raise self.erro(f"falta ';' depois do nome '{nome.valor}'")
        self.avancar()

        if self.atual.tipo == NOVA_LINHA:
            self.avancar()
        elif self.atual.tipo != FIM:
            raise self.erro(
                f"depois de ';' a linha deve terminar; "
                f"as propriedades vão nas linhas seguintes (encontrado {_descrever(self.atual)})"
            )

        propriedades = []
        while self.atual.tipo == TRACO:
            propriedades.append(self.propriedade())
        return Alerta(nome.valor, inicio.linha, propriedades)

    # propriedade = "-" chave ":" NUMERO ( NOVA_LINHA | FIM )
    def propriedade(self):
        self.avancar()  # TRACO

        chave = self.atual
        if chave.tipo != IDENT:
            raise self.erro(f"esperado o nome da propriedade depois de '-', encontrado {_descrever(chave)}")
        self.avancar()

        if self.atual.tipo != DOIS_PONTOS:
            raise self.erro(f"esperado ':' depois de '{chave.valor}', encontrado {_descrever(self.atual)}")
        self.avancar()

        valor = self.atual
        if valor.tipo != NUMERO:
            raise self.erro(
                f"esperado um número (inteiro ou decimal) para '{chave.valor}', "
                f"encontrado {_descrever(valor)}"
            )
        self.avancar()
        numero = float(valor.valor) if "." in valor.valor else int(valor.valor)
        if isinstance(numero, float) and not math.isfinite(numero):
            raise self.erro(f"número grande demais: '{valor.valor[:20]}...'", valor)

        if self.atual.tipo == NOVA_LINHA:
            self.avancar()
        elif self.atual.tipo != FIM:
            raise self.erro(
                f"cada propriedade deve ficar na sua própria linha (encontrado {_descrever(self.atual)})"
            )
        return Propriedade(chave.valor, numero, chave.linha)


def parse(tokens):
    return _Parser(tokens).programa()
