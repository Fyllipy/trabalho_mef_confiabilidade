"""
Script Python para o Abaqus CAE.
Execução: abaqus cae noGUI=run_abaqus_buckling.py
"""

from abaqus import *
from abaqusConstants import *
import regionToolset
import mesh
import math
import json
import os
import sys

def create_and_run():
    # 0. Carregar Configurações
    element_type = "QUAD4"
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
                element_type = settings.get("element_type", "QUAD4")
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
                                  idealization=NO_IDEALIZATION)
    
    faces = p.faces
    region = regionToolset.Region(faces=faces)
    p.SectionAssignment(region=region, sectionName='Section-1')
    
    # Montagem
    a = model.rootAssembly
    a.DatumCsysByDefault(CARTESIAN)
    inst = a.Instance(name='Cylinder-1', part=p, dependent=ON)
    
    # Step de Flambagem Linear
    model.BuckleStep(name='Step-1', previous='Initial', numEigen=1, vectors=3, maxIterations=50)
    
    # CCs
    edges = inst.edges
    bottom_edges = edges.getByBoundingBox(zMin=-0.1, zMax=0.1)
    bottom_region = a.Set(edges=bottom_edges, name='Bottom')
    model.EncastreBC(name='BC-1', createStepName='Initial', region=bottom_region)
    
    # Carga
    top_edges = edges.getByBoundingBox(zMin=L-0.1, zMax=L+0.1)
    top_region = a.Surface(side1Edges=top_edges, name='Top')
    q = P_total / (2.0 * math.pi * R)
    model.ShellEdgeLoad(name='Load-1', createStepName='Step-1', 
                        region=top_region, magnitude=q, 
                        distributionType=UNIFORM, field='')
    
    # Malha
    p.seedPart(size=30.0, deviationFactor=0.1, minSizeFactor=0.1)
    if element_type == "QUAD8":
        elemType = mesh.ElemType(elemCode=S8, elemLibrary=STANDARD)
    else:
        elemType = mesh.ElemType(elemCode=S4, elemLibrary=STANDARD)
        
    p.setElementType(regions=(faces,), elemTypes=(elemType,))
    p.generateMesh()
    
    # Job
    job_name = 'BuckleCylinder'
    job = mdb.Job(name=job_name, model='Model-1')
    job.submit(consistencyChecking=OFF)
    job.waitForCompletion()
    
    # Extrair Resultados
    import odbAccess
    odb = odbAccess.openOdb(path=job_name + '.odb')
    step = odb.steps['Step-1']
    frame = step.frames[1] 
    
    description = frame.description
    eigenvalue = None
    if "EigenValue =" in description:
        val_str = description.split("EigenValue =")[1].strip()
        eigenvalue = float(val_str)
        
    with open('abaqus_buckling_result.txt', 'w') as f:
        f.write(str(eigenvalue))
        
    odb.close()
    print("Concluido! Eigenvalue extraido: ", eigenvalue)

if __name__ == '__main__':
    create_and_run()
