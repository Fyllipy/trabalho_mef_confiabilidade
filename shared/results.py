from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class ShellResults:
    """
    Objeto hierárquico que encapsula os resultados do Solver MEF, 
    separando semanticamente os retornos para facilitar a extração 
    pelo módulo de confiabilidade e pós-processamento.
    """
    
    # --- Resultados Globais / Gerais ---
    vtk_file: Optional[str] = None
    
    # --- Resultados de Análise Estática Linear ---
    displacements: Optional[Any] = None
    rotations: Optional[Any] = None
    strains: Optional[Any] = None
    stresses: Optional[Any] = None
    raw_dofs: Optional[Any] = None
    
    # --- Resultados de Análise de Flambagem Linear (Eigenvalue) ---
    critical_load: Optional[float] = None
    eigenvalues: Optional[Any] = None
    buckling_modes: Optional[Any] = None
    
    # --- Resultados de Análise Não-Linear Geométrica ---
    iterations: Optional[int] = None
    converged: Optional[bool] = None
    load_displacement_curve: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __repr__(self) -> str:
        """Representação amigável dos resultados presentes."""
        res = ["ShellResults:"]
        if self.critical_load is not None:
            res.append(f"  - Carga Crítica: {self.critical_load}")
        if self.converged is not None:
            res.append(f"  - Convergiu (NL): {self.converged} em {self.iterations} iterações")
        if self.vtk_file:
            res.append(f"  - Exportado para: {self.vtk_file}")
        
        return "\n".join(res)
