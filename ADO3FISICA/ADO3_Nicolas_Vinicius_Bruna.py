"""
ADO-3 - Fisica: Praticas Extensivas
Colisoes elasticas unidimensionais (Opcao A)

Integrantes: Nicolas Morais, Vinicius Santos e Bruna Macruz
Professor: Prof. Ettore Baldini-Neto

Execucao:  python ADO3_Nicolas_Vinicius_Bruna.py

Todas as grandezas estao no SI: massa em kg, posicao em m, velocidade em m/s,
tempo em s e energia em J. Nao ha integracao numerica: as velocidades finais
saem das formulas fechadas da Secao 2 do enunciado.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.widgets import Button, RadioButtons, Slider

# =============================================================================
# 0. CONSTANTES DO "MUNDO" E DOS CONTROLES
# =============================================================================

X_INICIAL_1 = 2.0            # centro do bloco 1 no inicio (m)
X_INICIAL_2 = 8.0            # centro do bloco 2 no inicio (m)
LARGURA_BASE = 0.35          # meia-largura visual de um bloco de 1 kg (m)
ALTURA_BASE = 0.50           # altura visual de um bloco de 1 kg (m)
DT_CONTATO_PADRAO_MS = 10.0  # duracao do contato usada no caso padrao (ms)

# Limites da "pista" visivel (m) e altura util do eixo y (m).
X_MIN = 0.0
X_MAX = 10.5
Y_MAX = 1.6

# Tempo de simulacao mostrado depois do choque (s) e no caso sem colisao (s).
DURACAO_POS_CHOQUE = 1.2
TEMPO_SEM_COLISAO = 2.5

# Ritmo da animacao: cada quadro avanca DT_QUADRO segundos de simulacao.
# Com INTERVALO_MS entre quadros, a velocidade aparente e
# DT_QUADRO / (INTERVALO_MS/1000) vezes a real (aqui, 0,5x = camera lenta).
DT_QUADRO = 0.01
INTERVALO_MS = 20

# Casos da Opcao A (o bloco 2 comeca em repouso: v2 = 0).
CASOS = {
    "1 - massas iguais":        {"m1": 1.0, "m2": 1.0, "v1": 4.0, "v2": 0.0},
    "2 - projétil leve":        {"m1": 1.0, "m2": 4.0, "v1": 5.0, "v2": 0.0},
    "3 - projétil pesado":      {"m1": 4.0, "m2": 1.0, "v1": 5.0, "v2": 0.0},
}


# =============================================================================
# 1. GEOMETRIA DE CONTATO
#
# O tamanho desenhado do bloco depende da massa. Usamos a raiz cubica para
# que o "volume" aparente acompanhe a massa sem que o bloco cresca demais.
# A meia-largura e o que define o instante do choque: os centros se aproximam
# ate a distancia entre eles ser igual a soma das meias-larguras.
# =============================================================================

def meia_largura(m: float) -> float:
    """Metade da largura visual do bloco, em metros."""
    return LARGURA_BASE * float(m) ** (1.0 / 3.0)


def altura(m: float) -> float:
    """Altura visual do bloco, em metros."""
    return ALTURA_BASE * float(m) ** (1.0 / 3.0)


# =============================================================================
# 2. FISICA - FORMULAS FECHADAS
# =============================================================================

def momento(m: float, v: float) -> float:
    """Momento linear de um corpo: p = m * v  (kg*m/s)."""
    return float(m) * float(v)


def energia_cinetica(m: float, v: float) -> float:
    """Energia cinetica de um corpo: K = 1/2 * m * v^2  (J)."""
    return 0.5 * float(m) * float(v) ** 2


def momento_total(m1: float, m2: float, v1: float, v2: float) -> float:
    """Momento linear total do sistema de dois blocos."""
    return momento(m1, v1) + momento(m2, v2)


def energia_total(m1: float, m2: float, v1: float, v2: float) -> float:
    """Energia cinetica total do sistema de dois blocos."""
    return energia_cinetica(m1, v1) + energia_cinetica(m2, v2)


def colisao_elastica(m1: float, m2: float, v1: float, v2: float) -> tuple[float, float]:
    """Velocidades finais (u1, u2) de uma colisao elastica frontal.

    u1 = [(m1 - m2)*v1 + 2*m2*v2] / (m1 + m2)
    u2 = [(m2 - m1)*v2 + 2*m1*v1] / (m1 + m2)
    """
    soma = float(m1) + float(m2)
    u1 = ((m1 - m2) * v1 + 2.0 * m2 * v2) / soma
    u2 = ((m2 - m1) * v2 + 2.0 * m1 * v1) / soma
    return u1, u2


def impulso(m: float, u: float, v: float) -> float:
    """Impulso sobre um corpo: J = m*(u - v)  (N*s).

    Positivo quando o corpo ganha velocidade para a direita,
    negativo quando a perde (ou inverte o sentido).
    """
    return float(m) * (float(u) - float(v))


def forca_media(j: float, dt_s: float) -> float:
    """Modulo da forca media durante o contato: F = |J| / dt  (N)."""
    if dt_s <= 0.0:
        return float("inf")
    return abs(float(j)) / float(dt_s)


def instante_colisao(x1: float, x2: float, m1: float, m2: float,
                     v1: float, v2: float) -> float | None:
    """Instante tc em que os blocos se tocam (s), ou None se nunca se tocam.

    A folga inicial entre as superficies e
        folga = (x2 - x1) - (meia_largura(m1) + meia_largura(m2))
    e a velocidade de aproximacao e (v1 - v2). Logo tc = folga / (v1 - v2).
    So existe choque se a folga for positiva e v1 > v2.
    """
    folga = (float(x2) - float(x1)) - (meia_largura(m1) + meia_largura(m2))
    velocidade_relativa = float(v1) - float(v2)

    if folga <= 0.0:          # ja comecam encostados
        return 0.0
    if velocidade_relativa <= 0.0:  # nao se aproximam
        return None
    return folga / velocidade_relativa


# =============================================================================
# 3. RESULTADO COMPLETO DE UMA SITUACAO
# =============================================================================

@dataclass(frozen=True)
class ResultadoColisao:
    """Todas as grandezas que o painel e os graficos precisam mostrar."""

    m1: float
    m2: float
    v1: float
    v2: float
    u1: float
    u2: float
    p_antes: float
    p_depois: float
    k_antes: float
    k_depois: float
    j1: float
    j2: float
    dt_contato_s: float
    tc: float | None          # None => nao havera colisao
    colide: bool

    @property
    def delta_k(self) -> float:
        """Variacao da energia cinetica total: dK = K_depois - K_antes."""
        return self.k_depois - self.k_antes

    @property
    def f_media(self) -> float:
        """Modulo da forca media sobre o bloco 1 (N)."""
        return forca_media(self.j1, self.dt_contato_s)


def resolver_colisao(m1: float, m2: float, v1: float, v2: float,
                     dt_contato_ms: float = DT_CONTATO_PADRAO_MS,
                     x1: float = X_INICIAL_1,
                     x2: float = X_INICIAL_2) -> ResultadoColisao:
    """Aplica a formula fechada e devolve o resultado da situacao.

    Se v1 <= v2 nao existe colisao: os blocos mantem as velocidades e os
    impulsos sao nulos. Isso evita divisao por zero e erro de execucao (R5).
    """
    tc = instante_colisao(x1, x2, m1, m2, v1, v2)
    colide = tc is not None
    dt_contato_s = float(dt_contato_ms) / 1000.0

    if colide:
        u1, u2 = colisao_elastica(m1, m2, v1, v2)
        j1 = impulso(m1, u1, v1)
        j2 = impulso(m2, u2, v2)
    else:
        u1, u2 = float(v1), float(v2)
        j1 = j2 = 0.0

    return ResultadoColisao(
        m1=float(m1), m2=float(m2), v1=float(v1), v2=float(v2),
        u1=u1, u2=u2,
        p_antes=momento_total(m1, m2, v1, v2),
        p_depois=momento_total(m1, m2, u1, u2),
        k_antes=energia_total(m1, m2, v1, v2),
        k_depois=energia_total(m1, m2, u1, u2),
        j1=j1, j2=j2,
        dt_contato_s=dt_contato_s,
        tc=tc, colide=colide,
    )


# =============================================================================
# 4. CINEMATICA DA CENA
#
# Antes e depois do choque cada bloco esta em MRU. A funcao posicao() junta
# os dois trechos em uma unica expressao continua: no instante tc a posicao
# nao "salta", apenas a velocidade muda.
# =============================================================================

def posicao(t: float, x0: float, v_antes: float, v_depois: float,
            tc: float | None) -> float:
    """Posicao do centro de um bloco no instante t (MRU por partes)."""
    if tc is None or t <= tc:
        return x0 + v_antes * t
    return x0 + v_antes * tc + v_depois * (t - tc)


def posicoes(t: float, r: ResultadoColisao,
             x1_0: float = X_INICIAL_1,
             x2_0: float = X_INICIAL_2) -> tuple[float, float]:
    """Posicoes (x1, x2) dos dois centros no instante t."""
    x1 = posicao(t, x1_0, r.v1, r.u1, r.tc)
    x2 = posicao(t, x2_0, r.v2, r.u2, r.tc)
    return x1, x2


def velocidade_em(t: float, r: ResultadoColisao) -> tuple[float, float]:
    """Velocidades (v1, v2) validas no instante t."""
    if r.tc is not None and t > r.tc:
        return r.u1, r.u2
    return r.v1, r.v2


def tempo_total(r: ResultadoColisao) -> float:
    """Duracao da animacao, em segundos de simulacao."""
    if not r.colide:
        return TEMPO_SEM_COLISAO
    return r.tc + DURACAO_POS_CHOQUE


# =============================================================================
# 5. DESENHO DA CENA
# =============================================================================

COR_BLOCO_1 = "#1f77b4"
COR_BLOCO_2 = "#d62728"


def configurar_cena(ax) -> None:
    """Prepara eixos, pista e grade de um grafico da animacao."""
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(-0.70, Y_MAX)
    ax.set_xlabel("x (m)")
    ax.set_yticks([])
    ax.grid(axis="x", color="0.9", zorder=0)
    ax.axhline(0.0, color="0.35", lw=1.4, zorder=1)
    ax.set_aspect("equal", adjustable="box")


class BlocoCena:
    """Retangulo de um bloco e seus rotulos, atualizados a cada quadro."""

    def __init__(self, ax, massa: float, cor: str, rotulo: str,
                 y_velocidade: float = -0.25) -> None:
        self.largura = 2.0 * meia_largura(massa)
        self.altura = altura(massa)
        self.y_velocidade = y_velocidade

        self.retangulo = Rectangle(
            (0.0, 0.0), self.largura, self.altura,
            facecolor=cor, edgecolor="black", linewidth=1.0,
            alpha=0.85, zorder=3,
        )
        ax.add_patch(self.retangulo)

        self.texto_nome = ax.text(
            0.0, self.altura / 2.0, rotulo, ha="center", va="center",
            color="white", fontweight="bold", fontsize=11, zorder=4,
        )
        self.texto_vel = ax.text(
            0.0, y_velocidade, "", ha="center", va="center",
            fontsize=9, color="0.15", zorder=4, clip_on=True,
        )

    def atualizar(self, x: float, v: float, massa: float) -> None:
        """Move o bloco para x e atualiza largura, altura e velocidade."""
        self.largura = 2.0 * meia_largura(massa)
        self.altura = altura(massa)

        self.retangulo.set_x(x - self.largura / 2.0)
        self.retangulo.set_width(self.largura)
        self.retangulo.set_height(self.altura)

        self.texto_nome.set_position((x, self.altura / 2.0))
        self.texto_vel.set_position((x, self.y_velocidade))
        self.texto_vel.set_text(f"v = {v:+.2f} m/s")
        self.texto_vel.set_visible(X_MIN <= x <= X_MAX)

    @property
    def artistas(self) -> tuple:
        """Artistas que precisam ser redesenhados (uteis para blit)."""
        return (self.retangulo, self.texto_nome, self.texto_vel)


class CenaColisao:
    """Desenha um ResultadoColisao em um instante t. Nao controla o tempo."""

    def __init__(self, ax, resultado: ResultadoColisao) -> None:
        self.ax = ax
        self.resultado = resultado
        configurar_cena(ax)

        self.bloco1 = BlocoCena(ax, resultado.m1, COR_BLOCO_1, "1",
                                y_velocidade=-0.25)
        self.bloco2 = BlocoCena(ax, resultado.m2, COR_BLOCO_2, "2",
                                y_velocidade=-0.50)

        self.texto_tempo = ax.text(
            0.01, 0.94, "", transform=ax.transAxes,
            ha="left", va="top", fontsize=10, family="monospace",
        )
        self.texto_aviso = ax.text(
            0.5, 0.90, "", transform=ax.transAxes,
            ha="center", va="top", fontsize=11, fontweight="bold",
        )
        self.atualizar(0.0)

    def reiniciar(self, resultado: ResultadoColisao) -> None:
        """Troca a situacao fisica e volta ao instante t = 0."""
        self.resultado = resultado
        self.atualizar(0.0)

    def atualizar(self, t: float) -> None:
        """Coloca os blocos na posicao correta e atualiza os textos."""
        r = self.resultado
        x1, x2 = posicoes(t, r)
        v1, v2 = velocidade_em(t, r)

        self.bloco1.atualizar(x1, v1, r.m1)
        self.bloco2.atualizar(x2, v2, r.m2)
        self.texto_tempo.set_text(f"t = {t:5.2f} s")

        if not r.colide:
            self.texto_aviso.set_text("NÃO HÁ COLISÃO: v1 ≤ v2")
            self.texto_aviso.set_color("#b22222")
        elif abs(t - r.tc) <= 1.5 * DT_QUADRO:
            self.texto_aviso.set_text("CHOQUE")
            self.texto_aviso.set_color("#b22222")
        else:
            self.texto_aviso.set_text("")


class AnimacaoColisao:
    """Controla o relogio da simulacao e o FuncAnimation."""

    def __init__(self, fig, ax, resultado: ResultadoColisao) -> None:
        self.fig = fig
        self.ax = ax
        self.cena = CenaColisao(ax, resultado)
        self.resultado = resultado
        self.t = 0.0
        self.t_total = tempo_total(resultado)
        self.pausado = False

        self.anim = FuncAnimation(
            fig, self._proximo_quadro,
            interval=INTERVALO_MS, blit=False, cache_frame_data=False,
        )

    def _proximo_quadro(self, _frame):
        """Chamado pelo matplotlib a cada quadro."""
        if not self.pausado:
            self.t += DT_QUADRO
            if self.t >= self.t_total:   # fim: recomeca do zero
                self.t = 0.0
        self.cena.atualizar(self.t)
        return self.cena.bloco1.artistas + self.cena.bloco2.artistas

    def reiniciar(self, resultado: ResultadoColisao | None = None) -> None:
        """Volta ao inicio, opcionalmente com uma nova situacao fisica."""
        self.pausado = False
        if resultado is not None:
            self.resultado = resultado
            self.t_total = tempo_total(resultado)
            self.cena.reiniciar(resultado)
        self.t = 0.0
        self.cena.atualizar(0.0)

    def alternar_pausa(self) -> None:
        """Liga/desliga a pausa da animacao."""
        self.pausado = not self.pausado


# =============================================================================
# 6. PAINEL DE RESULTADOS E GRAFICOS DE BARRAS
# =============================================================================

POS_PAINEL = [0.685, 0.520, 0.300, 0.350]
POS_BARRA_P = [0.055, 0.325, 0.260, 0.160]
POS_BARRA_K = [0.345, 0.325, 0.260, 0.160]
POS_INFO = [0.685, 0.325, 0.300, 0.160]

COR_ANTES = "#9aa5b1"
COR_DEPOIS = "#2f6db3"


def formatar(valor: float, casas: int = 3, sinal: bool = False) -> str:
    """Formata um numero no padrao brasileiro (virgula decimal).

    Valores praticamente nulos viram zero exato, para nao exibir
    "+0,000" ou "-0,000" por causa de erro de ponto flutuante.
    """
    if abs(valor) < 0.5 * 10.0 ** (-casas):
        return f"{0.0:.{casas}f}".replace(".", ",")
    formato = f"{{:+.{casas}f}}" if sinal else f"{{:.{casas}f}}"
    return formato.format(valor).replace(".", ",")


def desenhar_barras(ax, titulo: str, unidade: str, valores: list[float],
                    delta_texto: str) -> None:
    """Duas barras (antes/depois) com o valor escrito em cima de cada uma."""
    ax.clear()

    barras = ax.bar(["antes", "depois"], valores,
                    color=[COR_ANTES, COR_DEPOIS], width=0.55, zorder=3)
    ax.axhline(0.0, color="0.35", lw=0.8, zorder=2)
    ax.set_title(f"{titulo} ({unidade})\n{delta_texto}", fontsize=8.5, pad=3)
    ax.tick_params(labelsize=8)
    ax.grid(axis="y", color="0.9", zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    maximo = max(abs(v) for v in valores)
    if maximo < 1e-9:
        maximo = 1.0
    if min(valores) < -1e-9:
        ax.set_ylim(-1.35 * maximo, 1.35 * maximo)
    else:
        ax.set_ylim(0.0, 1.35 * maximo)

    ax.bar_label(barras, labels=[formatar(v, 2) for v in valores],
                 padding=2, fontsize=8)


def desenhar_painel(ax, r: ResultadoColisao, caso: str) -> None:
    """Painel de texto com todas as grandezas do R3, em duas colunas."""
    ax.clear()
    ax.axis("off")
    ax.set_title("PAINEL DE RESULTADOS", loc="left", fontsize=9,
                 fontweight="bold", pad=6)

    esquerda = [
        caso,
        "",
        "PARÂMETROS",
        f"m1 = {formatar(r.m1, 1)} kg",
        f"m2 = {formatar(r.m2, 1)} kg",
        f"v1 = {formatar(r.v1, 2, True)} m/s",
        f"v2 = {formatar(r.v2, 2, True)} m/s",
        "",
        "ANTES",
        f"p = {formatar(r.p_antes, 3, True)} kg m/s",
        f"K = {formatar(r.k_antes, 3, True)} J",
    ]

    direita = [
        "DEPOIS",
        f"u1 = {formatar(r.u1, 2, True)} m/s",
        f"u2 = {formatar(r.u2, 2, True)} m/s",
        f"p = {formatar(r.p_depois, 3, True)} kg m/s",
        f"K = {formatar(r.k_depois, 3, True)} J",
        f"\u0394p = {formatar(r.p_depois - r.p_antes, 3, True)}",
        f"\u0394K = {formatar(r.delta_k, 3, True)} J",
        "",
        f"IMPULSO (\u0394t = {formatar(r.dt_contato_s * 1000, 0)} ms)",
        f"J1 = {formatar(r.j1, 3, True)} N s",
        f"J2 = {formatar(r.j2, 3, True)} N s",
        f"J1+J2 = {formatar(r.j1 + r.j2, 3, True)} N s",
        f"Fmed = {formatar(r.f_media, 1)} N",
    ]
    if r.tc is not None:
        direita.append(f"tc = {formatar(r.tc, 3)} s")

    for x, linhas in ((0.0, esquerda), (0.51, direita)):
        ax.text(x, 1.0, "\n".join(linhas), transform=ax.transAxes,
                ha="left", va="top", family="monospace", fontsize=8.5,
                linespacing=1.35)


def desenhar_info(ax, r: ResultadoColisao) -> None:
    """Explicacao curta da situacao atual (apoia o relatorio)."""
    ax.clear()
    ax.axis("off")
    ax.set_title("LEITURA FÍSICA", loc="left", fontsize=9,
                 fontweight="bold", pad=6)

    if not r.colide:
        linhas = [
            "NÃO HÁ COLISÃO",
            "v1 ≤ v2: o bloco 1 não alcança o bloco 2.",
            "Ajuste as velocidades para ter v1 > v2.",
        ]
        cor = "#b22222"
    else:
        linhas = [
            f"p_antes = p_depois = {formatar(r.p_antes, 3, True)} kg m/s",
            f"K_antes = K_depois = {formatar(r.k_antes, 3, True)} J",
            "J1 = -J2 (3ª lei de Newton).",
        ]
        if np.isclose(r.m1, r.m2):
            linhas.append("Massas iguais: os blocos trocam de velocidade.")
        elif r.u1 < -1e-9:
            linhas.append("m1 < m2: o bloco 1 volta (u1 < 0).")
        else:
            linhas.append("m1 > m2: o bloco 1 segue em frente (u1 > 0).")
        cor = "#1a5e1a"

    ax.text(0.0, 1.0, "\n".join(linhas), transform=ax.transAxes,
            ha="left", va="top", fontsize=8.5, color=cor, linespacing=1.45)


class PainelResultados:
    """Mantem o painel de texto e os dois graficos de barras sincronizados."""

    def __init__(self, fig: Figure, resultado: ResultadoColisao) -> None:
        self.ax_painel = fig.add_axes(POS_PAINEL)
        self.ax_barra_p = fig.add_axes(POS_BARRA_P)
        self.ax_barra_k = fig.add_axes(POS_BARRA_K)
        self.ax_info = fig.add_axes(POS_INFO)
        self.atualizar(resultado, "1 - massas iguais")

    def atualizar(self, r: ResultadoColisao, caso: str) -> None:
        desenhar_painel(self.ax_painel, r, caso)
        desenhar_barras(
            self.ax_barra_p, "Momento total", "kg m/s",
            [r.p_antes, r.p_depois],
            f"\u0394p = {formatar(r.p_depois - r.p_antes, 3)}",
        )
        desenhar_barras(
            self.ax_barra_k, "Energia cinética", "J",
            [r.k_antes, r.k_depois],
            f"\u0394K = {formatar(r.delta_k, 3)}",
        )
        desenhar_info(self.ax_info, r)


# =============================================================================
# 7. JANELA E CONTROLES
# =============================================================================

POS_ANIM = [0.045, 0.550, 0.620, 0.340]


class Controles:
    """Sliders, botoes e menu de casos. Todo controle leva ao mesmo aplicar()."""

    def __init__(self, fig: Figure, animacao: AnimacaoColisao,
                 painel: PainelResultados) -> None:
        self.fig = fig
        self.animacao = animacao
        self.painel = painel
        self.resultado = animacao.resultado
        self.caso_atual = next(iter(CASOS))
        self._atualizando = False   # evita recalcular varias vezes ao trocar de caso

        r = self.resultado
        self.slider_m1 = self._criar_slider(
            [0.055, 0.215, 0.29, 0.018], "m1 (kg)", 0.5, 6.0, r.m1, 0.1)
        self.slider_m2 = self._criar_slider(
            [0.055, 0.175, 0.29, 0.018], "m2 (kg)", 0.5, 6.0, r.m2, 0.1)
        self.slider_v1 = self._criar_slider(
            [0.055, 0.135, 0.29, 0.018], "v1 (m/s)", -5.0, 10.0, r.v1, 0.1)
        self.slider_v2 = self._criar_slider(
            [0.055, 0.095, 0.29, 0.018], "v2 (m/s)", -5.0, 10.0, r.v2, 0.1)
        self.slider_dt = self._criar_slider(
            [0.055, 0.055, 0.29, 0.018], "\u0394t (ms)", 1.0, 100.0,
            r.dt_contato_s * 1000.0, 1.0, formato="%d")

        self.ax_radio = fig.add_axes([0.395, 0.040, 0.185, 0.215])
        self.ax_radio.set_title("Caso (Opção A)", fontsize=9)
        self.radio = RadioButtons(self.ax_radio, tuple(CASOS.keys()), active=0)
        for rotulo in self.radio.labels:
            rotulo.set_fontsize(8)

        self.botao_pausar = self._criar_botao([0.600, 0.140, 0.105, 0.060],
                                              "Pausar")
        self.botao_reiniciar = self._criar_botao([0.600, 0.055, 0.105, 0.060],
                                                 "Reiniciar")

        self.slider_m1.on_changed(self._ao_mudar_slider)
        self.slider_m2.on_changed(self._ao_mudar_slider)
        self.slider_v1.on_changed(self._ao_mudar_slider)
        self.slider_v2.on_changed(self._ao_mudar_slider)
        self.slider_dt.on_changed(self._ao_mudar_slider)
        self.radio.on_clicked(self._ao_escolher_caso)
        self.botao_pausar.on_clicked(self._ao_pausar)
        self.botao_reiniciar.on_clicked(self._ao_reiniciar)

        self._atualizar_titulo()

    def _criar_slider(self, pos, rotulo, minimo, maximo, inicial, passo,
                      formato: str = "%.1f") -> Slider:
        eixo = self.fig.add_axes(pos)
        slider = Slider(eixo, rotulo, minimo, maximo, valinit=inicial,
                        valstep=passo, valfmt=formato)
        slider.label.set_fontsize(8)
        slider.valtext.set_fontsize(8)
        return slider

    def _criar_botao(self, pos, texto: str) -> Button:
        eixo = self.fig.add_axes(pos)
        botao = Button(eixo, texto)
        botao.label.set_fontsize(9)
        return botao

    def aplicar(self) -> None:
        """Le os controles, refaz a fisica e reinicia a animacao."""
        self.resultado = resolver_colisao(
            m1=self.slider_m1.val,
            m2=self.slider_m2.val,
            v1=self.slider_v1.val,
            v2=self.slider_v2.val,
            dt_contato_ms=self.slider_dt.val,
        )
        self.animacao.reiniciar(self.resultado)
        self.painel.atualizar(self.resultado, self.caso_atual)
        self._atualizar_rotulo_pausa()
        self._atualizar_titulo()
        self.fig.canvas.draw_idle()

    def _ao_mudar_slider(self, _valor: float) -> None:
        if self._atualizando:
            return
        self.caso_atual = "personalizado"
        self._limpar_destaque_radio()
        self.aplicar()

    def _limpar_destaque_radio(self) -> None:
        """Tira o destaque do menu quando os valores nao sao mais de um caso."""
        try:
            cores = self.radio._buttons.get_facecolor()
            cores[:] = (1.0, 1.0, 1.0, 0.0)
            self.radio._buttons.set_facecolor(cores)
            self.radio.value_selected = None
        except AttributeError:
            pass

    def _ao_escolher_caso(self, rotulo: str) -> None:
        if self._atualizando:
            return
        valores = CASOS[rotulo]
        self._atualizando = True
        self.slider_m1.set_val(valores["m1"])
        self.slider_m2.set_val(valores["m2"])
        self.slider_v1.set_val(valores["v1"])
        self.slider_v2.set_val(valores["v2"])
        self._atualizando = False

        self.caso_atual = rotulo
        self.aplicar()

    def _ao_pausar(self, _evento) -> None:
        self.animacao.alternar_pausa()
        self._atualizar_rotulo_pausa()
        self.fig.canvas.draw_idle()

    def _ao_reiniciar(self, _evento) -> None:
        self.animacao.reiniciar()
        self._atualizar_rotulo_pausa()
        self.fig.canvas.draw_idle()

    def _atualizar_rotulo_pausa(self) -> None:
        texto = "Continuar" if self.animacao.pausado else "Pausar"
        self.botao_pausar.label.set_text(texto)

    def _atualizar_titulo(self) -> None:
        if self.caso_atual in CASOS:
            sufixo = self.caso_atual
        else:
            sufixo = "caso personalizado"
        self.fig.suptitle(f"ADO-3 - Colisões elásticas  |  {sufixo}", fontsize=12)


def criar_janela(resultado: ResultadoColisao,
                 titulo: str = "ADO-3 - Colisões elásticas") -> tuple[Figure, AnimacaoColisao]:
    """Monta figura, eixo da animacao, cena e animacao."""
    fig = plt.figure(figsize=(13.5, 7.2))
    ax = fig.add_axes(POS_ANIM)
    fig.suptitle(titulo, fontsize=12)
    animacao = AnimacaoColisao(fig, ax, resultado)
    return fig, animacao


def criar_aplicacao(resultado: ResultadoColisao | None = None):
    """Monta a aplicacao completa (animacao + painel + controles)."""
    if resultado is None:
        resultado = resolver_colisao(**CASOS["1 - massas iguais"])
    fig, animacao = criar_janela(resultado)
    painel = PainelResultados(fig, resultado)
    controles = Controles(fig, animacao, painel)
    return fig, animacao, controles


def main() -> None:
    """Abre a janela interativa."""
    fig, animacao, controles = criar_aplicacao()
    _ = (fig, animacao, controles)   # mantem referencias vivas
    plt.show()


if __name__ == "__main__":
    main()

