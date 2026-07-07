import numpy as np
import scipy.sparse as sp
from typing import Tuple

from mef.elements.stiffness import compute_element_stiffness_local
from mef.elements.geometric_stiffness import compute_geometric_stiffness_local
from mef.materials.constitutive import compute_membrane_matrix, compute_bending_matrix
from mef.elements.B_matrix import compute_B_membrane, compute_B_bending
from mef.formulation.jacobian import compute_jacobian
from mef.elements.base_element import ShellElement
from mef.elements.quad4 import Quad4
from mef.elements.quad8 import Quad8

def get_element_instance(num_nodes: int) -> ShellElement:
    if num_nodes == 4:
        return Quad4()
    elif num_nodes == 8:
        return Quad8()
    else:
        raise ValueError(f"Elemento com {num_nodes} nós não suportado.")

def compute_element_transformation(element: ShellElement, element_coords: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calcula o sistema local bidimensional de um elemento de casca 
    imerso no espaço 3D global, extraindo a matriz de transformação.
    
    Atenção: O sistema de coordenadas locais (eixos x, y, z) continua
    sendo definido de forma determinística utilizando APENAS os 4 nós 
    de canto do elemento (índices 0 a 3), mesmo para o QUAD8. Os nós 
    médios acompanham geometricamente essa base local.
    
    Args:
        element: Instância de ShellElement.
        element_coords: Array (N, 3) com as coordenadas globais (X, Y, Z) dos nós do elemento.
        
    Returns:
        R: Matriz de rotação (3, 3).
        T: Matriz de transformação expandida (ndof, ndof).
        local_coords: Array (N, 2) com as coordenadas locais 2D (x, y) dos nós.
    """
    # 1. Definir vetores que definem o plano do elemento
    # Usa-se o lado 1-2 como eixo x local e o plano formado por 1-2 e 1-4.
    v12 = element_coords[1] - element_coords[0]
    v14 = element_coords[3] - element_coords[0]
    
    # Eixo X local (normalizado)
    L_x = np.linalg.norm(v12)
    e_x = v12 / L_x
    
    # Eixo Z local (normal à superfície)
    v_z = np.cross(v12, v14)
    e_z = v_z / np.linalg.norm(v_z)
    
    # Eixo Y local (ortogonal a Z e X)
    e_y = np.cross(e_z, e_x)
    e_y = e_y / np.linalg.norm(e_y)
    
    # Matriz de rotação (Global -> Local): v_local = R @ v_global
    R = np.vstack([e_x, e_y, e_z])
    
    # 2. Coordenadas nodais no sistema local 2D (z deve ser ~0)
    local_coords = np.zeros((element.num_nodes, 2))
    origin = element_coords[0]
    for i in range(element.num_nodes):
        p_local = R @ (element_coords[i] - origin)
        local_coords[i, :] = p_local[0:2]
        
    # 3. Montar a Matriz de Transformação T (ndof x ndof)
    ndof = element.num_nodes * element.dofs_per_node
    T = np.zeros((ndof, ndof))
    for i in range(element.num_nodes):
        idx = i * element.dofs_per_node
        # Translações u_x, u_y, u_z
        T[idx:idx+3, idx:idx+3] = R
        # Rotações theta_x, theta_y, theta_z
        T[idx+3:idx+6, idx+3:idx+6] = R
        
    return R, T, local_coords

def assemble_global_stiffness(
    nodes: np.ndarray, 
    elements: np.ndarray, 
    E: float, 
    nu: float, 
    h: float
) -> sp.csc_matrix:
    """
    Constrói a Matriz de Rigidez Global estruturada no formato esparso.
    
    Args:
        nodes: (N, 3) Coordenadas globais dos nós da malha.
        elements: (E, 4) Conectividade dos elementos QUAD4.
        E, nu, h: Propriedades de material e espessura.
        
    Returns:
        K_global: Matriz esparsa (CSC) da estrutura completa.
    """
    num_nodes_mesh = nodes.shape[0]
    nodes_per_elem = elements.shape[1]
    element = get_element_instance(nodes_per_elem)
    
    # Substituindo o 6 fixo pelo parametro dinamico
    total_dofs = num_nodes_mesh * element.dofs_per_node
    
    # Listas para montar a matriz esparsa no formato COO
    I = []
    J = []
    V = []
    
    ndof = element.num_nodes * element.dofs_per_node
    
    for elem_nodes in elements:
        # Coordenadas 3D dos nós do elemento
        elem_coords = nodes[elem_nodes]
        
        # Obter a transformação geométrica
        R, T, local_coords = compute_element_transformation(element, elem_coords)
        
        # Calcular Matriz de Rigidez Local (ndof x ndof)
        Ke_local = compute_element_stiffness_local(element, local_coords, E, nu, h)
        
        # Transformar para o sistema Global
        Ke_global = T.T @ Ke_local @ T
        
        # Vetor contendo os índices globais dos GDLs do elemento
        gdl_indices = np.zeros(ndof, dtype=int)
        for i in range(element.num_nodes):
            node_id = elem_nodes[i]
            dof = element.dofs_per_node
            gdl_indices[i*dof : i*dof+dof] = np.arange(node_id*dof, node_id*dof+dof)
            
        # Adicionar as contribuições nas listas esparsas
        for i in range(ndof):
            for j in range(ndof):
                val = Ke_global[i, j]
                if abs(val) > 1e-12: # Filtra zeros absolutos
                    I.append(gdl_indices[i])
                    J.append(gdl_indices[j])
                    V.append(val)
                    
    # Monta a matriz no formato COO e converte para CSC (ideal para solver linear)
    K_global = sp.coo_matrix((V, (I, J)), shape=(total_dofs, total_dofs)).tocsc()
    
    return K_global

def assemble_geometric_stiffness(
    nodes: np.ndarray, 
    elements: np.ndarray, 
    U_global: np.ndarray, 
    E: float, 
    nu: float, 
    h: float
) -> sp.csc_matrix:
    """
    Constrói a Matriz de Rigidez Geométrica Global baseada no campo 
    de deslocamentos da pré-flambagem (U_global).
    """
    num_nodes_mesh = nodes.shape[0]
    nodes_per_elem = elements.shape[1]
    element = get_element_instance(nodes_per_elem)
    
    total_dofs = num_nodes_mesh * element.dofs_per_node
    
    Dm = compute_membrane_matrix(E, nu, h)
    
    I = []
    J = []
    V = []
    
    ndof = element.num_nodes * element.dofs_per_node
    
    for elem_nodes in elements:
        elem_coords = nodes[elem_nodes]
        R, T, local_coords = compute_element_transformation(element, elem_coords)
        
        # 1. Extrair os deslocamentos nodais globais deste elemento
        gdl_indices = np.zeros(ndof, dtype=int)
        for i in range(element.num_nodes):
            node_id = elem_nodes[i]
            dof = element.dofs_per_node
            gdl_indices[i*dof : i*dof+dof] = np.arange(node_id*dof, node_id*dof+dof)
            
        u_global_elem = U_global[gdl_indices]
        
        # 2. Transformar os deslocamentos para o sistema local
        u_local_elem = T @ u_global_elem
        
        # 3. Calcular tensões de membrana médias (no centro, xi=0, eta=0)
        dN_dxi_eta = element.shape_function_derivatives(0.0, 0.0)
        _, _, dN_dx_y = compute_jacobian(dN_dxi_eta, local_coords)
        Bm = compute_B_membrane(element, dN_dx_y)
        
        # Forças de membrana [Nx, Ny, Nxy]
        N_m = Dm @ (Bm @ u_local_elem)
        N_x, N_y, N_xy = N_m[0], N_m[1], N_m[2]
        
        # 4. Calcular Kg local
        Kg_local = compute_geometric_stiffness_local(element, local_coords, N_x, N_y, N_xy)
        
        # 5. Transformar para o sistema Global
        Kg_global_e = T.T @ Kg_local @ T
        
        # 6. Adicionar nas listas COO
        for i in range(ndof):
            for j in range(ndof):
                val = Kg_global_e[i, j]
                if abs(val) > 1e-12:
                    I.append(gdl_indices[i])
                    J.append(gdl_indices[j])
                    V.append(val)
                    
    Kg_global = sp.coo_matrix((V, (I, J)), shape=(total_dofs, total_dofs)).tocsc()
    return Kg_global

def compute_all_element_gauss_variables(
    nodes: np.ndarray,
    elements: np.ndarray,
    U_global: np.ndarray,
    E: float,
    nu: float,
    h: float
) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
    """
    Loop over elements to compute all physical variables at the Gauss points:
    stresses (top, bottom, mid), strains (top, bottom), internal forces and moments,
    and the area of each element.
    """
    num_elements = len(elements)
    nodes_per_elem = elements.shape[1]
    element = get_element_instance(nodes_per_elem)
    gps = element.get_membrane_bending_integration_points()
    num_gp = len(gps)
    
    Dm = compute_membrane_matrix(E, nu, h)
    Db = compute_bending_matrix(E, nu, h)
    
    # Initialize component dictionaries
    stresses_top = np.zeros((num_elements, num_gp, 3))
    stresses_bottom = np.zeros((num_elements, num_gp, 3))
    stresses_mid = np.zeros((num_elements, num_gp, 3))
    mises_max = np.zeros((num_elements, num_gp, 1))
    
    strains_top = np.zeros((num_elements, num_gp, 3))
    strains_bottom = np.zeros((num_elements, num_gp, 3))
    
    internal_forces = np.zeros((num_elements, num_gp, 6))
    element_areas = np.zeros(num_elements)
    
    ndof = element.num_nodes * element.dofs_per_node
    
    for e in range(num_elements):
        elem_nodes = elements[e]
        elem_coords = nodes[elem_nodes]
        R, T, local_coords = compute_element_transformation(element, elem_coords)
        
        gdl_indices = np.zeros(ndof, dtype=int)
        for i in range(element.num_nodes):
            node_id = elem_nodes[i]
            dof = element.dofs_per_node
            gdl_indices[i*dof : i*dof+dof] = np.arange(node_id*dof, node_id*dof+dof)
            
        u_global_elem = U_global[gdl_indices]
        u_local_elem = T @ u_global_elem
        
        area_accum = 0.0
        
        for g_idx, gp in enumerate(gps):
            xi, eta, w = gp
            dN_dxi_eta = element.shape_function_derivatives(xi, eta)
            J, detJ, dN_dx_y = compute_jacobian(dN_dxi_eta, local_coords)
            
            # w * detJ is the differential area
            dA = detJ * w
            area_accum += dA
            
            Bm = compute_B_membrane(element, dN_dx_y)
            Bb = compute_B_bending(element, dN_dx_y)
            
            # Kinematics
            strain_m = Bm @ u_local_elem
            strain_b = Bb @ u_local_elem
            
            # Constitutive relationships
            N_force = Dm @ strain_m
            M_moment = Db @ strain_b
            
            # Stresses
            stress_m = N_force / h
            stress_b = 6.0 * M_moment / (h**2)
            
            s_top = stress_m + stress_b
            s_bottom = stress_m - stress_b
            s_mid = stress_m
            
            stresses_top[e, g_idx, :] = s_top
            stresses_bottom[e, g_idx, :] = s_bottom
            stresses_mid[e, g_idx, :] = s_mid
            
            # von Mises stresses
            mises_t = np.sqrt(s_top[0]**2 + s_top[1]**2 - s_top[0]*s_top[1] + 3.0*s_top[2]**2)
            mises_b = np.sqrt(s_bottom[0]**2 + s_bottom[1]**2 - s_bottom[0]*s_bottom[1] + 3.0*s_bottom[2]**2)
            mises_m = np.sqrt(s_mid[0]**2 + s_mid[1]**2 - s_mid[0]*s_mid[1] + 3.0*s_mid[2]**2)
            
            mises_max[e, g_idx, 0] = max(mises_t, mises_b, mises_m)
            
            # Strains
            strains_top[e, g_idx, :] = strain_m + 0.5 * h * strain_b
            strains_bottom[e, g_idx, :] = strain_m - 0.5 * h * strain_b
            
            # Forces and moments [Nx, Ny, Nxy, Mx, My, Mxy]
            internal_forces[e, g_idx, 0:3] = N_force
            internal_forces[e, g_idx, 3:6] = M_moment
            
        element_areas[e] = area_accum
        
    gp_results = {
        "stresses_top": stresses_top,
        "stresses_bottom": stresses_bottom,
        "stresses_mid": stresses_mid,
        "mises_max": mises_max,
        "strains_top": strains_top,
        "strains_bottom": strains_bottom,
        "internal_forces": internal_forces
    }
    
    return gp_results, element_areas
