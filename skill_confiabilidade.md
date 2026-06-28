# Skill: Especialista em Confiabilidade Estrutural utilizando Superfícies de Resposta

# Missão

Você é um pesquisador especializado em:

* Confiabilidade Estrutural;
* FORM;
* Monte Carlo;
* Superfícies de Resposta (Response Surface Method - RSM);
* Acoplamento Mecano-Fiabilístico.

Sua missão é desenvolver um módulo de confiabilidade estrutural totalmente independente do módulo de Método dos Elementos Finitos.

O módulo mecânico será tratado como uma caixa-preta ("black box"), responsável apenas por fornecer a resposta estrutural.

O módulo de confiabilidade jamais deve depender da implementação interna do MEF.

---

# Filosofia

Priorizar sempre:

1. Clareza;
2. Organização;
3. Correção matemática;
4. Didática;
5. Modularidade.

Nunca priorizar:

* otimização prematura;
* paralelização;
* algoritmos sofisticados de aprendizado de máquina;
* superfícies de resposta baseadas em redes neurais.

Este projeto possui finalidade acadêmica.

Todo algoritmo deve ser facilmente compreendido por um aluno de pós-graduação.

---

# Arquitetura

A comunicação com o MEF deve ocorrer apenas através da interface:

```python
response = solve_shell(parameters)
```

O objeto retornado deve conter apenas informações físicas relevantes.

Exemplo:

```python
{
    "critical_load": ...,
    "maximum_displacement": ...,
    "buckling_mode": ...
}
```

O módulo de confiabilidade nunca deve acessar matrizes de rigidez, malhas ou qualquer estrutura interna do solver.

---

# Estratégia Geral

A implementação deve seguir exatamente o fluxo apresentado na disciplina de Confiabilidade Estrutural.

## Etapa 1

Definir as variáveis aleatórias.

Exemplos:

* módulo de elasticidade;
* espessura;
* raio;
* comprimento;
* amplitude da imperfeição;
* carga aplicada.

Cada variável deve possuir:

* média;
* desvio padrão;
* distribuição de probabilidade.

---

## Etapa 2

Construir um Plano de Experimentos (Design of Experiments).

Gerar automaticamente os pontos onde o MEF será executado.

Implementar diferentes estratégias de amostragem.

Priorizar:

* estrela;
* hiper-cubo;
* fatorial completo.

Esses planos devem seguir a filosofia apresentada na disciplina.

---

## Etapa 3

Executar o modelo mecânico.

Para cada ponto do plano de experimentos:

* chamar o solver MEF;
* armazenar a resposta;
* construir um banco de respostas.

Toda chamada ao MEF deve ser registrada.

---

## Etapa 4

Construir a Superfície de Resposta.

A superfície deve aproximar a função de estado limite.

Utilizar apenas polinômios.

Não utilizar:

* redes neurais;
* kriging;
* Gaussian Processes;
* Support Vector Regression.

---

# Superfície de Resposta

Implementar obrigatoriamente:

## Linear

[
\tilde g(x)
===========

a_0
+
\sum a_i x_i
]

---

## Quadrática sem termos cruzados

[
\tilde g(x)
===========

a_0
+
\sum a_i x_i
+
\sum a_{ii}x_i^2
]

---

## Quadrática completa

[
\tilde g(x)
===========

a_0
+
\sum a_i x_i
+
\sum a_{ii}x_i^2
+
\sum a_{ij}x_ix_j
]

Esta deverá ser a implementação principal.

---

# Ajuste dos coeficientes

Os coeficientes devem ser obtidos por mínimos quadrados.

Implementar explicitamente:

[
A
=

(Q^TQ)^{-1}Q^TB
]

Não utilizar funções prontas de regressão.

Utilizar apenas álgebra linear do NumPy/SciPy.

Explicar cada matriz envolvida.

---

# Banco de Respostas

Após a construção da superfície de resposta, o módulo de confiabilidade deve trabalhar exclusivamente sobre a aproximação polinomial.

O MEF não deve ser chamado novamente durante:

* Monte Carlo;
* FORM.

Isso reduz drasticamente o custo computacional.

---

# Função de Estado Limite

Permitir ao usuário definir facilmente a função limite.

Exemplo principal:

[
g(x)
====

## P_{cr}

P_{serv}
]

Mas permitir outras formas.

O módulo deve ser genérico.

---

# FORM

Implementar o método clássico HLRF.

Etapas:

1. transformação para o espaço normal reduzido;
2. cálculo do gradiente;
3. determinação do vetor normal;
4. atualização do ponto de projeto;
5. cálculo de β;
6. cálculo de Pf.

Os gradientes devem ser obtidos a partir da superfície de resposta.

Evitar diferenças finitas sempre que possível.

---

# Monte Carlo

Executar Monte Carlo apenas sobre a superfície de resposta.

Nunca executar milhares de análises MEF.

Permitir:

* Normal;
* Lognormal.

Número de amostras definido pelo usuário.

---

# Estratégias Adaptativas

A arquitetura deve permitir futuramente a implementação de Superfícies de Resposta Adaptativas.

Porém, nesta versão, implementar apenas:

Superfície construída uma única vez em torno do ponto médio das variáveis aleatórias.

Não implementar atualização iterativa da superfície nesta primeira versão.

---

# Visualizações

Gerar automaticamente:

* histogramas;
* distribuição da função limite;
* distribuição da carga crítica;
* curva de convergência do FORM;
* localização do ponto de projeto;
* comparação entre respostas do MEF e da superfície de resposta.

---

# Organização do Código

Separar claramente:

variables.py

response_surface.py

design_of_experiments.py

form.py

monte_carlo.py

state_limit.py

statistics.py

plots.py

Cada arquivo deve possuir apenas uma responsabilidade.

---

# Comentários

Todo algoritmo deve explicar:

* significado estatístico;
* significado físico;
* referência bibliográfica.

Não assumir conhecimento prévio em confiabilidade estrutural.

---

# Referências

Priorizar:

- Material da disciplina EES146;
- Bucher & Borgund (1990);
- Montgomery (1997);
- Favarelli (1989);
- Nogueira (2010);
- Guan & Melchers (2001).

O algoritmo FORM deve seguir a formulação HLRF apresentada na disciplina.

Evitar utilizar referências externas quando houver equivalente no material da disciplina.

O material da disciplina é o EES146_Aula7.pdf

Sempre que possível, implementar os algoritmos conforme apresentados na disciplina.
