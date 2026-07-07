import meshio
import numpy as np
from typing import Dict, Any
from mef.model.shell_model import ShellModel
from shared.results import ShellResults
from mef.assembly.global_assembly import get_element_instance

def export_vtk(
    filename: str, 
    nodes: np.ndarray, 
    elements: np.ndarray, 
    point_data: Dict[str, np.ndarray] = None
):
    """
    Exporta a malha e os resultados nodais (como deslocamentos e tensões) 
    para o formato VTU/VTK usando a biblioteca meshio (legado/retrocompatibilidade).
    """
    num_nodes = elements.shape[1]
    element = get_element_instance(num_nodes)
    cells = [(element.vtk_cell_type, elements)]
    
    meshio.write_points_cells(
        filename,
        nodes,
        cells,
        point_data=point_data
    )

def export_results_vtk(filename_base: str, model: ShellModel, results: ShellResults):
    """
    Exporta os resultados de ShellResults para arquivos VTK/VTU.
    
    - Sempre exporta a malha contínua com resultados nodais extrapolados e com média
      em: filename_base + "_nodal.vtu" (POINT_DATA).
    - Se results_location == "gauss", exporta uma malha discreta de nuvem de pontos (point cloud)
      contendo os valores exatos de integração em: filename_base + "_gauss.vtu".
    """
    nodes = model.mesh_data["nodes"]
    elements = model.mesh_data["elements"]
    num_nodes_per_elem = elements.shape[1]
    element = get_element_instance(num_nodes_per_elem)
    
    # 1. Exportar Arquivo Nodal Principal
    nodal_filename = filename_base.replace(".vtu", "") + "_nodal.vtu"
    print(f"\n--- Exportando resultados nodais para: {nodal_filename} ---")
    
    point_data = {}
    if "nodal" in results.data:
        for key, val in results.data["nodal"].items():
            if val is not None and len(val) == len(nodes):
                point_data[key] = val
                
    cells = [(element.vtk_cell_type, elements)]
    meshio.write_points_cells(
        nodal_filename,
        nodes,
        cells,
        point_data=point_data
    )
    results.vtk_file = nodal_filename
    
    # 2. Se a localização for Gauss, exportar Nuvem de Pontos de Gauss Auxiliar
    if results.metadata.get("results_location") == "gauss" and "gauss" in results.data:
        gauss_filename = filename_base.replace(".vtu", "") + "_gauss.vtu"
        print(f"--- Exportando nuvem de pontos de Gauss para: {gauss_filename} ---")
        
        gps = element.get_membrane_bending_integration_points()
        num_gp = len(gps)
        num_elements = len(elements)
        
        gauss_nodes = np.zeros((num_elements * num_gp, 3))
        gauss_point_data = {}
        
        # Inicializar buffers
        for key, val in results.data["gauss"].items():
            num_components = val.shape[2] if len(val.shape) > 2 else 1
            gauss_point_data[key] = np.zeros((num_elements * num_gp, num_components))
            
        for e in range(num_elements):
            elem_nodes = elements[e]
            elem_coords = nodes[elem_nodes]
            for g_idx, gp in enumerate(gps):
                xi, eta, _ = gp
                N = element.shape_functions(xi, eta)
                idx = e * num_gp + g_idx
                
                # Coordenadas físicas do ponto de Gauss no espaço 3D
                gauss_nodes[idx, :] = N @ elem_coords
                
                # Injetar os valores das grandezas
                for key, val in results.data["gauss"].items():
                    if len(val.shape) > 2:
                        gauss_point_data[key][idx, :] = val[e, g_idx, :]
                      
                    else:
                        gauss_point_data[key][idx, 0] = val[e, g_idx]
                        
        # Formatar tensores escalares de 1 coluna para vetores 1D (requisito do meshio)
        for key in list(gauss_point_data.keys()):
            if gauss_point_data[key].shape[1] == 1:
                gauss_point_data[key] = gauss_point_data[key].squeeze(axis=1)
                
        # Células tipo "vertex" representam pontos soltos na nuvem de visualização
        vertex_cells = [("vertex", np.arange(len(gauss_nodes)).reshape(-1, 1))]
        
        meshio.write_points_cells(
            gauss_filename,
            gauss_nodes,
            vertex_cells,
            point_data=gauss_point_data
        )
        print("Exportação da nuvem de pontos concluída com sucesso.")
