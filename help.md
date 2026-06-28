# Manual do Usuário: Framework Analítico de Confiabilidade Estrutural (Cascas Cilíndricas)

Bem-vindo ao manual do usuário do **Framework de Análise de Confiabilidade de Cascas Cilíndricas**. Este programa foi desenvolvido para avaliar a segurança estrutural de cilindros de parede fina sujeitos à compressão axial, englobando duas disciplinas fundamentais: o **Método dos Elementos Finitos (MEF)** para a obtenção da resistência determinística, e a **Confiabilidade Estrutural**, baseada em Superfícies de Resposta Estocásticas.

---

## 1. Módulo MEF (Método dos Elementos Finitos)

O módulo MEF é a fundação para a análise de capacidade resistente do cilindro. Ele realiza análises estáticas e análises de estabilidade elástica (Flambagem Linear ou *Eigenbuckling*), baseadas na formulação de cascas (Degenerated Shell ou combinações de Membrana-Flexão). 

### Como Funciona
1. **Malha e Geometria**: O domínio cilíndrico é discretizado parametrizando as direções circunferencial ($\theta$) e axial ($z$). 
2. **Matrizes Elementares**: Calcula a matriz de rigidez elástica ($[k]$) e a matriz de rigidez geométrica/tensões iniciais ($[k_g]$) aplicando a Quadratura de Gauss Gauss-Legendre.
3. **Flambagem Linear**: Resolve o problema de autovalor generalizado $([K] + \lambda [K_G])\{\phi\} = \{0\}$. O autovalor crítico ($\lambda_1$) multiplicado pela carga aplicada determina a Carga Crítica de Flambagem ($P_{cr}$).
4. **Imperfeições Geométricas**: Permite perturbar a malha alinhando-a ao formato do primeiro modo de flambagem ($\phi_1$) multiplicado por uma amplitude máxima definida $A$.

### Parâmetros de Configuração (Dicionário `geometry_params`)

Ao instanciar a malha e a análise, os seguintes parâmetros regem a física do problema:

| Parâmetro | Tipo | Descrição | Opções / Exemplo |
| :--- | :--- | :--- | :--- |
| `radius` | `float` | Raio nominal do cilindro. | Ex: `150.0` (mm) |
| `length` | `float` | Comprimento total ao longo do eixo axial. | Ex: `300.0` (mm) |
| `thickness` | `float` | Espessura da chapa da casca. | Ex: `2.0` (mm) |
| `E` | `float` | Módulo de Elasticidade Longitudinal (Young). | Ex: `70000.0` (Alumínio) |
| `nu` | `float` | Coeficiente de Poisson. | Ex: `0.3` |
| `elem_type` | `str` | Tipo de elemento finito bidimensional. | `'QUAD4'` (Recomendado) ou `'QUAD8'` |
| `num_nodes_circ` | `int` | Número de nós ao longo da direção circunferencial. | Ex: `18` (Define a densidade da malha) |
| `num_nodes_axial` | `int` | Número de nós ao longo da direção axial. | Ex: `10` (Define a densidade da malha) |
| `load_value` | `float` | Carga compressiva estática axial aplicada de referência. | Ex: `1.0` (Para gerar o fator $\lambda$) |

### Exemplo Completo de Script MEF

```python
import sys
import os
from mef.mesh.cylinder import CylinderMesh
from mef.analysis.linear_buckling import LinearBuckling
from mef.analysis.imperfection import ImperfectionInjector

# 1. Parâmetros Determinísticos Iniciais
params = {
    "radius": 150.0,
    "length": 300.0,
    "thickness": 2.0,
    "E": 70000.0,
    "nu": 0.3,
    "elem_type": "QUAD4",
    "num_nodes_circ": 18,
    "num_nodes_axial": 10
}

# 2. Gerar a Malha Cilíndrica
mesh = CylinderMesh(params)
mesh.generate()

# 3. Solver de Flambagem Linear (Casca Perfeita)
buckling_perf = LinearBuckling(mesh, params)
buckling_perf.assemble_global_stiffness()
p_cr_perf, nodes_perf, res_perf = buckling_perf.solve(load_value=1.0)
print(f"Carga Crítica (Cilindro Perfeito): {p_cr_perf:.2f} N")

# 4. Injeção de Imperfeição Geométrica
injector = ImperfectionInjector(nodes_perf, res_perf)
amplitude = 0.5 # mm
nodes_imp = injector.apply_mode_shape(mode_index=0, max_amplitude=amplitude)

# 5. Solver com Cilindro Imperfeito
mesh_imp = CylinderMesh(params)
mesh_imp.generate()
mesh_imp.nodes = nodes_imp # Sobrescreve coordenadas

buckling_imp = LinearBuckling(mesh_imp, params)
buckling_imp.assemble_global_stiffness()
p_cr_imp, _, res_imp = buckling_imp.solve(load_value=1.0)
print(f"Carga Crítica (Com Imperfeição {amplitude}mm): {p_cr_imp:.2f} N")
```

---

## 2. Módulo de Confiabilidade Estrutural

O módulo de confiabilidade é um *wrapper* estocástico ao redor do MEF. Devido ao alto custo computacional, avaliações diretas de Monte Carlo sobre o MEF são inviáveis. Assim, a arquitetura orquestra o Design de Experimentos (DOE), treina uma Superfície de Resposta (RSM) substituta para aproximar o MEF e aplica métodos probabilísticos clássicos na RSM.

### Como Funciona
1. **Design de Experimentos (DOE)**: O algoritmo *Central Composite Design* (CCD) projeta pontos vetoriais contendo as variáveis críticas de projeto (Ex: Espessura $t$, Imperfeição $A$).
2. **Avaliação MEF**: O algoritmo aciona o solver MEF para todos os vetores estruturados pelo DOE, criando um *Dataset* determinístico.
3. **Superfície de Resposta (RSM)**: Uma regressão quadrática polinomial ajusta o polinômio metamodelo $RSM(t,A) \approx P_{cr}$, substituindo o software rigoroso de MEF por uma função algébrica de avaliação instantânea. O Hold-Out valida a aderência (R², RMSE).
4. **Análise First-Order Reliability Method (FORM)**: O algoritmo HLRF resolve o problema de otimização em busca do Ponto de Projeto (MPP).
5. **Relatório**: Os escritores dinâmicos compilam `.docx` e `.md` contendo todos os cruzamentos estatísticos.

### Componentes de Configuração

#### A. Criação de Variáveis Aleatórias (`RandomModel`)
O usuário cria um ecossistema estatístico atribuindo as distribuições de probabilidade inerentes a cada parâmetro.
* **Nome**: `'t'`, `'A'`, `'P'`
* **Distribuição**: `'normal'`, `'lognormal'`
* **Média**: Valor determinístico.
* **Desvio Padrão**: Incerteza (covariância global).

#### B. Algoritmo FORM e Função Estado Limite (LSF)
No construtor `FORM()`, é obrigatório diferenciar quais variáveis fazem parte do MEF (geométricas/materiais) e qual compõe a Carga atuante (demanda). A LSF é dada implicitamente por $g(X) = RSM(\text{variáveis estruturais}) - P(\text{demanda})$. O FORM resolve analiticamente a derivada e o gradiente (HLRF).

### Exemplo Completo de Script de Confiabilidade

```python
import numpy as np
import os
from mef.mesh.cylinder import CylinderMesh
from reliability.variables.random_model import RandomModel
from reliability.design_of_experiments.ccd import CentralCompositeDesign
from reliability.database.response_database import ResponseDatabase
from reliability.response_surface.rsm_models import QuadraticFullRSM
from reliability.response_surface.validation import validate_rsm
from reliability.methods.form import FORM
from reliability.methods.monte_carlo import MonteCarlo
from reliability.report.builder import ReportBuilder
from reliability.report.plotter import ReportPlotter

# Dummy de avaliador de MEF (Para script de exemplo limpo, 
# em prática substitui-se por chamadas reais ao MEF)
def evaluate_mef_mock(t_val, A_val):
    # RSM falsa: 1.3e6 * (t/2.0) - A*1000
    return 1300000.0 * (t_val/2.0) - A_val*1000.0

# 1. Declarar o Modelo Estocástico
rm = RandomModel()
rm.add_variable(name='t', distribution='normal', mean=2.0, std_dev=0.1)
rm.add_variable(name='A', distribution='lognormal', mean=0.5, std_dev=0.1)
rm.add_variable(name='P', distribution='normal', mean=1100000.0, std_dev=50000.0)

# Variáveis estruturais exclusivas que afetam o Pcr:
rsm_vars = ['t', 'A'] 

# 2. Design of Experiments (CCD)
ccd = CentralCompositeDesign(rm, variables=rsm_vars, alpha=1.0)
doe_points = ccd.generate_points()

# 3. Gerar Banco de Dados (Acoplamento ao MEF)
db = ResponseDatabase()
for pt in doe_points:
    t_val = pt[0]
    A_val = pt[1]
    p_cr_val = evaluate_mef_mock(t_val, A_val)
    db.add_evaluation(params={'t': t_val, 'A': A_val}, pcr=p_cr_val)

X_data, Y_data = db.get_training_data(rsm_vars)

# 4. Construir Superfície de Resposta Matemática
rsm = QuadraticFullRSM()
rsm.fit(X_data, Y_data)

# 5. Algoritmo FORM (HLRF)
form = FORM(random_model=rm, rsm=rsm, load_var_name='P', rsm_var_names=rsm_vars)
beta, pf_form, x_star, u_star, beta_history = form.run(max_iter=50, tol=1e-4)

print(f"Índice de Confiabilidade (FORM): {beta:.4f}")
print(f"Probabilidade de Falha (FORM):   {pf_form:.2e}")

# 6. Monte Carlo na RSM
mc = MonteCarlo(random_model=rm, rsm=rsm, load_var_name='P', rsm_var_names=rsm_vars)
pf_mc, pcr_samples, g_samples = mc.run(num_samples=1_000_000)
print(f"Probabilidade de Falha (MC):     {pf_mc:.2e}")

# 7. Gerar Relatórios Acadêmicos Automáticos
out_dir = os.path.join(os.getcwd(), "relatorio_output")
builder = ReportBuilder(out_dir)
plotter = ReportPlotter(out_dir)

# Passar métricas (omitiu-se o MEF original por clareza do snippet)
builder.build_section_4(rm)
builder.build_section_5_6(X_data, Y_data, rsm, 1.0, 0.0, 0.0)
builder.build_section_7_8_9(beta, pf_form, x_star, u_star, form.alpha_star, form.var_names, rm)
builder.build_section_10_11(pf_mc, 1000000, beta, pf_form)

# Gráficos
path_i = plotter.plot_importance_factors(form.alpha_star, form.var_names)
builder.add_figure("fig_importancia", path_i, "Fatores de Importância")

builder.generate_discussion(r2=1.0, beta=beta)
builder.export()
```

### Principais Exportações do Relatório Automático
Ao final da etapa 7, a pasta `relatorio_output` conterá um arquivo `relatorio.docx` (editável) contendo:
- Histograma de Interferência Capacidade x Demanda.
- Histograma do Estado Limite.
- Estudo Paramétrico de Sensibilidade.
- Plot tridimensional da Superfície Analítica.
- Tabela resumo das predições de probabilidade.

O documento é autoexplicativo, formulado inteiramente pelo objeto `ReportBuilder`.

---

## 3. Perguntas Frequentes (FAQ)

### Posso simular uma Placa Plana em vez de um Cilindro?
**Sim!** O gerador de malha já foi implementado de forma genérica. Para analisar uma placa retangular, basta substituir o tipo de geometria e seus parâmetros, além de atualizar as condições de contorno de acordo com a nova topologia (O gerador de placas trabalha no plano $X-Y$ ao invés de um cilindro ao redor de $Z$).
Exemplo de alteração na declaração do `ShellModel`:
```python
model = ShellModel(
    geometry_type="plate",
    geometry_params={"width": 500.0, "length": 1000.0, "thickness": 2.0},
    material_params={"E": 200e3, "nu": 0.3},
    element_type="QUAD4",
    mesh_params={"num_width": 20, "num_length": 40},
    analysis_type="linear_buckling"
)

Para anáise com instabilidade:
model = ShellModel(
    # ...
    # Usa o solver que atualiza a geometria passo-a-passo (NLGEOM)
    analysis_type="nonlinear_static", 
    
    # E aplica uma perturbação para "engatilhar" a instabilidade
    imperfection_params={
        "type": "modal",       # ou "geometric"
        "amplitude": 0.5       # mm
    }
)

# Atualize a lógica de forças/engastes conforme os novos limites
# A placa irá de x=0 até x=500 e y=0 até y=1000
fixed_nodes = np.where(np.abs(nodes[:, 1]) < 1e-6)[0].tolist() # y = 0
```

### Como posso exportar os arquivos `.vtu` de cada passo da simulação não-linear?
Por padrão (para economizar dezenas de megabytes no disco), o `solve_nonlinear_static` (NLGEOM) exporta o VTK apenas da deformação estática *final*. Contudo, os dados são gerados passo a passo internamente. Se você quiser um `.vtu` para cada incremento para poder criar animações no ParaView, modifique a função `solve_nonlinear_static` no arquivo `mef/analysis/nonlinear_static.py`:

Dentro do loop de incrementos (`for step in range(1, num_steps + 1):`), imediatamente após o loop interno do Newton-Raphson (logo após `converged = True`, linha 106), injete uma chamada à exportação com a biblioteca nativa, da seguinte forma:

```python
from mef.postprocess.vtk_export import export_vtk

# ... (Após convergência do step)
if converged:
    point_data = {
        "Deslocamentos": U_total.reshape(-1, 6)[:, 0:3],
        "Rotacoes": U_total.reshape(-1, 6)[:, 3:6]
    }
    export_vtk(f"resultado_step_{step}.vtu", nodes_0, elements, point_data)
```
Desta forma o algoritmo cuspirá cada etapa da simulação no seu diretório para visualização animada.


---

## Para o Abaqus:

Para definir o tipo de elemento (QUAD4 ou QUAD8) no script Python do Abaqus, você só precisa alterar o código do elemento (elemCode) na função mesh.ElemType.

No seu script atual run_abaqus_nonlinear.py, observe a linha 72:

```python
elemType = mesh.ElemType(elemCode=S4, elemLibrary=STANDARD)
```
No ecossistema do Abaqus:

QUAD4 é equivalente aos elementos S4 (integração completa) ou S4R (integração reduzida).
QUAD8 é equivalente aos elementos S8R (casca espessa/fina de 8 nós com integração reduzida) ou S8R5 (casca fina de 8 nós e 5 graus de liberdade por nó).
Como alterar o script para suportar ambos
Você pode adicionar um parâmetro element_type na sua função create_and_run para decidir isso dinamicamente:

```python
def create_and_run(element_type="QUAD4"):
    # ... código anterior ...
    
    # Define o tipo de elemento do Abaqus baseado na string
    if element_type == "QUAD8":
        # S8R é o análogo exato ao QUAD8 Serendipity com integração 
        # reduzida de cisalhamento que implementamos no nosso solver MEF
        abaqus_elem = S8R 
    else:
        abaqus_elem = S4 # ou S4R
        
    elemType = mesh.ElemType(elemCode=abaqus_elem, elemLibrary=STANDARD)
    p.setElementType(regions=(faces,), elemTypes=(elemType,))
    p.generateMesh()
```
Assim, se você for automatizar as rodadas no Abaqus pelo terminal via script externo (usando os.system), você pode inclusive ler os argumentos de terminal usando sys.argv dentro desse arquivo e passar o tipo desejado dinamicamente para que sua suíte de validação compare de forma totalmente espelhada o QUAD4 (MEF) com S4 (Abaqus) e o QUAD8 (MEF) com o S8R (Abaqus)!
