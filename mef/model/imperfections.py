import numpy as np
from mef.model.shell_model import ShellModel
from shared.results import ShellResults

def apply_geometric_imperfection(model: ShellModel, buckling_results: ShellResults, amplitude: float):
    """
    Aplica uma imperfeição geométrica à malha original do modelo.
    Este método é fundamental para análises não-lineares de estabilidade,
    pois induz a estrutura a seguir o caminho de pós-flambagem esperado.
    
    A imperfeição é introduzida perturbando as coordenadas nodais
    pela forma do modo crítico de flambagem escalonado por uma amplitude.
    
    Args:
        model: Objeto do modelo contendo a malha.
        buckling_results: Resultados da análise de eigenbuckling (contendo raw_dofs).
        amplitude: Escala máxima da imperfeição (ex: espessura / 10).
    """
    print(f"\n--- Aplicando Imperfeição Geométrica ---")
    print(f"Amplitude máxima alvo: {amplitude:.6f}")
    
    phi = buckling_results.raw_dofs
    if phi is None:
        raise ValueError("O modo de flambagem (raw_dofs) não está disponível.")
        
    nodes = model.mesh_data["nodes"]
    num_nodes = len(nodes)
    
    # Extrai apenas as componentes de translação (U_X, U_Y, U_Z) do autovetor
    translations = phi.reshape(-1, 6)[:, 0:3]
    
    # phi já foi normalizado para ter o valor absoluto máximo de 1.0 no linear_buckling.py.
    # Garantindo a normalização caso não esteja:
    max_val = np.max(np.abs(translations))
    if max_val > 1e-12:
        translations = translations / max_val
        
    # Perturba a malha
    nodes_imperfeitos = nodes + translations * amplitude
    
    # Substitui a malha no modelo
    model.mesh_data["nodes"] = nodes_imperfeitos
    
    print("Malha perturbada com sucesso usando o 1º modo de flambagem.")
