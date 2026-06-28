import sys
import os
import numpy as np

# Adiciona o diretório raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from mef.model.shell_model import ShellModel
from mef.mesh.generator import generate_mesh
from mef.mesh.converter import convert_mesh
from mef.analysis.linear_static import solve_linear_static

def run_abaqus_static_general_validation():
    """
    Validação contra Abaqus (Etapa 15)
    Compara o deslocamento e tensões de um cilindro sob compressão pura
    com resultados de referência teóricos/obtidos previamente no Abaqus.
    """
    print("\n" + "="*50)
    print("INICIANDO VALIDAÇÃO ABAQUS: STATIC GENERAL")
    print("="*50)
    
    E = 200e3      # MPa
    nu = 0.3
    radius = 100.0 # R
    length = 500.0 # L
    h = 2.0        # espessura
    P_total = -1000.0 # Carga axial
    
    # 1. Configurar o Modelo
    model = ShellModel(
        geometry_type="cylinder",
        geometry_params={"radius": radius, "length": length, "thickness": h},
        material_params={"E": E, "nu": nu},
        element_type="QUAD4",
        mesh_params={"num_circumferential": 20, "num_longitudinal": 20},
        analysis_type="linear_static"
    )
    
    # 2. Gerar malha
    raw_mesh = generate_mesh(model)
    nodes, elements = convert_mesh(raw_mesh)
    model.mesh_data = {"nodes": nodes, "elements": elements}
    
    # 3. Condições de contorno (Base Z=0 engastada)
    fixed_nodes = np.where(np.abs(nodes[:, 2]) < 1e-6)[0].tolist()
    model.boundary_conditions = {"fixed_nodes": fixed_nodes}
    
    # 4. Carregamento (Topo Z=L comprimido uniformemente)
    top_nodes = np.where(np.abs(nodes[:, 2] - length) < 1e-6)[0].tolist()
    force_per_node = P_total / len(top_nodes) if len(top_nodes) > 0 else 0
    nodal_loads = [(n, 2, force_per_node) for n in top_nodes]
    model.loads = {"nodal_loads": nodal_loads}
    
    # 5. Solver Linear
    results = solve_linear_static(model)
    
    # Deslocamento Axial no topo obtido
    uz_top_mef = np.mean(results.displacements[top_nodes, 2])
    
    # Lendo a solução Abaqus de referência exportada pelo script (se existir)
    abaqus_file = os.path.join(os.path.dirname(__file__), "abaqus_static_result.txt")
    
    if os.path.exists(abaqus_file):
        with open(abaqus_file, 'r') as f:
            uz_abaqus = float(f.read().strip())
        is_mock = False
    else:
        # Aproximação analítica (viga 1D) para mock
        A = 2 * np.pi * radius * h
        uz_abaqus = (P_total * length) / (E * A)
        is_mock = True
    
    # Ajuste: Comparamos as magnitudes (rigidez absoluta) pois a extração do 
    # ShellEdgeLoad no Abaqus gerou um valor de compressão positivo dependendo da normal da aresta.
    erro = abs((abs(uz_top_mef) - abs(uz_abaqus)) / abs(uz_abaqus)) * 100
    
    print("\n--- COMPARAÇÃO ABAQUS (REFERÊNCIA) ---")
    if is_mock:
        print("[!] Arquivo 'abaqus_static_result.txt' não encontrado.")
        print("[!] Usando aproximação analítica de barra 1D como mock.")
        print("[!] Rode: abaqus cae noGUI=run_abaqus_static.py para gerar a resposta oficial.")
        
    print(f"Deslocamento Z Abaqus (Referência): {uz_abaqus:.6e} mm")
    print(f"Deslocamento Z Solver MEF:          {uz_top_mef:.6e} mm")
    print(f"Erro relativo:                        {erro:.2f} %")
    
    if erro < 5.0:
        print(">>> VALIDAÇÃO BEM SUCEDIDA! (Erro aceitável)")
    else:
        print(">>> AVISO: Discrepância alta com a referência.")

if __name__ == "__main__":
    run_abaqus_static_general_validation()
