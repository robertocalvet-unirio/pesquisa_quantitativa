#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Confiabilidade interavaliador (kappa de Cohen) E acuracia do classificador por
gazetteer, sobre a amostra de 150 organizacoes gerada por analise_rede.py.

PASSO DE CODIFICACAO HUMANA (necessario; nao automatizavel):
  1. Abra  saida/codificacao_setorial.csv  (150 organizacoes).
  2. Dois pesquisadores preenchem, de forma INDEPENDENTE, uma coluna cada:
       - setor_codificador_1
       - setor_codificador_2
     Valores validos: Estado | Mercado | Terceiro setor | Indefinido
  3. Rode:  python3 compute_kappa.py
     (ou:   python3 compute_kappa.py <diretorio_saida> )
  4. Use o kappa e a acuracia para preencher o \\todo{...} da Secao de Validacao.

O arquivo saida/predicoes_classificador.csv (gerado por analise_rede.py) traz,
por id, a predicao do classificador por gazetteer (coluna classificador_novo);
o script mede a acuracia contra o padrao-ouro humano adjudicado (itens em que os
dois codificadores concordam).
"""
import csv, os, sys, json
from collections import Counter

OUT = sys.argv[1] if len(sys.argv) > 1 else "saida"
SHEET = os.path.join(OUT, "codificacao_setorial.csv")
PRED = os.path.join(OUT, "predicoes_classificador.csv")
VALID_JSON = os.path.join(OUT, "validacao_classificador.json")


def load_pred_both(arq):
    """id -> (heuristica_antiga, classificador_novo)."""
    rows = {}
    with open(arq, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[r["id"]] = ((r.get("heuristica_antiga") or "").strip(),
                             (r.get("classificador_novo") or "").strip())
    return rows


def concordancia_heur_gazetteer(arq):
    """Reproduz, sem codificacao humana, a concordancia entre a heuristica antiga e o
    classificador por gazetteer sobre a amostra (numero citado no artigo: 70,0%)."""
    both = load_pred_both(arq)
    pares = [(h, g) for h, g in both.values() if h and g]
    n = len(pares)
    conc = sum(1 for h, g in pares if h == g)
    pct = round(100 * conc / n, 1) if n else 0.0
    return n, conc, pct



def load_sheet(arq):
    rows = {}
    with open(arq, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[r["id"]] = ((r.get("setor_codificador_1") or "").strip(),
                             (r.get("setor_codificador_2") or "").strip())
    return rows


def load_pred(arq):
    pred = {}
    with open(arq, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pred[r["id"]] = (r.get("classificador_novo") or "").strip()
    return pred


def kappa(pairs):
    n = len(pairs); cats = sorted({c for p in pairs for c in p})
    po = sum(1 for a, b in pairs if a == b) / n
    c1 = Counter(a for a, _ in pairs); c2 = Counter(b for _, b in pairs)
    pe = sum((c1[c] / n) * (c2[c] / n) for c in cats)
    k = (po - pe) / (1 - pe) if (1 - pe) else float("nan")
    return n, po, pe, k


def interp(k):
    if k < 0:    return "pior que o acaso"
    if k < 0.20: return "leve (slight)"
    if k < 0.40: return "razoavel (fair)"
    if k < 0.60: return "moderada (moderate)"
    if k < 0.80: return "substancial (substantial)"
    return "quase perfeita (almost perfect)"


def main():
    valida = {"n_amostra": None, "concordancia_heuristica_gazetteer_pct": None,
              "kappa_cohen": None, "acuracia_gazetteer_pct": None,
              "kappa_pendente_codificacao_humana": True}

    # (1) Concordancia heuristica x gazetteer: reproduzivel agora, sem codificacao humana.
    if os.path.exists(PRED):
        n_hg, conc_hg, pct_hg = concordancia_heur_gazetteer(PRED)
        valida["n_amostra"] = n_hg
        valida["concordancia_heuristica_gazetteer_pct"] = pct_hg
        print(f"[Concordancia heuristica x gazetteer]  n={n_hg}")
        print(f"  itens em que as duas rotulagens coincidem: {conc_hg}/{n_hg}")
        print(f"  concordancia = {pct_hg}%   (valor citado no artigo)")

    if not os.path.exists(SHEET):
        with open(VALID_JSON, "w", encoding="utf-8") as f:
            json.dump(valida, f, ensure_ascii=False, indent=2)
        print(f"\n[validacao gravada em {VALID_JSON}; kappa pendente: codificacao humana]")
        print(f"Arquivo de codificacao nao encontrado: {SHEET}")
        sys.exit(0)
    sheet = load_sheet(SHEET)
    pairs = [(a, b) for a, b in sheet.values() if a and b]
    if not pairs:
        with open(VALID_JSON, "w", encoding="utf-8") as f:
            json.dump(valida, f, ensure_ascii=False, indent=2)
        print(f"\n[validacao gravada em {VALID_JSON}; kappa pendente: codificacao humana]")
        print(f"Nenhuma linha com AMBAS as colunas preenchidas em {SHEET}")
        print("Preencha setor_codificador_1 e setor_codificador_2 e rode de novo.")
        sys.exit(0)
    n, po, pe, k = kappa(pairs)
    valida["n_amostra"] = n
    valida["kappa_cohen"] = round(k, 3)
    valida["kappa_pendente_codificacao_humana"] = False
    print(f"[Confiabilidade interavaliador]  n={n}")
    print(f"  concordancia observada p_o = {po:.3f}")
    print(f"  concordancia esperada  p_e = {pe:.3f}")
    print(f"  kappa de Cohen = {k:.3f}  ({interp(k)})")

    try:
        pred = load_pred(PRED)
    except FileNotFoundError:
        pred = {}
    if pred:
        gold = {i: a for i, (a, b) in sheet.items() if a and b and a == b}  # adjudicado
        ok = [i for i in gold if i in pred and pred[i]]
        if ok:
            acc = sum(1 for i in ok if pred[i] == gold[i]) / len(ok)
            valida["acuracia_gazetteer_pct"] = round(100 * acc, 1)
            print("\n[Acuracia do classificador por gazetteer vs padrao-ouro adjudicado]")
            print(f"  itens com concordancia entre codificadores: {len(ok)}")
            print(f"  acuracia = {100 * acc:.1f}%")
        for col, idx in (("codificador_1", 0), ("codificador_2", 1)):
            items = [i for i in sheet if sheet[i][idx] and i in pred and pred[i]]
            if items:
                a = sum(1 for i in items if pred[i] == sheet[i][idx]) / len(items)
                print(f"  acuracia vs {col} (n={len(items)}): {100 * a:.1f}%")
    with open(VALID_JSON, "w", encoding="utf-8") as f:
        json.dump(valida, f, ensure_ascii=False, indent=2)
    print(f"\n[validacao gravada em {VALID_JSON}]")
    print("\nFrase para o artigo:")
    print(f"  kappa de Cohen = {k:.2f} ({interp(k)})")


if __name__ == "__main__":
    main()
