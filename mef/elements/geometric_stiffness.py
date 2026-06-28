import numpy as np

from mef.elements.base_element import ShellElement
from mef.formulation.jacobian import compute_jacobian

def compute_geometric_stiffness_local(element: ShellElement, local_coords: np.ndarray, N_x: float, N_y: float, N_xy: float) -> np.ndarray:
    """
    Calcula a matriz de rigidez geométrica local de um elemento de casca plana.
    
    A matriz geométrica (Kg) depende do estado de tensões de membrana (N_x, N_y, N_xy)
    no plano do elemento, calculado na etapa de pré-flambagem estática.
    
    Args:
        element: Instância de ShellElement.
        local_coords: (N, 2) coordenadas (x, y) dos N nós locais.
        N_x: Força normal de membrana na direção x local (força / comprimento).
        N_y: Força normal de membrana na direção y local.
        N_xy: Força de cisalhamento de membrana no plano local.
        
    Returns:
        Kg_local: Array (ndof, ndof)
    """
    ndof = element.num_nodes * element.dofs_per_node
    Kg = np.zeros((ndof, ndof))
    
    # Matriz de tensões de membrana
    M_sigma = np.array([[N_x, N_xy], 
                        [N_xy, N_y]])
    
    for xi, eta, w in element.get_membrane_bending_integration_points():
        dN_dxi_eta = element.shape_function_derivatives(xi, eta)
        
        J, detJ, dN_dx_y = compute_jacobian(dN_dxi_eta, local_coords)
        
        # Matriz G que relaciona as derivadas espaciais dos deslocamentos (dw/dx, dw/dy)
        # com os deslocamentos nodais (w, translação z local).
        # G tem dimensões (2, ndof)
        
        G = np.zeros((2, ndof))
        for i in range(element.num_nodes):
            idx = i * element.dofs_per_node
            # G associa as derivadas dw/dx e dw/dy ao grau de liberdade u_z (índice idx+2)
            G[0, idx + 2] = dN_dx_y[0, i] # dN_i/dx
            G[1, idx + 2] = dN_dx_y[1, i] # dN_i/dy
            
        dA = detJ * w
        
        # Contribuição elementar: Integral(G^T * M_sigma * G * dA)
        Kg += G.T @ M_sigma @ G * dA
        
    return Kg
