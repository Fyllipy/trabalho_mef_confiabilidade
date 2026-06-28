import numpy as np
import scipy.sparse as sp
from typing import List, Tuple

def apply_boundary_conditions_penalty(
    K_global: sp.csc_matrix, 
    F_global: np.ndarray, 
    prescribed_dofs: List[int], 
    prescribed_values: List[float]
) -> Tuple[sp.csc_matrix, np.ndarray]:
    """
    Aplica as condições de contorno de Dirichlet (deslocamentos impostos)
    utilizando o método de penalidade.
    
    Método didático: Adicionamos um número muito grande (fator de penalidade) 
    na diagonal principal da matriz de rigidez correspondente ao grau de 
    liberdade prescrito. A força correspondente recebe o produto deste fator 
    pelo valor imposto. Isso forçará U_i = valor_imposto na solução sem 
    alterar a simetria ou o tamanho da matriz.
    
    Args:
        K_global: Matriz esparsa de rigidez global.
        F_global: Vetor de forças nodais equivalentes.
        prescribed_dofs: Lista com os índices globais dos graus de liberdade restritos.
        prescribed_values: Lista com os valores impostos (ex: 0.0 para engaste).
        
    Returns:
        K_mod: Matriz K modificada (convertida para LIL para modificação eficiente, 
               retornada no formato CSR).
        F_mod: Vetor de força modificado.
    """
    # Converte para LIL pois é eficiente para alterar a estrutura da matriz (alterar diagonal)
    K_mod = K_global.tolil()
    F_mod = F_global.copy()
    
    # Fator de penalidade: suficientemente grande para não ser ignorado 
    # (K médio tipicamente ~1e5 a 1e9, 1e15 é uma magnitude segura em double precision)
    penalty = 1e15
    
    for dof, val in zip(prescribed_dofs, prescribed_values):
        # Aumentamos brutalmente a rigidez na diagonal daquele GDL
        K_mod[dof, dof] += penalty
        
        # Ajustamos o vetor de forças para que u_dof aproxime de 'val'
        F_mod[dof] += penalty * val
        
    # Converte para CSR, que é o formato ótimo para a solução de sistemas lineares
    return K_mod.tocsr(), F_mod
