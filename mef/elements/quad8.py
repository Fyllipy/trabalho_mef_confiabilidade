import numpy as np
from typing import List, Tuple
from mef.elements.base_element import ShellElement
from mef.formulation.gauss import get_gauss_points_3x3, get_gauss_points_2x2

class Quad8(ShellElement):
    """
    Elemento Finito Isoparamétrico de Casca Quadrilateral Serendipity de 8 Nós.
    """
    
    @property
    def name(self) -> str:
        return "QUAD8"
        
    @property
    def num_nodes(self) -> int:
        return 8
        
    @property
    def dofs_per_node(self) -> int:
        return 6
        
    @property
    def vtk_cell_type(self) -> str:
        # Meshio utiliza a string 'quad8' para designar elementos quadrilaterais de 8 nós.
        return "quad8"
        
    def shape_functions(self, xi: float, eta: float) -> np.ndarray:
        """
        Calcula as funções de forma do QUAD8.
        Nós 1 a 4: Vértices (-1,-1), (1,-1), (1,1), (-1,1)
        Nós 5 a 8: Pontos médios das arestas (0,-1), (1,0), (0,1), (-1,0)
        """
        N = np.zeros(8)
        
        # Vértices (1 a 4)
        N[0] = -0.25 * (1.0 - xi) * (1.0 - eta) * (1.0 + xi + eta)
        N[1] = -0.25 * (1.0 + xi) * (1.0 - eta) * (1.0 - xi + eta)
        N[2] = -0.25 * (1.0 + xi) * (1.0 + eta) * (1.0 - xi - eta)
        N[3] = -0.25 * (1.0 - xi) * (1.0 + eta) * (1.0 + xi - eta)
        
        # Nós médios (5 a 8)
        N[4] = 0.5 * (1.0 - xi**2) * (1.0 - eta)
        N[5] = 0.5 * (1.0 + xi) * (1.0 - eta**2)
        N[6] = 0.5 * (1.0 - xi**2) * (1.0 + eta)
        N[7] = 0.5 * (1.0 - xi) * (1.0 - eta**2)
        
        return N

    def shape_function_derivatives(self, xi: float, eta: float) -> np.ndarray:
        """
        Calcula as derivadas em relação a xi e eta.
        """
        dN_dxi = np.zeros(8)
        dN_deta = np.zeros(8)
        
        # dN/dxi
        dN_dxi[0] = 0.25 * (1.0 - eta) * (2.0 * xi + eta)
        dN_dxi[1] = 0.25 * (1.0 - eta) * (2.0 * xi - eta)
        dN_dxi[2] = 0.25 * (1.0 + eta) * (2.0 * xi + eta)
        dN_dxi[3] = 0.25 * (1.0 + eta) * (2.0 * xi - eta)
        dN_dxi[4] = -xi * (1.0 - eta)
        dN_dxi[5] = 0.5 * (1.0 - eta**2)
        dN_dxi[6] = -xi * (1.0 + eta)
        dN_dxi[7] = -0.5 * (1.0 - eta**2)
        
        # dN/deta
        dN_deta[0] = 0.25 * (1.0 - xi) * (xi + 2.0 * eta)
        dN_deta[1] = 0.25 * (1.0 + xi) * (-xi + 2.0 * eta)
        dN_deta[2] = 0.25 * (1.0 + xi) * (xi + 2.0 * eta)
        dN_deta[3] = 0.25 * (1.0 - xi) * (-xi + 2.0 * eta)
        dN_deta[4] = -0.5 * (1.0 - xi**2)
        dN_deta[5] = -eta * (1.0 + xi)
        dN_deta[6] = 0.5 * (1.0 - xi**2)
        dN_deta[7] = -eta * (1.0 - xi)
        
        return np.vstack([dN_dxi, dN_deta])

    def get_membrane_bending_integration_points(self) -> List[Tuple[float, float, float]]:
        # Integração Plena (3x3) para membrana e flexão de cascas quadráticas
        return get_gauss_points_3x3()

    def get_shear_integration_points(self) -> List[Tuple[float, float, float]]:
        # Integração Reduzida (2x2) para evitar shear locking transversal em cascas quadráticas
        return get_gauss_points_2x2()
