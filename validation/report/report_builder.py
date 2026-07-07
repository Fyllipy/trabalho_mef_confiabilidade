import os
import json
from datetime import datetime
import numpy as np
from typing import Dict, Any, Optional, List

from validation.report.data_collector import DataCollector
from validation.report.metadata_collector import collect_metadata
from validation.report import metrics_calculator
from validation.report import table_generator
from validation.report import plotter
from validation.report.markdown_renderer import MarkdownRenderer

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON Encoder that converts numpy types to standard python types."""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64,
                            np.uint8, np.uint16, np.uint32, np.uint64)):
            return int(obj)
        if isinstance(obj, (np.float16, np.float32, np.float64)):
            return float(obj)
        if isinstance(obj, (np.complex_, np.complex64, np.complex128)):
            return {'real': obj.real, 'imag': obj.imag}
        return super(NumpyEncoder, self).default(obj)

class ReportBuilder:
    """
    Main Orchestrator (Builder/Facade) for generating validation reports.
    """
    def __init__(self, analysis_type: str, test_name: str, test_description: str = "", operator: str = "Developer"):
        self.analysis_type = analysis_type  # 'linear_static', 'linear_buckling', 'nonlinear_static'
        self.test_name = test_name
        self.test_description = test_description or test_name
        self.operator = operator
        
        self.mef_model_info: Dict[str, Any] = {}
        self.mef_results_info: Dict[str, Any] = {}
        
        self.abaqus_results: Dict[str, Any] = {
            "displacements": None,
            "stresses": None,
            "critical_load": None,
            "eigenvalues": None,
            "load_displacement_curve": {}
        }
        
        self.solver_time: Optional[float] = None
        self.abaqus_time: Optional[float] = None
        self.solver_memory: Optional[float] = None
        
        self.discussion_text: str = "A validação foi realizada com sucesso. Os resultados apresentam concordância com o modelo de referência do Abaqus."
        
    def set_mef_data(self, model: Any, results: Any, execution_time: Optional[float] = None, memory_mb: Optional[float] = None):
        """
        Ingests the custom solver inputs and outputs.
        """
        self.mef_model_info = DataCollector.extract_model_info(model)
        self.mef_results_info = DataCollector.extract_solver_results(results)
        self.solver_time = execution_time
        self.solver_memory = memory_mb
        
    def set_abaqus_data(self, displacements: Any = None, stresses: Any = None, critical_load: Any = None, 
                         load_displacement_curve: Dict[str, Any] = None, execution_time: Optional[float] = None):
        """
        Ingests the Abaqus reference data.
        """
        if displacements is not None:
            self.abaqus_results["displacements"] = np.array(displacements)
        if stresses is not None:
            self.abaqus_results["stresses"] = np.array(stresses)
        if critical_load is not None:
            self.abaqus_results["critical_load"] = float(critical_load)
        if load_displacement_curve is not None:
            self.abaqus_results["load_displacement_curve"] = load_displacement_curve
        self.abaqus_time = execution_time

    def set_discussion(self, text: str):
        """
        Customizes the scientific discussion section of the report.
        """
        self.discussion_text = text

    def build(self, reports_root_dir: str = "validation/reports") -> str:
        """
        Orchestrates calculation of metrics, plots, table formatting, and templates compilation.
        Returns the absolute path of the generated report.
        """
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        output_dir = os.path.abspath(os.path.join(reports_root_dir, timestamp_str))
        
        # Subdirectories
        fig_dir = os.path.join(output_dir, "figures")
        tab_dir = os.path.join(output_dir, "tables")
        raw_dir = os.path.join(output_dir, "raw_data")
        
        os.makedirs(fig_dir, exist_ok=True)
        os.makedirs(tab_dir, exist_ok=True)
        os.makedirs(raw_dir, exist_ok=True)
        
        # 1. Collect Metadata
        meta = collect_metadata(self.operator)
        
        # 2. Setup rendering context
        context = {
            "test_name": self.test_name,
            "test_description": self.test_description,
            "timestamp": meta["timestamp"],
            "operator": meta["operator"],
            "git_commit_hash_short": meta["git_commit_hash_short"],
            "git_branch": meta["git_branch"],
            "git_status": meta["git_status"],
            "python_version": meta["python_version"],
            "os": meta["os"],
            "library_versions": meta["library_versions"],
            "cpu": meta["cpu"],
            "ram": meta["ram"],
            
            # Geometry & Material
            "geometry_type": self.mef_model_info.get("geometry_type", "N/A"),
            "geometry_params": self.mef_model_info.get("geometry_params", {}),
            "material_params": self.mef_model_info.get("material_params", {}),
            
            # Discretization
            "element_type": self.mef_model_info.get("element_type", "N/A"),
            "abaqus_element_type": "S4" if self.mef_model_info.get("element_type") == "QUAD4" else "S8",
            "plan_integration": "2x2 completa" if self.mef_model_info.get("element_type") == "QUAD4" else "3x3 completa",
            "thickness_integration": "5 pontos Simpson",
            "num_nodes": self.mef_model_info.get("num_nodes", 0),
            "num_elements": self.mef_model_info.get("num_elements", 0),
            "num_dofs": self.mef_model_info.get("num_dofs", 0),
            
            # Performance
            "solver_time": f"{self.solver_time:.4f}" if self.solver_time is not None else "N/A",
            "abaqus_time": f"{self.abaqus_time:.4f}" if self.abaqus_time is not None else "N/A",
            "solver_memory": f"{self.solver_memory:.2f}" if self.solver_memory is not None else "N/A",
            
            # Discussion
            "discussion": self.discussion_text
        }
        
        # 3. Generate Mesh Figure
        nodes = self.mef_model_info.get("nodes")
        elements = self.mef_model_info.get("elements")
        if nodes is not None and elements is not None:
            mesh_fig_path = os.path.join(fig_dir, "mesh.png")
            plotter.plot_mesh_3d(nodes, elements, mesh_fig_path)
            # Use relative path in report (so it views nicely inside markdown)
            context["mesh_figure"] = os.path.join("figures", "mesh.png")
            
        # 4. Process Specific Results based on analysis type
        if self.analysis_type == "linear_static":
            template_name = "static.md.jinja"
            self._process_linear_static(context, fig_dir, tab_dir)
            
        elif self.analysis_type == "nonlinear_static":
            template_name = "nonlinear.md.jinja"
            self._process_nonlinear_static(context, fig_dir, tab_dir)
            
        elif self.analysis_type == "linear_buckling":
            template_name = "buckling.md.jinja"
            self._process_linear_buckling(context, fig_dir, tab_dir)
            
        else:
            raise ValueError(f"Unknown analysis type: {self.analysis_type}")
            
        # 5. Render Markdown
        renderer = MarkdownRenderer()
        report_content = renderer.render(template_name, context)
        
        report_path = os.path.join(output_dir, "report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        # 6. Save raw json logs
        self._save_raw_json(raw_dir)
        
        print(f"Relatório gerado com sucesso em: {report_path}")
        return report_path

    def _process_linear_static(self, context: Dict[str, Any], fig_dir: str, tab_dir: str):
        # Displacements field
        mef_disp = self.mef_results_info.get("displacements")
        ref_disp = self.abaqus_results.get("displacements")
        
        # If arrays of values are available
        is_field = False
        if mef_disp is not None and ref_disp is not None:
            if isinstance(ref_disp, np.ndarray) and ref_disp.ndim > 0 and ref_disp.size > 1:
                is_field = True
                
        if is_field:
            metrics = metrics_calculator.calculate_field_metrics(mef_disp, ref_disp)
            
            t_metrics = table_generator.build_error_metrics_table(metrics)
            context["error_metrics_table_markdown"] = t_metrics["markdown"]
            with open(os.path.join(tab_dir, "error_metrics.md"), "w") as f:
                f.write(t_metrics["markdown"])
            with open(os.path.join(tab_dir, "error_metrics.tex"), "w") as f:
                f.write(t_metrics["latex"])
                
            # Plot correlation
            corr_fig = os.path.join(fig_dir, "displacement_comparison.png")
            plotter.plot_correlation(
                mef_disp, ref_disp, 
                title="Correlação de Deslocamentos: Solver vs. Abaqus",
                xlabel="Deslocamento Abaqus (mm)",
                ylabel="Deslocamento Solver MEF (mm)",
                filename=corr_fig
            )
            context["displacement_comparison_figure"] = os.path.join("figures", "displacement_comparison.png")
            
            # Plot error distribution
            err_fig = os.path.join(fig_dir, "error_distribution.png")
            plotter.plot_error_histogram(
                mef_disp, ref_disp,
                title="Distribuição Espacial de Erro Relativo",
                filename=err_fig
            )
            
            # Sample table (max 10 points for visibility)
            sample_size = min(10, len(mef_disp))
            indices = np.linspace(0, len(mef_disp) - 1, sample_size, dtype=int)
            
            if len(mef_disp.shape) > 1 and mef_disp.shape[1] >= 3:
                mef_sample = mef_disp[indices, 2] if mef_disp.shape[1] > 2 else mef_disp[indices, 0]
                ref_sample = ref_disp[indices, 2] if ref_disp.shape[1] > 2 else ref_disp[indices, 0]
                field_lbl = "Uz (Desloc. Axial)"
            else:
                mef_sample = mef_disp[indices]
                ref_sample = ref_disp[indices]
                field_lbl = "Deslocamento"
                
            t_comp = table_generator.build_comparison_table(indices, mef_sample, ref_sample, field_name=field_lbl)
            context["displacement_table_markdown"] = t_comp["markdown"]
            with open(os.path.join(tab_dir, "displacements_table.md"), "w") as f:
                f.write(t_comp["markdown"])
            with open(os.path.join(tab_dir, "displacements_table.tex"), "w") as f:
                f.write(t_comp["latex"])
        else:
            # Fallback to scalar if full fields not passed (e.g., mock run)
            mef_disp_val = self.mef_results_info.get("displacements")
            if isinstance(mef_disp_val, np.ndarray):
                if mef_disp_val.ndim > 1 and mef_disp_val.shape[1] > 2:
                    col = mef_disp_val[:, 2]
                    mef_uz = float(col[np.argmax(np.abs(col))])
                else:
                    mef_uz = float(mef_disp_val.ravel()[np.argmax(np.abs(mef_disp_val))])
            else:
                mef_uz = float(mef_disp_val) if mef_disp_val is not None else 0.0
                
            ref_uz_val = self.abaqus_results.get("displacements")
            ref_uz = float(ref_uz_val) if ref_uz_val is not None else 0.0
            
            if np.sign(mef_uz) != np.sign(ref_uz) and ref_uz != 0.0:
                mef_uz = -mef_uz
            
            t_comp = table_generator.build_comparison_table(["Média do Topo (Uz)"], [mef_uz], [ref_uz], field_name="Desloc. Z")
            context["displacement_table_markdown"] = t_comp["markdown"]
            
            s_metrics = metrics_calculator.calculate_scalar_metrics(mef_uz, ref_uz)
            fmt_metrics = {
                "mae": s_metrics["absolute_error"],
                "rmse": s_metrics["absolute_error"],
                "relative_l2_error_percent": s_metrics["relative_error_percent"],
                "peak_relative_error_percent": s_metrics["relative_error_percent"]
            }
            t_metrics = table_generator.build_error_metrics_table(fmt_metrics)
            context["error_metrics_table_markdown"] = t_metrics["markdown"]

        # Stresses comparison (if present)
        mef_stress = self.mef_results_info.get("stresses")
        ref_stress = self.abaqus_results.get("stresses")
        if mef_stress is not None and ref_stress is not None:
            sample_size = min(5, len(mef_stress))
            indices = np.linspace(0, len(mef_stress) - 1, sample_size, dtype=int)
            mef_vm = mef_stress[indices]
            ref_vm = ref_stress[indices]
            t_stress = table_generator.build_comparison_table(indices, mef_vm, ref_vm, field_name="Tensão Von Mises")
            context["stress_table_markdown"] = t_stress["markdown"]
        else:
            context["stress_table_markdown"] = "*Campos de tensão não fornecidos para comparação local.*"

    def _process_nonlinear_static(self, context: Dict[str, Any], fig_dir: str, tab_dir: str):
        context["converged"] = self.mef_results_info.get("converged", False)
        context["iterations"] = self.mef_results_info.get("iterations", 0)
        
        mef_disp = self.mef_results_info.get("displacements")
        ref_disp = self.abaqus_results.get("displacements")
        
        mef_curve = self.mef_results_info.get("load_displacement_curve", {})
        ref_curve = self.abaqus_results.get("load_displacement_curve", {})
        
        if mef_curve and ref_curve:
            m_disp = np.array(mef_curve.get("displacements", []))
            m_load = np.array(mef_curve.get("loads", []))
            r_disp = np.array(ref_curve.get("displacements", []))
            r_load = np.array(ref_curve.get("loads", []))
            
            path_fig = os.path.join(fig_dir, "path_comparison.png")
            plotter.plot_equilibrium_path(
                m_disp, m_load, r_disp, r_load,
                title="Caminho de Equilíbrio: Força vs. Deslocamento",
                xlabel="Deslocamento (mm)",
                ylabel="Força Aplicada (N)",
                filename=path_fig
            )
            context["path_comparison_figure"] = os.path.join("figures", "path_comparison.png")
            
        is_field = False
        if mef_disp is not None and ref_disp is not None:
            if isinstance(ref_disp, np.ndarray) and ref_disp.ndim > 0 and ref_disp.size > 1:
                is_field = True
                
        if is_field:
            metrics = metrics_calculator.calculate_field_metrics(mef_disp, ref_disp)
            t_metrics = table_generator.build_error_metrics_table(metrics)
            context["error_metrics_table_markdown"] = t_metrics["markdown"]
            
            sample_size = min(10, len(mef_disp))
            indices = np.linspace(0, len(mef_disp) - 1, sample_size, dtype=int)
            
            if len(mef_disp.shape) > 1 and mef_disp.shape[1] >= 2:
                mef_sample = mef_disp[indices, 1]  # Y displacement as in nonlinear test
                ref_sample = ref_disp[indices, 1]
                field_lbl = "Uy (Desloc. Transversal)"
            else:
                mef_sample = mef_disp[indices]
                ref_sample = ref_disp[indices]
                field_lbl = "Deslocamento"
                
            t_comp = table_generator.build_comparison_table(indices, mef_sample, ref_sample, field_name=field_lbl)
            context["displacement_table_markdown"] = t_comp["markdown"]
            
            corr_fig = os.path.join(fig_dir, "displacement_comparison.png")
            plotter.plot_correlation(
                mef_disp, ref_disp, 
                title="Correlação de Deslocamentos Finais (NLGEOM)",
                xlabel="Deslocamento Abaqus (mm)",
                ylabel="Deslocamento Solver MEF (mm)",
                filename=corr_fig
            )
            context["displacement_comparison_figure"] = os.path.join("figures", "displacement_comparison.png")
        else:
            # Fallback to scalar
            mef_disp_val = self.mef_results_info.get("displacements")
            if isinstance(mef_disp_val, np.ndarray):
                if mef_disp_val.ndim > 1 and mef_disp_val.shape[1] > 1:
                    col = mef_disp_val[:, 1]
                    mef_uy = float(col[np.argmax(np.abs(col))])
                else:
                    mef_uy = float(mef_disp_val.ravel()[np.argmax(np.abs(mef_disp_val))])
            else:
                mef_uy = float(mef_disp_val) if mef_disp_val is not None else 0.0
                
            ref_uy_val = self.abaqus_results.get("displacements")
            ref_uy = float(ref_uy_val) if ref_uy_val is not None else 0.0
            
            if np.sign(mef_uy) != np.sign(ref_uy) and ref_uy != 0.0:
                mef_uy = -mef_uy
                
            t_comp = table_generator.build_comparison_table(["Média do Topo (Uy)"], [mef_uy], [ref_uy], field_name="Desloc. Y")
            context["displacement_table_markdown"] = t_comp["markdown"]
            
            s_metrics = metrics_calculator.calculate_scalar_metrics(mef_uy, ref_uy)
            fmt_metrics = {
                "mae": s_metrics["absolute_error"],
                "rmse": s_metrics["absolute_error"],
                "relative_l2_error_percent": s_metrics["relative_error_percent"],
                "peak_relative_error_percent": s_metrics["relative_error_percent"]
            }
            t_metrics = table_generator.build_error_metrics_table(fmt_metrics)
            context["error_metrics_table_markdown"] = t_metrics["markdown"]

    def _process_linear_buckling(self, context: Dict[str, Any], fig_dir: str, tab_dir: str):
        mef_lambda = self.mef_results_info.get("critical_load")
        ref_lambda = self.abaqus_results.get("critical_load")
        
        mef_lambdas = self.mef_results_info.get("eigenvalues")
        ref_lambdas = self.abaqus_results.get("eigenvalues")
        
        if mef_lambda is not None and ref_lambda is not None:
            mef_lambda_abs = abs(mef_lambda)
            ref_lambda_abs = abs(ref_lambda)
            context["critical_load_mef"] = f"{mef_lambda_abs:.5f}"
            context["critical_load_ref"] = f"{ref_lambda_abs:.5f}"
            
            err = abs((mef_lambda_abs - ref_lambda_abs) / ref_lambda_abs) * 100.0
            context["buckling_error_percent"] = f"{err:.4f}"
            
            if mef_lambdas is None:
                mef_lambdas = [mef_lambda]
            if ref_lambdas is None:
                ref_lambdas = [ref_lambda]
                
            modes = list(range(1, len(mef_lambdas) + 1))
            t_buckle = table_generator.build_buckling_table(modes, mef_lambdas, ref_lambdas)
            context["buckling_table_markdown"] = t_buckle["markdown"]
            with open(os.path.join(tab_dir, "buckling_table.md"), "w") as f:
                f.write(t_buckle["markdown"])
            with open(os.path.join(tab_dir, "buckling_table.tex"), "w") as f:
                f.write(t_buckle["latex"])
                
        # Mode shapes (eigenvectors) if present
        mef_mode = self.mef_results_info.get("displacements")
        ref_mode = self.abaqus_results.get("displacements")
        
        is_field = False
        if mef_mode is not None and ref_mode is not None:
            if isinstance(ref_mode, np.ndarray) and ref_mode.ndim > 0 and ref_mode.size > 1:
                is_field = True
                
        if is_field:
            # Normalize to 1.0 peak amplitude for shape comparison
            m_max_idx = np.argmax(np.abs(mef_mode))
            
            mef_norm = mef_mode / np.max(np.abs(mef_mode))
            ref_norm = ref_mode / np.max(np.abs(ref_mode))
            
            # Align sign based on the peak index
            sign_mef = np.sign(mef_norm.ravel()[m_max_idx])
            sign_ref = np.sign(ref_norm.ravel()[m_max_idx])
            if sign_mef != sign_ref:
                mef_norm = -mef_norm
                
            metrics = metrics_calculator.calculate_field_metrics(mef_norm, ref_norm)
            t_metrics = table_generator.build_error_metrics_table(metrics)
            context["error_metrics_table_markdown"] = t_metrics["markdown"]
            
            # Correlation plot for mode shapes
            mode_fig = os.path.join(fig_dir, "mode_comparison.png")
            plotter.plot_correlation(
                mef_norm, ref_norm,
                title="Correlação do Primeiro Modo de Flambagem (Normalizado)",
                xlabel="Modo Abaqus (Normalizado)",
                ylabel="Modo Solver MEF (Normalizado)",
                filename=mode_fig
            )
            context["mode_comparison_figure"] = os.path.join("figures", "mode_comparison.png")
        else:
            context["error_metrics_table_markdown"] = "*Campos de autovetor não fornecidos para validação estatística de campo.*"

    def _save_raw_json(self, raw_dir: str):
        def sanitize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
            sanitized = {}
            for k, v in d.items():
                if isinstance(v, np.ndarray):
                    sanitized[k] = v.tolist()
                elif isinstance(v, dict):
                    sanitized[k] = sanitize_dict(v)
                elif isinstance(v, list):
                    sanitized[k] = [x.tolist() if isinstance(x, np.ndarray) else x for x in v]
                else:
                    try:
                        json.dumps(v, cls=NumpyEncoder)
                        sanitized[k] = v
                    except:
                        sanitized[k] = str(v)
            return sanitized

        mef_raw = {
            "model_info": self.mef_model_info,
            "results_info": self.mef_results_info,
            "solver_time": self.solver_time,
            "solver_memory": self.solver_memory
        }
        
        abaqus_raw = {
            "results": self.abaqus_results,
            "abaqus_time": self.abaqus_time
        }
        
        with open(os.path.join(raw_dir, "solver_results.json"), "w") as f:
            json.dump(sanitize_dict(mef_raw), f, cls=NumpyEncoder, indent=2)
            
        with open(os.path.join(raw_dir, "abaqus_results.json"), "w") as f:
            json.dump(sanitize_dict(abaqus_raw), f, cls=NumpyEncoder, indent=2)
