#!/usr/bin/env python3
"""CLI do transpilador .gyu -> Python.

    python gyu.py entrada.gyu -o saida.py

Códigos de saída: 0 = ok, 1 = arquivo .gyu inválido, 2 = problema de uso/leitura.
Se houver qualquer erro, NENHUM arquivo de saída é escrito.
"""
import argparse
import os
import sys

from transpilador.arvore import descrever
from transpilador.erros import ErroGyu
from transpilador.gerador import gerar
from transpilador.parser import parse
from transpilador.semantica import analisar
from transpilador.tokenizador import tokenizar


def main(argv=None):
    ap = argparse.ArgumentParser(prog="gyu.py", description="Transpila arquivos .gyu (alertas) para Python.")
    ap.add_argument("entrada", help="arquivo .gyu de entrada")
    ap.add_argument("-o", "--saida", help="arquivo .py de saída (padrão: mesmo nome da entrada, com .py)")
    ap.add_argument("--tokens", action="store_true", help="mostra os tokens (etapa 1) e continua")
    ap.add_argument("--ast", action="store_true", help="mostra a AST (etapa 2) e continua")
    args = ap.parse_args(argv)

    nome_arquivo = os.path.basename(args.entrada)
    try:
        with open(args.entrada, encoding="utf-8-sig") as f:
            texto = f.read()
    except OSError as e:
        print(f"gyu: não foi possível ler '{args.entrada}': {e.strerror}", file=sys.stderr)
        return 2
    except UnicodeDecodeError:
        print(f"gyu: '{args.entrada}' não está em UTF-8", file=sys.stderr)
        return 2

    try:
        tokens = tokenizar(texto)                      # 1. léxico
        if args.tokens:
            for t in tokens:
                print(f"{t.linha:>3}:{t.coluna:<3} {t.tipo:<16} {t.valor!r}")
        programa = parse(tokens)                       # 2. sintaxe
        if args.ast:
            print(descrever(programa))
    except ErroGyu as erro:
        print(erro.formatar(nome_arquivo), file=sys.stderr)
        print("1 erro. Nenhum arquivo gerado.", file=sys.stderr)
        return 1

    erros = analisar(programa)                         # 3. semântica
    if erros:
        for erro in erros:
            print(erro.formatar(nome_arquivo), file=sys.stderr)
        print(f"{len(erros)} erro(s). Nenhum arquivo gerado.", file=sys.stderr)
        return 1

    codigo = gerar(programa, nome_arquivo)             # 4/5. geração
    saida = args.saida or os.path.splitext(args.entrada)[0] + ".py"
    with open(saida, "w", encoding="utf-8", newline="\n") as f:
        f.write(codigo)
    print(f"OK: {len(programa.alertas)} alerta(s) gerado(s) em {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
