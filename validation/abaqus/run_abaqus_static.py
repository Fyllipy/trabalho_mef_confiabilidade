"""
Script Python para o Abaqus CAE.
Execução: abaqus cae noGUI=run_abaqus_static.py
"""

from abaqus import *
from abaqusConstants import *
import regionToolset
import mesh
import math
import json
import os
import sys

def get_element_shape_functions(elem_type, xi, eta):
    if elem_type == "S4":
        N1 = 0.25 * (1.0 - xi) * (1.0 - eta)
        N2 = 0.25 * (1.0 + xi) * (1.0 - eta)
        N3 = 0.25 * (1.0 + xi) * (1.0 + eta)
        N4 = 0.25 * (1.0 - xi) * (1.0 + eta)
        return [N1, N2, N3, N4]
    elif elem_type == "S8":
        N = [0.0] * 8
        N[0] = -0.25 * (1.0 - xi) * (1.0 - eta) * (1.0 + xi + eta)
        N[1] = -0.25 * (1.0 + xi) * (1.0 - eta) * (1.0 - xi + eta)
        N[2] = -0.25 * (1.0 + xi) * (1.0 + eta) * (1.0 - xi - eta)
        N[3] = -0.25 * (1.0 - xi) * (1.0 + eta) * (1.0 + xi - eta)
        N[4] = 0.5 * (1.0 - xi**2) * (1.0 - eta)
        N[5] = 0.5 * (1.0 + xi) * (1.0 - eta**2)
        N[6] = 0.5 * (1.0 - xi**2) * (1.0 + eta)
        N[7] = 0.5 * (1.0 - xi) * (1.0 - eta**2)
        return N
    return []

def get_gp_coords(elem_type):
    if elem_type == "S4":
        p = 1.0 / math.sqrt(3.0)
        return [(-p, -p), (p, -p), (p, p), (-p, p)]
    elif elem_type == "S8":
        p = math.sqrt(3.0 / 5.0)
        pts_1d = [-p, 0.0, p]
        gps = []
        for i in range(3):
            for j in range(3):
                gps.append((pts_1d[i], pts_1d[j]))
        return gps
    return []

def create_and_run():
    # 0. Carregar Configurações
    element_type = "S4"
    results_location = "nodal"
    
    settings_file = 'abaqus_settings.json'
    if not os.path.exists(settings_file):
        try:
            script_dir = os.path.dirname(os.path.abspath(sys.argv[-1]))
            settings_file = os.path.join(script_dir, 'abaqus_settings.json')
        except:
            pass
            
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                element_type = settings.get("element_type", "S4")
                results_location = settings.get("results_location", "nodal")
        except:
            pass
            
    print("Abaqus rodando com:")
    print("  element_type: " + element_type)
    print("  results_location: " + results_location)

    # Parâmetros Físicos
    R = 100.0
    L = 500.0
    h = 2.0
    E = 200e3
    nu = 0.3
    P_total = -1000.0
    
    # Criar Modelo
    Mdb()
    model = mdb.models['Model-1']
    
    # Criar Geometria
    s = model.ConstrainedSketch(name='__profile__', sheetSize=1000.0)
    s.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(R, 0.0))
    p = model.Part(name='Cylinder', dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.BaseShellExtrude(sketch=s, depth=L)
    del model.sketches['__profile__']
    
    # Criar Material e Seção
    mat = model.Material(name='Steel')
    mat.Elastic(table=((E, nu), ))
    model.HomogeneousShellSection(name='Section-1', preIntegrate=OFF, 
                                  material='Steel', thicknessType=UNIFORM, 
                                  thickness=h, thicknessField='', 
                                  idealization=NO_IDEALIZATION, 
                                  poissonDefinition=DEFAULT, 
                                  thicknessModulus=None, temperature=GRADIENT, 
                                  useDensity=OFF, integrationRule=SIMPSON, 
                                  numIntPts=5)
    
    faces = p.faces
    region = regionToolset.Region(faces=faces)
    p.SectionAssignment(region=region, sectionName='Section-1', offset=0.0, 
                        offsetType=MIDDLE_SURFACE, offsetField='', 
                        thicknessAssignment=FROM_SECTION)
    
    # Montagem
    a = model.rootAssembly
    a.DatumCsysByDefault(CARTESIAN)
    inst = a.Instance(name='Cylinder-1', part=p, dependent=ON)
    
    # Criar Step (Análise Estática Linear)
    model.StaticStep(name='Step-1', previous='Initial', nlgeom=OFF)
    
    # CCs
    edges = inst.edges
    bottom_edges = edges.getByBoundingBox(zMin=-0.1, zMax=0.1)
    bottom_region = a.Set(edges=bottom_edges, name='Bottom')
    model.EncastreBC(name='BC-1', createStepName='Initial', region=bottom_region, localCsys=None)
    
    # Carga
    top_edges = edges.getByBoundingBox(zMin=L-0.1, zMax=L+0.1)
    top_region = a.Surface(side1Edges=top_edges, name='Top')
    q = P_total / (2.0 * math.pi * R)
    model.ShellEdgeLoad(name='Load-1', createStepName='Step-1', 
                        region=top_region, magnitude=q, 
                        distributionType=UNIFORM, field='', localCsys=None)
    
    # Malha
    p.seedPart(size=30.0, deviationFactor=0.1, minSizeFactor=0.1)
    if element_type == "S8":
        elemType = mesh.ElemType(elemCode=S8, elemLibrary=STANDARD)
    else:
        elemType = mesh.ElemType(elemCode=S4, elemLibrary=STANDARD)
        
    p.setElementType(regions=(faces,), elemTypes=(elemType,))
    p.generateMesh()
    
    # Job
    job_name = 'StaticCylinder'
    job = mdb.Job(name=job_name, model='Model-1', description='Teste Static General')
    job.submit(consistencyChecking=OFF)
    job.waitForCompletion()
    
    # Extrair Resultados
    import odbAccess
    odb = odbAccess.openOdb(path=job_name + '.odb')
    step = odb.steps['Step-1']
    frame = step.frames[-1]
    u_field = frame.fieldOutputs['U']
    
    # Encontrar nós na base superior (Z = L)
    top_node_labels = []
    for node in odb.rootAssembly.instances['CYLINDER-1'].nodes:
        if abs(node.coordinates[2] - L) < 1e-4:
            top_node_labels.append(node.label)
            
    # Mapear deslocamentos nodais
    u_dict = {}
    for val in u_field.values:
        if val.instance.name == 'CYLINDER-1':
            u_dict[val.nodeLabel] = val.data
            
    # Mapear coordenadas nodais
    nodes_dict = {}
    for node in odb.rootAssembly.instances['CYLINDER-1'].nodes:
        nodes_dict[node.label] = node.coordinates
        
    if results_location == "gauss":
        gp_coords = get_gp_coords(element_type)
        top_u3_list = []
        
        for elem in odb.rootAssembly.instances['CYLINDER-1'].elements:
            elem_nodes = elem.connectivity
            has_top_node = False
            for nl in elem_nodes:
                if nl in top_node_labels:
                    has_top_node = True
                    break
            
            if has_top_node:
                for gp in gp_coords:
                    xi, eta = gp
                    N = get_element_shape_functions(element_type, xi, eta)
                    
                    z_gp = 0.0
                    u3_gp = 0.0
                    for idx, nl in enumerate(elem_nodes):
                        z_gp += N[idx] * nodes_dict[nl][2]
                        if nl in u_dict:
                            u3_gp += N[idx] * u_dict[nl][2]
                            
                    if abs(z_gp - L) < 5.0:
                        top_u3_list.append(u3_gp)
                        
        avg_u3 = sum(top_u3_list) / len(top_u3_list) if len(top_u3_list) > 0 else 0.0
    else:
        # Nodal
        sum_u3 = 0.0
        count = 0
        for label in top_node_labels:
            if label in u_dict:
                sum_u3 += u_dict[label][2]
                count += 1
        avg_u3 = sum_u3 / count if count > 0 else 0.0
        
    with open('abaqus_static_result.txt', 'w') as f:
        f.write(str(avg_u3))
        
    odb.close()
    print("Concluido! Deslocamento extraido: ", avg_u3)

if __name__ == '__main__':
    create_and_run()
