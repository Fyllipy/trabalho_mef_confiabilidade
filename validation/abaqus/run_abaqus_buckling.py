"""
Script Python para o Abaqus CAE.
Execução: abaqus cae noGUI=run_abaqus_buckling.py
Extrai o primeiro autovalor para "abaqus_buckling_result.txt".
"""

from abaqus import *
from abaqusConstants import *
import regionToolset
import mesh
import math

def create_and_run():
    R = 100.0
    L = 500.0
    h = 2.0
    E = 200e3
    nu = 0.3
    P_total = -1000.0 # Carga de referência
    
    Mdb()
    model = mdb.models['Model-1']
    
    s = model.ConstrainedSketch(name='__profile__', sheetSize=1000.0)
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
    
    # Step de Flambagem Linear (Buckling)
    model.BuckleStep(name='Step-1', previous='Initial', numEigen=1, vectors=3, maxIterations=50)
    
    edges = inst.edges
    bottom_edges = edges.getByBoundingBox(zMin=-0.1, zMax=0.1)
    bottom_region = a.Set(edges=bottom_edges, name='Bottom')
    model.EncastreBC(name='BC-1', createStepName='Initial', region=bottom_region)
    
    top_edges = edges.getByBoundingBox(zMin=L-0.1, zMax=L+0.1)
    top_region = a.Surface(side1Edges=top_edges, name='Top')
    
    q = P_total / (2.0 * math.pi * R)
    model.ShellEdgeLoad(name='Load-1', createStepName='Step-1', 
                        region=top_region, magnitude=q, 
                        distributionType=UNIFORM, field='')
    
    # Malha respeitando licença estudantil
    p.seedPart(size=30.0, deviationFactor=0.1, minSizeFactor=0.1)
    elemType = mesh.ElemType(elemCode=S4, elemLibrary=STANDARD)
    p.setElementType(regions=(faces,), elemTypes=(elemType,))
    p.generateMesh()
    
    job_name = 'BuckleCylinder'
    job = mdb.Job(name=job_name, model='Model-1')
    job.submit(consistencyChecking=OFF)
    job.waitForCompletion()
    
    # Extrair primeiro autovalor
    import odbAccess
    odb = odbAccess.openOdb(path=job_name + '.odb')
    step = odb.steps['Step-1']
    frame = step.frames[1] # Frame 0 é base state, Frame 1 é Mode 1
    
    # O valor do autovalor está armazenado na descrição do frame no Abaqus
    description = frame.description
    # ex: "Mode 1: EigenValue =  3.4567 "
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
