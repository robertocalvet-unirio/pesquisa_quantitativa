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

Os arquivos devem ser colocados em um diretorio (por convencao, "dados/").
O script le todos os arquivos eventos-*.json desse diretorio, une-os, elimina
duplicidades por identificador de evento e atribui cada evento ao seu
ano-calendario pela data de inicio. Os meses de janeiro aparecem vazios em todos
os anos (recesso parlamentar); a comparabilidade entre anos preserva-se de
fevereiro a dezembro.

O download dos arquivos pode ser feito pelo script auxiliar baixar_dados.py.
O dominio dadosabertos.camara.leg.br precisa estar acessivel na rede.


--------------------------------------------------------------------------------
3. EXECUCAO
--------------------------------------------------------------------------------

Pipeline principal (metricas por ano, retencao interanual, persistencia):

    python3 analise_multiano.py dados

    (equivalente: DADOS_DIR=dados python3 analise_multiano.py)

O diretorio de saida default e "saida_multiano/" e pode ser alterado pela
variavel de ambiente SAIDA_DIR.

O componente estocastico (teste de permutacao e teste de robustez a ruido) tem
semente fixa, de modo que a execucao e deterministica e reproduz os mesmos
numeros a cada corrida.


--------------------------------------------------------------------------------
4. SAIDAS
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
5. ARQUIVOS DE CODIGO
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

compute_kappa.py
    Confiabilidade interavaliador e validacao do classificador (ver secao 6).

baixar_dados.py
    Download dos arquivos de eventos do Portal de Dados Abertos.

requirements.txt
    Dependencias.


--------------------------------------------------------------------------------
6. VALIDACAO DO CLASSIFICADOR SETORIAL (ESTADO)
--------------------------------------------------------------------------------

A validacao do classificador por gazetteer contra padrao-ouro humano, por
acuracia e por confiabilidade interavaliador (kappa de Cohen), depende da dupla
codificacao independente de uma amostra de 150 organizacoes, registrada em:

    codificacao_setorial.csv

Essa codificacao e etapa de trabalho humano e esta PENDENTE: as colunas dos dois
codificadores ainda nao foram preenchidas. Enquanto isso, o artigo mantem, no
Anexo de validacao, um espaco reservado (marcado em vermelho) com a forma e a
extensao do resultado final, a ser substituido pelos valores reais apos a
codificacao.

Para computar os indices apos preencher as duas colunas:

    python3 compute_kappa.py

O mesmo script ja computa, a partir de predicoes_classificador.csv, a
concordancia entre a heuristica anterior e o classificador por gazetteer
(70,0% sobre a amostra de 150), reportada no artigo como medida de consistencia
entre os dois procedimentos, nao de acuracia.


--------------------------------------------------------------------------------
7. ESTRUTURA SUGERIDA DO REPOSITORIO
--------------------------------------------------------------------------------

    pesquisa_quantitativa/
    |- README.txt
    |- requirements.txt
    |- analise_multiano.py
    |- extracao_camara.py
    |- compute_kappa.py
    |- baixar_dados.py
    |- codificacao_setorial.csv          (amostra n=150 para dupla codificacao)
    |- predicoes_classificador.csv        (predicoes heuristica x gazetteer)
    |- dados/
    |   |- eventos-2023.json
    |   |- eventos-2024.json
    |   |- eventos-2025.json
    |- saida_multiano/                    (gerado pela execucao)
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
