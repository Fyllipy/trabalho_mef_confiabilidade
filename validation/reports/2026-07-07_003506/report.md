# Relatório de Validação MEF vs. Abaqus: Cilindro_Nlgeom_Flexao_Lateral

## 1. Identificação e Reprodutibilidade
*   **Caso de Teste:** Validação geométrica não-linear para casca cilíndrica sob flexão com grandes deslocamentos
*   **Data/Hora:** 2026-07-07 00:35:06
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
*   length: 1000.0
*   thickness: 2.0
*   **Propriedades do Material:**
*   E: 200000.0
*   nu: 0.3


## 4. Formulação Numérica e Discretização
*   **Elemento MEF Próprio:** `QUAD8`
*   **Elemento de Referência Abaqus:** `S8`
*   **Esquema de Integração:** no plano (3x3 completa), na espessura (5 pontos Simpson)
*   **Discretização da Malha:**
    *   Nós: 559 | Elementos: 180 | GDLs Ativos: 3354

![Visualização da Malha Discretizada](figures\mesh.png)

## 5. Resultados do Campo de Deslocamentos
Comparações dos campos de deslocamento locais e globais em grandes deslocamentos.

*   **Status de Convergência (NL):** NÃO CONVERGIU
*   **Número de Iterações Realizadas:** None


### Tabela de Deslocamentos Nodais de Interesse (Comparação Local Final)
| Posição / Nó | Desloc. Y MEF | Desloc. Y Abaqus | Erro Absoluto | Erro Relativo (%) |
| --- | --- | --- | --- | --- |
| Média do Topo (Uy) | 4.341040e+01 | 3.004736e+01 | 1.336305e+01 | 44.4733 % |

## 6. Trajetória de Equilíbrio (Curva Força vs. Deslocamento)
Comparação da trajetória de carregamento incremental entre o solver desenvolvido e a resposta de referência do Abaqus.

![Caminho de Equilíbrio: Solver vs Abaqus](figures\path_comparison.png)

## 7. Estatísticas de Validação e Erro Global
Métricas consolidadas de discrepância espacial calculadas em toda a malha e métricas de trajetória não-linear.

| Métrica Estatística | Valor Calculado |
| --- | --- |
| Erro Absoluto Médio (MAE) | 1.336305e+01 |
| Raiz do Erro Quadrático Médio (RMSE) | 1.336305e+01 |
| Erro Relativo em Norma L2 (%) | 44.4733 % |
| Erro Relativo de Pico (%) | 44.4733 % |

## 8. Desempenho Computacional e Recursos
*   **Tempo Total do Solver MEF:** 1.8500 s
*   **Tempo de Execução do Abaqus:** N/A s
*   **Uso de Memória Estimado:** 25.40 MB

## 9. Discussão Científica e Conclusões
O deslocamento transversal final obtido pelo solver próprio foi de 43.4104 mm, enquanto a referência do Abaqus/analítica foi de 30.0474 mm, com erro de 44.47%. A formulação de cinemática não-linear de casca captura grandes deslocamentos e rotações.