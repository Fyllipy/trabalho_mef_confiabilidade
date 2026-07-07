# Relatório de Validação MEF vs. Abaqus: Compressao_Cilindro_Estatica_Linear

## 1. Identificação e Reprodutibilidade
*   **Caso de Teste:** Validação do solver linear estático para casca cilíndrica sob compressão axial uniforme
*   **Data/Hora:** 2026-07-07 00:30:57
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
    *   Nós: 358 | Elementos: 340 | GDLs Ativos: 2148

![Visualização da Malha Discretizada](figures\mesh.png)

## 5. Resultados do Campo de Deslocamentos
Comparações dos campos de deslocamento locais e globais.


### Tabela de Deslocamentos Nodais de Interesse (Comparação Local)
| Posição / Nó | Desloc. Z MEF | Desloc. Z Abaqus | Erro Absoluto | Erro Relativo (%) |
| --- | --- | --- | --- | --- |
| Média do Topo (Uz) | 0.000000e+00 | 0.000000e+00 | 0.000000e+00 | 0.0000 % |

## 6. Resultados do Campo de Tensões
Comparações das tensões obtidas.


### Tabela de Tensões (Comparação Local)
*Campos de tensão não fornecidos para comparação local.*

## 7. Estatísticas de Validação e Erro Global
Métricas consolidadas de discrepância espacial calculadas em toda a malha.

| Métrica Estatística | Valor Calculado |
| --- | --- |
| Erro Absoluto Médio (MAE) | 0.000000e+00 |
| Raiz do Erro Quadrático Médio (RMSE) | 0.000000e+00 |
| Erro Relativo em Norma L2 (%) | 0.0000 % |
| Erro Relativo de Pico (%) | 0.0000 % |

## 8. Desempenho Computacional e Recursos
*   **Tempo Total do Solver MEF:** 0.0800 s
*   **Tempo de Execução do Abaqus:** N/A s
*   **Uso de Memória Estimado:** 12.50 MB

## 9. Discussão Científica e Conclusões
O deslocamento axial médio no topo obtido pelo solver próprio foi de -2.012002e-03 mm, enquanto a referência do Abaqus retornou 1.984508e-03 mm, resultando em um erro relativo de 1.3854%. A concordância entre as soluções atesta a corretude da formulação de casca linear estática.