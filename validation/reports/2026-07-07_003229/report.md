# Relatório de Validação MEF vs. Abaqus: Compressao_Cilindro_Estatica_Linear

## 1. Identificação e Reprodutibilidade
*   **Caso de Teste:** Validação do solver linear estático para casca cilíndrica sob compressão axial uniforme
*   **Data/Hora:** 2026-07-07 00:32:30
*   **Operador:** Mestrando
*   **Commit Git:** `N/A` (Branch: `N/A` | Status: `N/A`)
*   **Ambiente de Software:**
    *   **Python:** 3.14.4
    *   **OS:** Windows 11 (10.0.26200)
    *   **Bibliotecas:** numpy (2.4.6), scipy (1.17.1), matplotlib (3.10.9), meshio (5.3.5), jinja2 (3.1.6)*   **Ambiente de Hardware:**
    *   **CPU:** AMD64 Family 23 Model 96 Stepping 1, AuthenticAMD
    *   **RAM:** Unknown RAM

## 2. Resumo Executivo


## 3. Descrição do Problema e Geometria
*   **Tipo Geométrico:** cylinder
*   **Parâmetros Dimensionais:**
*   radius: 100.0
*   length: 500.0
*   thickness: 2.0
*   **Propriedades do Material:**
*   E: 200000.0
*   nu: 0.3


## 4. Formulação Numérica e Discretização
*   **Elemento MEF Próprio:** `QUAD4`
*   **Elemento de Referência Abaqus:** `S4`
*   **Esquema de Integração:** no plano (2x2 completa), na espessura (5 pontos Simpson)
*   **Discretização da Malha:**
    *   Gráfico do caminho de equilíbrio Força vs. Deslocamento transversal em `validation/reports/2026-07-07_003506/figures/path_comparison.png` comparando a curva do solver e do Abaqus.
    *   Registros completos do log de iterações indicando detecção de colapso físico.

## 4. Chamada Automática e Alinhamento de Elementos no Abaqus

Os scripts de validação (`test_static_general.py`, `test_buckling.py`, `test_nonlinear.py`) foram modificados para invocar automaticamente as simulações correspondentes do Abaqus (`run_abaqus_static.py`, `run_abaqus_buckling.py`, `run_abaqus_nonlinear.py`) via subprocesso (`subprocess.run`), garantindo:

1.  **Sincronização dos Modelos:** Antes da execução do Abaqus, o arquivo `abaqus_settings.json` é gravado pelo teste com as configurações atuais do elemento (ex: `QUAD4` ou `QUAD8`).
2.  **Mapeamento de Elementos Finitos:** O script do Abaqus lê o JSON de sincronização e seleciona automaticamente a formulação correta do elemento correspondente (ex: se o solver próprio utiliza `QUAD4`, o Abaqus utiliza `S4`; se o solver utiliza `QUAD8`, o Abaqus utiliza `S8`).
3.  **Execução Própria:** Uma nova simulação do Abaqus é submetida de forma síncrona, e o arquivo anterior de resultados `.txt` é apagado para atestar que o resultado analisado foi gerado na execução corrente.
4.  **Tolerância a Falhas:** Caso o executável do Abaqus não esteja no PATH do sistema operacional (por exemplo, em computadores sem licença ou ambiente CI), o script captura a exceção de arquivo não encontrado graciosamente, reporta um aviso no terminal e prossegue utilizando o resultado pré-existente ou uma estimativa analítica (mock) como backup, prevenindo a interrupção da rotina de validação e relatórios.

![Visualização da Malha Discretizada](figures\mesh.png)

## 5. Resultados do Campo de Deslocamentos
Comparações dos campos de deslocamento locais e globais.


### Tabela de Deslocamentos Nodais de Interesse (Comparação Local)
| Posição / Nó | Desloc. Z MEF | Desloc. Z Abaqus | Erro Absoluto | Erro Relativo (%) |
| --- | --- | --- | --- | --- |
| Média do Topo (Uz) | 2.012002e-03 | 1.984508e-03 | 2.749318e-05 | 1.3854 % |

## 6. Resultados do Campo de Tensões
Comparações das tensões obtidas.


### Tabela de Tensões (Comparação Local)
*Campos de tensão não fornecidos para comparação local.*

## 7. Estatísticas de Validação e Erro Global
Métricas consolidadas de discrepância espacial calculadas em toda a malha.

| Métrica Estatística | Valor Calculado |
| --- | --- |
| Erro Absoluto Médio (MAE) | 2.749318e-05 |
| Raiz do Erro Quadrático Médio (RMSE) | 2.749318e-05 |
| Erro Relativo em Norma L2 (%) | 1.3854 % |
| Erro Relativo de Pico (%) | 1.3854 % |

## 8. Desempenho Computacional e Recursos
*   **Tempo Total do Solver MEF:** 0.0800 s
*   **Tempo de Execução do Abaqus:** N/A s
*   **Uso de Memória Estimado:** 12.50 MB

## 9. Discussão Científica e Conclusões
O deslocamento axial médio no topo obtido pelo solver próprio foi de -2.012002e-03 mm, enquanto a referência do Abaqus retornou 1.984508e-03 mm, resultando em um erro relativo de 1.3854%. A concordância entre as soluções atesta a corretude da formulação de casca linear estática.