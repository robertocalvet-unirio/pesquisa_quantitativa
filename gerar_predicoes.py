# -*- coding: utf-8 -*-
"""
gerar_predicoes.py

Gera predicoes_classificador.csv de forma reproduzivel, a partir da amostra de 150
organizacoes (codificacao_setorial_v2.csv). As duas colunas de predicao NAO sao
codificacao humana: sao saidas deterministicas dos dois classificadores definidos
em extracao_camara.py --- setor_old (heuristica anterior por palavras-chave) e
setor_new (classificador por gazetteer). O script apenas aplica esses dois
classificadores a cada nome de organizacao da amostra.

ENTRADA:  codificacao_setorial_v2.csv   (colunas: id, organizacao, ...)
SAIDA:    predicoes_classificador.csv    (colunas: id, organizacao,
                                          heuristica_antiga, classificador_novo)

USO: python3 gerar_predicoes.py
"""
import csv
import extracao_camara as ec

ENTRADA = "codificacao_setorial_v2.csv"
SAIDA = "predicoes_classificador.csv"


def main():
    linhas = []
    with open(ENTRADA, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            org = r["organizacao"]
            linhas.append((int(r["id"]), org,
                           ec.setor_old(org), ec.setor_new(org)))
    linhas.sort()
    with open(SAIDA, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "organizacao", "heuristica_antiga", "classificador_novo"])
        w.writerows(linhas)
    print(f"{len(linhas)} predicoes gravadas em {SAIDA}")


if __name__ == "__main__":
    main()
