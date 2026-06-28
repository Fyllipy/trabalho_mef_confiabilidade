from typing import Dict
import numpy as np
from .random_variable import RandomVariable

class RandomModel:
    """
    Container configurável para gerenciar as variáveis aleatórias da análise de confiabilidade.
    """
    def __init__(self):
        self.random_variables: Dict[str, RandomVariable] = {}
        
    def add_variable(self, name: str, distribution: str, mean: float, std_dev: float):
        self.random_variables[name] = RandomVariable(name, distribution, mean, std_dev)
        
    def get_variable(self, name: str) -> RandomVariable:
        return self.random_variables[name]
        
    def get_variable_names(self) -> list:
        return list(self.random_variables.keys())
        
    def generate_samples(self, num_samples: int) -> Dict[str, np.ndarray]:
        """
        Gera amostras para todas as variáveis aleatórias.
        """
        samples = {}
        for name, var in self.random_variables.items():
            samples[name] = var.sample(num_samples)
        return samples
