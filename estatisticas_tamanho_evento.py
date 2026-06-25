# -*- coding: utf-8 -*-
"""
estatisticas_tamanho_evento.py

Calcula estatisticas descritivas do TAMANHO DOS EVENTOS, isto e, do numero de
organizacoes distintas extraidas por evento-alvo, por ano. Produz media, desvio
padrao, mediana, minimo, maximo e quartis. Reaproveita o modulo extracao_camara
ja validado, de modo que os numeros sao consistentes com o pipeline principal e
rastreaveis.

USO:
    python3 estatisticas_tamanho_evento.py dados

onde "dados" e o diretorio com os arquivos eventos-*.json (o mesmo usado pelo
analise_multiano.py). Imprime uma tabela por ano e grava tambem em
saida_tamanho/estatisticas_tamanho_evento.json para conferencia.

O "tamanho do evento" e contado de duas formas, ambas reportadas:
  - sobre eventos COM ao menos uma organizacao (exclui eventos vazios);
  - sobre TODOS os eventos-alvo (inclui zeros).
A primeira costuma ser a mais informativa; a segunda e o complemento honesto.
"""
import sys, os, glob, json, statistics
from collections import defaultdict

# importa o modulo compartilhado do pipeline (precisa estar na mesma pasta)
import extracao_camara as ec

DADOS = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DADOS_DIR", "dados")
OUT = os.environ.get("SAIDA_DIR", "saida_tamanho")
ANOS_COMPLETOS = ["2023", "2024", "2025"]

def is_alvo(e):
    cod = str(e.get("codTipoEvento") or e.get("idTipoEvento") or "")
    tt = (e.get("descricaoTipo") or "").lower()
    return cod in ec.TIPOS_ALVO or any(
        p in tt for p in ["audi", "comiss", "debate"]
    )

def quartis(xs):
    """Q1, Q2 (mediana), Q3 por interpolacao simples."""
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return (0.0, 0.0, 0.0)
    def pct(p):
        if n == 1:
            return float(s[0])
        k = (n - 1) * p
        f = int(k)
        c = min(f + 1, n - 1)
        return s[f] + (s[c] - s[f]) * (k - f)
    return (round(pct(0.25), 2), round(pct(0.50), 2), round(pct(0.75), 2))

def descreve(valores):
    if not valores:
        return dict(n=0, media=0.0, desvio=0.0, mediana=0.0,
                    minimo=0, maximo=0, q1=0.0, q3=0.0)
    q1, q2, q3 = quartis(valores)
    return dict(
        n=len(valores),
        media=round(statistics.mean(valores), 2),
        desvio=round(statistics.pstdev(valores), 2) if len(valores) > 1 else 0.0,
        mediana=q2,
        minimo=min(valores),
        maximo=max(valores),
        q1=q1,
        q3=q3,
    )

# --- leitura e deduplicacao por id, binagem por ano-calendario ---
eventos_por_ano = defaultdict(list)
vistos = set()
arquivos = sorted(glob.glob(os.path.join(DADOS, "eventos-*.json")))
if not arquivos:
    print(f"Nenhum eventos-*.json em {DADOS}")
    sys.exit(1)
for f in arquivos:
    d = json.load(open(f, encoding="utf-8"))
    for e in (d.get("dados", d) if isinstance(d, dict) else d):
        i = e.get("id")
        if i in vistos:
            continue
        vistos.add(i)
        dh = e.get("dataHoraInicio") or ""
        if len(dh) >= 4:
            eventos_por_ano[dh[:4]].append(e)

print(f"Arquivos lidos: {len(arquivos)} | eventos unicos: {len(vistos)}")
print()

resultado = {}
# cabecalho
hdr = f"{'Ano':<6}{'n_alvo':>8}{'n_com_org':>11}{'media':>8}{'desvio':>8}{'mediana':>9}{'min':>5}{'max':>6}{'Q1':>6}{'Q3':>6}"
print("=== Tamanho do evento = nº de organizações DISTINTAS por evento ===")
print("--- (A) sobre eventos COM >=1 organizacao ---")
print(hdr)
for ano in ANOS_COMPLETOS:
    eventos = [e for e in eventos_por_ano.get(ano, []) if is_alvo(e)]
    tamanhos_todos = []      # inclui zeros
    tamanhos_com_org = []    # exclui zeros
    for e in eventos:
        orgs = set()
        for o in ec.extrair(e.get("descricao")):
            orgs.add(ec.norm(o))
        k = len(orgs)
        tamanhos_todos.append(k)
        if k > 0:
            tamanhos_com_org.append(k)
    d_com = descreve(tamanhos_com_org)
    d_todos = descreve(tamanhos_todos)
    resultado[ano] = {"com_organizacao": d_com, "todos_os_eventos": d_todos,
                      "n_alvo": len(eventos)}
    print(f"{ano:<6}{len(eventos):>8}{d_com['n']:>11}{d_com['media']:>8}"
          f"{d_com['desvio']:>8}{d_com['mediana']:>9}{d_com['minimo']:>5}"
          f"{d_com['maximo']:>6}{d_com['q1']:>6}{d_com['q3']:>6}")

print()
print("--- (B) sobre TODOS os eventos-alvo (inclui eventos sem organizacao) ---")
print(hdr)
for ano in ANOS_COMPLETOS:
    d = resultado[ano]["todos_os_eventos"]
    print(f"{ano:<6}{resultado[ano]['n_alvo']:>8}{d['n']:>11}{d['media']:>8}"
          f"{d['desvio']:>8}{d['mediana']:>9}{d['minimo']:>5}"
          f"{d['maximo']:>6}{d['q1']:>6}{d['q3']:>6}")

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "estatisticas_tamanho_evento.json"), "w", encoding="utf-8") as fp:
    json.dump(resultado, fp, ensure_ascii=False, indent=2)

print()
print(f"JSON gravado em {os.path.join(OUT, 'estatisticas_tamanho_evento.json')}")
print()
print("COMO LER: 'media' e o numero medio de organizacoes distintas por evento;")
print("'desvio' e o desvio padrao populacional desse numero. Use os valores da")
print("tabela (A), sobre eventos com ao menos uma organizacao, salvo se preferir (B).")
