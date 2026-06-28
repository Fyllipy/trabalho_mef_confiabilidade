import numpy as np
from typing import Dict, Any, Tuple

def convert_mesh(raw_data: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Converte os dados brutos extraídos do Gmsh para arrays NumPy estruturados,
    que serão utilizados na montagem das matrizes do Método dos Elementos Finitos.
    
    Args:
        raw_data: Dicionário retornado pela função generate_mesh do generator.py.
        
    Returns:
        nodes: np.ndarray (N, 3) com as coordenadas [X, Y, Z] de cada nó.
               O índice da linha corresponderá ao "ID interno" do nó, que começa em 0.
        elements: np.ndarray (E, num_nos_por_elemento) contendo as conectividades.
                  Cada linha possui os IDs internos dos nós que formam o elemento.
    """
    node_tags = raw_data["node_tags"]
    node_coords = raw_data["node_coords"]
    
    # Gmsh retorna as coordenadas como um array flat [x1, y1, z1, x2, y2, z2, ...]
    coords = np.array(node_coords).reshape(-1, 3)
    
    # Cria um mapeamento de Tag (id do Gmsh) para Índice interno (0, 1, 2, ...)
    # Isto garante que a matriz global não tenha buracos, já que tags do Gmsh
    # podem não ser perfeitamente contínuas e começar do 1.
    tag_to_index = {tag: idx for idx, tag in enumerate(node_tags)}
    
    # Extrair os elementos
    element_types = raw_data["element_types"]
    element_node_tags = raw_data["element_node_tags"]
    
    # O Gmsh codifica tipos de elementos por números inteiros:
    # 3 = QUAD4 (4 nós)
    # 16 = QUAD8 (8 nós serendipity incomplete)
    target_type = 3 if raw_data["element_type"] == "QUAD4" else 16
    
    elements = []
    
    # O gmsh retorna listas de listas quando há múltiplos tipos de entidades (ex: triângulos e quads misturados)
    for e_type, node_tags_for_type in zip(element_types, element_node_tags):
        if e_type == target_type:
            # O array node_tags_for_type contém uma lista flat dos nós
            nodes_per_elem = 4 if target_type == 3 else 8
            
            # Formatar em (número_de_elementos, nós_por_elemento)
            elem_array = np.array(node_tags_for_type).reshape(-1, nodes_per_elem)
            
            # Converter as Tags do Gmsh para nossos Índices Internos
            for i in range(elem_array.shape[0]):
                mapped_nodes = [tag_to_index[tag] for tag in elem_array[i]]
                elements.append(mapped_nodes)
                
    elements = np.array(elements, dtype=int)
    
    # Em uma análise didática, é importante garantir que geramos a quantidade correta de nós
    if len(elements) == 0:
        raise ValueError(f"Nenhum elemento do tipo {raw_data['element_type']} gerado.")
    
    return coords, elements
