"""Etapa 3 - Análise semântica: a sintaxe está certa, mas o arquivo faz sentido?

Ao contrário do parser, coleta TODOS os erros, para o PO corrigir de uma vez.

Regras:
  1. nome inválido   - letras (com/sem acento), números e '_', começando por letra
  2. nome repetido   - dois alertas com o mesmo nome
  3. chave estranha  - propriedade diferente de min e max
  4. chave repetida  - mesma propriedade duas vezes no mesmo alerta
  5. sem limites     - alerta sem min e sem max
  6. limites invertidos - min maior que max (min == max é permitido)
"""
import re

from .erros import ErroSemantico

CHAVES_VALIDAS = ("min", "max")
_NOME_VALIDO = re.compile(r"[^\W\d_]\w*")  # começa com letra; depois letra/dígito/_


def analisar(programa):
    erros = []
    declarados = {}

    for alerta in programa.alertas:
        # 1. nome inválido
        if not _NOME_VALIDO.fullmatch(alerta.nome):
            erros.append(ErroSemantico(
                f"nome de alerta inválido '{alerta.nome}': use letras (com ou sem acento), "
                "números e '_', começando por letra",
                alerta.linha))

        # 2. nome repetido
        if alerta.nome in declarados:
            erros.append(ErroSemantico(
                f"nome de alerta repetido '{alerta.nome}' (já declarado na linha {declarados[alerta.nome]})",
                alerta.linha))
        else:
            declarados[alerta.nome] = alerta.linha

        limites = {}
        tem_chave_estranha = False
        for prop in alerta.propriedades:
            # 3. chave estranha
            if prop.chave not in CHAVES_VALIDAS:
                tem_chave_estranha = True
                erros.append(ErroSemantico(
                    f"propriedade desconhecida '{prop.chave}' no alerta '{alerta.nome}' "
                    "(só existem min e max)",
                    prop.linha))
                continue
            # 4. chave repetida
            if prop.chave in limites:
                erros.append(ErroSemantico(
                    f"propriedade '{prop.chave}' repetida no alerta '{alerta.nome}' "
                    f"(já definida na linha {limites[prop.chave].linha})",
                    prop.linha))
                continue
            limites[prop.chave] = prop

        # 5. sem limites (se já há chave estranha, evita erro em cascata)
        if not limites and not tem_chave_estranha:
            erros.append(ErroSemantico(
                f"o alerta '{alerta.nome}' precisa de pelo menos um limite (min ou max)",
                alerta.linha))

        # 6. limites invertidos
        if "min" in limites and "max" in limites and limites["min"].valor > limites["max"].valor:
            erros.append(ErroSemantico(
                f"limites invertidos no alerta '{alerta.nome}': "
                f"min ({limites['min'].valor}) é maior que max ({limites['max'].valor})",
                limites["min"].linha))

    return sorted(erros, key=lambda e: e.linha)
