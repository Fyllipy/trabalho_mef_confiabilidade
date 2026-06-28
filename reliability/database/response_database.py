import numpy as np
from typing import List, Dict, Any, Tuple

class ResponseDatabase:
    """
    Armazena e gerencia os resultados do MEF gerados pelo DOE.
    Além do vetor de entrada (X) e a resposta (Y), grava metadados de auditoria.
    """
    def __init__(self, variable_names: List[str]):
        self.variable_names = variable_names
        self.X_data = []
        self.Y_data = []
        self.metadata = []
        
    def add_sample(self, X: np.ndarray, Y: float, meta: Dict[str, Any]):
        """
        Registra uma avaliação pontual do solver MEF.
        
        :param X: Vetor de variáveis físicas (ex: [espessura, imperfeição]).
        :param Y: Resposta de interesse (Carga Crítica - P_cr).
        :param meta: Dicionário contendo metadados (tempo_s, convergencia, iteracoes, solver_type).
        """
        if len(X) != len(self.variable_names):
            raise ValueError("O tamanho de X não corresponde ao número de variáveis aleatórias.")
            
        self.X_data.append(np.array(X, dtype=float))
        self.Y_data.append(float(Y))
        self.metadata.append(meta)
        
    def get_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Retorna as matrizes consolidadas X e Y para construção da Superfície de Resposta.
        :return: (X_matrix, Y_vector)
        """
        if not self.X_data:
            return np.array([]), np.array([])
            
        return np.vstack(self.X_data), np.array(self.Y_data)
        
    def get_metadata(self) -> List[Dict[str, Any]]:
        return self.metadata
        
    def __len__(self):
        return len(self.X_data)
