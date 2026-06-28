from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class ShellModel:
    """
    Modelo representativo central para a análise mecano-fiabilística da casca.
    Armazena toda a definição do problema físico e computacional a ser analisado.
    Nenhum parâmetro solto deverá ser enviado ao solver; tudo está encapsulado aqui.
    """
    
    # --- 1. Geometria ---
    geometry_type: str = "cylinder"  # ex: "cylinder", "plate"
    geometry_params: Dict[str, float] = field(default_factory=dict) 
    # Ex: {"radius": 100.0, "length": 500.0, "thickness": 2.0} ou {"width": 100.0, "length": 100.0}

    # --- 2. Material ---
    material_params: Dict[str, float] = field(default_factory=dict)
    # Ex: {"E": 200e3, "nu": 0.3}

    # --- 3. Propriedades de Seção ---
    section_params: Dict[str, Any] = field(default_factory=dict)
    # Ex: espessura associada aos elementos

    # --- 4. Configuração de Elemento Finito ---
    element_type: str = "QUAD4"  # QUAD4 ou QUAD8
    
    # --- 5. Malha ---
    mesh_params: Dict[str, int] = field(default_factory=dict)
    # Ex: {"num_circumferential": 20, "num_longitudinal": 40}
    # (Poderá também conter a referência para os arrays de nós/elementos gerados)
    mesh_data: Optional[Dict[str, Any]] = None

    # --- 6. Carregamentos (Loads) ---
    loads: Dict[str, Any] = field(default_factory=dict)
    # Ex: {"axial_compression": 1000.0, "pressure": 0.0}

    # --- 7. Condições de Contorno (Boundary Conditions) ---
    boundary_conditions: Dict[str, Any] = field(default_factory=dict)
    # Ex: {"bottom_edge": ["uX", "uY", "uZ"], "top_edge": ["uX", "uY"]}

    # --- 8. Imperfeições Geométricas ---
    imperfection_params: Dict[str, Any] = field(default_factory=dict)
    # Ex: {"type": "modal", "amplitude": 0.5, "mode_number": 1}

    # --- 9. Configurações de Análise e Solucionador ---
    analysis_type: str = "linear_static" # linear_static, linear_buckling, nonlinear
    solver_options: Dict[str, Any] = field(default_factory=dict)
    # Ex: {"tolerance": 1e-6, "max_iterations": 50, "load_steps": 10}

    def validate(self) -> bool:
        """
        Valida a consistência do modelo antes de enviá-lo ao solver MEF.
        """
        # Validação didática simples: checa atributos essenciais
        if not self.geometry_params:
            raise ValueError("Parâmetros geométricos não definidos.")
        if not self.material_params:
            raise ValueError("Parâmetros de material (E, nu) não definidos.")
        
        return True
