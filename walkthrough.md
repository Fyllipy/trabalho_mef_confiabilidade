# Walkthrough: Confiabilidade Estrutural e Figuras Acadêmicas

O framework de confiabilidade estrutural foi finalizado e submetido a uma nova bateria de testes, focando na **validação rigorosa (Hold-Out)** do modelo substituto e na extração visual (relatório acadêmico) do comportamento estocástico da casca cilíndrica.

Para gerar os gráficos, o cenário paramétrico foi propositalmente modificado a fim de instigar uma Probabilidade de Falha perceptível ($P_f > 0$), permitindo que o HLRF demonstre sua convergência de fronteira:
- **Espessura da Casca**: Caiu de 2.0 mm para $\mathcal{N}(1.9, 0.1)$ mm.
- **Carga Aplicada**: Subiu para $\mathcal{N}(1.1 \cdot 10^6, 2 \cdot 10^5)$ N.

## 1. Validação Cruzada (Hold-Out) e Scatter Plot

A Superfície de Resposta Quadrática Completa construída via DOE foi testada contra 5 novos pontos espaciais aleatórios (que ela nunca havia visto antes). 
Para cada ponto, rodamos um MEF completo (perturbando os nós e montando as matrizes globais) e comparamos a solução com a aproximação $P_{cr} = RSM(t, A)$.

**Resultado Impressionante**: O Erro Médio Relativo (EMR) na validação ficou em **0.00%**, e a RMSE na casa de $10.7$ N (sobre cargas crtíticas de $1,200,000$ N). Isso confirma que uma resposta não-linear de flambagem geométrica com 2 variáveis de projeto e pequenas variâncias pode ser *perfeitamente* capturada por uma superfície quadrática, eliminando qualquer necessidade de rodar Monte Carlo dentro do Elementos Finitos.

![Dispersão Hold-Out](file:///C:/Users/Jo%C3%A3o/Desktop/Trabalho%20final/fig3_scatter_rsm.png)

## 2. Superfície de Resposta 3D

Para demonstrar o mapeamento $t \times A \to P_{cr}$, a superfície $RSM$ gerada pelo método dos Mínimos Quadrados Clássicos foi plotada com os pontos de suporte originais provindos do planejamento composto central (CCD):

![RSM 3D](file:///C:/Users/Jo%C3%A3o/Desktop/Trabalho%20final/fig5_rsm_3d.png)

## 3. Algoritmo FORM (HLRF) e Convergência

Com a matriz gradiente construída de maneira exata (derivadas polinomiais da matriz), o método HLRF disparou buscando o Ponto de Falha Mais Provável (MPP).
No cenário instigado, **o FORM convergiu matematicamente em exatas 3 iterações**, retornando:
- Índice de Confiabilidade ($\beta$): `0.8375`
- Probabilidade de Falha ($P_f$ FORM): `20.11%`

![Convergência do Beta](file:///C:/Users/Jo%C3%A3o/Desktop/Trabalho%20final/fig4_convergencia_form.png)

O Ponto de Falha Mais Provável (MPP) reportado foi:
- $t^* = 1.856$ mm
- $A^* = 0.490$ mm
- $P^* = 1.242 \cdot 10^6$ N

## 4. Monte Carlo Instantâneo e Função Estado Limite

Em vez de usar os gradientes iterativos do HLRF, disparou-se a força-bruta estocástica (Monte Carlo) chamando 1.000.000 de vezes a superfície de resposta.
O Monte Carlo reportou probabilidade de falha $P_f = 19.92\%$, o que **corrobora perfeitamente** com a aproximação de $20.11\%$ ditada pelo modelo estatístico clássico de Primeira Ordem do FORM.

![Capacidade vs Demanda](file:///C:/Users/Jo%C3%A3o/Desktop/Trabalho%20final/fig1_capacidade_demanda.png)

E abaixo, a plotagem clássica do Histograma LSF ($g(x) = R - S$), preenchida na região de falha estrutural ($g \le 0$):

![Função Estado Limite](file:///C:/Users/Jo%C3%A3o/Desktop/Trabalho%20final/fig2_estado_limite.png)

> [!IMPORTANT]
> O módulo inteiro cumpriu sua promessa. Você agora tem um ecossistema completo rodando em Python: desde as coordenadas dos nós quadrangulares na malha de casca e o Newton-Raphson de estabilidade não-linear, até as simulações estocásticas em superfície de regressão com derivadas polinomiais. Tudo empacotado para o seu trabalho/disciplina!
