import numpy as np
from scipy import stats
from typing import List, Dict

from ..variables.random_model import RandomModel
from ..response_surface.base import ResponseSurface

class FORM:
    """
    First-Order Reliability Method (HLRF Algorithm).
    A avaliação do limite de estado e seu gradiente dependem exclusivamente da Superfície de Resposta.
    """
    def __init__(self, random_model: RandomModel, rsm: ResponseSurface, load_var_name: str, rsm_var_names: List[str]):
        """
        :param random_model: Container com todas as variáveis aleatórias.
        :param rsm: Superfície de resposta já ajustada (aproximando P_cr).
        :param load_var_name: Nome da variável que representa a Carga P (demanda).
        :param rsm_var_names: Lista dos nomes das variáveis que entram no RSM (ex: ['t', 'A']).
        """
        self.rm = random_model
        self.rsm = rsm
        self.load_name = load_var_name
        self.rsm_var_names = rsm_var_names
        self.var_names = self.rm.get_variable_names() # Todas as variáveis (inclui RSM e Carga)
        
    def _transform_u_to_x(self, u: np.ndarray) -> np.ndarray:
        x = np.zeros_like(u)
        for i, name in enumerate(self.var_names):
            var = self.rm.get_variable(name)
            # p = Phi(u)
            p = stats.norm.cdf(u[i])
            p = np.clip(p, 1e-9, 1.0 - 1e-9)
            x[i] = var.icdf(p)
        return x
        
    def _evaluate_g_and_grad(self, x: np.ndarray) -> tuple[float, np.ndarray]:
        # 1. Separar variáveis do RSM e da Carga
        x_dict = {name: val for name, val in zip(self.var_names, x)}
        
        x_rsm = np.array([x_dict[name] for name in self.rsm_var_names])
        load_val = x_dict[self.load_name]
        
        # 2. Avaliar G(X) = RSM(X_rsm) - P
        p_cr = self.rsm.predict(x_rsm)[0]
        g_val = p_cr - load_val
        
        # 3. Gradiente Analítico
        grad_rsm = self.rsm.gradient(x_rsm)
        
        grad_x = np.zeros_like(x)
        for i, name in enumerate(self.var_names):
            if name == self.load_name:
                grad_x[i] = -1.0 # dg/dP = -1
            else:
                # É uma variável geométrica
                idx_in_rsm = self.rsm_var_names.index(name)
                grad_x[i] = grad_rsm[idx_in_rsm]
                
        return g_val, grad_x
        
    def run(self, max_iter=100, tol=1e-4, verbose=True):
        n_vars = len(self.var_names)
        u = np.zeros(n_vars) # Inicia na origem do espaço normal padrão
        
        beta_history = []
        self.alpha_star = np.zeros(n_vars)
        
        if verbose:
            print("\n" + "="*45)
            print("INICIANDO ANÁLISE DE CONFIABILIDADE (FORM)")
            print("="*45)
        
        for i in range(max_iter):
            # Transformação inversa U -> X
            x = self._transform_u_to_x(u)
            
            # Avaliar Função Limite e Gradiente no espaço X
            g_val, grad_x = self._evaluate_g_and_grad(x)
            
            # Transformação do gradiente para o espaço U (Regra da Cadeia e Rackwitz-Fiessler)
            grad_u = np.zeros_like(u)
            for j, name in enumerate(self.var_names):
                var = self.rm.get_variable(name)
                # J_jj = dx_j / du_j = phi(u_j) / f_x(x_j)
                f_x = var.pdf(x[j])
                phi_u = stats.norm.pdf(u[j])
                
                if f_x < 1e-12:
                    f_x = 1e-12
                    
                dx_du = phi_u / f_x
                grad_u[j] = grad_x[j] * dx_du
                
            # Norma do gradiente em U
            norm_grad_u = np.linalg.norm(grad_u)
            alpha = -grad_u / norm_grad_u
            
            # Atualização HLRF
            beta = np.dot(alpha, u) + g_val / norm_grad_u
            u_new = beta * alpha
            beta_history.append(beta)
            
            erro = np.linalg.norm(u_new - u)
            u = u_new
            
            if erro < tol:
                self.alpha_star = alpha
                if verbose:
                    print(f"FORM convergiu em {i+1} iterações.")
                    print(f"Índice de Confiabilidade (Beta): {beta:.4f}")
                    p_f = stats.norm.cdf(-beta)
                    print(f"Probabilidade de Falha (Pf):     {p_f:.4e}")
                    
                    mpp_x = self._transform_u_to_x(u)
                    print(f"Ponto de Falha Mais Provável (MPP) em X:")
                    for name, val in zip(self.var_names, mpp_x):
                        print(f"  {name} = {val:.4e}")
                else:
                    p_f = stats.norm.cdf(-beta)
                    mpp_x = self._transform_u_to_x(u)
                    
                return beta, p_f, u, mpp_x, beta_history
                
        if verbose:
            print("Aviso: FORM não convergiu no número máximo de iterações.")
        return None, None, u, self._transform_u_to_x(u), beta_history
