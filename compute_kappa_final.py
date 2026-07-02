# -*- coding: utf-8 -*-
"""
compute_kappa_final.py

Reproduz a validação por confiabilidade interavaliador reportada no artigo:
  - kappa de Cohen entre os dois codificadores humanos (n=150), com IC 95% por
    bootstrap (10000 reamostragens, semente 42);
  - concordância observada;
  - acurácia do classificador por gazetteer contra o consenso dos codificadores
    (casos em que ambos concordam), com decomposição dos desacertos em
    abstenções (Indefinido) e atribuições divergentes.

ENTRADAS (mesma pasta):
  codificacao_setorial_fabiano.xlsx  (coluna setor_codificador_1 preenchida)
  codificacao_setorial_vanessa.xlsx  (coluna setor_codificador_2 preenchida)
  predicoes_classificador.csv        (colunas: id, organizacao,
                                      heuristica_antiga, classificador_novo)

SAÍDA: imprime o relatório e grava kappa_resultado.json.

USO: python3 compute_kappa_final.py
"""
import csv, json, random
from collections import Counter

import openpyxl

CANON = {"estado": "Estado", "mercado": "Mercado",
         "terceiro setor": "Terceiro setor", "indefinido": "Indefinido"}

def norm(v):
    if v is None:
        raise ValueError("célula vazia na codificação")
    k = " ".join(str(v).split()).strip().casefold()
    if k not in CANON:
        raise ValueError(f"rótulo fora do conjunto: {v!r}")
    return CANON[k]

def ler_planilha(nome, coluna):
    wb = openpyxl.load_workbook(nome)
    ws = wb.active
    dados = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        rid, org, c1, c2 = row[0], row[1], row[2], row[3]
        dados[rid] = (org, norm(c1 if coluna == 1 else c2))
    return dados

def kappa_cohen(pares):
    n = len(pares)
    cats = sorted({a for a, _ in pares} | {b for _, b in pares})
    po = sum(1 for a, b in pares if a == b) / n
    m1 = Counter(a for a, _ in pares)
    m2 = Counter(b for _, b in pares)
    pe = sum((m1[c] / n) * (m2[c] / n) for c in cats)
    return (po - pe) / (1 - pe), po, pe

def main():
    fab = ler_planilha("codificacao_setorial_fabiano.xlsx", 1)
    van = ler_planilha("codificacao_setorial_vanessa.xlsx", 2)
    assert set(fab) == set(van), "IDs divergem entre planilhas"
    assert all(fab[i][0] == van[i][0] for i in fab), "organizações divergem"
    ids = sorted(fab)
    n = len(ids)

    pares = [(fab[i][1], van[i][1]) for i in ids]
    k, po, pe = kappa_cohen(pares)

    # IC 95% por bootstrap, semente fixa
    random.seed(42)
    boots = []
    for _ in range(10000):
        amostra = [pares[random.randrange(n)] for _ in range(n)]
        boots.append(kappa_cohen(amostra)[0])
    boots.sort()
    lo, hi = boots[249], boots[9749]

    # gazetteer x consenso
    pred = {int(r["id"]): norm(r["classificador_novo"])
            for r in csv.DictReader(open("predicoes_classificador.csv",
                                          encoding="utf-8"))}
    consenso = {i: fab[i][1] for i in ids if fab[i][1] == van[i][1]}
    acertos = sum(1 for i in consenso if pred[i] == consenso[i])
    abst = sum(1 for i in consenso
               if pred[i] == "Indefinido" and consenso[i] != "Indefinido")
    atrib = {i for i in consenso if pred[i] != "Indefinido"}
    acertos_atrib = sum(1 for i in atrib if pred[i] == consenso[i])

    div = [(i, fab[i][0], fab[i][1], van[i][1])
           for i in ids if fab[i][1] != van[i][1]]
    pessoa_org = sum(1 for d in div if d[2] == "Indefinido" and d[3] == "Estado")

    print(f"n = {n}")
    print(f"kappa de Cohen = {k:.4f}  (reportado: {k:.2f})")
    print(f"IC 95% bootstrap (10000, semente 42) = [{lo:.2f}; {hi:.2f}]")
    print(f"concordância observada = {sum(1 for a,b in pares if a==b)}/{n}"
          f" = {po*100:.1f}%")
    print(f"consenso (padrão-ouro) = {len(consenso)}")
    print(f"acurácia gazetteer no consenso = {acertos}/{len(consenso)}"
          f" = {acertos/len(consenso)*100:.1f}%")
    print(f"desacertos por abstenção (Indefinido) = {abst}"
          f" | atribuições divergentes = {len(consenso)-acertos-abst}")
    print(f"quando atribui: {acertos_atrib}/{len(atrib)}"
          f" = {acertos_atrib/len(atrib)*100:.1f}%")
    print(f"divergências entre codificadores = {len(div)},"
          f" das quais Indefinido->Estado (pessoa c/ organização) = {pessoa_org}")

    json.dump({"n": n, "kappa": k, "ic95": [lo, hi], "po": po, "pe": pe,
               "consenso_n": len(consenso), "acuracia_acertos": acertos,
               "abstencoes": abst, "atrib_n": len(atrib),
               "atrib_acertos": acertos_atrib,
               "divergencias_total": len(div),
               "divergencias_pessoa_org": pessoa_org},
              open("kappa_resultado.json", "w"), ensure_ascii=False, indent=1)
    print("\nkappa_resultado.json gravado")

if __name__ == "__main__":
    main()
