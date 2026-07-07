import numpy as np
from typing import Dict, Any
from shared.results import ShellResults
from mef.model.shell_model import ShellModel
from mef.assembly.global_assembly import get_element_instance

def get_extrapolation_matrix(num_nodes: int) -> np.ndarray:
    """
    Constrói a matriz de extrapolação local E para mapear valores dos pontos de Gauss
    para os nós locais do elemento.
    
    - Para 4 nós (QUAD4, Gauss 2x2): Usa a inversão da matriz de funções de forma H.
    - Para 8 nós (QUAD8, Gauss 3x3): Usa a interpolação Lagrangeana biquadrática clássica
      conforme a literatura de Bathe e Zienkiewicz.
    """
    if num_nodes == 4:
        # QUAD4: 2x2 Gauss integration (4 Gauss points)
        # H[g, i] = N_i(xi_g, eta_g)
        p = 1.0 / np.sqrt(3.0)
        gps = [
            (-p, -p), # GP 1
            ( p, -p), # GP 2
            ( p,  p), # GP 3
            (-p,  p)  # GP 4
        ]
        H = np.zeros((4, 4))
        for g, (xi, eta) in enumerate(gps):
            H[g, 0] = 0.25 * (1.0 - xi) * (1.0 - eta)
            H[g, 1] = 0.25 * (1.0 + xi) * (1.0 - eta)
            H[g, 2] = 0.25 * (1.0 + xi) * (1.0 + eta)
            H[g, 3] = 0.25 * (1.0 - xi) * (1.0 + eta)
        return np.linalg.inv(H)
        
    elif num_nodes == 8:
        # QUAD8: 3x3 Gauss integration (9 Gauss points)
        # Extrapolação biquadrática de Lagrange clássica.
        p = np.sqrt(3.0 / 5.0)
        
        # 9 pontos de Gauss ordenados lexicograficamente (i, j de 0 a 2)
        pts_1d = [-p, 0.0, p]
        gps = []
        for i in range(3):
            for j in range(3):
                gps.append((pts_1d[i], pts_1d[j]))
        
        # Nós locais do QUAD8:
        # 1 a 4: vertices (-1,-1), (1,-1), (1,1), (-1,1)
        # 5 a 8: pontos médios (0,-1), (1,0), (0,1), (-1,0)
        nodes_local = [
            (-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0),
            (0.0, -1.0), (1.0, 0.0), (0.0, 1.0), (-1.0, 0.0)
        ]
        
        # Funções 1D de Lagrange correspondentes aos nós de interpolação [-p, 0, p]
        def l_func(val: float, idx: int) -> float:
            if idx == 0:
                return val * (val - p) / (2.0 * p**2)
            elif idx == 1:
                return 1.0 - val**2 / p**2
            elif idx == 2:
                return val * (val + p) / (2.0 * p**2)
            raise ValueError("Índice de Lagrange inválido.")

        E = np.zeros((8, 9))
        for n, (xi_n, eta_n) in enumerate(nodes_local):
            for g in range(9):
                i = g // 3
                j = g % 3
                # M_g(xi, eta) = l_i(xi) * l_j(eta)
                val_m = l_func(xi_n, i) * l_func(eta_n, j)
                E[n, g] = val_m
        return E
    else:
        raise ValueError(f"Extrapolação não suportada para elementos com {num_nodes} nós.")

def postprocess_results(
    model: ShellModel,
    U_global: np.ndarray,
    gp_results: Dict[str, np.ndarray],
    element_areas: np.ndarray
) -> ShellResults:
    """
    Executa o pós-processamento completo dos resultados obtidos.
    
    1. Armazena os resultados de Gauss brutos.
    2. Interpola deslocamentos nodais para os pontos de Gauss.
    3. Extrapola todas as variáveis de Gauss para os nós dos elementos.
    4. Realiza a média nodal ponderada pela área real dos elementos (A_e).
    5. Retorna o objeto ShellResults configurado.
    """
    nodes = model.mesh_data["nodes"]
    elements = model.mesh_data["elements"]
    num_nodes = len(nodes)
    num_elements = len(elements)
    
    nodes_per_elem = elements.shape[1]
    element = get_element_instance(nodes_per_elem)
    
    # Obter pontos de integração completos (membrane/bending)
    gps = element.get_membrane_bending_integration_points()
    num_gp = len(gps)
    
    res = ShellResults()
    
    # Injetar metadados ricos e extensíveis
    res.metadata = {
        "element_type": model.element_type,
        "integration_order": "3x3" if nodes_per_elem == 8 else "2x2",
        "num_gauss_points": num_gp,
        "extrapolation_method": "biquadratic_lagrange" if nodes_per_elem == 8 else "bilinear_shape_functions",
        "nodal_averaging": "element_area",
        "results_location": model.results_location
    }
    
    # -------------------------------------------------------------
    # 1. Armazenamento e Interpolação no nível Gauss
    # -------------------------------------------------------------
    res.data["gauss"] = {}
    for key, val in gp_results.items():
        res.data["gauss"][key] = val
        
    # Interpolar deslocamentos nodais para pontos de Gauss
    # u_GP = N * u_e
    gp_displacements = np.zeros((num_elements, num_gp, 3))
    
    # Obter os deslocamentos nodais em formato (num_nodes, 6)
    U_reshaped = U_global.reshape(-1, 6)
    u_nodal_trans = U_reshaped[:, 0:3]
    
    for e in range(num_elements):
        elem_nodes = elements[e]
        elem_disp = u_nodal_trans[elem_nodes] # (num_nodes, 3)
        for g_idx, gp in enumerate(gps):
            xi, eta, _ = gp
            N = element.shape_functions(xi, eta) # (num_nodes,)
            gp_displacements[e, g_idx, :] = N @ elem_disp
            
    res.data["gauss"]["displacements"] = gp_displacements
    
    # -------------------------------------------------------------
    # 2. Extrapolação e Média Nodal (Nível Nodal)
    # -------------------------------------------------------------
    res.data["nodal"] = {
        "displacements": u_nodal_trans,
        "rotations": U_reshaped[:, 3:6]
    }
    
    # Matriz de extrapolação E do elemento
    E_mat = get_extrapolation_matrix(nodes_per_elem) # (nodes_per_elem, num_gp)
    
    # Para cada grandeza calculada em Gauss, extrapolar para os nós e aplicar média ponderada por A_e
    # gp_results contém arrays com forma (num_elements, num_gp, num_components)
    for var_name, gp_data in gp_results.items():
        num_components = gp_data.shape[2]
        
        # Array acumulador global de numeradores e denominadores para média ponderada
        global_numerator = np.zeros((num_nodes, num_components))
        global_denominator = np.zeros(num_nodes)
        
        for e in range(num_elements):
            elem_nodes = elements[e]
            elem_gp_data = gp_data[e] # (num_gp, num_components)
            
            # Extrapolação local para os nós do elemento: (nodes_per_elem, num_components)
            # E_mat é (nodes_per_elem, num_gp) e elem_gp_data é (num_gp, num_components)
            elem_node_data = E_mat @ elem_gp_data
            
            # Ponderação pela área do elemento A_e
            A_e = element_areas[e]
            
            for local_idx, global_node_id in enumerate(elem_nodes):
                global_numerator[global_node_id, :] += elem_node_data[local_idx, :] * A_e
                global_denominator[global_node_id] += A_e
                
        # Calcular média final
        nodal_averaged_data = np.zeros((num_nodes, num_components))
        for n in range(num_nodes):
            denom = global_denominator[n]
            if denom > 1e-14:
                nodal_averaged_data[n, :] = global_numerator[n, :] / denom
                
        res.data["nodal"][var_name] = nodal_averaged_data
        
    return res
