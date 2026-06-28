from mef.model.shell_model import ShellModel
from shared.results import ShellResults
from mef.mesh.generator import generate_mesh
from mef.mesh.converter import convert_mesh
from mef.analysis.linear_static import solve_linear_static
from mef.analysis.linear_buckling import solve_linear_buckling
from mef.analysis.nonlinear_static import solve_nonlinear_static
from mef.postprocess.vtk_export import export_vtk

def solve_shell(model: ShellModel) -> ShellResults:
    """
    Função principal que orquestra a solução determinística do modelo MEF.
    Esta é a única interface pública que deve ser chamada externamente 
    (por exemplo, pelo módulo de confiabilidade).
    
    O fluxo interno da função passará pelas etapas da análise:
    - Geração da malha
    - Avaliação das matrizes (forma, B, constitutiva, rigidez elementar)
    - Montagem global
    - Solução (Estática, Flambagem ou Não Linear)
    - Pós-processamento e exportação VTK
    """
    # Valida parâmetros de entrada do modelo
    model.validate()
    
    # 1. Geração da Malha (Etapa 3)
    # -----------------------------
    raw_mesh = generate_mesh(model)
    nodes, elements = convert_mesh(raw_mesh)
    
    # Injetamos os dados puros da malha no objeto model para uso nas próximas etapas
    model.mesh_data = {
        "nodes": nodes,
        "elements": elements
    }
    
    print(f"Malha '{model.geometry_type}' gerada com sucesso: {nodes.shape[0]} nós e {elements.shape[0]} elementos {model.element_type}.")
    
    # 1.5. Aplicação de Imperfeições Geométricas (Pré-análise)
    # --------------------------------------------------------
    if model.imperfection_params and model.imperfection_params.get("type") == "modal":
        from mef.model.imperfections import apply_geometric_imperfection
        amplitude = model.imperfection_params.get("amplitude", 1.0)
        print("\n[Pré-Análise] Resolvendo flambagem linear para obter modo de imperfeição...")
        
        # Guardar temporariamente o tipo de análise original e forçar flambagem
        original_analysis = model.analysis_type
        
        res_buckling = solve_linear_buckling(model)
        
        # Restaurar
        model.analysis_type = original_analysis
        
        # Aplicar imperfeição na malha
        apply_geometric_imperfection(model, res_buckling, amplitude)
    
    # 2. Despachante da Análise (Etapa 12+)
    # -------------------------------------
    if model.analysis_type == "linear_static":
        results = solve_linear_static(model)
        
        # Etapa 13: Exportação VTK
        if results.displacements is not None:
            point_data = {
                "Deslocamentos": results.displacements,
                "Rotacoes": results.rotations
            }
            vtk_name = f"resultados_{model.geometry_type}_estatica.vtu"
            export_vtk(vtk_name, nodes, elements, point_data)
            results.vtk_file = vtk_name
            
    elif model.analysis_type == "linear_buckling":
        results = solve_linear_buckling(model)
        
        # Etapa 13: Exportação VTK do Modo de Flambagem
        if results.displacements is not None:
            point_data = {
                "Modo_Flambagem": results.displacements,
                "Rotacoes": results.rotations
            }
            vtk_name = f"resultados_{model.geometry_type}_buckling.vtu"
            export_vtk(vtk_name, nodes, elements, point_data)
            results.vtk_file = vtk_name
            
    elif model.analysis_type == "nonlinear_static":
        results = solve_nonlinear_static(model, num_steps=10, max_iter=20, tol=1e-3)
        
        if results.displacements is not None:
            point_data = {
                "Deslocamentos_Finais": results.displacements,
                "Rotacoes_Finais": results.rotations
            }
            vtk_name = f"resultados_{model.geometry_type}_nlgeom.vtu"
            export_vtk(vtk_name, nodes, elements, point_data)
            results.vtk_file = vtk_name
            
    else:
        print(f"Análise {model.analysis_type} ainda não implementada.")
        results = ShellResults()
        
    return results

if __name__ == "__main__":
    # Exemplo de uso simples (determinístico) do Solver MEF isolado
    modelo_exemplo = ShellModel(
        geometry_type="cylinder",
        geometry_params={"radius": 100.0, "length": 500.0, "thickness": 2.0},
        material_params={"E": 200e3, "nu": 0.3},
        element_type="QUAD4",
        mesh_params={"num_circumferential": 20, "num_longitudinal": 40},
        analysis_type="linear_static"
    )
    
    resultados = solve_shell(modelo_exemplo)
    print("Análise (Mock) concluída.")
    print(resultados)
