import sys
import os
import numpy as np

# Adiciona o diretório raiz para importar os módulos do MEF
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from mef.model.shell_model import ShellModel
from mef.mesh.generator import generate_mesh
from mef.mesh.converter import convert_mesh
from mef.analysis.linear_static import solve_linear_static

def run_analytical_plate_test():
    """
    Validação Analítica (Etapa 14)
    Problema: Placa plana engastada e livre (Cantilever) sob carga concentrada na ponta livre.
    Validação da flecha máxima com a Teoria de Euler-Bernoulli.
    """
    print("\n" + "="*50)
    print("INICIANDO VALIDAÇÃO ANALÍTICA: PLACA EM BALANÇO")
    print("="*50)
    
    E = 200e3      # MPa
    nu = 0.3
    width = 10.0   # b
    length = 100.0 # L
    h = 2.0        # espessura
    P = -100.0     # Carga total na ponta livre em Z
    
    # Solução analítica (Teoria de Vigas para flecha na ponta)
    # v = (P * L^3) / (3 * E * I)
    I = (width * h**3) / 12.0
    v_analitico = (P * length**3) / (3.0 * E * I)
    
    # 1. Configurar o Modelo
    model = ShellModel(
        geometry_type="plate",
        geometry_params={"width": width, "length": length, "thickness": h},
        material_params={"E": E, "nu": nu},
        element_type="QUAD4",
        mesh_params={"num_width": 4, "num_length": 20},
        analysis_type="linear_static"
    )
    
    # 2. Gerar Malha manualmente para capturar e atribuir cargas corretamente
    raw_mesh = generate_mesh(model)
    nodes, elements = convert_mesh(raw_mesh)
    model.mesh_data = {"nodes": nodes, "elements": elements}
    
    # 3. Aplicar Condições de Contorno (Engaste em Y = 0)
    # Procuramos nós que estão em y = 0
    fixed_nodes = np.where(np.abs(nodes[:, 1]) < 1e-6)[0].tolist()
    model.boundary_conditions = {"fixed_nodes": fixed_nodes}
    
    # 4. Aplicar Carregamento (Carga na ponta Y = length)
    loaded_nodes = np.where(np.abs(nodes[:, 1] - length) < 1e-6)[0].tolist()
    force_per_node = P / len(loaded_nodes) if len(loaded_nodes) > 0 else 0
    nodal_loads = [(n, 2, force_per_node) for n in loaded_nodes] # GDL 2 = deslocamento Z
    model.loads = {"nodal_loads": nodal_loads}
    
    # 5. Resolver Análise
    results = solve_linear_static(model)
    
    # 6. Comparação Analítica
    # O deslocamento máximo será na ponta
    v_mef = np.min(results.displacements[:, 2])
    
    erro = abs((v_mef - v_analitico) / v_analitico) * 100
    
    print("\n--- RESULTADOS DA VALIDAÇÃO ---")
    print(f"Deslocamento Z Analítico (Viga): {v_analitico:.6f} mm")
    print(f"Deslocamento Z MEF (Placa):    {v_mef:.6f} mm")
    print(f"Erro relativo:                   {erro:.2f} %")
    
    if erro < 5.0:
        print(">>> VALIDAÇÃO BEM SUCEDIDA! (Erro < 5%)")
    else:
        print(">>> AVISO: Erro acima do limite esperado.")

if __name__ == "__main__":
    run_analytical_plate_test()
