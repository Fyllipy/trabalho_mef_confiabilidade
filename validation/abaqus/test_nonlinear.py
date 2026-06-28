import sys
import os
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from mef.model.shell_model import ShellModel
from mef.mesh.generator import generate_mesh
from mef.mesh.converter import convert_mesh
from main import solve_shell

def run_abaqus_nlgeom_validation():
    print("\n" + "="*50)
    print("INICIANDO VALIDAÇÃO ABAQUS: NONLINEAR STATIC (NLGEOM)")
    print("="*50)
    
    E = 200e3
    nu = 0.3
    radius = 100.0
    length = 1000.0
    h = 2.0
    P_lateral = 1e5 # Carga lateral ajustada para evitar inversão (detJ < 0)
    
    # 1. Configurar o Modelo
    model = ShellModel(
        geometry_type="cylinder",
        geometry_params={"radius": radius, "length": length, "thickness": h},
        material_params={"E": E, "nu": nu},
        element_type="QUAD8",
        mesh_params={"num_circumferential": 12, "num_longitudinal": 20},
        analysis_type="nonlinear_static",
    )
    
    # 2. Gerar malha
    raw_mesh = generate_mesh(model)
    nodes, elements = convert_mesh(raw_mesh)
    model.mesh_data = {"nodes": nodes, "elements": elements}
    
    # 3. Condições de contorno (Base engastada)
    fixed_nodes = np.where(np.abs(nodes[:, 2]) < 1e-6)[0].tolist()
    model.boundary_conditions = {"fixed_nodes": fixed_nodes}
    
    # 4. Carregamento Lateral Uniforme (Tração em Y)
    top_nodes = np.where(np.abs(nodes[:, 2] - length) < 1e-6)[0].tolist()
    force_per_node = P_lateral / len(top_nodes) if len(top_nodes) > 0 else 0
    nodal_loads = [(n, 1, force_per_node) for n in top_nodes] # GDL 1 = uY
    model.loads = {"nodal_loads": nodal_loads}
    
    # 5. Solver Não-Linear
    results = solve_shell(model)
    
    if results.displacements is None:
        print(">>> FALHA: Ocorreu um erro na análise não-linear.")
        return
        
    uy_top_mef = np.mean(results.displacements[top_nodes, 1])
    
    # Lendo referência do Abaqus
    abaqus_file = os.path.join(os.path.dirname(__file__), "abaqus_nlgeom_result.txt")
    
    is_mock = False
    if os.path.exists(abaqus_file):
        with open(abaqus_file, 'r') as f:
            uy_abaqus = float(f.read().strip())
    else:
        # Se não rodou Abaqus, usa teoria linear de Euler Bernoulli para mock 
        # (vai ter erro gigante porque a carga é enorme e a geometria muda muito)
        I = np.pi * radius**3 * h
        uy_abaqus = (P_lateral * length**3) / (3.0 * E * I)
        is_mock = True
    
    erro = abs((uy_top_mef - uy_abaqus) / uy_abaqus) * 100
    
    print("\n--- COMPARAÇÃO NLGEOM (GRANDES DESLOCAMENTOS) ---")
    if is_mock:
        print("[!] Arquivo 'abaqus_nlgeom_result.txt' não encontrado.")
        print("[!] Usando teoria linear 1D como mock (esperado Erro MUITO ALTO).")
        print("[!] Rode: abaqus cae noGUI=run_abaqus_nonlinear.py para o Abaqus NLGEOM oficial.")
        
    print(f"Deslocamento Y Abaqus (Referência): {uy_abaqus:.2f} mm")
    print(f"Deslocamento Y Solver MEF:          {uy_top_mef:.2f} mm")
    print(f"Erro relativo final:                  {erro:.2f} %")
    
    if erro < 20.0:
        print(">>> VALIDAÇÃO BEM SUCEDIDA! (A captura de grandes deslocamentos está correlacionada com a cinemática não-linear!)")
    else:
        print(">>> AVISO: Discrepância alta.")

if __name__ == "__main__":
    run_abaqus_nlgeom_validation()
