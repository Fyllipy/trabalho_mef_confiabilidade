import numpy as np
from scipy import stats

class RandomVariable:
    """
    Encapsula as operações estatísticas para não depender diretamente do scipy.stats no resto do código.
    """
    def __init__(self, name: str, distribution: str, mean: float, std_dev: float):
        self.name = name
        self.distribution = distribution.lower()
        self.mean = mean
        self.std_dev = std_dev
        self._dist = self._init_distribution()
        
    def _init_distribution(self):
        if self.distribution == "normal":
            return stats.norm(loc=self.mean, scale=self.std_dev)
        elif self.distribution == "lognormal":
            # Para a Lognormal, precisamos converter os parâmetros reais (média e desvio) 
            # para os parâmetros da Normal subjacente (mu e sigma).
            cov = self.std_dev / self.mean
            sigma_ln = np.sqrt(np.log(1.0 + cov**2))
            mu_ln = np.log(self.mean) - 0.5 * sigma_ln**2
            return stats.lognorm(s=sigma_ln, scale=np.exp(mu_ln))
        else:
            raise ValueError(f"Distribuição não suportada: {self.distribution}")
            
    def pdf(self, x):
        """Probability Density Function (Função Densidade de Probabilidade)"""
        return self._dist.pdf(x)
        
    def cdf(self, x):
        """Cumulative Distribution Function (Função Acumulada)"""
        return self._dist.cdf(x)
        
    def icdf(self, p):
        """Inverse Cumulative Distribution Function (Inversa da Acumulada, ppf)"""
        return self._dist.ppf(p)
        
    def sample(self, num_samples=1):
        """Gera amostras aleatórias da distribuição"""
        return self._dist.rvs(size=num_samples)
