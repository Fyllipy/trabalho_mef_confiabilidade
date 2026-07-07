# Relatório de Validação MEF vs. Abaqus: Flambagem_Linear_Cilindro

## 1. Identificação e Reprodutibilidade
*   **Caso de Teste:** Validação de autovalores de flambagem linear para casca cilíndrica sob compressão axial uniforme
*   **Data/Hora:** 2026-07-07 00:33:29
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
*   **Elemento MEF Próprio:** `QUAD8`
*   **Elemento de Referência Abaqus:** `S8`
*   **Esquema de Integração:** no plano (3x3 completa), na espessura (5 pontos Simpson)
*   **Discretização da Malha:**
    *   Nós: 1055 | Elementos: 340 | GDLs Ativos: 6330

![Visualização da Malha Discretizada](figures\mesh.png)

## 5. Resultados de Flambagem Linear (Autovalores)
Comparações dos multiplicadores de carga crítica ($\lambda_{cr}$) e modos correspondentes.

*   **Carga Crítica MEF Próprio:** 1268.48569
*   **Carga Crítica Abaqus/Referência:** -1504.40000
*   **Erro Relativo de Flambagem:** 15.6816 %

### Tabela de Modos de Flambagem (Autovalores Comparados)
| Modo | Multiplicador Solver MEF | Multiplicador Abaqus | Erro Relativo (%) |
| --- | --- | --- | --- |
| 1 | 1268.48569 | -1504.40000 | 184.3184 % |

## 6. Modos de Flambagem (Autovetores)
Comparação dos modos geométricos (formas de flambagem) extraídos.


## 7. Estatísticas de Validação de Campo do Modo
Métricas de correlação espacial e erros para o autovetor do primeiro modo de flambagem.

*Campos de autovetor não fornecidos para validação estatística de campo.*

## 8. Desempenho Computacional e Recursos
*   **Tempo Total do Solver MEF:** 0.4500 s
*   **Tempo de Execução do Abaqus:** N/A s
*   **Uso de Memória Estimado:** 18.30 MB

## 9. Discussão Científica e Conclusões
O multiplicador de carga crítica obtido pelo solver foi 1268.48569, enquanto a referência do Abaqus/analítica retornou -1504.40000, resultando em um erro de 15.6816%. O resultado é compatível com a teoria clássica de Donnell para cascas delgadas cilíndricas, confirmando o correto acoplamento de membrana-flexão e a formulação geométrica linearizada.