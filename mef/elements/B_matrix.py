import numpy as np
from mef.elements.base_element import ShellElement

def compute_B_membrane(element: ShellElement, dN_dx_y: np.ndarray) -> np.ndarray:
    """
    Calcula a Matriz B de Membrana (Bm) que relaciona os deslocamentos 
    nodais locais com as deformações de membrana (e_x, e_y, gamma_xy).
    
    Args:
        element: Instância de ShellElement.
        dN_dx_y: Array (2, N) com as derivadas espaciais (Linha 0: dN/dx, Linha 1: dN/dy)
        
    Returns:
        Bm: Array (3, ndof)
    """
    num_nodes = element.num_nodes
    dof = element.dofs_per_node
    Bm = np.zeros((3, num_nodes * dof))
    
    for i in range(num_nodes):
        dN_dx = dN_dx_y[0, i]
        dN_dy = dN_dx_y[1, i]
        
        # O índice da coluna inicial para os GDLs do nó i (u_x, u_y, u_z, th_x, th_y, th_z)
        col = i * dof
        
        # e_x = du_x/dx
        Bm[0, col + 0] = dN_dx
        # e_y = du_y/dy
        Bm[1, col + 1] = dN_dy
        # gamma_xy = du_x/dy + du_y/dx
        Bm[2, col + 0] = dN_dy
        Bm[2, col + 1] = dN_dx
        
    return Bm

def compute_B_bending(element: ShellElement, dN_dx_y: np.ndarray) -> np.ndarray:
    """
    Calcula a Matriz B de Flexão (Bb) que relaciona as rotações nodais 
    com as curvaturas da casca (kappa_x, kappa_y, kappa_xy).
    Seguindo a convenção da regra da mão direita para as rotações (Bathe).
    
    Args:
        element: Instância de ShellElement.
        dN_dx_y: Array (2, N) com as derivadas espaciais (dN/dx, dN/dy)
        
    Returns:
        Bb: Array (3, ndof)
    """
    num_nodes = element.num_nodes
    dof = element.dofs_per_node
    Bb = np.zeros((3, num_nodes * dof))
    
    for i in range(num_nodes):
        dN_dx = dN_dx_y[0, i]
        dN_dy = dN_dx_y[1, i]
        
        col = i * dof
        
        # kappa_x = d(th_y)/dx
        Bb[0, col + 4] = dN_dx
        # kappa_y = -d(th_x)/dy
        Bb[1, col + 3] = -dN_dy
        # kappa_xy = d(th_y)/dy - d(th_x)/dx
        Bb[2, col + 3] = -dN_dx
        Bb[2, col + 4] = dN_dy
        
    return Bb

def compute_B_shear(element: ShellElement, dN_dx_y: np.ndarray, N: np.ndarray) -> np.ndarray:
    """
    Calcula a Matriz B de Cisalhamento (Bs) que relaciona os deslocamentos 
    transversais e rotações com as deformações de cisalhamento (gamma_xz, gamma_yz).
    
    Args:
        element: Instância de ShellElement.
        dN_dx_y: Array (2, N)
        N: Array (N,) com valores das funções de forma.
        
    Returns:
        Bs: Array (2, ndof)
    """
    num_nodes = element.num_nodes
    dof = element.dofs_per_node
    Bs = np.zeros((2, num_nodes * dof))
    
    for i in range(num_nodes):
        dN_dx = dN_dx_y[0, i]
        dN_dy = dN_dx_y[1, i]
        Ni = N[i]
        
        col = i * dof
        
        # gamma_xz = du_z/dx + th_y
        Bs[0, col + 2] = dN_dx
        Bs[0, col + 4] = Ni
        
        # gamma_yz = du_z/dy - th_x
        Bs[1, col + 2] = dN_dy
        Bs[1, col + 3] = -Ni
        
    return Bs
