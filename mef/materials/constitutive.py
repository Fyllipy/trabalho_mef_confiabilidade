import numpy as np

def compute_membrane_matrix(E: float, nu: float, h: float) -> np.ndarray:
    """
    Constrói a Matriz Constitutiva de Membrana (Dm) para estado plano de tensões.
    Relaciona as tensões (forças por unidade de comprimento) com as deformações no plano.
    
    Args:
        E: Módulo de Elasticidade (Young)
        nu: Coeficiente de Poisson
        h: Espessura da casca
        
    Returns:
        Dm: Array 3x3
    """
    coef = (E * h) / (1.0 - nu**2)
    Dm = np.array([
        [1.0,  nu,  0.0],
        [ nu, 1.0,  0.0],
        [0.0, 0.0, (1.0 - nu) / 2.0]
    ])
    return coef * Dm

def compute_bending_matrix(E: float, nu: float, h: float) -> np.ndarray:
    """
    Constrói a Matriz Constitutiva de Flexão (Db).
    Relaciona os momentos fletores com as curvaturas da casca.
    
    Args:
        E: Módulo de Elasticidade
        nu: Coeficiente de Poisson
        h: Espessura
        
    Returns:
        Db: Array 3x3
    """
    coef = (E * h**3) / (12.0 * (1.0 - nu**2))
    Db = np.array([
        [1.0,  nu,  0.0],
        [ nu, 1.0,  0.0],
        [0.0, 0.0, (1.0 - nu) / 2.0]
    ])
    return coef * Db

def compute_shear_matrix(E: float, nu: float, h: float) -> np.ndarray:
    """
    Constrói a Matriz Constitutiva de Cisalhamento Transversal (Ds).
    Inclui o fator de correção de cisalhamento de Mindlin/Reissner.
    
    Args:
        E: Módulo de Elasticidade
        nu: Coeficiente de Poisson
        h: Espessura
        
    Returns:
        Ds: Array 2x2
    """
    # Módulo de cisalhamento G = E / [2*(1 + nu)]
    G = E / (2.0 * (1.0 + nu))
    
    # Fator de correção de cisalhamento para placas homogêneas (k = 5/6)
    k_shear = 5.0 / 6.0
    
    coef = G * h * k_shear
    Ds = np.array([
        [1.0, 0.0],
        [0.0, 1.0]
    ])
    return coef * Ds
