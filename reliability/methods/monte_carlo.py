import numpy as np
from typing import List

from ..variables.random_model import RandomModel
from ..response_surface.base import ResponseSurface

class MonteCarlo:
    """
    Simulação de Monte Carlo operando EXCLUSIVAMENTE sobre a Superfície de Resposta.
    Extremamente rápido, permite avaliar milhões de amostras.
    """
    def __init__(self, random_model: RandomModel, rsm: ResponseSurface, load_var_name: str, rsm_var_names: List[str]):
        self.rm = random_model
        self.rsm = rsm
        self.load_name = load_var_name
        self.rsm_var_names = rsm_var_names
        
    def run(self, num_samples: int = 1000000):
        print(f"\nIniciando Monte Carlo com {num_samples} amostras...")
        
        # 1. Gerar as amostras para todas as variáveis aleatórias
        samples_dict = self.rm.generate_samples(num_samples)
        
        # 2. Extrair matriz de amostras que vão para o RSM
        x_rsm_samples = np.column_stack([samples_dict[name] for name in self.rsm_var_names])
        
        # 3. Prever a Carga Crítica (Capacidade) usando o RSM velozmente
        p_cr_samples = self.rsm.predict(x_rsm_samples)
        
        # 4. Extrair amostras da Carga Aplicada (Demanda)
        load_samples = samples_dict[self.load_name]
        
        # 5. Avaliar Equação de Estado Limite: g(X) = P_cr - P
        g_samples = p_cr_samples - load_samples
        
        # 6. Contabilizar falhas
        num_fails = np.sum(g_samples < 0)
        p_f = num_fails / float(num_samples)
        
        print(f"Monte Carlo concluído.")
        print(f"Falhas detectadas: {num_fails} em {num_samples}")
        print(f"Probabilidade de Falha (Pf): {p_f:.4e}")
        
        return p_f, p_cr_samples, g_samples
