"""Erros do transpilador .gyu, um tipo por etapa do pipeline."""


class ErroGyu(Exception):
    etapa = "erro"

    def __init__(self, mensagem, linha=None, coluna=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna

    def formatar(self, arquivo="<entrada>"):
        local = arquivo
        if self.linha is not None:
            local += f":{self.linha}"
            if self.coluna is not None:
                local += f":{self.coluna}"
        return f"{local}: erro {self.etapa}: {self.mensagem}"


class ErroLexico(ErroGyu):
    etapa = "léxico"


class ErroSintatico(ErroGyu):
    etapa = "sintático"


class ErroSemantico(ErroGyu):
    etapa = "semântico"


class FalhaTranspilacao(Exception):
    """Agrupa um ou mais ErroGyu que impediram a geração do Python."""

    def __init__(self, erros):
        super().__init__(f"{len(erros)} erro(s)")
        self.erros = erros
