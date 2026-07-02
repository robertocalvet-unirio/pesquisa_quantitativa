================================================================================
PACOTE DE REPRODUTIBILIDADE
Analise multianual (2023-2025) da rede de coparticipacao organizacional
nas audiencias, debates e comissoes gerais da Camara dos Deputados,
tratada como arena de relacoes interorganizacionais (RIO).
================================================================================

Repositorio: https://github.com/robertocalvet-unirio/pesquisa_quantitativa

Este pacote reproduz integralmente os numeros reportados no artigo. Todos os
valores do corpo do artigo derivam de execucao deste codigo sobre os arquivos
de dados abertos da Camara dos Deputados, e sao gravados nas saidas em JSON e
XLSX. Numeros provenientes de outros trabalhos sao apenas citados no artigo e
nao constam destas saidas.

Duas etapas independentes compoem o pacote:
  (A) o pipeline de rede (secoes 2-5), que produz cobertura, composicao setorial,
      centralidade, teste de permutacao, retencao e persistencia;
  (B) a validacao do classificador setorial (secao 6), que produz o kappa de
      Cohen entre dois codificadores humanos e a acuracia do classificador por
      gazetteer contra o consenso humano.


--------------------------------------------------------------------------------
1. REQUISITOS
--------------------------------------------------------------------------------

Python 3.10 ou superior.

Dependencias (arquivo requirements.txt):
    networkx
    matplotlib
    openpyxl

Instalacao:
    pip install -r requirements.txt

Em ambiente gerenciado (Debian/Ubuntu), pode ser necessario:
    pip install -r requirements.txt --break-system-packages


--------------------------------------------------------------------------------
2. DADOS DE ENTRADA
--------------------------------------------------------------------------------

Fonte: Portal de Dados Abertos da Camara dos Deputados.
    https://dadosabertos.camara.leg.br

Arquivos esperados, um por ano-calendario, no formato JSON de eventos:
    eventos-2023.json
    eventos-2024.json
    eventos-2025.json

Sao TRES arquivos anuais. O recorte cobre apenas 2023, 2024 e 2025; nao ha dados
de 2026. O script le todos os arquivos eventos-*.json do diretorio de dados,
une-os, elimina duplicidades por identificador de evento e atribui cada evento
ao seu ano-calendario pela data de inicio (campo dataHoraInicio). Os meses de
janeiro aparecem vazios em todos os anos (recesso parlamentar); a comparabilidade
entre anos preserva-se de fevereiro a dezembro.

O download dos arquivos pode ser feito pelo script auxiliar baixar_dados.py.
O dominio dadosabertos.camara.leg.br precisa estar acessivel na rede.


--------------------------------------------------------------------------------
3. EXECUCAO DO PIPELINE DE REDE
--------------------------------------------------------------------------------

Pipeline principal (metricas por ano, retencao interanual, persistencia):

    python3 analise_multiano.py dados

    (equivalente: DADOS_DIR=dados python3 analise_multiano.py)

O diretorio de saida default e "saida_multiano/" e pode ser alterado pela
variavel de ambiente SAIDA_DIR.

O componente estocastico (teste de permutacao e teste de robustez a ruido) tem
semente fixa (42), de modo que a execucao e deterministica e reproduz os mesmos
numeros a cada corrida.


--------------------------------------------------------------------------------
4. SAIDAS DO PIPELINE DE REDE
--------------------------------------------------------------------------------

resultados_multiano.json
    Todos os numeros por ano (cobertura, composicao setorial, descritores da
    rede, centralidade, teste de permutacao sob as duas rotulagens, teste de
    robustez a ruido), a retencao interanual de diades e de organizacoes, e a
    persistencia de organizacoes ao longo do trienio.

resultados_multiano.xlsx
    Onze abas:
      1.  Resumo_por_ano          cobertura e descritores da rede, por ano
      2.  Composicao_por_ano      contagem setorial (Estado, Mercado, Terceiro
                                  setor, Indefinido), por ano
      3.  Homofilia_permutacao    teste de permutacao com as duas rotulagens
                                  (gazetteer e heuristica), observado, nulo,
                                  desvio-padrao, z e p
      4.  Top_intermediacao       organizacoes de maior intermediacao, por ano
      5.  Retencao_diadica        diades retidas entre anos consecutivos
      6.  Retencao_organizacoes   organizacoes retidas entre anos consecutivos
      7.  Persistencia_orgs       distribuicao por numero de anos de presenca e
                                  total de organizacoes distintas no trienio
      8.  Brokers_persistentes    organizacoes no topo de intermediacao em mais
                                  de um ano
      9.  Recorrencia_pesos       distribuicao de recorrencia das diades
      10. Robustez_ruido          z medio do teste de homofilia sob perturbacao
                                  crescente dos rotulos (ano de 2025) e limiar
                                  de significancia
      11. Metadados               eventos unicos, anos completos, ano parcial,
                                  eventos por ano

Figuras (geradas em PNG): distribuicao de participacoes por organizacao,
composicao setorial e diversidade setorial por evento.


--------------------------------------------------------------------------------
5. VALIDACAO DO CLASSIFICADOR SETORIAL
--------------------------------------------------------------------------------

A validacao afere a qualidade do classificador setorial por gazetteer contra um
padrao-ouro humano, por dois indices: (i) confiabilidade interavaliador entre os
dois codificadores humanos, pelo kappa de Cohen; e (ii) acuracia do classificador
contra o consenso dos codificadores. A dupla codificacao independente de uma
amostra de 150 organizacoes foi realizada por dois codificadores (identificados
nos nomes de arquivo). Esta etapa esta CONCLUIDA.

Entradas, distinguidas por natureza:

  (a) Codificacao humana (padrao-ouro), uma coluna preenchida por codificador:
        codificacao_setorial_fabiano.xlsx   coluna setor_codificador_1
        codificacao_setorial_vanessa.xlsx   coluna setor_codificador_2
        codificacao_setorial_v2.csv         consolidacao das duas (ambas as
                                            colunas num unico arquivo), para
                                            leitura e adjudicacao; e a planilha
                                            referida no anexo de validacao do
                                            artigo

  (b) Predicoes dos classificadores --- NAO e codificacao humana:
        predicoes_classificador.csv         colunas id, organizacao,
                                            heuristica_antiga, classificador_novo

      As duas colunas de predicao sao saidas DETERMINISTICAS dos classificadores
      setor_old (heuristica anterior por palavras-chave) e setor_new (classificador
      por gazetteer), definidos em extracao_camara.py e aplicados aos 150 nomes de
      organizacao da amostra. Nao ha julgamento humano nessas colunas; por isso o
      arquivo e regeneravel por codigo (ver gerar_predicoes.py, abaixo), e nao um
      artefato de anotacao.

Execucao (dois passos):

    python3 gerar_predicoes.py        # gera predicoes_classificador.csv a partir de
                                      # codificacao_setorial_v2.csv, aplicando
                                      # setor_old e setor_new a cada organizacao
    python3 compute_kappa_final.py    # computa kappa, IC, acuracia e decomposicao

O gerar_predicoes.py torna as predicoes regeneraveis por codigo, em vez de um
arquivo estatico que teria de ser aceito de boa-fe: documenta, de forma auditavel,
que aquelas colunas sao saida de classificador e nao uma segunda codificacao humana.
O compute_kappa_final.py le as duas planilhas dos codificadores, computa o kappa de
Cohen e a concordancia observada, deriva o consenso (casos em que ambos concordam)
como padrao-ouro, mede a acuracia do classificador por gazetteer contra esse consenso
e decompoe os desacertos em abstencoes (Indefinido) e atribuicoes divergentes. O
intervalo de confianca de 95% do kappa e obtido por bootstrap (10000 reamostragens,
semente fixa 42), de modo deterministico. A saida e impressa e gravada em
kappa_resultado.json.

Resultados reproduzidos (gravados em kappa_resultado.json):

    n = 150
    kappa de Cohen = 0,68            (0,6752; IC 95% bootstrap [0,57; 0,78])
    concordancia observada = 82,0%   (123 de 150)
    consenso (padrao-ouro) = 123
    acuracia do gazetteer no consenso = 81,3%   (100 de 123)
    quando atribui (exclui abstencao) = 93,5%   (100 de 107)
    desacertos = 23 = 16 abstencoes + 7 atribuicoes divergentes
    divergencias entre codificadores = 27, das quais 11 do tipo pessoa
        classificada como organizacao (Indefinido vs Estado)

O numero de 70,0% de concordancia entre a heuristica anterior e o classificador
por gazetteer, reportado no artigo como medida de consistencia entre os dois
procedimentos (nao de acuracia), e computado sobre as duas colunas de
predicoes_classificador.csv (heuristica_antiga vs classificador_novo).


--------------------------------------------------------------------------------
6. ARQUIVOS DE CODIGO
--------------------------------------------------------------------------------

analise_multiano.py
    Pipeline multianual. Une os arquivos por ano, deduplica, bina por
    ano-calendario, calcula metricas por ano, retencao entre anos consecutivos
    e persistencia, e grava JSON e XLSX. Reutiliza, sem alteracao, o modulo
    extracao_camara.py.

extracao_camara.py
    Modulo compartilhado: extracao das organizacoes do texto livre das pautas
    (orientada a marcadores institucionais, com normalizacao leve de grafia) e
    classificacao setorial por gazetteer e entity linking.

gerar_predicoes.py
    Gera predicoes_classificador.csv a partir de codificacao_setorial_v2.csv,
    aplicando os classificadores setor_old e setor_new de extracao_camara.py a
    cada organizacao da amostra. As predicoes sao saida deterministica de codigo,
    nao codificacao humana.

compute_kappa_final.py
    Validacao do classificador (secao 5): kappa de Cohen com IC por bootstrap,
    concordancia observada, acuracia contra o consenso e decomposicao dos
    desacertos. Grava kappa_resultado.json.

baixar_dados.py
    Download dos arquivos de eventos do Portal de Dados Abertos.

requirements.txt
    Dependencias.


--------------------------------------------------------------------------------
7. ESTRUTURA DO REPOSITORIO
--------------------------------------------------------------------------------

    pesquisa_quantitativa/
    |- README.txt
    |- requirements.txt
    |- analise_multiano.py
    |- extracao_camara.py
    |- gerar_predicoes.py
    |- compute_kappa_final.py
    |- baixar_dados.py
    |- codificacao_setorial_fabiano.xlsx    (codificador 1; n=150)
    |- codificacao_setorial_vanessa.xlsx    (codificador 2; n=150)
    |- codificacao_setorial_v2.csv          (consolidacao das duas codificacoes)
    |- predicoes_classificador.csv          (heuristica x gazetteer, por id)
    |- kappa_resultado.json                 (saida da validacao)
    |- eventos-2023.json
    |- eventos-2024.json
    |- eventos-2025.json
    |- saida_multiano/                      (gerado pela execucao do pipeline)
        |- resultados_multiano.json
        |- resultados_multiano.xlsx


--------------------------------------------------------------------------------
8. OBSERVACOES SOBRE O RECORTE
--------------------------------------------------------------------------------

A janela 2023-2025 corresponde aos tres anos completos do atual governo federal.
A restricao a um unico governo e metodologica: evita o confundidor da
renomeacao, fusao e criacao de ministerios na transicao de 2022 para 2023, que
quebraria artificialmente a identidade das organizacoes entre anos e
contaminaria a medida de retencao e a leitura da composicao. O custo assumido e
um horizonte longitudinal curto, de dois intervalos interanuais.
