"""
Script Python para o Abaqus CAE.
Instruções de execução:
Abra o Abaqus Command (Terminal do Abaqus) e navegue até este diretório.
Execute o comando:
abaqus cae noGUI=run_abaqus_static.py

Ele irá criar o modelo, rodar a análise Static General e extrair o resultado
de deslocamento Z para o arquivo "abaqus_static_result.txt".
"""

from abaqus import *
from abaqusConstants import *
import regionToolset
import mesh
import math

def create_and_run():
    # Parâmetros
    R = 100.0
    L = 500.0
    h = 2.0
    E = 200e3
    nu = 0.3
    P_total = -1000.0
    
    # Criar Modelo
    Mdb()
    model = mdb.models['Model-1']
    
    # Criar Geometria (Casca cilíndrica)
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
    
    # Atribuir seção
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
    
    # Condição de contorno (Base engastada)
    edges = inst.edges
    bottom_edges = edges.getByBoundingBox(zMin=-0.1, zMax=0.1)
    bottom_region = a.Set(edges=bottom_edges, name='Bottom')
    model.EncastreBC(name='BC-1', createStepName='Initial', region=bottom_region, localCsys=None)
    
    # Carregamento (Compressão na aresta do topo)
    top_edges = edges.getByBoundingBox(zMin=L-0.1, zMax=L+0.1)
    top_region = a.Surface(side1Edges=top_edges, name='Top')
    
    # q = Força por unidade de comprimento (Força total / perímetro)
    q = P_total / (2.0 * math.pi * R)
    model.ShellEdgeLoad(name='Load-1', createStepName='Step-1', 
                        region=top_region, magnitude=q, 
                        distributionType=UNIFORM, field='', localCsys=None)
    
    # Malha mais grossa para respeitar o limite de 1000 nós da Learning Edition
    p.seedPart(size=30.0, deviationFactor=0.1, minSizeFactor=0.1)
    # Elemento S4 (4 nós, full integration como o nosso)
    elemType = mesh.ElemType(elemCode=S4, elemLibrary=STANDARD)
    p.setElementType(regions=(faces,), elemTypes=(elemType,))
    p.generateMesh()
    
    # Job
    job_name = 'StaticCylinder'
    job = mdb.Job(name=job_name, model='Model-1', description='Teste Static General')
    job.submit(consistencyChecking=OFF)
    job.waitForCompletion()
    
    # Extrair Resultados (Deslocamento Z no topo)
    import odbAccess
    odb = odbAccess.openOdb(path=job_name + '.odb')
    step = odb.steps['Step-1']
    frame = step.frames[-1]
    u_field = frame.fieldOutputs['U']
    
    # Encontrar os nós que estão na base superior (Z = L)
    top_node_labels = []
    for node in odb.rootAssembly.instances['CYLINDER-1'].nodes:
        if abs(node.coordinates[2] - L) < 1e-4:
            top_node_labels.append(node.label)
            
    # Calcular o deslocamento médio em Z
    sum_u3 = 0.0
    for val in u_field.values:
        if val.nodeLabel in top_node_labels and val.instance.name == 'CYLINDER-1':
            sum_u3 += val.data[2]
            
    avg_u3 = sum_u3 / len(top_node_labels) if len(top_node_labels) > 0 else 0.0
    
    # Escrever resultado no arquivo
    with open('abaqus_static_result.txt', 'w') as f:
        f.write(str(avg_u3))
        
    odb.close()
    print("Concluido! Deslocamento extraido: ", avg_u3)

if __name__ == '__main__':
    create_and_run()
