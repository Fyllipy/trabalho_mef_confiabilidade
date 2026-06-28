"""
Script Python para o Abaqus CAE.
Execução: abaqus cae noGUI=run_abaqus_nonlinear.py
Extrai a curva P-delta do deslocamento lateral de um cilindro em balanço
com NLGEOM ativado para validação de grandes deflexões.
"""

from abaqus import *
from abaqusConstants import *
import regionToolset
import mesh

def create_and_run():
    R = 100.0
    L = 1000.0
    h = 2.0
    E = 200e3
    nu = 0.3
    P_lateral = 1e5 # Carga lateral coerente (reduzida para evitar crash numérico do solver Abaqus)
    
    Mdb()
    model = mdb.models['Model-1']
    
    s = model.ConstrainedSketch(name='__profile__', sheetSize=2000.0)
    s.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(R, 0.0))
    p = model.Part(name='Cylinder', dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.BaseShellExtrude(sketch=s, depth=L)
    del model.sketches['__profile__']
    
    mat = model.Material(name='Steel')
    mat.Elastic(table=((E, nu), ))
    model.HomogeneousShellSection(name='Section-1', preIntegrate=OFF, 
                                  material='Steel', thicknessType=UNIFORM, 
                                  thickness=h, thicknessField='', 
                                  idealization=NO_IDEALIZATION)
    
    faces = p.faces
    region = regionToolset.Region(faces=faces)
    p.SectionAssignment(region=region, sectionName='Section-1')
    
    a = model.rootAssembly
    a.DatumCsysByDefault(CARTESIAN)
    inst = a.Instance(name='Cylinder-1', part=p, dependent=ON)
    
    # Step NLGEOM=ON com 10 incrementos fixos (para ser igual ao MEF)
    model.StaticStep(name='Step-1', previous='Initial', nlgeom=ON, 
                     initialInc=0.1, minInc=0.1, maxInc=0.1)
    
    edges = inst.edges
    bottom_edges = edges.getByBoundingBox(zMin=-0.1, zMax=0.1)
    bottom_region = a.Set(edges=bottom_edges, name='Bottom')
    model.EncastreBC(name='BC-1', createStepName='Initial', region=bottom_region)
    
    # Aplicar força concentrada no nó do topo em Y
    # Para simplificar, aplicamos na aresta como tração em Y
    top_edges = edges.getByBoundingBox(zMin=L-0.1, zMax=L+0.1)
    top_region = a.Surface(side1Edges=top_edges, name='Top')
    
    # ShellEdgeLoad usa Força por Unidade de Comprimento. 
    # Carga Total = P_lateral, Comprimento = 2 * pi * R
    import math
    p_lin = P_lateral / (2.0 * math.pi * R)
    
    model.ShellEdgeLoad(name='Load-1', createStepName='Step-1', 
                        region=top_region, magnitude=p_lin, 
                        directionVector=((0.0, 0.0, 0.0), (0.0, 1.0, 0.0)), 
                        distributionType=UNIFORM, field='', localCsys=None, 
                        traction=GENERAL)
    
    # Seed para ~12 elementos circunferenciais e 20 longitudinais (mesmo do MEF)
    p.seedPart(size=52.3, deviationFactor=0.1, minSizeFactor=0.1)
    elemType = mesh.ElemType(elemCode=S4, elemLibrary=STANDARD)
    p.setElementType(regions=(faces,), elemTypes=(elemType,))
    p.generateMesh()
    
    job_name = 'NonlinearCylinder'
    job = mdb.Job(name=job_name, model='Model-1')
    job.submit(consistencyChecking=OFF)
    job.waitForCompletion()
    
    # Extrair U2 no final do step
    import odbAccess
    odb = odbAccess.openOdb(path=job_name + '.odb')
    step = odb.steps['Step-1']
    
    if len(step.frames) == 0:
        print("Erro: O Abaqus não conseguiu convergir (0 frames no Step-1). O job abortou precocemente.")
        odb.close()
        return
        
    frame = step.frames[-1] 
    u_field = frame.fieldOutputs['U']
    
    top_node_labels = []
    
    inst_name = odb.rootAssembly.instances.keys()[0]
    
    for node in odb.rootAssembly.instances[inst_name].nodes:
        if abs(node.coordinates[2] - L) < 1e-4:
            top_node_labels.append(node.label)
            
    sum_u2 = 0.0
    for val in u_field.values:
        if val.nodeLabel in top_node_labels and val.instance.name == inst_name:
            sum_u2 += val.data[1]
            
    avg_u2 = sum_u2 / len(top_node_labels) if len(top_node_labels) > 0 else 0.0
    
    import os
    
    out_path = r'C:\Users\João\Desktop\Trabalho final\validation\abaqus\abaqus_nlgeom_result.txt'
    
    with open(out_path, 'w') as f:
        f.write(str(avg_u2))
        
    odb.close()
    print("Concluido! Deslocamento Y maximo extraido: ", avg_u2)
    print("Arquivo gravado em: ", out_path)

if __name__ == '__main__':
    create_and_run()
