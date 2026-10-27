"""Etapa 1 - Análise léxica: texto -> lista de tokens (tipo, valor, linha, coluna).

Regras do léxico:
  * '#' inicia um comentário que vai até o fim da linha;
  * espaços e tabs separam tokens e são descartados;
  * ';' e ':' são delimitadores; '-' sozinho é o TRACO das propriedades;
  * qualquer outra sequência sem espaço é uma "palavra" e é classificada como
    ALERT (a palavra 'alert'), NUMERO (inteiro/decimal, com '-' opcional) ou IDENT.
    Se o nome tem formato estranho (ex.: '1abc', 'temp-sensor'), quem recusa é a
    análise semântica, porque o léxico só sabe separar pedaços.
  * NOVA_LINHA só é emitido para linhas que tinham algum token (linhas em branco
    e só-comentário não geram nada).
  * caracteres invisíveis/de controle (ex.: espaço de largura zero, comum ao
    copiar e colar de Word/Slack) geram erro léxico.
"""
import re
import unicodedata
from dataclasses import dataclass

from .erros import ErroLexico

ALERT = "ALERT"
IDENT = "IDENT"
NUMERO = "NUMERO"
TRACO = "TRACO"
DOIS_PONTOS = "DOIS_PONTOS"
PONTO_E_VIRGULA = "PONTO_E_VIRGULA"
NOVA_LINHA = "NOVA_LINHA"
FIM = "FIM"


@dataclass(frozen=True)
class Token:
    tipo: str
    valor: str
    linha: int
    coluna: int


_PADRAO = re.compile(r"\s+|;|:|[^\s;:#]+")
_NUMERO = re.compile(r"-?[0-9]+(\.[0-9]+)?")
_CATEGORIAS_INVALIDAS = {"Cc", "Cf", "Co", "Cn", "Cs"}


def tokenizar(texto):
    # NFC: "é" digitado como 'e' + acento (macOS) vira o caractere único.
    texto = unicodedata.normalize("NFC", texto)
    linhas = texto.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    tokens = []

    for numero_linha, linha in enumerate(linhas, start=1):
        pos = 0
        teve_token = False
        while pos < len(linha):
            if linha[pos] == "#":
                break  # comentário até o fim da linha
            m = _PADRAO.match(linha, pos)
            lexema, coluna, pos = m.group(), pos + 1, m.end()
            if lexema.isspace():
                continue

            for deslocamento, ch in enumerate(lexema):
                if unicodedata.category(ch) in _CATEGORIAS_INVALIDAS:
                    raise ErroLexico(
                        f"caractere inválido (U+{ord(ch):04X}); "
                        "provavelmente um caractere invisível copiado de outro programa",
                        numero_linha,
                        coluna + deslocamento,
                    )

            if lexema == ";":
                tipo = PONTO_E_VIRGULA
            elif lexema == ":":
                tipo = DOIS_PONTOS
            elif lexema == "-":
                tipo = TRACO
            elif lexema == "alert":
                tipo = ALERT
            elif _NUMERO.fullmatch(lexema):
                tipo = NUMERO
            else:
                tipo = IDENT
            tokens.append(Token(tipo, lexema, numero_linha, coluna))
            teve_token = True

        if teve_token:
            tokens.append(Token(NOVA_LINHA, "\n", numero_linha, len(linha) + 1))

    tokens.append(Token(FIM, "", len(linhas), 1))
    return tokens
