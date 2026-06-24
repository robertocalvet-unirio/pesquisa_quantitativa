#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aquisicao dos dados de eventos da Camara dos Deputados (portal de dados abertos).
Usa apenas a biblioteca padrao (urllib); nao requer 'requests'.

Dois modos:
  --bulk  (padrao): baixa o arquivo anual oficial em JSON. Esta e a fonte
          CANONICA, que reproduz exatamente os numeros do artigo.
          https://dadosabertos.camara.leg.br/arquivos/eventos/json/eventos-<ano>.json
  --api : reconstroi um conjunto equivalente paginando o endpoint /api/v2/eventos,
          filtrando por periodo (ano) e por tipo de evento (codTipoEvento
          120, 125, 191, 194 = audiencias, debates e comissoes gerais).
          Fornecido para transparencia. NAO foi executado no ambiente de
          desenvolvimento (rede restrita); execute-o no seu ambiente. Se o campo
          'descricao' (a pauta) vier vazio ou abreviado na listagem, use --detalhe
          para buscar a pauta completa em /eventos/<id>.

Saida: um JSON no formato {"dados": [ ... ]}, lido diretamente por analise_rede.py.

Exemplos:
  python3 baixar_dados.py --bulk --ano 2025
  python3 baixar_dados.py --api  --ano 2025
  python3 baixar_dados.py --api  --ano 2025 --detalhe
"""
import argparse, json, sys, time
import urllib.request, urllib.parse, urllib.error

BASE_API = "https://dadosabertos.camara.leg.br/api/v2/eventos"
BASE_BULK = "https://dadosabertos.camara.leg.br/arquivos/eventos/json/eventos-{ano}.json"
TIPOS = ["120", "125", "191", "194"]   # tipos-alvo do estudo (codTipoEvento)
UA = {"User-Agent": "repro-rio-audiencias/1.0", "Accept": "application/json"}


def _get_json(url, tentativas=3, espera=2.0):
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as e:
            if i == tentativas - 1:
                raise
            print(f"  [aviso] tentativa {i+1} falhou ({e}); aguardando...")
            time.sleep(espera * (i + 1))


def baixar_bulk(ano, saida):
    url = BASE_BULK.format(ano=ano)
    print(f"[bulk] baixando {url}")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r:
        bruto = r.read().decode("utf-8")
    obj = json.loads(bruto)
    n = len(obj.get("dados", obj) if isinstance(obj, dict) else obj)
    with open(saida, "w", encoding="utf-8") as f:
        f.write(bruto)
    print(f"[bulk] {n} eventos salvos em {saida} (fonte canonica)")


def baixar_api(ano, saida, detalhe=False):
    print(f"[api] paginando {BASE_API} (ano={ano}, tipos={','.join(TIPOS)})")
    base_params = [("dataInicio", f"{ano}-01-01"), ("dataFim", f"{ano}-12-31"),
                   ("ordem", "ASC"), ("ordenarPor", "dataHoraInicio"), ("itens", "100")]
    for t in TIPOS:
        base_params.append(("codTipoEvento", t))
    eventos, pagina = [], 1
    while True:
        q = base_params + [("pagina", str(pagina))]
        url = BASE_API + "?" + urllib.parse.urlencode(q)
        d = _get_json(url)
        lote = d.get("dados", [])
        if not lote:
            break
        eventos.extend(lote)
        print(f"[api] pagina {pagina}: +{len(lote)} (total {len(eventos)})")
        prox = next((l for l in d.get("links", []) if l.get("rel") == "next"), None)
        if not prox:
            break
        pagina += 1
        time.sleep(0.3)
    if detalhe:
        print(f"[api] buscando pauta completa de {len(eventos)} eventos em /eventos/<id> ...")
        for i, e in enumerate(eventos, 1):
            try:
                det = _get_json(f"{BASE_API}/{e.get('id')}").get("dados", {})
                if det.get("descricao"):
                    e["descricao"] = det["descricao"]
                if det.get("descricaoTipo"):
                    e["descricaoTipo"] = det["descricaoTipo"]
            except Exception as ex:
                print(f"  [aviso] id={e.get('id')}: {ex}")
            if i % 50 == 0:
                print(f"  ...{i}/{len(eventos)}")
            time.sleep(0.2)
    with open(saida, "w", encoding="utf-8") as f:
        json.dump({"dados": eventos}, f, ensure_ascii=False)
    print(f"[api] {len(eventos)} eventos salvos em {saida}")
    print("[api] OBS: modo nao executado no ambiente de desenvolvimento; "
          "para replicacao exata dos numeros do artigo use --bulk.")


def main():
    ap = argparse.ArgumentParser(description="Aquisicao de eventos da Camara dos Deputados.")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--bulk", action="store_true", help="baixa o arquivo anual oficial (canonico)")
    g.add_argument("--api", action="store_true", help="reconstroi via API /eventos")
    ap.add_argument("--ano", type=int, default=2025)
    ap.add_argument("--detalhe", action="store_true",
                    help="(api) busca /eventos/<id> para obter a pauta completa")
    ap.add_argument("--saida", default=None, help="arquivo de saida (padrao: eventos-<ano>.json)")
    a = ap.parse_args()
    saida = a.saida or f"eventos-{a.ano}.json"
    if a.api:
        baixar_api(a.ano, saida, a.detalhe)
    else:
        baixar_bulk(a.ano, saida)   # padrao = bulk (canonico)


if __name__ == "__main__":
    main()
