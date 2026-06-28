import meshio
import numpy as np
from typing import Dict

def export_vtk(
    filename: str, 
    nodes: np.ndarray, 
    elements: np.ndarray, 
    point_data: Dict[str, np.ndarray] = None
):
    """
    Exporta a malha e os resultados nodais (como deslocamentos e tensões) 
    para o formato VTU/VTK usando a biblioteca meshio.
    Este formato é nativamente suportado pelo software ParaView para visualização.
    
    Args:
        filename: Caminho e nome do arquivo de saída (ex: 'output.vtu').
        nodes: (N, 3) Array com coordenadas dos nós.
        elements: (E, 4) Array de conectividade (elementos QUAD4).
        point_data: Dicionário contendo arrays de dados mapeados nos nós.
                    Ex: {"Deslocamentos": array(N, 3)}
    """
    from mef.assembly.global_assembly import get_element_instance
    print(f"\n--- Exportando resultados para {filename} ---")
    
    # Identificar o tipo do elemento via fábrica de elementos baseada no número de colunas (nós)
    num_nodes = elements.shape[1]
    element = get_element_instance(num_nodes)
    
    # Meshio utiliza a string (ex: 'quad', 'quad8') para designar o elemento
    cells = [(element.vtk_cell_type, elements)]
    
    meshio.write_points_cells(
        filename,
        nodes,
        cells,
        point_data=point_data
    )
    
    print("Exportação VTK concluída com sucesso.")
