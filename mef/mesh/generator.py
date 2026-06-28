import gmsh
import numpy as np
from typing import Tuple, Dict, Any
from mef.model.shell_model import ShellModel

def _create_cylinder(radius: float, length: float, num_circ: int, num_long: int):
    """
    Cria a geometria de uma casca cilíndrica e configura a malha transfinita (estruturada).
    A casca é dividida em 4 quadrantes para garantir uma malha estruturada perfeita.
    """
    # Centro e pontos do círculo na base (z=0)
    p0 = gmsh.model.occ.addPoint(0, 0, 0)
    p1 = gmsh.model.occ.addPoint(radius, 0, 0)
    p2 = gmsh.model.occ.addPoint(0, radius, 0)
    p3 = gmsh.model.occ.addPoint(-radius, 0, 0)
    p4 = gmsh.model.occ.addPoint(0, -radius, 0)
    
    # 4 arcos de círculo formando a base
    c1 = gmsh.model.occ.addCircleArc(p1, p0, p2)
    c2 = gmsh.model.occ.addCircleArc(p2, p0, p3)
    c3 = gmsh.model.occ.addCircleArc(p3, p0, p4)
    c4 = gmsh.model.occ.addCircleArc(p4, p0, p1)
    
    # Extrusão ao longo do eixo Z (comprimento)
    # A extrusão de uma curva (dim=1) gera uma superfície (dim=2)
    # Passamos numElements=[num_long] para garantir divisão estruturada ao longo da altura
    ext1 = gmsh.model.occ.extrude([(1, c1)], 0, 0, length, numElements=[num_long])
    ext2 = gmsh.model.occ.extrude([(1, c2)], 0, 0, length, numElements=[num_long])
    ext3 = gmsh.model.occ.extrude([(1, c3)], 0, 0, length, numElements=[num_long])
    ext4 = gmsh.model.occ.extrude([(1, c4)], 0, 0, length, numElements=[num_long])
    
    # Fundamental para fundir as arestas coincidentes (costuras do cilindro)
    gmsh.model.occ.removeAllDuplicates()
    gmsh.model.occ.synchronize()
    
    # Configurar divisões circunferenciais em cada quarto de arco
    # (num_circ é o total, então dividimos por 4 e somamos 1 para virar número de nós na curva)
    nodes_per_arc = max(2, (num_circ // 4) + 1)
    for c in [c1, c2, c3, c4]:
        gmsh.model.mesh.setTransfiniteCurve(c, nodes_per_arc)
        
    # Identifica as curvas no topo geradas pela extrusão para aplicar o mesmo transfinite
    # (Não é estritamente necessário se o recombine já cuidar disso, mas garante simetria)
    
    # Transformar todas as superfícies em malhas estruturadas (Transfinite Surface)
    surfaces = gmsh.model.getEntities(2)
    for s in surfaces:
        gmsh.model.mesh.setTransfiniteSurface(s[1])
        gmsh.model.mesh.setRecombine(2, s[1]) # Força a recombinação para criar QUADs em vez de TRI

def _create_plate(width: float, length: float, num_w: int, num_l: int):
    """
    Cria a geometria de uma placa plana no plano X-Y e configura a malha transfinita.
    """
    # Cria o retângulo
    rect = gmsh.model.occ.addRectangle(0, 0, 0, width, length)
    gmsh.model.occ.synchronize()
    
    # Identifica as curvas da placa para divisão estruturada
    curves = gmsh.model.getEntities(1)
    for c in curves:
        c_tag = c[1]
        # Simplificação: em um retângulo originado no zero, linhas paralelas ao eixo X
        # costumam ter índices previsíveis. 
        # O Gmsh aplica as divisões transfinite nas curvas.
        # Definiremos um tamanho de elemento aproximado em vez de caçar as curvas específicas
        pass 
    
    # Aplica recombinação
    gmsh.option.setNumber("Mesh.RecombineAll", 1)
    # Define o tamanho médio global caso o transfinite falhe
    element_size = min(width/num_w, length/num_l)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", element_size)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", element_size)
    
    surfaces = gmsh.model.getEntities(2)
    for s in surfaces:
        gmsh.model.mesh.setTransfiniteSurface(s[1])
        gmsh.model.mesh.setRecombine(2, s[1])

def generate_mesh(model: ShellModel) -> Dict[str, Any]:
    """
    Gera a malha invocando o Gmsh de acordo com os parâmetros do modelo.
    Retorna os dados brutos que serão processados pelo converter.
    """
    if not gmsh.isInitialized():
        gmsh.initialize()
    
    gmsh.clear()
    gmsh.option.setNumber("General.Terminal", 0) # Silencia o terminal do Gmsh
    
    if model.element_type == "QUAD4":
        gmsh.option.setNumber("Mesh.ElementOrder", 1)
    elif model.element_type == "QUAD8":
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.option.setNumber("Mesh.SecondOrderIncomplete", 1) # Omitir nó central (QUAD8 em vez de QUAD9)
    else:
        raise ValueError(f"Tipo de elemento não suportado: {model.element_type}")

    if model.geometry_type == "cylinder":
        _create_cylinder(
            radius=model.geometry_params["radius"],
            length=model.geometry_params["length"],
            num_circ=model.mesh_params.get("num_circumferential", 20),
            num_long=model.mesh_params.get("num_longitudinal", 20)
        )
    elif model.geometry_type == "plate":
        _create_plate(
            width=model.geometry_params["width"],
            length=model.geometry_params["length"],
            num_w=model.mesh_params.get("num_width", 10),
            num_l=model.mesh_params.get("num_length", 10)
        )
    else:
        raise ValueError(f"Geometria não suportada: {model.geometry_type}")
    
    # Gera malha 2D (superfície)
    gmsh.model.mesh.generate(2)
    
    # Extrai os dados brutos da malha gerada
    nodeTags, nodeCoords, _ = gmsh.model.mesh.getNodes()
    elementTypes, elementTags, elementNodeTags = gmsh.model.mesh.getElements(dim=2)
    
    raw_data = {
        "node_tags": nodeTags,
        "node_coords": nodeCoords,
        "element_types": elementTypes,
        "element_tags": elementTags,
        "element_node_tags": elementNodeTags,
        "element_type": model.element_type
    }
    
    # Opcional: Para finalidades de debug, o gmsh pode ser finalizado 
    # apenas ao final do programa, não encerramos aqui para permitir 
    # sucessivas chamadas num laço de confiabilidade.
    
    return raw_data
