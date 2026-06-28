# Convenções Matemáticas e Estruturais do Projeto

Este documento define todas as convenções matemáticas que guiarão o desenvolvimento do Solver MEF para a análise de cascas cilíndricas imperfeitas, garantindo a coesão de todas as rotinas.

## 1. Sistema de Coordenadas

*   **Global (X, Y, Z)**: Sistema de coordenadas cartesianas no qual a geometria global da casca é definida.
*   **Local do Elemento (x, y, z)**: Sistema atrelado ao plano médio do elemento de casca. O plano $x-y$ representa o plano médio, enquanto o eixo $z$ define a direção normal (espessura).
*   **Natural / Isoparamétrico ($\xi$, $\eta$)**: Coordenadas paramétricas bidimensionais variando no intervalo $[-1, 1]$.

## 2. Ordem dos Graus de Liberdade (GDL)

Para cada nó $i$ da malha, a ordem padrão dos 6 graus de liberdade é estritamente definida como:

1.  $u_{X,i}$ : Translação global na direção X
2.  $u_{Y,i}$ : Translação global na direção Y
3.  $u_{Z,i}$ : Translação global na direção Z
4.  $\theta_{X,i}$ : Rotação em torno do eixo global X
5.  $\theta_{Y,i}$ : Rotação em torno do eixo global Y
6.  $\theta_{Z,i}$ : Rotação em torno do eixo global Z (Drilling DOF)

*Nota: Em elementos de casca que nativamente possuem 5 GDL (sem o drilling DOF), a rotação em torno do eixo normal (frequentemente mapeada para o eixo Z global em cascas planas não coplanares) recebe tratamento específico (rigidez fictícia ou formulação drill) para evitar singularidades durante a montagem global.*

## 3. Numeração dos Nós e Elementos (Elemento QUAD4)

O elemento base de desenvolvimento é o quadrilátero de 4 nós (QUAD4). O percurso da numeração dos nós locais, visto pelo eixo $z$ positivo (regra da mão direita), será **anti-horário**:

*   Nó 1 local: $(\xi = -1, \eta = -1)$
*   Nó 2 local: $(\xi =  1, \eta = -1)$
*   Nó 3 local: $(\xi =  1, \eta =  1)$
*   Nó 4 local: $(\xi = -1, \eta =  1)$

## 4. Ordem e Posição dos Pontos de Gauss

A integração numérica padrão para o elemento QUAD4 utilizará uma regra de Gauss-Legendre completa ($2 \times 2$), resultando em 4 pontos de integração:

*   PG 1: $(-\frac{1}{\sqrt{3}}, -\frac{1}{\sqrt{3}})$
*   PG 2: $( \frac{1}{\sqrt{3}}, -\frac{1}{\sqrt{3}})$
*   PG 3: $( \frac{1}{\sqrt{3}},  \frac{1}{\sqrt{3}})$
*   PG 4: $(-\frac{1}{\sqrt{3}},  \frac{1}{\sqrt{3}})$

Os pesos para todos os 4 pontos são $W_i = 1.0$.

*(Para tratamento do "shear locking" no futuro, poderá ser introduzida subintegração $1 \times 1$ exclusivamente para a matriz de cisalhamento, com PG em $(0,0)$ e peso $4.0$).*

## 5. Convenção de Sinais e Forças Internas

*   **Esforços Normais (Membrana)**: Tração é positiva (+); Compressão é negativa (-).
*   **Momentos Fletores**: O momento fletor positivo traciona as fibras inferiores da casca (onde a coordenada local $z < 0$).
*   **Rotações**: Seguem rigorosamente a regra da mão direita ao redor dos eixos correspondentes.

## 6. Convenção de Matrizes e Vetores (Notação de Voigt)

Os tensores de tensão e deformação são mapeados em arranjos vetoriais para uso direto com matrizes constitutivas (matriz $D$ ou $C$):

*   **Comportamento de Membrana**:
    *   Deformações: $\boldsymbol{\epsilon}_m = [\epsilon_x, \epsilon_y, \gamma_{xy}]^T$
    *   Esforços: $\mathbf{N} = [N_x, N_y, N_{xy}]^T$
*   **Comportamento de Flexão**:
    *   Curvaturas: $\boldsymbol{\kappa} = [\kappa_x, \kappa_y, \kappa_{xy}]^T$
    *   Esforços: $\mathbf{M} = [M_x, M_y, M_{xy}]^T$
*   **Comportamento de Cisalhamento Transversal** (Teoria de Reissner-Mindlin):
    *   Deformações de cisalhamento: $\boldsymbol{\gamma}_s = [\gamma_{xz}, \gamma_{yz}]^T$
    *   Esforços transversos: $\mathbf{Q} = [Q_x, Q_y]^T$
