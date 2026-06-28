import numpy as np

from mef.elements.base_element import ShellElement
from mef.formulation.jacobian import compute_jacobian
from mef.elements.B_matrix import compute_B_membrane, compute_B_bending, compute_B_shear
from mef.materials.constitutive import compute_membrane_matrix, compute_bending_matrix, compute_shear_matrix

def compute_element_stiffness_local(element: ShellElement, local_coords: np.ndarray, E: float, nu: float, h: float) -> np.ndarray:
    """
    Calcula a matriz de rigidez local de um elemento de casca.
    A formulação desacopla explicitamente a contribuição da membrana, flexão e cisalhamento.
    As regras de integração dependem do tipo de elemento para evitar shear locking.
    
    Args:
        element: Instância de ShellElement (ex: Quad4, Quad8).
        local_coords: (N, 2) coordenadas (x, y) dos N nós no plano 2D local do elemento.
        E: Módulo de elasticidade.
        nu: Coeficiente de Poisson.
        h: Espessura da casca.
        
    Returns:
        Ke_local: Array (ndof, ndof) contendo a rigidez no sistema local de coordenadas.
    """
    ndof = element.num_nodes * element.dofs_per_node
    Ke = np.zeros((ndof, ndof))

    
    # 1. Obter matrizes constitutivas
    Dm = compute_membrane_matrix(E, nu, h)
    Db = compute_bending_matrix(E, nu, h)
    Ds = compute_shear_matrix(E, nu, h)
    
    # 2. Integração Plena para Membrana e Flexão
    for xi, eta, w in element.get_membrane_bending_integration_points():
        # Avaliar derivadas das funções de forma
        dN_dxi_eta = element.shape_function_derivatives(xi, eta)
        
        # Calcular Jacobiano e derivadas cartesianas
        J, detJ, dN_dx_y = compute_jacobian(dN_dxi_eta, local_coords)
        
        # Obter matrizes B
        Bm = compute_B_membrane(element, dN_dx_y)
        Bb = compute_B_bending(element, dN_dx_y)
        
        # Elemento de área diferencial
        dA = detJ * w
        
        # Contribuições
        Ke += Bm.T @ Dm @ Bm * dA
        Ke += Bb.T @ Db @ Bb * dA
        
    # 3. Integração Reduzida para Cisalhamento Transversal
    for xi, eta, w in element.get_shear_integration_points():
        N = element.shape_functions(xi, eta)
        dN_dxi_eta = element.shape_function_derivatives(xi, eta)
        
        J, detJ, dN_dx_y = compute_jacobian(dN_dxi_eta, local_coords)
        
        Bs = compute_B_shear(element, dN_dx_y, N)
        
        dA = detJ * w
        
        # Contribuição (previne shear locking)
        Ke += Bs.T @ Ds @ Bs * dA
        
    # 4. Tratamento do Grau de Liberdade 'Drilling' (Rotação em torno do eixo z local)
    # Em uma casca plana pura, a rigidez de membrana e flexão não oferece resistência à 
    # rotação no próprio plano (drilling DOF), deixando colunas nulas na matriz Ke_local.
    # Adiciona-se uma rigidez fictícia pequena para evitar matrizes globais singulares.
    
    # Estimativa de rigidez fictícia baseada no traço da matriz para garantir escalonamento
    trace_Ke = np.sum(np.diag(Ke))
    alpha = 1e-4 # Fator empírico pequeno
    k_fictitious = alpha * trace_Ke / float(ndof)
    
    for i in range(element.num_nodes):
        idx = i * element.dofs_per_node + 5 # O 6º grau de liberdade (índice 5) é o theta_z local
        Ke[idx, idx] = k_fictitious
        
    return Ke
