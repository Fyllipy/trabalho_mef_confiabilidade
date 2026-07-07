import numpy as np
from scipy.sparse.linalg import spsolve
from typing import List, Tuple

from mef.model.shell_model import ShellModel
from shared.results import ShellResults
from mef.assembly.global_assembly import assemble_global_stiffness, compute_all_element_gauss_variables
from mef.assembly.boundary_conditions import apply_boundary_conditions_penalty
from mef.postprocess.postprocessor import postprocess_results

def solve_linear_static(model: ShellModel) -> ShellResults:
    """
    Resolve o problema elástico estático linear: K * U = F.
    
    Nesta etapa, validamos a estrutura de malha e materiais gerados 
    montando o sistema global e submetendo-o a condições de contorno
    e carregamentos aplicados.
    
    Args:
        model: Objeto do tipo ShellModel devidamente preenchido.
        
    Returns:
        results: Instância de ShellResults contendo os deslocamentos.
    """
    print("\n--- Iniciando Análise Estática Linear ---")
    
    # 1. Extração de parâmetros fundamentais do modelo
    nodes = model.mesh_data["nodes"]
    elements = model.mesh_data["elements"]
    E = model.material_params["E"]
    nu = model.material_params["nu"]
    h = model.geometry_params["thickness"]
    
    num_nodes = len(nodes)
    total_dofs = num_nodes * 6
    
    print(f"Montando Matriz Global K ({total_dofs}x{total_dofs})...")
    # 2. Montagem da Matriz de Rigidez Global
    K_global = assemble_global_stiffness(nodes, elements, E, nu, h)
    
    print("Aplicando cargas...")
    # 3. Construção do Vetor de Forças Globais
    F_global = np.zeros(total_dofs)
    
    if "nodal_loads" in model.loads:
        # nodal_loads é esperado ser uma lista de tuplas: (node_id, dof_idx_0_a_5, value)
        for node_id, dof_idx, value in model.loads["nodal_loads"]:
            F_global[node_id * 6 + dof_idx] += value
            
    print("Aplicando condições de contorno...")
    # 4. Construção das Condições de Contorno Essenciais
    prescribed_dofs: List[int] = []
    prescribed_vals: List[float] = []
    
    if "fixed_nodes" in model.boundary_conditions:
        # fixed_nodes é uma lista de IDs de nós totalmente restritos
        for node_id in model.boundary_conditions["fixed_nodes"]:
            for dof_idx in range(6):
                prescribed_dofs.append(node_id * 6 + dof_idx)
                prescribed_vals.append(0.0)
                
    if "prescribed_dofs" in model.boundary_conditions:
        # Listagem fina: dof global prescrito
        for dof_idx, value in model.boundary_conditions["prescribed_dofs"]:
            prescribed_dofs.append(dof_idx)
            prescribed_vals.append(value)
            
    K_mod, F_mod = apply_boundary_conditions_penalty(K_global, F_global, prescribed_dofs, prescribed_vals)
    
    print("Resolvendo sistema linear (K * U = F)...")
    # 5. Solução do Sistema Linear de Equações
    U_global = spsolve(K_mod, F_mod)
    
    print("Análise estática concluída com sucesso.")
    
    # 6. Agrupamento e pós-processamento dos resultados
    gp_results, element_areas = compute_all_element_gauss_variables(nodes, elements, U_global, E, nu, h)
    res = postprocess_results(model, U_global, gp_results, element_areas)
    res.raw_dofs = U_global
    
    return res
