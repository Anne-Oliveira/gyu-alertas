"""Gera docs/arquitetura.png (requer matplotlib).  python docs/gerar_diagrama.py"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

AZUL, ESCURO, ROSA, VERDE, CINZA = "#0B62C4", "#1F2A44", "#E8185C", "#2E9E6B", "#EEF1F5"

fig, ax = plt.subplots(figsize=(16, 9.2))
ax.set_xlim(0, 16); ax.set_ylim(0, 9.2); ax.axis("off")


def caixa(x, y, w, h, titulo, texto, cor, num=None, txt="white"):
    ax.add_patch(FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.02,rounding_size=0.15",
                                fc=cor, ec="none"))
    ax.text(x, y + h/2 - 0.3, (f"{num}  " if num else "") + titulo, ha="center", va="center",
            color=txt, fontsize=12, fontweight="bold")
    ax.text(x, y - 0.18, texto, ha="center", va="center", color=txt, fontsize=9.2, linespacing=1.45)


def seta(x1, y1, x2, y2, cor=ESCURO, estilo="-", rotulo=None, rx=0, ry=0.22):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=cor, lw=2, linestyle=estilo, shrinkA=0, shrinkB=0))
    if rotulo:
        ax.text((x1+x2)/2 + rx, (y1+y2)/2 + ry, rotulo, ha="center", color=cor, fontsize=10, fontweight="bold")


ax.text(0.4, 8.85, "Arquitetura: do .gyu escrito pelo PO até o serviço de alertas em produção",
        fontsize=16, fontweight="bold", color=ESCURO, va="center")

W, H = 3.0, 1.9
# linha A: edição -> repositório -> CI -> decisão
yA = 5.5
caixa(2.0, yA, W, H, "Edição", "PO edita alertas/alertas.gyu\nno editor web do GitHub\n(sem instalar nada) e abre\num Pull Request", ESCURO, "1")
caixa(5.8, yA, W, H, "Repositório Git", "Fonte da verdade, com histórico\nde quem mudou o quê e quando.\nBranch main protegida", AZUL, "2")
caixa(9.6, yA, W, H, "Validação (CI)", "A cada commit no PR:\ngyu.py: léxico, sintaxe e semântica\n+ testes automatizados", AZUL, "3")
# losango
cx, cy = 13.5, yA
ax.add_patch(Polygon([(cx, cy+1.05), (cx+1.35, cy), (cx, cy-1.05), (cx-1.35, cy)], fc=ROSA, ec="none"))
ax.text(cx, cy, "Arquivo\nválido?", ha="center", va="center", color="white", fontsize=11.5, fontweight="bold")
seta(2.0+W/2, yA, 5.8-W/2, yA); seta(5.8+W/2, yA, 9.6-W/2, yA); seta(9.6+W/2, yA, cx-1.35, yA)

# falha: feedback
yF = 7.85
caixa(9.6, yF, 7.0, 1.3, "Feedback ao PO (falhou)",
      "Check vermelho no PR + mensagem com arquivo:linha\n(ex.: alertas.gyu:6: nome de alerta repetido) + comentário\nautomático no PR + aviso por Slack/e-mail. Merge bloqueado.", ROSA, "4a")
ax.plot([cx, cx], [cy+1.05, yF], color=ROSA, lw=2)
ax.text(cx+0.2, (cy+1.05+yF)/2, "não", color=ROSA, fontsize=10, fontweight="bold")
seta(cx, yF, 9.6+3.5, yF, ROSA)
seta(9.6-3.5, yF, 2.0, yF, ROSA, "--")
seta(2.0, yF, 2.0, yA+H/2, ROSA, "--", "PO corrige e faz novo commit", rx=1.55, ry=0.45)
ax.text(5.0, yF+0.25, "", fontsize=1)

# sucesso: linha B (da direita para a esquerda)
yB = 2.5
seta(cx, cy-1.05, cx, yB+H/2, VERDE, rotulo="sim", rx=0.35, ry=0)
caixa(13.5, yB, W, H, "Aprovação e merge", "Pull Request aprovado\n(ex.: um dev ou o líder\ndo PO) e mergeado na main", VERDE, "4b")
caixa(9.6, yB, W, H, "Geração e build (CD)", "Na main: gyu.py gera alertas.py\n+ smoke test (import ALERTAS).\nArtefato identificado pelo commit", AZUL, "5")
caixa(5.8, yB, W, H, "Implantação", "Nova versão do serviço sobe\n(rolling). Rollback = reverter\no commit e rodar de novo", AZUL, "6")
caixa(2.0, yB, W, H, "Produção", "Serviço de alertas já existente\nimporta ALERTAS do alertas.py\ne passa a usar os novos limites", ESCURO, "7")
seta(13.5-W/2, yB, 9.6+W/2, yB); seta(9.6-W/2, yB, 5.8+W/2, yB); seta(5.8-W/2, yB, 2.0+W/2, yB)

ax.add_patch(FancyBboxPatch((0.4, 0.25), 15.2, 0.8, boxstyle="round,pad=0.02,rounding_size=0.12", fc=CINZA, ec="none"))
ax.text(8.0, 0.65, "O alertas.py é artefato de build (não é versionado nem editado à mão): a fonte da verdade é sempre o .gyu.\n"
        "Só chega à produção o que passou pelo mesmo transpilador e pelos mesmos testes.",
        ha="center", va="center", fontsize=10, color=ESCURO)

os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "arquitetura.png"), dpi=130,
            bbox_inches="tight", facecolor="white")
