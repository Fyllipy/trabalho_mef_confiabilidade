import numpy as np
import scipy.sparse as sp

from mef.assembly.global_assembly import compute_element_transformation, get_element_instance
from mef.elements.stiffness import compute_element_stiffness_local
from mef.elements.geometric_stiffness import compute_geometric_stiffness_local
from mef.formulation.jacobian import compute_jacobian
from mef.elements.B_matrix import compute_B_membrane
from mef.materials.constitutive import compute_membrane_matrix

def assemble_tangent_stiffness(nodes_current, elements, E, nu, h, membrane_forces):
    """
    Monta a Matriz de Rigidez Tangente (K_T = K_L + K_g) baseada na 
    geometria deformada ATUAL (Formulação Updated Lagrangian simplificada).
    """
    num_nodes = len(nodes_current)
    nodes_per_elem = elements.shape[1]
    element = get_element_instance(nodes_per_elem)
    
    total_dofs = num_nodes * element.dofs_per_node
    I, J, V = [], [], []
    
    ndof = element.num_nodes * element.dofs_per_node
    
    for e_idx, elem_nodes in enumerate(elements):
        elem_coords = nodes_current[elem_nodes]
        R, T, local_coords = compute_element_transformation(element, elem_coords)
        
        # Rigidez elástica na geometria deformada
        Ke_local = compute_element_stiffness_local(element, local_coords, E, nu, h)
        
        # Rigidez geométrica devido às tensões acumuladas
        Nx, Ny, Nxy = membrane_forces[e_idx]
        Kg_local = compute_geometric_stiffness_local(element, local_coords, Nx, Ny, Nxy)
        
        # Rotaciona para o sistema global
        KT_global = T.T @ (Ke_local + Kg_local) @ T
        
        gdl_indices = np.zeros(ndof, dtype=int)
        for i in range(element.num_nodes):
            node_id = elem_nodes[i]
            dof = element.dofs_per_node
            gdl_indices[i*dof : i*dof+dof] = np.arange(node_id*dof, node_id*dof+dof)
            
        # Adiciona aos arrays esparsos
        for i in range(ndof):
            for j in range(ndof):
                val = KT_global[i, j]
                if abs(val) > 1e-12:
                    I.append(gdl_indices[i])
                    J.append(gdl_indices[j])
                    V.append(val)
                    
    K_T = sp.coo_matrix((V, (I, J)), shape=(total_dofs, total_dofs)).tocsc()
    return K_T

def update_internal_forces_and_stresses(nodes_current, elements, dU_global, E, nu, h, F_int_local_hist, membrane_forces_hist):
    """
    Atualiza as forças internas acumuladas (F_int) e as tensões de membrana (N).
    O incremento de força é calculado no sistema corrotacionado/local atual e 
    então acumulado e projetado para o vetor global.
    """
    num_nodes = len(nodes_current)
    nodes_per_elem = elements.shape[1]
    element = get_element_instance(nodes_per_elem)
    
    total_dofs = num_nodes * element.dofs_per_node
    F_int_global = np.zeros(total_dofs)
    
    Dm = compute_membrane_matrix(E, nu, h)
    
    ndof = element.num_nodes * element.dofs_per_node
    
    for e_idx, elem_nodes in enumerate(elements):
        elem_coords = nodes_current[elem_nodes]
        R, T, local_coords = compute_element_transformation(element, elem_coords)
        
        gdl_indices = np.zeros(ndof, dtype=int)
        for i in range(element.num_nodes):
            node_id = elem_nodes[i]
            dof = element.dofs_per_node
            gdl_indices[i*dof : i*dof+dof] = np.arange(node_id*dof, node_id*dof+dof)
            
        # Pega o incremento de deslocamento (da iteração de Newton-Raphson)
        dU_elem_global = dU_global[gdl_indices]
        
        # Mapeia para o sistema local atual
        dU_elem_local = T @ dU_elem_global
        
        # Avalia a matriz de rigidez elástica atual
        Ke_local = compute_element_stiffness_local(element, local_coords, E, nu, h)
        
        # O incremento de força elástica gerado por esse movimento incremental
        dF_int_local = Ke_local @ dU_elem_local
        
        # Acumula no histórico local
        F_int_local_hist[e_idx] += dF_int_local
        
        # Transforma a força ACUMULADA de volta para a direção global atual
        F_int_global_elem = T.T @ F_int_local_hist[e_idx]
        F_int_global[gdl_indices] += F_int_global_elem
        
        # --- Atualizar os esforços de membrana para alimentar K_g ---
        dN_dxi_eta = element.shape_function_derivatives(0.0, 0.0)
        _, _, dN_dx_y = compute_jacobian(dN_dxi_eta, local_coords)
        Bm = compute_B_membrane(element, dN_dx_y)
        
        # Deformação de membrana puramente gerada no incremento
        de_m = Bm @ dU_elem_local
        dN_m = Dm @ de_m
        
        # Acumula as forças de membrana [Nx, Ny, Nxy]
        membrane_forces_hist[e_idx] += dN_m
        
    return F_int_global
