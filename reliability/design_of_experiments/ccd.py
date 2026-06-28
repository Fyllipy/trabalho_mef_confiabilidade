import numpy as np
from itertools import product
from .base import DesignOfExperiments

class CentralCompositeDesign(DesignOfExperiments):
    """
    Central Composite Design (CCD) puro em numpy.
    Apropriado para ajuste de superfícies de resposta quadráticas.
    """
    def __init__(self, alpha: str = 'orthogonal', center_points: int = 1):
        """
        :param alpha: 'orthogonal', 'rotatable', 'spherical', ou um valor numérico float.
        :param center_points: Número de pontos centrais a serem gerados.
        """
        self.alpha = alpha
        self.center_points = center_points
        
    def generate_samples(self, num_vars: int) -> np.ndarray:
        # 1. Pontos fatoriais (+1 e -1)
        factorial_pts = np.array(list(product([-1.0, 1.0], repeat=num_vars)))
        
        # 2. Definição do valor de alpha
        if isinstance(self.alpha, str):
            if self.alpha == 'orthogonal':
                # Para CCD ortogonal, depende do número de variáveis e pontos centrais.
                # Aproximação comum para k variáveis e F=2^k:
                F = len(factorial_pts)
                alpha_val = ((np.sqrt(F + 2*num_vars + self.center_points) - np.sqrt(F))**2 * F / 4.0)**0.25
            elif self.alpha == 'rotatable' or self.alpha == 'spherical':
                alpha_val = (len(factorial_pts))**0.25
            else:
                alpha_val = float(self.alpha)
        else:
            alpha_val = float(self.alpha)
            
        # 3. Pontos axiais (estrela)
        axial_pts = np.zeros((2 * num_vars, num_vars))
        for i in range(num_vars):
            axial_pts[2*i, i] = alpha_val
            axial_pts[2*i+1, i] = -alpha_val
            
        # 4. Pontos centrais (0, 0, ..., 0)
        center_pts = np.zeros((self.center_points, num_vars))
        
        # Concatenar todos os blocos
        design_matrix = np.vstack((factorial_pts, axial_pts, center_pts))
        return design_matrix
