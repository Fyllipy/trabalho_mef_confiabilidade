import numpy as np
import scipy.sparse.linalg as sla

from mef.model.shell_model import ShellModel
from shared.results import ShellResults
from mef.analysis.linear_static import solve_linear_static
from mef.assembly.global_assembly import assemble_global_stiffness, assemble_geometric_stiffness

def solve_linear_buckling(model: ShellModel, num_modes: int = 1) -> ShellResults:
    """
    Resolve o problema clássico de Autovalor para Flambagem Linear.
    Equação Governante: (K - lambda * Kg) * phi = 0
    onde:
      K é a matriz de rigidez elástica
      Kg é a matriz de rigidez geométrica
      lambda é o fator de carga crítica multiplicador
      phi é o modo de flambagem (autovetor)
    """
    print("\n--- Iniciando Análise de Flambagem Linear (Eigenbuckling) ---")
    
    # 1. Pré-flambagem (Análise estática linear sob carga de referência)
    print("Passo 1: Resolvendo pré-flambagem estática...")
    
    # Truque para aproveitar a função estática que já temos sem despachar VTK lá dentro
    original_type = model.analysis_type
    model.analysis_type = "linear_static"
    res_static = solve_linear_static(model)
    model.analysis_type = original_type
    
    U_global = res_static.raw_dofs
    if U_global is None:
        raise ValueError("Falha ao obter deslocamentos da pré-flambagem.")
        
    nodes = model.mesh_data["nodes"]
    elements = model.mesh_data["elements"]
    E = model.material_params["E"]
    nu = model.material_params["nu"]
    h = model.geometry_params["thickness"]
    
    total_dofs = len(nodes) * 6
    
    # 2. Matrizes Globais
    print("Passo 2: Montando Matrizes de Rigidez Elástica (K) e Geométrica (Kg)...")
    K_global = assemble_global_stiffness(nodes, elements, E, nu, h)
    Kg_global = assemble_geometric_stiffness(nodes, elements, U_global, E, nu, h)
    
    # 3. Tratamento de Condições de Contorno por particionamento (Redução)
    # A técnica de penalidade modifica Kg artificialmente e distorce autovalores,
    # então a redução direta do sistema é obrigatória.
    print("Passo 3: Aplicando restrições de contorno (Redução de sistema)...")
    prescribed_dofs = []
    
    if "fixed_nodes" in model.boundary_conditions:
        for node_id in model.boundary_conditions["fixed_nodes"]:
            for dof_idx in range(6):
                prescribed_dofs.append(node_id * 6 + dof_idx)
                
    prescribed_dofs = list(set(prescribed_dofs))
    all_dofs = np.arange(total_dofs)
    free_dofs = np.setdiff1d(all_dofs, prescribed_dofs)
    
    K_free = K_global[free_dofs, :][:, free_dofs]
    Kg_free = Kg_global[free_dofs, :][:, free_dofs]
    
    print(f"Resolvendo problema de autovalor generalizado ({len(free_dofs)} GDLs livres)...")
    
    # Kg * phi = (1/lambda) * K * phi 
    # O solver iterativo ARPACK (eigsh) frequentemente falha na convergência devido ao mal 
    # condicionamento gerado pela rigidez fictícia do grau de liberdade de rotação 'drilling'.
    # Como as malhas didáticas/estudantis são pequenas (< 5000 GDLs), a solução densa 
    # direta (eigh) é computacionalmente viável, imediata e 100% robusta.
    import scipy.linalg as la
    
    try:
        K_dense = K_free.toarray()
        Kg_dense = Kg_free.toarray()
        
        # Resolve Kg * phi = mu * K * phi. K é simétrica positiva definida.
        # Retorna todos os autovalores.
        vals, vecs_free = la.eigh(Kg_dense, K_dense)
    except Exception as e:
        print(f"Erro na extração de autovalores densa: {e}")
        return res_static
        
    # Processar autovalores (A equação teórica é K + lambda*Kg = 0)
    # Como resolvemos Kg * phi = mu * K * phi, temos lambda = -1 / mu
    lambdas = []
    modes_free = []
    for i in range(len(vals)):
        if abs(vals[i]) > 1e-12:
            lmb = -1.0 / vals[i]
            # Consideramos apenas fatores de flambagem positivos (no sentido da carga aplicada)
            if lmb > 1e-10:
                lambdas.append(lmb)
                modes_free.append(vecs_free[:, i])
            
    if len(lambdas) == 0:
        print("Nenhum modo de flambagem positivo encontrado.")
        return res_static
        
    # Ordenar do modo mais crítico (menor carga)
    idx = np.argsort(lambdas)
    lambdas = np.array(lambdas)[idx]
    modes_free = [modes_free[i] for i in idx]
    
    # 4. Expandir o vetor livre para o tamanho original e montar resultados
    first_mode = np.zeros(total_dofs)
    first_mode[free_dofs] = modes_free[0]
    
    # Normalizar o modo primário para que o deslocamento máximo seja 1.0 (ajuda visualização)
    max_disp = np.max(np.abs(first_mode))
    if max_disp > 0:
        first_mode = first_mode / max_disp
    
    res = ShellResults()
    res.displacements = first_mode.reshape(-1, 6)[:, 0:3]
    res.rotations = first_mode.reshape(-1, 6)[:, 3:6]
    res.critical_load = lambdas[0]
    res.raw_dofs = first_mode
    
    print(f"Flambagem Linear concluída! Fator de carga crítica global: {lambdas[0]:.4f}")
    return res
