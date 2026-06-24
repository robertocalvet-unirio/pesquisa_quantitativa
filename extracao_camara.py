# -*- coding: utf-8 -*-
"""Modulo compartilhado: extracao de organizacoes da pauta e classificador setorial
por gazetteer. Fatorado de analise_rede.py (versao validada) para reuso no script
multiano, garantindo identidade exata de extracao e rotulagem.

Expoe: TIPOS_ALVO, extrair(descricao), norm(org), setor_new(org), setor_old(org).
"""
import re, json, random, statistics, math, csv as _csv, os, sys
from collections import Counter
import networkx as nx

random.seed(42)
TIPOS_ALVO = {"120", "125", "191", "194"}

# ===================== EXTRACAO (identica ao v1) =====================
LINHA_CONV = re.compile(r"^\s*[-•]\s*(.+)$")
REP = re.compile(r"representante\s+d[aeo]s?\s+(.+?)(?:\s*\(\s*req|\s*;|\s*\.\s|$)", re.I)
CARGO_AFIL = re.compile(
    r"\b(?:Procurador|Advogad[oa]|Diretor[ae]?|Presidente|Vice-?Presidente|Secretári[oa]|"
    r"Coordenador[ae]?|Superintendente|Assessor[ae]?|Gerente|Ministr[oa]|Subsecretári[oa]|"
    r"Chefe|Conselheir[oa]|Membro)\b.*?\bd[aeo]s?\s+(.+?)(?:\s*\(\s*req|\s*;|\s*\.\s|$)", re.I)
HEADER_KW = ("convidad","palestrante","expositor","participante","debatedor","a confirmar",
  "a serem confirmad","demais","lista de","composição da mesa","programação","autoridades",
  "abertura dos trabalhos","expedient","mesa de","ordem dos trabalhos","demais convidados",
  "objetivo de","tribuna das")
ROLE_EXACT = {"presidente","presidenta","vice-presidente","representante","advogado","advogada",
  "advogados","advogadas","diretor","diretora","diretor-presidente","diretora-presidente",
  "diretor-geral","diretora-geral","diretor executivo","diretora executiva","secretário","secretária",
  "coordenador","coordenadora","coordenador geral","ministro","ministra","deputado","deputada",
  "deputado estadual","deputada estadual","vereador","vereadora","senador","senadora","procurador",
  "procuradora","promotor","promotora","promotora de justiça","promotor de justiça","conselheiro",
  "conselheira","superintendente","assessor","assessora","gerente","chefe","membro","relator","relatora",
  "mediador","mediadora","moderador","moderadora","jornalista","professor","professora","médico",
  "médica","médico cardiologista","perito","perita","palestrante","palestrantes","convidado",
  "convidados","expositor","expositores","participante","participantes","debatedor","debatedores",
  "mesa","autoridades","outros","cidadão","cidadã"}
INSTITUICAO = ("ministério","ministerio","secretaria","agência","agencia","autarquia",
  "superintendência","superintendencia","procuradoria","ministério público","ministerio publico",
  "tribunal","defensoria","advocacia-geral","advocacia geral","controladoria","casa civil",
  "câmara dos deputados","camara dos deputados","senado","assembleia","assembléia","prefeitura",
  "banco central","receita federal","polícia","policia","departamento nacional","instituto nacional",
  " estado d","conselho","instituto","universidade","faculdade","fundação","fundacao","associação",
  "associacao","federação","federacao","confederação","confederacao","sindicato","ordem dos advogados",
  " oab"," central","coletivo","movimento","frente parlamentar","cooperativa","câmara de comércio",
  "camara de comercio","sociedade","fórum","forum"," rede ","empresa","companhia"," banco "," s.a",
  " s/a","departamento intersindical","comitê","comite","núcleo","nucleo","centro brasileiro",
  "observatório","observatorio"," ong "," abes"," anvisa"," aneel"," anatel"," antt"," funai",
  " ibama"," ipea"," inss"," dnit"," embrapa"," petrobras"," fiocruz"," febraban")
AUTOR_PREFIX = ("autor:","autora:","autores:","autoria:","requerente:","req.","autor ","autora ")

def _eh_org(org):
    ks = org.casefold()
    if org.endswith(":"): return False
    if ks in ROLE_EXACT: return False
    if any(ks.startswith(p) for p in AUTOR_PREFIX): return False
    if any(kw in ks for kw in HEADER_KW): return False
    return True
def _tem_marcador(org):
    o = " " + org.casefold() + " "
    return any(m in o for m in INSTITUICAO)
def _peel(item):
    rm = REP.search(item)
    if rm: return rm.group(1)
    cm = CARGO_AFIL.search(item)
    if cm: return cm.group(1)
    return item
def extrair(descricao):
    if not descricao: return []
    orgs = []
    for raw in descricao.splitlines():
        l = raw.strip()
        if not l or len(l) < 4: continue
        m = LINHA_CONV.match(l)
        item = m.group(1).strip() if m else l
        org = _peel(item)
        org = re.sub(r"\s+", " ", org).strip(" .;,-")
        if 4 <= len(org) <= 90 and _eh_org(org) and _tem_marcador(org):
            orgs.append(org)
    seen, out = set(), []
    for o in orgs:
        k = o.casefold()
        if k not in seen: seen.add(k); out.append(o)
    return out
def norm(o):
    o = re.sub(r"\s+", " ", o).strip(" .;,-")
    o = re.sub(r"\s*[\(\-–]\s*[A-Za-zÀ-ÿ\.]{2,10}\s*\)?\s*$", "", o) if re.search(r"[\(\-–]\s*[A-ZÀ-Ý]{2,}", o) else o
    return re.sub(r"\s+", " ", o).strip(" .;,-").casefold()

# ===================== CLASSIFICADOR SETORIAL ANTIGO (para comparacao) =====================
def setor_old(org):
    o = " " + org.lower() + " "
    estado = ["ministério","ministerio","secretaria","agência","agencia","procuradoria",
      "ministério público","ministerio publico","tribunal","autarquia","superintendência",
      "superintendencia","advocacia-geral","advocacia geral"," união","governo","prefeitura",
      "banco central","receita federal","polícia","policia","defensoria"," estado d",
      "instituto nacional","departamento nacional","casa civil","câmara dos deputados","senado","controladoria"]
    mercado = ["s.a","s/a"," ltda","companhia"," empresa","concessionária","concessionaria",
      "federação das indústrias","febraban","confederação nacional da indústria"," cni ",
      "associação comercial","sindicato patronal","câmara de comércio"," banco ","s.a."]
    terceiro = ["ong","associação","associacao","fundação","fundacao","sindicato","federação",
      "federacao","confederação","confederacao","movimento","central única","central unica",
      "ordem dos advogados"," oab ","cooperativa","pastoral","instituto ","conselho","fórum","forum"]
    publico = ["universidade federal","universidade estadual","universidade do estado",
      "universidade de são paulo"," usp "," unb ","universidade de brasília","instituto federal",
      "instituto de pesquisa econômica aplicada"," ipea ","fundação oswaldo cruz","fiocruz",
      "empresa brasileira de pesquisa","embrapa","instituto brasileiro de geografia"," ibge ",
      "instituto nacional de pesquisas espaciais"," inpe ","banco nacional de desenvolvimento",
      " bndes ","caixa econômica","petróleo brasileiro","petrobras","correios","fundação nacional"]
    def hit(ks): return any(k in o for k in ks)
    if hit(publico): return "Estado"
    if hit(estado): return "Estado"
    if hit(mercado): return "Mercado"
    if hit(terceiro): return "Terceiro setor"
    return "Indefinido"

# ===================== CLASSIFICADOR NOVO: gazetteer + entity-linking =====================
# Acronimos canonicos -> setor (match por token isolado, casefold)
ACR = {
 # Estado: orgaos, agencias, autarquias, MP, tribunais, empresas publicas, conselhos profissionais
 "stf":"Estado","stj":"Estado","tse":"Estado","tst":"Estado","tcu":"Estado","trf":"Estado",
 "mpf":"Estado","mpt":"Estado","mpu":"Estado","agu":"Estado","cgu":"Estado","cade":"Estado",
 "bcb":"Estado","cvm":"Estado","susep":"Estado","anvisa":"Estado","anatel":"Estado","aneel":"Estado",
 "antt":"Estado","anac":"Estado","anp":"Estado","ans":"Estado","anm":"Estado","ancine":"Estado",
 "antaq":"Estado","ana":"Estado","anpd":"Estado","inss":"Estado","incra":"Estado","ibama":"Estado",
 "icmbio":"Estado","funai":"Estado","inpi":"Estado","inmetro":"Estado","dnit":"Estado","iphan":"Estado",
 "funasa":"Estado","ipea":"Estado","ibge":"Estado","inpe":"Estado","fiocruz":"Estado","embrapa":"Estado",
 "bndes":"Estado","conab":"Estado","serpro":"Estado","dataprev":"Estado","conitec":"Estado",
 "usp":"Estado","unb":"Estado","unicamp":"Estado","unesp":"Estado","ufrj":"Estado","ufmg":"Estado",
 "ufrgs":"Estado","ufba":"Estado","ufpe":"Estado","ufpr":"Estado","ufsc":"Estado","ufc":"Estado",
 "oab":"Estado","cfm":"Estado","cofen":"Estado","confea":"Estado","crea":"Estado","cfc":"Estado",
 "cfp":"Estado","cfess":"Estado","cff":"Estado","cfmv":"Estado","confef":"Estado","cfo":"Estado",
 # Mercado: confederacoes patronais, federacoes empresariais, associacoes setoriais, firmas
 "cni":"Mercado","cna":"Mercado","cnc":"Mercado","cnt":"Mercado","cnf":"Mercado","cnseg":"Mercado",
 "febraban":"Mercado","fenabrave":"Mercado","fenaseg":"Mercado","fenasaude":"Mercado","anbima":"Mercado",
 "anfavea":"Mercado","abinee":"Mercado","abimaq":"Mercado","abras":"Mercado","abiquim":"Mercado",
 "abrafarma":"Mercado","sindicom":"Mercado","abividro":"Mercado","fiesp":"Mercado","firjan":"Mercado",
 "fiemg":"Mercado","fiep":"Mercado","fiergs":"Mercado","fieb":"Mercado","fiec":"Mercado",
 "fecomercio":"Mercado","ciesp":"Mercado","abrasca":"Mercado","abramge":"Mercado","consif":"Mercado",
 # Terceiro setor: centrais sindicais, confederacoes/federacoes de trabalhadores, ONGs, movimentos
 "cut":"Terceiro setor","ctb":"Terceiro setor","ugt":"Terceiro setor","ncst":"Terceiro setor",
 "csb":"Terceiro setor","cgtb":"Terceiro setor","cnte":"Terceiro setor","contag":"Terceiro setor",
 "cspb":"Terceiro setor","cntss":"Terceiro setor","cnts":"Terceiro setor","idec":"Terceiro setor",
 "mst":"Terceiro setor","mtst":"Terceiro setor","cfemea":"Terceiro setor","inesc":"Terceiro setor",
 "conic":"Terceiro setor","cimi":"Terceiro setor","apib":"Terceiro setor","cobap":"Terceiro setor",
}
ACR_RE = {a: re.compile(r"(?<![0-9a-zà-ÿ])" + re.escape(a) + r"(?![0-9a-zà-ÿ])") for a in ACR}

LABOR = ["trabalhador","empregad","servidor","profissionai","profissional","docente","professor",
  "médic","medic","enfermeir","metalúrgic","metalurgic","rural","campones","aposentad","pescador",
  "categoria","da educação","da educacao","dos correios"]
EMPLOYER = ["indústria","industria","comércio","comercio","agricultura","pecuária","pecuaria",
  "transporte","instituições financeiras","instituicoes financeiras","empresar","patron","produtor",
  "varejo","atacad","logístic","logistic","dos bancos","seguros","construção civil","construcao civil",
  "sistema financeiro","da habitação","da habitacao","do agronegócio","do agronegocio","supermercado"]
STATE = ["ministério","ministerio","secretaria de","secretaria especial","secretaria nacional",
  "secretaria municipal","secretaria estadual","secretaria de estado","agência nacional","agencia nacional",
  "autarquia","superintendência federal","superintendencia federal","ministério público","ministerio publico",
  "procuradoria","advocacia-geral","advocacia geral da união","controladoria","defensoria pública",
  "defensoria publica","supremo tribunal","superior tribunal","tribunal de contas","tribunal regional",
  "tribunal de justiça","tribunal superior","conselho nacional de justiça","casa civil","governo do estado",
  "governo federal","governo do distrito","prefeitura","câmara municipal","camara municipal",
  "assembleia legislativa","assembléia legislativa","câmara dos deputados","camara dos deputados",
  "senado federal","congresso nacional","banco central","receita federal","polícia federal","policia federal",
  "polícia rodoviária","departamento de polícia","instituto nacional","departamento nacional","fundação nacional",
  "universidade federal","universidade estadual","universidade do estado","instituto federal",
  "universidade de são paulo","universidade de brasília","universidade de brasilia",
  "instituto de pesquisa econômica","instituto brasileiro de geografia","fundação oswaldo cruz",
  "empresa brasileira de pesquisa","instituto nacional de pesquisas","banco nacional de desenvolvimento",
  "caixa econômica","banco do brasil","empresa de tecnologia","empresa brasil de comunicação",
  "petróleo brasileiro","petrobras","eletrobras","conselho administrativo de defesa"]
MARKET = ["confederação nacional da indústria","confederacao nacional da industria",
  "confederação nacional da agricultura","confederação da agricultura e pecuária",
  "confederação nacional do comércio","confederacao nacional do comercio",
  "confederação nacional do transporte","confederação nacional das instituições financeiras",
  "confederação nacional de saúde","confederação nacional de saude","confederação nacional das empresas",
  "confederação nacional do sistema financeiro","confederação nacional dos transportadores",
  "federação brasileira de bancos","federação nacional de seguros","federação nacional de saúde suplementar",
  "federação das indústrias","federação da indústria","federacao das industrias","federação do comércio",
  "federacao do comercio","federação da agricultura","federação nacional da indústria",
  "federação das câmaras","federação do agronegócio","associação comercial","câmara de comércio",
  "camara de comercio","câmara de dirigentes lojistas","associação brasileira da indústria",
  "associação brasileira das empresas","associação brasileira de bancos","associação nacional dos bancos",
  "associação brasileira da infraestrutura","associação nacional das empresas","instituto livre mercado",
  "instituto aço brasil","instituto brasileiro de mineração","sindicato patronal","sindicato nacional da indústria",
  "sindicato nacional das empresas","sindicato das empresas","sindicato da indústria","sindicato do comércio",
  "sindicato nacional das","sindicato da habitação","sindicato dos produtores"," s.a"," s/a"," s.a."," ltda",
  "companhia "," cia."," cia ","concessionária","concessionaria","incorporadora","mineradora","siderúrgica",
  "montadora"," holding"]
THIRD = ["central única dos trabalhadores","central unica dos trabalhadores","força sindical","forca sindical",
  "união geral dos trabalhadores","central dos trabalhadores e trabalhadoras","nova central sindical",
  "central sindical e popular","intersindical","departamento intersindical",
  "confederação nacional dos trabalhadores","confederacao nacional dos trabalhadores",
  "confederação dos servidores públicos","confederação dos trabalhadores","federação dos trabalhadores",
  "federação nacional dos trabalhadores","federação dos empregados","federação dos servidores",
  "organização não governamental","organizacao nao governamental"," ong ","instituto de defesa do consumidor",
  "instituto brasileiro de defesa do consumidor","movimento ","pastoral","cáritas","caritas","fórum nacional",
  "forum nacional","fórum da sociedade","coletivo"," rede "," frente nacional","frente brasil",
  "associação brasileira de pacientes","associação de moradores","associação dos","associação nacional dos",
  "associação dos portadores","associação dos familiares","greenpeace","conectas","instituto socioambiental",
  "sociedade civil","centro de defesa","casa de","liga ","articulação","articulacao",
  # marcadores genericos de 3o setor (apos esgotar Estado/Mercado)
  "associação","associacao","fundação","fundacao","sindicato","cooperativa","instituto ","federação",
  "federacao","comitê","comite","observatório","observatorio","núcleo","nucleo","sociedade"," central"]

def _has(o, terms): return any(t in o for t in terms)

def setor_new(org):
    o = " " + re.sub(r"\s+", " ", org.casefold()) + " "
    # 1) acronimo canonico (token isolado)
    for a, rx in ACR_RE.items():
        if rx.search(o):
            return ACR[a]
    # 2) desambiguacao patronal/laboral para confederacao/federacao/sindicato
    if _has(o, ["confederação","confederacao","federação","federacao","sindicato"]):
        if _has(o, LABOR): return "Terceiro setor"
        if _has(o, EMPLOYER): return "Mercado"
        if "sindicato" in o: return "Terceiro setor"   # sindicato sem qualificador: laboral por padrao
        # confederacao/federacao sem qualificador -> segue regras gerais
    # 3) conselhos: pessoa juridica de direito publico (autarquia/conselho de politica) -> Estado
    if _has(o, ["conselho federal de","conselho regional de","conselho nacional dos direitos",
                "conselho nacional de saúde","conselho nacional de saude","conselho nacional de educa",
                "conselho nacional de assistência","conselho nacional de assistencia",
                "conselho nacional do meio ambiente","conselho nacional de justiça",
                "conselho nacional do ministério","ordem dos advogados","conselho administrativo de defesa"]):
        if _has(o, ["empresarial","empresário","empresario","de comércio exterior"]): return "Mercado"
        return "Estado"
    # 4) aparato estatal e entes publicos
    if _has(o, STATE): return "Estado"
    # 5) mercado explicito
    if _has(o, MARKET): return "Mercado"
    # 6) terceiro setor (inclui marcadores genericos)
    if _has(o, THIRD): return "Terceiro setor"
    return "Indefinido"

