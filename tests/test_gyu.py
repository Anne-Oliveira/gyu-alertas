"""Testes do transpilador .gyu.  Rodar:  python -m unittest discover -s tests -v"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from transpilador import transpilar                                # noqa: E402
from transpilador.erros import ErroLexico, ErroSintatico, FalhaTranspilacao  # noqa: E402
from transpilador.parser import parse                              # noqa: E402
from transpilador.semantica import analisar                        # noqa: E402
from transpilador.tokenizador import (ALERT, DOIS_PONTOS, FIM, IDENT, NOVA_LINHA,  # noqa: E402
                                      NUMERO, PONTO_E_VIRGULA, TRACO, tokenizar)


def erros_de(texto):
    """Mensagens de erro (de qualquer etapa) para um texto .gyu."""
    with unittest.TestCase().assertRaises(FalhaTranspilacao) as ctx:
        transpilar(texto)
    return [e.mensagem for e in ctx.exception.erros]


def carregar_modulo(codigo):
    with tempfile.TemporaryDirectory() as pasta:
        caminho = os.path.join(pasta, "alertas.py")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(codigo)
        spec = importlib.util.spec_from_file_location("alertas", caminho)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
        return modulo


class TestTokenizador(unittest.TestCase):
    def test_tipos_e_linhas(self):
        tipos = [(t.tipo, t.valor, t.linha) for t in tokenizar("alert a;\n- min: -3.5\n")]
        self.assertEqual(tipos, [
            (ALERT, "alert", 1), (IDENT, "a", 1), (PONTO_E_VIRGULA, ";", 1), (NOVA_LINHA, "\n", 1),
            (TRACO, "-", 2), (IDENT, "min", 2), (DOIS_PONTOS, ":", 2), (NUMERO, "-3.5", 2),
            (NOVA_LINHA, "\n", 2), (FIM, "", 3),
        ])

    def test_comentarios_e_linhas_em_branco_sao_ignorados(self):
        tokens = tokenizar("# oi\n\n   \nalert a; # fim\n")
        self.assertEqual([t.tipo for t in tokens], [ALERT, IDENT, PONTO_E_VIRGULA, NOVA_LINHA, FIM])

    def test_caractere_invisivel_e_erro_lexico(self):
        with self.assertRaises(ErroLexico):
            tokenizar("alert a\u200b;\n")


class TestParser(unittest.TestCase):
    def test_ast(self):
        prog = parse(tokenizar("alert a;\n- min: 1\n- max: 2.5\nalert b;\n- max: 3\n"))
        self.assertEqual([a.nome for a in prog.alertas], ["a", "b"])
        self.assertEqual([(p.chave, p.valor) for p in prog.alertas[0].propriedades], [("min", 1), ("max", 2.5)])

    def test_erros_de_sintaxe(self):
        casos = {
            "alert;\n- max: 1\n": "precisa de um nome",
            "alert meu alerta;\n- max: 1\n": "espaços",
            "alert a\n- max: 1\n": "falta ';'",
            "alert a;\n- max:\n": "esperado um número",
            "alert a;\n- max: abc\n": "esperado um número",
            "alert a;\n- max 5\n": "esperado ':'",
            "alert a;\n- min: 1 - max: 2\n": "própria linha",
            "alert a; - max: 1\n": "linha deve terminar",
            "- max: 1\n": "fora de um alerta",
            "Alert a;\n": "esperado 'alert'",
        }
        for texto, trecho in casos.items():
            with self.subTest(texto=texto):
                with self.assertRaises(ErroSintatico) as ctx:
                    parse(tokenizar(texto))
                self.assertIn(trecho, ctx.exception.mensagem)


class TestSemantica(unittest.TestCase):
    def test_seis_regras(self):
        casos = {
            "alert 1abc;\n- max: 1\n": "nome de alerta inválido",
            "alert temp-sensor;\n- max: 1\n": "nome de alerta inválido",
            "alert a;\n- max: 1\nalert a;\n- max: 2\n": "repetido",
            "alert a;\n- media: 1\n": "propriedade desconhecida",
            "alert a;\n- max: 1\n- max: 2\n": "repetida",
            "alert a;\n": "pelo menos um limite",
            "alert a;\n- min: 5\n- max: 1\n": "invertidos",
        }
        for texto, trecho in casos.items():
            with self.subTest(texto=texto):
                self.assertTrue(any(trecho in m for m in erros_de(texto)), erros_de(texto))

    def test_min_igual_a_max_e_permitido(self):
        transpilar("alert a;\n- min: 5\n- max: 5\n")

    def test_acumula_varios_erros(self):
        self.assertGreaterEqual(len(erros_de("alert a;\n- foo: 1\nalert a;\n")), 2)

    def test_nome_com_acento_e_valido(self):
        transpilar("alert pressão_câmara2;\n- min: 1\n")

    def test_acento_decomposto_e_normalizado(self):
        transpilar("alert pressa\u0303o;\n- min: 1\n")  # 'a' + til combinante


class TestGerador(unittest.TestCase):
    def test_exemplo_do_enunciado(self):
        modulo = carregar_modulo(transpilar("alert temperatura_do_forno;\n- max: 90\n"))
        alerta = modulo.ALERTAS[0]
        self.assertEqual(alerta.nome, "temperatura_do_forno")
        self.assertIs(alerta.disparou(95), True)
        self.assertIs(alerta.disparou(50), False)

    def test_faixa_min_max_e_bordas(self):
        alerta = carregar_modulo(transpilar("alert t;\n- min: 10\n- max: 80\n")).ALERTAS[0]
        self.assertTrue(alerta.disparou(9.9))
        self.assertTrue(alerta.disparou(80.1))
        self.assertFalse(alerta.disparou(10))
        self.assertFalse(alerta.disparou(80))
        self.assertFalse(alerta.disparou(45))

    def test_somente_min_e_negativos(self):
        alerta = carregar_modulo(transpilar("alert t;\n- min: -2.5\n")).ALERTAS[0]
        self.assertTrue(alerta.disparou(-3))
        self.assertFalse(alerta.disparou(1000))

    def test_deterministico(self):
        texto = "alert a;\n- max: 1\n"
        self.assertEqual(transpilar(texto, "x.gyu"), transpilar(texto, "x.gyu"))


class TestExemplosECli(unittest.TestCase):
    def _gyu(self, *args):
        return subprocess.run([sys.executable, os.path.join(RAIZ, "gyu.py"), *args],
                              capture_output=True, text=True, encoding="utf-8")

    def test_exemplos_validos(self):
        pasta = os.path.join(RAIZ, "exemplos")
        validos = sorted(f for f in os.listdir(pasta) if f.startswith("valido_"))
        self.assertEqual(len(validos), 3)
        for nome in validos:
            with self.subTest(nome), tempfile.TemporaryDirectory() as tmp:
                saida = os.path.join(tmp, "saida.py")
                r = self._gyu(os.path.join(pasta, nome), "-o", saida)
                self.assertEqual(r.returncode, 0, r.stderr)
                with open(saida, encoding="utf-8") as f:
                    self.assertTrue(carregar_modulo(f.read()).ALERTAS)

    def test_exemplos_invalidos(self):
        pasta = os.path.join(RAIZ, "exemplos")
        esperado = {"invalido_1_nome_repetido.gyu": "repetido",
                    "invalido_2_chave_estranha.gyu": "desconhecida",
                    "invalido_3_limites_invertidos.gyu": "invertidos"}
        for nome, trecho in esperado.items():
            with self.subTest(nome), tempfile.TemporaryDirectory() as tmp:
                saida = os.path.join(tmp, "saida.py")
                r = self._gyu(os.path.join(pasta, nome), "-o", saida)
                self.assertEqual(r.returncode, 1)
                self.assertIn(trecho, r.stderr)
                self.assertFalse(os.path.exists(saida), "não deve gerar arquivo quando há erro")

    def test_arquivo_inexistente(self):
        self.assertEqual(self._gyu("nao_existe.gyu").returncode, 2)


if __name__ == "__main__":
    unittest.main()
