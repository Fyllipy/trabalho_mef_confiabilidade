from abc import ABC, abstractmethod
import numpy as np

class DesignOfExperiments(ABC):
    """
    Classe base para métodos de Planejamento de Experimentos (DOE).
    """
    @abstractmethod
    def generate_samples(self, num_vars: int) -> np.ndarray:
        """
        Gera a matriz de projeto (design matrix) no espaço normalizado (espaço de fatores).
        
        :param num_vars: Número de variáveis do problema.
        :return: Array numpy de shape (n_amostras, num_vars).
        """
        pass
