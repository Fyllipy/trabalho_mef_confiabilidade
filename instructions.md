# Projeto: Análise Mecano-Fiabilística da Flambagem de Cascas Cilíndricas Imperfeitas via Método dos Elementos Finitos

# Objetivo

Desenvolver um software acadêmico em Python para análise de flambagem de cascas cilíndricas imperfeitas utilizando o Método dos Elementos Finitos, integrado a um módulo de Confiabilidade Estrutural através da técnica de Superfícies de Resposta (Response Surface Method - RSM).

O projeto deve possuir duas partes totalmente independentes:

1. Solver Mecânico (MEF)
2. Solver de Confiabilidade

A comunicação entre ambos deve ocorrer exclusivamente através de uma interface pública.

O módulo de confiabilidade jamais poderá acessar estruturas internas do MEF.

---

# Arquitetura Geral

Fluxo esperado:

```
Modelo
        ↓

Solver MEF

        ↓

Banco de respostas

        ↓

Superfície de resposta

        ↓

FORM
Monte Carlo
```

O Solver MEF deve funcionar independentemente da existência do módulo de confiabilidade.

O usuário deve poder executar apenas análises determinísticas.

---

# Filosofia

Este projeto possui finalidade exclusivamente acadêmica.

Priorizar sempre:

* clareza;
* organização;
* didática;
* facilidade de validação;
* simplicidade matemática.

Nunca priorizar:

* desempenho;
* paralelização;
* otimizações prematuras;
* técnicas avançadas de engenharia de software.

Todo algoritmo deve ser escrito para ser facilmente compreendido por um aluno de pós-graduação.

---

# Linguagem

Python 3.12+

Bibliotecas permitidas:

* numpy
* scipy
* gmsh
* meshio
* pyvista
* matplotlib

Evitar dependências adicionais.

---

# Estrutura do Projeto

```
project/

mef/
    mesh/
    elements/
    materials/
    assembly/
    nonlinear/
    postprocess/

reliability/
    variables/
    design_of_experiments/
    response_surface/
    form/
    monte_carlo/
    statistics/

shared/
    state_limit.py

examples/

outputs/

main.py
```

---

# Solver Mecânico

Responsável apenas pela solução determinística.

Entradas:

* geometria;
* material;
* condições de contorno;
* carregamento.

Saídas:

* carga crítica;
* modos de flambagem;
* deslocamentos;
* tensões;
* deformações.

Nunca realizar cálculos probabilísticos.

---

# Interface Pública

O único ponto de comunicação permitido entre os módulos será:

```python
response = solve_shell(parameters)
```

O objeto retornado deverá conter apenas informações físicas.

Exemplo:

```python
{
    "critical_load": ...,
    "buckling_mode": ...,
    "maximum_displacement": ...
}
```

---

# Geometria

Casca cilíndrica parametrizada.

Parâmetros mínimos:

* raio;
* comprimento;
* espessura.

Parâmetros opcionais:

* número de divisões circunferenciais;
* número de divisões longitudinais.

---

# Elementos

Implementar obrigatoriamente:

* QUAD4
* QUAD8

O usuário escolhe o elemento através do arquivo de entrada.

---

# Malha

Utilizar Gmsh.

Toda malha deve ser gerada automaticamente.

Nenhum arquivo .geo deverá ser editado manualmente.

---

# Formulação

Utilizar teoria de cascas de Reissner-Mindlin.

Implementar separadamente:

* membrana;
* flexão;
* cisalhamento.

---

# Flambagem

Implementar:

* flambagem linear;
* imperfeições geométricas;
* não linearidade geométrica.

Utilizar:

* Green-Lagrange;
* Second Piola-Kirchhoff;
* Newton-Raphson.

---

# Imperfeições

Implementar:

* modal;
* harmônica.

Implementar Yoshimura apenas se não aumentar significativamente a complexidade do projeto.

---

# Exportação

Gerar arquivos VTK compatíveis com ParaView.

Exportar:

* deslocamentos;
* tensões;
* deformações;
* modos de flambagem.

---

# Variáveis Aleatórias

O projeto deve permitir qualquer conjunto de variáveis aleatórias.

O caso de exemplo deverá utilizar:

* módulo de elasticidade (Normal);
* espessura (Normal);
* amplitude da imperfeição (Lognormal);
* carga axial aplicada (Normal).

Cada variável deverá possuir:

* média;
* desvio padrão;
* distribuição;
* descrição física.

---

# Função de Estado Limite

A função limite deverá ser desacoplada do MEF.

Exemplo padrão:

g(x)=Pcr−P

onde:

Pcr é obtido pelo Solver MEF.

P é a carga aplicada.

---

# Superfície de Resposta

A comunicação entre o MEF e os métodos probabilísticos deverá ocorrer através de uma superfície de resposta polinomial.

Implementar:

* linear;
* quadrática;
* quadrática completa.

A superfície deverá ser construída a partir de um Plano de Experimentos.

---

# Plano de Experimentos

Implementar geração automática de pontos.

Permitir:

* estrela;
* hiper-cubo;
* fatorial completo.

---

# Confiabilidade

Implementar:

FORM (HLRF)

Monte Carlo

Os dois métodos deverão utilizar exclusivamente a superfície de resposta.

O MEF não deverá ser chamado durante as iterações destes algoritmos.

---

# Validação

Validar o Solver MEF utilizando:

* solução analítica;
* Abaqus Linear Buckling;
* Abaqus Static General;
* Abaqus Static Riks.

Validar a superfície de resposta comparando:

* resposta do polinômio;
* resposta direta do MEF.

---

# Documentação

Todo módulo deverá conter:

* descrição matemática;
* significado físico;
* referências bibliográficas;
* comentários detalhados.

Cada algoritmo deve explicar não apenas "como", mas também "por que" ele está sendo implementado.

O projeto deverá ser suficientemente didático para ser utilizado como material de apoio em uma disciplina de Método dos Elementos Finitos e Confiabilidade Estrutural.
