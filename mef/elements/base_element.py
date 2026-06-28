from abc import ABC, abstractmethod
import numpy as np
from typing import List, Tuple

class ShellElement(ABC):
    """
    Interface base genérica para elementos finitos de casca (Shell).
    Define o contrato necessário para a montagem de matrizes de rigidez
    independente da ordem do elemento (ex: QUAD4, QUAD8).
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nome identificador do elemento (ex: 'QUAD4')."""
        pass
        
    @property
    @abstractmethod
    def num_nodes(self) -> int:
        """Número de nós por elemento."""
        pass
        
    @property
    @abstractmethod
    def dofs_per_node(self) -> int:
        """Número de graus de liberdade por nó (ex: 6 para cascas planares gerais)."""
        pass
        
    @property
    @abstractmethod
    def vtk_cell_type(self) -> str:
        """Nome do tipo de célula esperado pela biblioteca meshio/VTK (ex: 'quad', 'quad8')."""
        pass

    @abstractmethod
    def shape_functions(self, xi: float, eta: float) -> np.ndarray:
        """
        Retorna os valores das funções de forma em um ponto (xi, eta).
        
        Args:
            xi, eta: Coordenadas paramétricas (-1 a 1).
        Returns:
            np.ndarray de tamanho (num_nodes,).
        """
        pass

    @abstractmethod
    def shape_function_derivatives(self, xi: float, eta: float) -> np.ndarray:
        """
        Retorna as derivadas das funções de forma em relação a xi e eta.
        
        Args:
            xi, eta: Coordenadas paramétricas (-1 a 1).
        Returns:
            np.ndarray de tamanho (2, num_nodes) onde:
            Linha 0: dNi/dxi
            Linha 1: dNi/deta
        """
        pass

    @abstractmethod
    def get_membrane_bending_integration_points(self) -> List[Tuple[float, float, float]]:
        """
        Retorna os pontos de integração de Gauss para a matriz de membrana e flexão (Full Integration).
        Returns:
            Lista de tuplas (xi, eta, peso).
        """
        pass

    @abstractmethod
    def get_shear_integration_points(self) -> List[Tuple[float, float, float]]:
        """
        Retorna os pontos de integração de Gauss para a matriz de cisalhamento transversal (Reduced Integration).
        Returns:
            Lista de tuplas (xi, eta, peso).
        """
        pass
