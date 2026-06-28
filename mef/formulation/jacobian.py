import numpy as np
from typing import Tuple

def compute_jacobian(
    dN_dxi_eta: np.ndarray, 
    local_node_coords: np.ndarray
) -> Tuple[np.ndarray, float, np.ndarray]:
    """
    Calcula a Matriz Jacobiana J, seu determinante |J|, e as derivadas 
    espaciais Cartesianas das funções de forma (dN/dx, dN/dy) em um 
    dado ponto de integração.
    
    Esta formulação isoparamétrica mapeia as derivadas do domínio natural 
    (xi, eta) para as derivadas no domínio físico local bidimensional (x, y).
    
    NOTA DIDÁTICA: Em análise de cascas 3D, 'local_node_coords' deve representar 
    as coordenadas dos nós já projetadas no plano bidimensional local do elemento.
    
    Args:
        dN_dxi_eta: Array (2, N_nos) com as derivadas paramétricas. 
                    (Linha 0: dN/dxi, Linha 1: dN/deta)
        local_node_coords: Array (N_nos, 2) com as coordenadas reais (x, y)
                           dos nós no sistema local do elemento de casca.
                           
    Returns:
        J: Matriz Jacobiana (2x2). 
           [dx/dxi,  dy/dxi ]
           [dx/deta, dy/deta]
        detJ: Determinante do Jacobiano (usado para converter áreas dA = detJ * dxi * deta).
        dN_dx_y: Array (2, N_nos) com as derivadas espaciais.
                 (Linha 0: dN/dx, Linha 1: dN/dy)
    """
    
    # A Matriz Jacobiana relaciona variações em (xi, eta) com variações em (x, y).
    # Pela regra da cadeia: x = sum(Ni * xi), então dx/dxi = sum(dNi/dxi * xi)
    J = dN_dxi_eta @ local_node_coords
    
    # Determinante
    detJ = np.linalg.det(J)
    
    # Verificação de inversibilidade
    if detJ <= 0.0:
        raise ValueError(
            f"Determinante Jacobiano inválido (detJ = {detJ:.4e}). "
            "Isso ocorre se a malha estiver muito distorcida ou se a numeração "
            "dos nós não estiver no sentido anti-horário apropriado."
        )
        
    # As derivadas cartesianas são obtidas pela multiplicação da inversa 
    # da Matriz Jacobiana pelo vetor das derivadas paramétricas.
    # [dN/dx] = J^-1 * [dN/dxi ]
    # [dN/dy]          [dN/deta]
    J_inv = np.linalg.inv(J)
    dN_dx_y = J_inv @ dN_dxi_eta
    
    return J, detJ, dN_dx_y
