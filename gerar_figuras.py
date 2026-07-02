# -*- coding: utf-8 -*-
"""
gerar_figuras.py

Gera as tres figuras do artigo (ano de 2025) a partir dos mesmos dados e do mesmo
classificador do pipeline, de forma reproduzivel:

  fig_setor.png  composicao setorial das organizacoes (Estado, Mercado, Terceiro
                 setor, Indefinido)
  fig_dist.png   distribuicao de participacoes por organizacao (log-log): numero
                 de eventos em que cada organizacao aparece
  fig_div.png    diversidade setorial por evento: numero de setores distintos por
                 evento, excluindo Indefinido (mesma definicao do multissetorial)

O script re-extrai a rede de 2025 (une eventos-*.json, deduplica, bina por ano,
extrai organizacoes e classifica por gazetteer) e AUTO-VALIDA os agregados
(n_nos, composicao, n_multiorg, n_multissetor) contra resultados_multiano.json
antes de plotar: se algo divergir, aborta em vez de gerar figura inconsistente.

ENTRADAS: eventos-*.json (mesmos do pipeline) e resultados_multiano.json (validacao).
SAIDA:    fig_setor.png, fig_dist.png, fig_div.png
USO:      python3 gerar_figuras.py
"""
import json, glob, os, sys
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import extracao_camara as ec

ANO = "2025"
CROSSWALK = {}


def canon(display):
    k = ec.norm(display)
    return CROSSWALK.get(k, k)


def is_alvo(e):
    cod = str(e.get("codTipoEvento") or e.get("idTipoEvento") or "")
    tt = (e.get("descricaoTipo") or "").lower()
    return cod in ec.TIPOS_ALVO or any(
        k in tt for k in ["audiência", "audiencia", "debate", "comissão geral", "comissao geral"])


def carrega_ano(ano):
    eventos_por_ano = defaultdict(list); vistos = set()
    for f in sorted(glob.glob("eventos-*.json")):
        d = json.load(open(f, encoding="utf-8"))
        for e in (d.get("dados", d) if isinstance(d, dict) else d):
            i = e.get("id")
            if i in vistos:
                continue
            vistos.add(i)
            dh = e.get("dataHoraInicio") or ""
            if len(dh) >= 4:
                eventos_por_ano[dh[:4]].append(e)
    return eventos_por_ano.get(ano, [])


def extrai(eventos):
    ev_orgs, canon_display, org_freq = {}, {}, Counter()
    for e in [e for e in eventos if is_alvo(e)]:
        ks = []
        for o in ec.extrair(e.get("descricao")):
            k = canon(o); canon_display.setdefault(k, o); ks.append(k)
        ks = sorted(set(ks))
        if ks:
            ev_orgs[e.get("id")] = ks
            for k in ks:
                org_freq[k] += 1
    return ev_orgs, canon_display, org_freq


def valida(ev_orgs, canon_display):
    """Confere os agregados contra resultados_multiano.json. Aborta se divergir."""
    labmap = {k: ec.setor_new(canon_display[k]) for k in canon_display}
    comp = Counter(labmap.values())
    nodes = set()
    for v in ev_orgs.values():
        nodes.update(v)
    n_multiorg = sum(1 for v in ev_orgs.values() if len(v) >= 2)
    n_mss = sum(1 for v in ev_orgs.values()
                if len({labmap[o] for o in v if labmap[o] != "Indefinido"}) >= 2)
    J = json.load(open("resultados_multiano.json"))["por_ano"][ANO]
    checa = {
        "n_nos": (len(nodes), J["n_nos"]),
        "n_multiorg": (n_multiorg, J["n_multiorg"]),
        "n_multissetor": (n_mss, J["n_multissetor"]),
        "comp": ({s: comp.get(s, 0) for s in J["comp"]}, J["comp"]),
    }
    ruins = {k: v for k, v in checa.items() if v[0] != v[1]}
    if ruins:
        print("ABORTADO: agregados divergem de resultados_multiano.json:")
        for k, (a, b) in ruins.items():
            print(f"  {k}: reconstruido={a} publicado={b}")
        sys.exit(1)
    return labmap, comp


def estilo():
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 10,
        "axes.linewidth": 0.8, "axes.edgecolor": "#333333", "axes.labelcolor": "#111111",
        "xtick.color": "#333333", "ytick.color": "#333333", "text.color": "#111111",
        "figure.dpi": 200, "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.pad_inches": 0.05,
    })


def main():
    ev_orgs, canon_display, org_freq = extrai(carrega_ano(ANO))
    labmap, comp = valida(ev_orgs, canon_display)
    estilo()
    AZUL, CINZA, PONTO = "#3B6A9A", "#8A94A0", "#1F3B57"

    # fig_setor
    ordem = ["Estado", "Mercado", "Terceiro setor", "Indefinido"]
    vals = [comp.get(s, 0) for s in ordem]
    fig, ax = plt.subplots(figsize=(5.0, 3.3))
    b = ax.bar(range(len(ordem)), vals, width=0.62, edgecolor="white", linewidth=0.5,
               color=[AZUL, AZUL, AZUL, CINZA])
    ax.set_xticks(range(len(ordem))); ax.set_xticklabels(ordem)
    ax.set_ylabel("Número de organizações"); ax.set_ylim(0, max(vals) * 1.15)
    for r, v in zip(b, vals):
        ax.text(r.get_x() + r.get_width() / 2, v + max(vals) * 0.02, str(v), ha="center", va="bottom", fontsize=9)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False); ax.tick_params(length=3)
    fig.savefig("fig_setor.png"); plt.close(fig)

    # fig_dist
    of = Counter(org_freq.values())
    ks = sorted(of); ys = [of[k] for k in ks]
    fig, ax = plt.subplots(figsize=(5.0, 3.3))
    ax.scatter(ks, ys, s=26, color=PONTO, edgecolor="white", linewidth=0.4, zorder=3)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Participações por organização ($k$)")
    ax.set_ylabel("Número de organizações")
    ax.grid(True, which="both", linewidth=0.3, color="#DDDDDD", zorder=0)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False); ax.tick_params(length=3)
    fig.savefig("fig_dist.png"); plt.close(fig)

    # fig_div
    spe = Counter(len({labmap[o] for o in v if labmap[o] != "Indefinido"}) for v in ev_orgs.values())
    xs = sorted(spe); ys = [spe[x] for x in xs]
    fig, ax = plt.subplots(figsize=(5.0, 3.3))
    b = ax.bar(xs, ys, width=0.6, edgecolor="white", linewidth=0.5, color=AZUL)
    ax.set_xlabel("Setores distintos por evento (excluindo Indefinido)")
    ax.set_ylabel("Número de eventos"); ax.set_xticks(xs); ax.set_ylim(0, max(ys) * 1.15)
    for r, v in zip(b, ys):
        ax.text(r.get_x() + r.get_width() / 2, v + max(ys) * 0.02, str(v), ha="center", va="bottom", fontsize=9)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False); ax.tick_params(length=3)
    fig.savefig("fig_div.png"); plt.close(fig)

    print("Figuras geradas: fig_setor.png, fig_dist.png, fig_div.png")
    print(f"  composicao {vals} | participacoes k=1..{max(ks)} | setores/evento {dict(spe)}")


if __name__ == "__main__":
    main()
