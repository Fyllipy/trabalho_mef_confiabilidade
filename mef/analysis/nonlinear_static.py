import numpy as np
import scipy.sparse.linalg as sla

from mef.model.shell_model import ShellModel
from shared.results import ShellResults
from mef.assembly.boundary_conditions import apply_boundary_conditions_penalty
from mef.analysis.nonlinear_assembly import assemble_tangent_stiffness, update_internal_forces_and_stresses

def solve_nonlinear_static(model: ShellModel, num_steps: int = 10, max_iter: int = 20, tol: float = 1e-4) -> ShellResults:
    """
    Resolve a resposta estática usando o método incremental-iterativo de Newton-Raphson.
    Captura grandes deslocamentos e instabilidade utilizando a formulação Updated Lagrangian.
    """
    print("\n--- Iniciando Análise Não-Linear Geométrica (NLGEOM) ---")
    
    # Estado indeformado inicial
    nodes_0 = model.mesh_data["nodes"].copy()
    elements = model.mesh_data["elements"]
    E = model.material_params["E"]
    nu = model.material_params["nu"]
    h = model.geometry_params["thickness"]
    
    from mef.assembly.global_assembly import get_element_instance
    nodes_per_elem = elements.shape[1]
    element = get_element_instance(nodes_per_elem)
    
    num_nodes = len(nodes_0)
    dof = element.dofs_per_node
    ndof = element.num_nodes * dof
    total_dofs = num_nodes * dof
    
    # 1. Definir a carga total de referência
    F_ext_ref = np.zeros(total_dofs)
    if "nodal_loads" in model.loads:
        for node_id, dof_idx, value in model.loads["nodal_loads"]:
            F_ext_ref[node_id * dof + dof_idx] += value
            
    # 2. CCs (apenas os GDLs, valores aplicaremos a cada iteração)
    prescribed_dofs = []
    prescribed_vals = []
    if "fixed_nodes" in model.boundary_conditions:
        for node_id in model.boundary_conditions["fixed_nodes"]:
            for dof_idx in range(dof):
                prescribed_dofs.append(node_id * dof + dof_idx)
                prescribed_vals.append(0.0)
                
    free_dofs = np.setdiff1d(np.arange(total_dofs), prescribed_dofs)
    
    # 3. Variáveis de Estado Acumulado
    U_total = np.zeros(total_dofs) # Deslocamento Total
    F_int_global = np.zeros(total_dofs) # Força Interna Global
    
    # Variáveis elementares para integração de histórico
    F_int_local_hist = np.zeros((len(elements), ndof))
    membrane_forces_hist = np.zeros((len(elements), 3)) # [Nx, Ny, Nxy]
    
    # Inicializa resultados para plotagem
    res = ShellResults()
    res.stresses = {"load_factors": [], "max_displacements": []}
    
    # Loop de Incrementos de Carga (Arc-Length simplificado seria melhor para snap-through, 
    # mas Newton-Raphson com controle de carga é incrivelmente didático)
    for step in range(1, num_steps + 1):
        lambda_factor = step / float(num_steps)
        F_ext_current = F_ext_ref * lambda_factor
        
        print(f"Incremento {step}/{num_steps} (Lambda = {lambda_factor:.3f})")
        
        converged = False
        # Loop do Newton-Raphson (Iterativo)
        for iteration in range(max_iter):
            # Geometria Atualizada X = X_0 + U_total
            nodes_current = nodes_0 + U_total.reshape(-1, dof)[:, 0:3]
            
            try:
                # Montar Matriz Tangente (K_T = K_L + K_g) baseada em X e N
                K_T = assemble_tangent_stiffness(nodes_current, elements, E, nu, h, membrane_forces_hist)
                
                # Vetor Residual (Forças desequilibradas)
                R = F_ext_current - F_int_global
                
                # Aplicação de CCs (Penalty Method) na K_T e no Residual
                K_T_mod, R_mod = apply_boundary_conditions_penalty(K_T, R, prescribed_dofs, prescribed_vals)
                
                # Resolver o incremento de deslocamento dU
                dU = sla.spsolve(K_T_mod, R_mod)
                
                # Atualizar Deslocamento Global Acumulado (Temporário para esta iteração)
                U_total += dU
                
                # Geometria re-atualizada para cálculo correto do F_int
                nodes_next = nodes_0 + U_total.reshape(-1, dof)[:, 0:3]
                
                # Atualizar os estados internos elementares (F_int e Esforços) devido ao incremento dU
                F_int_global = update_internal_forces_and_stresses(
                    nodes_next, elements, dU, E, nu, h, 
                    F_int_local_hist, membrane_forces_hist
                )
            except ValueError as e:
                print(f"\n>>> AVISO DE COLAPSO ESTRUTURAL: A iteração divergiu drasticamente causando inversão da malha.")
                print(f">>> Detalhe: {e}")
                print(f">>> Abortando os incrementos de carga restantes.")
                converged = False
                break # Quebra o loop iterativo, sinalizando divergência fatal
            
            # Checar Convergência: Norma do residual nos GDLs livres
            R_free = F_ext_current[free_dofs] - F_int_global[free_dofs]
            norm_R = np.linalg.norm(R_free)
            norm_F = np.linalg.norm(F_ext_current[free_dofs])
            if norm_F < 1e-12: norm_F = 1.0
            
            error = norm_R / norm_F
            
            if error < tol:
                print(f"   -> Convergiu na iter {iteration+1} (Erro = {error:.2e})")
                converged = True
                break
            else:
                print(f"   -> Iter {iteration+1}: Erro = {error:.2e}")
                
        if not converged:
            print(">>> AVISO: Newton-Raphson não convergiu neste incremento (Possível colapso estrutural). Abortando incrementos de carga restantes.")
            break
            
        # Armazena o deslocamento no grau de liberdade crítico para o gráfico de P-delta
        max_disp_Z = np.min(U_total.reshape(-1, dof)[:, 2]) # Deslocamento de compressão
        res.stresses["load_factors"].append(lambda_factor)
        res.stresses["max_displacements"].append(max_disp_Z)
        
    res.displacements = U_total.reshape(-1, dof)[:, 0:3]
    res.rotations = U_total.reshape(-1, dof)[:, 3:6] if dof >= 6 else None
    res.raw_dofs = U_total
    
    print("Análise NLGEOM finalizada.")
    return res
