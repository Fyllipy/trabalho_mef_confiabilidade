import sys
import os

try:
    import odbAccess
    odb = odbAccess.openOdb(path='NonlinearCylinder.odb')
    step = odb.steps['Step-1']
    frame = step.frames[-1]
    u_field = frame.fieldOutputs['U']
    
    inst_name = odb.rootAssembly.instances.keys()[0]
    
    L = 1000.0
    top_node_labels = []
    for node in odb.rootAssembly.instances[inst_name].nodes:
        if abs(node.coordinates[2] - L) < 1e-4:
            top_node_labels.append(node.label)
            
    sum_u2 = 0.0
    for val in u_field.values:
        if val.nodeLabel in top_node_labels and val.instance.name == inst_name:
            sum_u2 += val.data[1]
            
    avg_u2 = sum_u2 / len(top_node_labels) if len(top_node_labels) > 0 else 0.0
    
    out_path = r'C:\Users\João\Desktop\Trabalho final\validation\abaqus\abaqus_nlgeom_result.txt'
    with open(out_path, 'w') as f:
        f.write(str(avg_u2))
        
    odb.close()
    print("SUCCESS: " + str(avg_u2))
except Exception as e:
    with open(r'C:\Users\João\Desktop\Trabalho final\validation\abaqus\abaqus_nlgeom_result.txt', 'w') as f:
        f.write("ERROR: " + str(e))
