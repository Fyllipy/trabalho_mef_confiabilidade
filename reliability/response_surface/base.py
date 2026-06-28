from abc import ABC, abstractmethod
import numpy as np

class ResponseSurface(ABC):
    """
    Classe base para todas as Superfícies de Resposta (RSM).
    Permite polimorfismo entre modelos lineares, quadráticos e estendidos.
    """
    def __init__(self):
        self.coefficients = None
        self.is_fitted = False
        
    @abstractmethod
    def fit(self, X: np.ndarray, Y: np.ndarray):
        """
        Ajusta os coeficientes da regressão usando a matriz (X) e o vetor resposta (Y).
        """
        pass
        
    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Prevê o valor de Y (ex: P_cr) para um dado vetor ou matriz X.
        """
        pass
        
    @abstractmethod
    def gradient(self, X: np.ndarray) -> np.ndarray:
        """
        Calcula o gradiente analítico (dY/dX) da superfície no ponto X.
        Essencial para o FORM.
        """
        pass
