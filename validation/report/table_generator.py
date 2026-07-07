from typing import List, Dict, Any

def generate_markdown_table(headers: List[str], rows: List[List[Any]]) -> str:
    """
    Generates a GitHub Flavored Markdown (GFM) table.
    """
    if not headers or not rows:
        return ""
    
    header_str = " | ".join(str(h) for h in headers)
    separator_str = " | ".join("---" for _ in headers)
    
    row_strs = []
    for row in rows:
        row_strs.append(" | ".join(str(r) for r in row))
        
    return f"| {header_str} |\n| {separator_str} |\n" + "\n".join(f"| {r} |" for r in row_strs)

def generate_latex_table(headers: List[str], rows: List[List[Any]], label: str = "", caption: str = "") -> str:
    """
    Generates a publication-ready LaTeX table using the booktabs package.
    """
    if not headers or not rows:
        return ""
    
    col_def = "c" * len(headers)
    tex_lines = [
        "\\begin{table}[htbp]",
        "  \\centering",
        f"  \\caption{{{caption}}}" if caption else "",
        f"  \\label{{tab:{label}}}" if label else "",
        f"  \\begin{{tabular}}{{{col_def}}}",
        "    \\toprule",
        "    " + " & ".join(str(h) for h in headers) + " \\\\",
        "    \\midrule"
    ]
    
    for row in rows:
        formatted_row = []
        for r in row:
            if isinstance(r, float):
                formatted_row.append(f"{r:.6e}")
            else:
                formatted_row.append(str(r))
        tex_lines.append("    " + " & ".join(formatted_row) + " \\\\")
        
    tex_lines.extend([
        "    \\bottomrule",
        "  \\end{tabular}",
        "\\end{table}"
    ])
    
    return "\n".join(line for line in tex_lines if line)

def build_error_metrics_table(metrics: Dict[str, Any]) -> Dict[str, str]:
    """
    Builds the error metrics summary table in Markdown and LaTeX.
    """
    headers = ["Métrica Estatística", "Valor Calculado"]
    rows = []
    
    key_mapping = [
        ("mae", "Erro Absoluto Médio (MAE)", "{:.6e}"),
        ("rmse", "Raiz do Erro Quadrático Médio (RMSE)", "{:.6e}"),
        ("relative_l2_error_percent", "Erro Relativo em Norma L2 (%)", "{:.4f} %"),
        ("relative_linf_error_percent", "Erro Relativo em Norma L_inf (%)", "{:.4f} %"),
        ("peak_relative_error_percent", "Erro Relativo de Pico (%)", "{:.4f} %"),
        ("pearson_correlation", "Correlação de Pearson (r)", "{:.6f}"),
        ("r2_coefficient", "Coeficiente de Determinação (R²)", "{:.6f}")
    ]
    
    for key, name, fmt in key_mapping:
        if key in metrics:
            val = metrics[key]
            rows.append([name, fmt.format(val)])
            
    return {
        "markdown": generate_markdown_table(headers, rows),
        "latex": generate_latex_table(headers, rows, label="error_metrics", caption="Métricas de erro estatísticas globais")
    }

def build_comparison_table(node_labels: List[Any], mef_vals: List[float], ref_vals: List[float], field_name: str = "Deslocamento") -> Dict[str, str]:
    """
    Builds a detailed node-by-node or point-by-point comparison table.
    """
    headers = ["Posição / Nó", f"{field_name} MEF", f"{field_name} Abaqus", "Erro Absoluto", "Erro Relativo (%)"]
    rows = []
    
    for label, mef, ref in zip(node_labels, mef_vals, ref_vals):
        abs_err = abs(mef - ref)
        rel_err = (abs_err / abs(ref)) * 100.0 if abs(ref) > 1e-15 else 0.0
        rows.append([
            str(label),
            f"{mef:.6e}",
            f"{ref:.6e}",
            f"{abs_err:.6e}",
            f"{rel_err:.4f} %"
        ])
        
    return {
        "markdown": generate_markdown_table(headers, rows),
        "latex": generate_latex_table(headers, rows, label=f"{field_name.lower()}_comparison", caption=f"Comparação local para {field_name}")
    }

def build_buckling_table(modes: List[Any], mef_lambdas: List[float], ref_lambdas: List[float]) -> Dict[str, str]:
    """
    Builds the eigenvalue buckling load multiplier comparison table.
    """
    headers = ["Modo", "Multiplicador Solver MEF", "Multiplicador Abaqus", "Erro Relativo (%)"]
    rows = []
    
    for mode, mef, ref in zip(modes, mef_lambdas, ref_lambdas):
        abs_err = abs(abs(mef) - abs(ref))
        rel_err = (abs_err / abs(ref)) * 100.0 if abs(ref) > 1e-15 else 0.0
        rows.append([
            str(mode),
            f"{mef:.5f}",
            f"{ref:.5f}",
            f"{rel_err:.4f} %"
        ])
        
    return {
        "markdown": generate_markdown_table(headers, rows),
        "latex": generate_latex_table(headers, rows, label="buckling_comparison", caption="Comparação de multiplicadores de carga crítica de flambagem")
    }
