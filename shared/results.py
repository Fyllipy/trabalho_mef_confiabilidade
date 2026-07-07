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
    
    # --- Metadados e Estrutura Geral ---
    metadata: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    _fallback_data: Dict[str, Any] = field(default_factory=dict, repr=False)
    
    # --- Resultados de Análise de Flambagem Linear (Eigenvalue) ---
    critical_load: Optional[float] = None
    eigenvalues: Optional[Any] = None
    buckling_modes: Optional[Any] = None
    
    # --- Resultados de Análise Não-Linear Geométrica ---
    iterations: Optional[int] = None
    converged: Optional[bool] = None
    load_displacement_curve: Optional[Dict[str, Any]] = field(default_factory=dict)

    # --- Propriedades de Compatibilidade ---
    @property
    def displacements(self) -> Optional[Any]:
        loc = self.metadata.get("results_location", "nodal")
        if loc in self.data and "displacements" in self.data[loc]:
            return self.data[loc]["displacements"]
        return self._fallback_data.get("displacements")

    @displacements.setter
    def displacements(self, val: Any):
        self._fallback_data["displacements"] = val

    @property
    def rotations(self) -> Optional[Any]:
        loc = self.metadata.get("results_location", "nodal")
        if loc in self.data and "rotations" in self.data[loc]:
            return self.data[loc]["rotations"]
        return self._fallback_data.get("rotations")

    @rotations.setter
    def rotations(self, val: Any):
        self._fallback_data["rotations"] = val

    @property
    def strains(self) -> Optional[Any]:
        loc = self.metadata.get("results_location", "nodal")
        if loc in self.data and "strains" in self.data[loc]:
            return self.data[loc]["strains"]
        return self._fallback_data.get("strains")

    @strains.setter
    def strains(self, val: Any):
        self._fallback_data["strains"] = val

    @property
    def stresses(self) -> Optional[Any]:
        loc = self.metadata.get("results_location", "nodal")
        if loc in self.data and "stresses" in self.data[loc]:
            return self.data[loc]["stresses"]
        return self._fallback_data.get("stresses")

    @stresses.setter
    def stresses(self, val: Any):
        self._fallback_data["stresses"] = val

    @property
    def raw_dofs(self) -> Optional[Any]:
        return self._fallback_data.get("raw_dofs")

    @raw_dofs.setter
    def raw_dofs(self, val: Any):
        self._fallback_data["raw_dofs"] = val
    
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
