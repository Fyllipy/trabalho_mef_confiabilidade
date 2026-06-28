import numpy as np
from typing import List, Tuple
from mef.elements.base_element import ShellElement
from mef.formulation.gauss import get_gauss_points_2x2, get_gauss_points_1x1

class Quad4(ShellElement):
    """
    Elemento Finito Isoparamétrico de Casca Quadrilateral de 4 Nós.
    """
    
    @property
    def name(self) -> str:
        return "QUAD4"
        
    @property
    def num_nodes(self) -> int:
        return 4
        
    @property
    def dofs_per_node(self) -> int:
        return 6
        
    @property
    def vtk_cell_type(self) -> str:
        return "quad"
        
    def shape_functions(self, xi: float, eta: float) -> np.ndarray:
        """
        Os nós seguem a convenção (numeração anti-horária a partir do inferior esquerdo):
        Nó 1: (-1, -1), Nó 2: (1, -1), Nó 3: (1, 1), Nó 4: (-1, 1).
        """
        N1 = 0.25 * (1.0 - xi) * (1.0 - eta)
        N2 = 0.25 * (1.0 + xi) * (1.0 - eta)
        N3 = 0.25 * (1.0 + xi) * (1.0 + eta)
        N4 = 0.25 * (1.0 - xi) * (1.0 + eta)
        return np.array([N1, N2, N3, N4])

    def shape_function_derivatives(self, xi: float, eta: float) -> np.ndarray:
        dN_dxi = np.array([
            -0.25 * (1.0 - eta),
             0.25 * (1.0 - eta),
             0.25 * (1.0 + eta),
            -0.25 * (1.0 + eta)
        ])
        
        dN_deta = np.array([
            -0.25 * (1.0 - xi),
            -0.25 * (1.0 + xi),
             0.25 * (1.0 + xi),
             0.25 * (1.0 - xi)
        ])
        return np.vstack([dN_dxi, dN_deta])

    def get_membrane_bending_integration_points(self) -> List[Tuple[float, float, float]]:
        # Integração plena (Full Integration)
        return get_gauss_points_2x2()

    def get_shear_integration_points(self) -> List[Tuple[float, float, float]]:
        # Integração reduzida (Reduced Integration) para evitar shear locking
        return get_gauss_points_1x1()
