import numpy as np
from typing import Dict, Any, Optional

class DataCollector:
    """
    Adapter class to collect, extract, and structure data from:
    - ShellModel (MEF Solver inputs)
    - ShellResults (MEF Solver outputs)
    - Reference data (Abaqus outputs)
    
    This class decouples the ReportBuilder from the internal structures of the solver.
    """
    
    @staticmethod
    def extract_model_info(model: Any) -> Dict[str, Any]:
        """
        Extracts parameters from a ShellModel object.
        Uses dynamic reflection/getattr to avoid hard runtime dependency.
        """
        info = {
            "geometry_type": getattr(model, "geometry_type", "N/A"),
            "geometry_params": getattr(model, "geometry_params", {}),
            "material_params": getattr(model, "material_params", {}),
            "element_type": getattr(model, "element_type", "N/A"),
            "mesh_params": getattr(model, "mesh_params", {}),
            "analysis_type": getattr(model, "analysis_type", "N/A"),
            "results_location": getattr(model, "results_location", "nodal"),
            "num_nodes": 0,
            "num_elements": 0,
            "num_dofs": 0,
            "nodes": None,
            "elements": None
        }
        
        # Extract mesh sizes if available
        mesh_data = getattr(model, "mesh_data", None)
        if mesh_data and isinstance(mesh_data, dict):
            nodes = mesh_data.get("nodes")
            elements = mesh_data.get("elements")
            if nodes is not None:
                nodes_arr = np.array(nodes)
                info["nodes"] = nodes_arr
                info["num_nodes"] = len(nodes_arr)
                info["num_dofs"] = len(nodes_arr) * 6 # 6 DOFs per node
            if elements is not None:
                info["elements"] = np.array(elements)
                info["num_elements"] = len(elements)
                
        return info

    @staticmethod
    def extract_solver_results(results: Any) -> Dict[str, Any]:
        """
        Extracts numerical fields from ShellResults object.
        """
        info = {
            "critical_load": getattr(results, "critical_load", None),
            "eigenvalues": getattr(results, "eigenvalues", None),
            "iterations": getattr(results, "iterations", None),
            "converged": getattr(results, "converged", None),
            "load_displacement_curve": getattr(results, "load_displacement_curve", {}),
            "vtk_file": getattr(results, "vtk_file", None),
            "displacements": None,
            "rotations": None,
            "strains": None,
            "stresses": None
        }
        
        # Safely extract properties
        for field in ["displacements", "rotations", "strains", "stresses"]:
            val = getattr(results, field, None)
            if val is not None:
                info[field] = np.array(val)
                
        return info

    @staticmethod
    def read_reference_file(filepath: str) -> Optional[float]:
        """
        Reads a single float value from a reference results file (e.g. abaqus_static_result.txt).
        """
        try:
            with open(filepath, "r") as f:
                return float(f.read().strip())
        except Exception:
            return None

    @staticmethod
    def read_reference_field(filepath: str) -> Optional[np.ndarray]:
        """
        Reads a reference field (like displacement or stress array) from a file.
        Supports numpy text files (.txt or .npy).
        """
        try:
            if filepath.endswith(".npy"):
                return np.load(filepath)
            else:
                return np.loadtxt(filepath)
        except Exception:
            return None
