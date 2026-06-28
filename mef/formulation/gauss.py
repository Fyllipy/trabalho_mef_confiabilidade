import numpy as np
from typing import List, Tuple

def get_gauss_points_2x2() -> List[Tuple[float, float, float]]:
    """
    Retorna os pontos de integração de Gauss-Legendre de ordem 2x2.
    Esta é a regra de integração completa para matriz de rigidez 
    de membrana e flexão do elemento QUAD4.
    
    Cada ponto de integração é retornado em suas coordenadas 
    paramétricas naturais (xi, eta) variando de -1 a 1, e possui 
    um peso 'w' associado.
    
    Returns:
        Uma lista contendo 4 tuplas. Cada tupla tem o formato (xi, eta, peso).
    """
    # A raiz da quadratura de Gauss para n=2 é +/- 1/sqrt(3)
    p = 1.0 / np.sqrt(3.0)
    
    # O peso bidimensional w = w_xi * w_eta. Para n=2, os pesos unidimensionais são 1.0
    w = 1.0 * 1.0
    
    return [
        (-p, -p, w), # Ponto 1 (Quadrante 3)
        ( p, -p, w), # Ponto 2 (Quadrante 4)
        ( p,  p, w), # Ponto 3 (Quadrante 1)
        (-p,  p, w)  # Ponto 4 (Quadrante 2)
    ]

def get_gauss_points_1x1() -> List[Tuple[float, float, float]]:
    """
    Retorna os pontos de integração de Gauss-Legendre de ordem 1x1.
    Usualmente chamada de integração reduzida (subintegração), útil para
    evitar "shear locking" (travamento ao cisalhamento) na matriz de 
    cisalhamento transversal de elementos de casca como o QUAD4.
    
    Returns:
        Uma lista contendo 1 tupla no formato (xi, eta, peso).
    """
    # Ponto no centro do sistema paramétrico
    xi = 0.0
    eta = 0.0
    
    # O peso é a área total do retângulo natural (-1 a 1)x(-1 a 1) = 2*2 = 4
    w = 4.0
    
    return [
        (xi, eta, w)
    ]

def get_gauss_points_3x3() -> List[Tuple[float, float, float]]:
    """
    Retorna os pontos de integração de Gauss-Legendre de ordem 3x3.
    Esta é a regra de integração completa para matriz de rigidez 
    de membrana e flexão do elemento QUAD8.
    
    Returns:
        Uma lista contendo 9 tuplas no formato (xi, eta, peso).
    """
    # Raízes da quadratura de Gauss para n=3
    pts = [-np.sqrt(3.0/5.0), 0.0, np.sqrt(3.0/5.0)]
    
    # Pesos unidimensionais correspondentes
    weights = [5.0/9.0, 8.0/9.0, 5.0/9.0]
    
    points = []
    for i in range(3):
        for j in range(3):
            xi = pts[i]
            eta = pts[j]
            w = weights[i] * weights[j]
            points.append((xi, eta, w))
            
    return points
