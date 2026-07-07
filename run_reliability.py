import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mef.model.shell_model import ShellModel
from mef.mesh.generator import generate_mesh
from mef.mesh.converter import convert_mesh
from main import solve_shell
from mef.model.imperfections import apply_geometric_imperfection

from reliability.variables.random_model import RandomModel
from reliability.design_of_experiments.ccd import CentralCompositeDesign
from reliability.database.response_database import ResponseDatabase
from reliability.response_surface.rsm_models import QuadraticFullRSM
from reliability.response_surface.validation import validate_rsm
from reliability.methods.form import FORM
from reliability.methods.monte_carlo import MonteCarlo
from reliability.methods.sensitivity import SensitivityAnalysis
from reliability.report.builder import ReportBuilder
from reliability.report.plotter import ReportPlotter

def evaluate_mef(t_val, A_val, base_model, nodes_perf, res_perf):
    base_model.geometry_params["thickness"] = t_val
    base_model.mesh_data["nodes"] = nodes_perf.copy()
    apply_geometric_imperfection(base_model, res_perf, amplitude=A_val)
    res_imp = solve_shell(base_model)
    return res_imp.critical_load

def run_reliability_analysis():
    print("="*50)
    print("INICIANDO FRAMEWORK DE CONFIABILIDADE ESTRUTURAL")
    print("="*50)
    
    t_start_total = time.time()
    
    # ---------------------------------------------------------
    # 1. Definição das Variáveis Aleatórias (Ajustadas para Pf > 0)
    # ---------------------------------------------------------
    rm = RandomModel()
    
    # Reduzindo a espessura média para cair a resistência
    rm.add_variable(name='t', distribution='normal', mean=1.9, std_dev=0.1)
    
    # Imperfeição A
    rm.add_variable(name='A', distribution='lognormal', mean=0.5, std_dev=0.1)
    
    # Aumentando drasticamente a carga aplicada para haver sobreposição
    rm.add_variable(name='P', distribution='normal', mean=1100000.0, std_dev=200000.0)
    
    rsm_vars = ['t', 'A']
    
    # ---------------------------------------------------------
    # 2. Setup do Modelo Base Deterministico (Malha Perfeita)
    # ---------------------------------------------------------
    print("\nCalculando Modo de Flambagem Linear (Malha Perfeita)...")
    base_model = ShellModel(
        geometry_type="cylinder",
        geometry_params={"radius": 100.0, "length": 1000.0, "thickness": 2.0},
        material_params={"E": 200e3, "nu": 0.3},
        element_type="QUAD4",
        mesh_params={"num_circumferential": 15, "num_longitudinal": 25},
        analysis_type="linear_buckling"
    )
    raw_mesh = generate_mesh(base_model)
    nodes_perf, elements = convert_mesh(raw_mesh)
    base_model.mesh_data = {"nodes": nodes_perf, "elements": elements}
    
    fixed_nodes = np.where(np.abs(nodes_perf[:, 2]) < 1e-6)[0].tolist()
    base_model.boundary_conditions = {"fixed_nodes": fixed_nodes}
    
    top_nodes = np.where(np.abs(nodes_perf[:, 2] - 1000.0) < 1e-6)[0].tolist()
    force_per_node = 1.0 / len(top_nodes) if len(top_nodes) > 0 else 0
    nodal_loads = [(n, 2, -force_per_node) for n in top_nodes]
    base_model.loads = {"nodal_loads": nodal_loads}
    
    res_perf = solve_shell(base_model)
    
    # ---------------------------------------------------------
    # 3. Design of Experiments (DOE)
    # ---------------------------------------------------------
    t_start_doe = time.time()
    ccd = CentralCompositeDesign(alpha='orthogonal', center_points=1)
    norm_samples = ccd.generate_samples(num_vars=len(rsm_vars))
    
    x_samples = np.zeros_like(norm_samples)
    for i, var_name in enumerate(rsm_vars):
        var = rm.get_variable(var_name)
        x_samples[:, i] = var.mean + norm_samples[:, i] * var.std_dev
    t_doe = time.time() - t_start_doe
        
    # ---------------------------------------------------------
    # 4. Avaliações no MEF (Construção)
    # ---------------------------------------------------------
    db = ResponseDatabase(variable_names=rsm_vars)
    print(f"\nIniciando avaliações no MEF ({len(x_samples)} corridas do DOE)...")
    
    t_start_mef = time.time()
    for i, x in enumerate(x_samples):
        p_cr = evaluate_mef(x[0], x[1], base_model, nodes_perf, res_perf)
        db.add_sample(x, p_cr, {"fonte": "DOE"})
        print(f"  DOE Amostra {i+1}/{len(x_samples)} | t={x[0]:.2f}, A={x[1]:.2f} -> P_cr = {p_cr:.2e} N")
    t_mef = time.time() - t_start_mef
        
    X_data, Y_data = db.get_data()
    
    t_start_rsm = time.time()
    rsm = QuadraticFullRSM()
    rsm.fit(X_data, Y_data)
    t_rsm = time.time() - t_start_rsm
    
    # ---------------------------------------------------------
    # Validação Hold-Out
    # ---------------------------------------------------------
    print("\nGerando amostras Hold-Out (Validação Cruzada) não vistas no DOE...")
    num_val = 5
    x_val = np.zeros((num_val, 2))
    x_val[:, 0] = rm.get_variable('t').sample(num_val)
    x_val[:, 1] = rm.get_variable('A').sample(num_val)
    
    y_val_mef = np.zeros(num_val)
    for i in range(num_val):
        y_val_mef[i] = evaluate_mef(x_val[i, 0], x_val[i, 1], base_model, nodes_perf, res_perf)
        print(f"  Hold-Out {i+1}/{num_val} | t={x_val[i, 0]:.2f}, A={x_val[i, 1]:.2f} -> P_cr = {y_val_mef[i]:.2e} N")
        
    y_val_pred = rsm.predict(x_val)
    print("\n>>> Métricas no Conjunto Hold-Out:")
    r2, rmse, emr = validate_rsm(y_val_mef, y_val_pred)
    
    # ---------------------------------------------------------
    # Geração do Relatório Automático
    # ---------------------------------------------------------
    print("\nInicializando Gerador Automático de Relatórios Científicos...")
    out_dir = os.path.join(os.path.dirname(__file__), "relatorio_output")
    os.makedirs(out_dir, exist_ok=True)
    builder = ReportBuilder(out_dir)
    plotter = ReportPlotter(out_dir)
    
    # Sec 1, 2 e 3
    builder.build_section_1_2_3(base_model, res_perf)
    path_m = plotter.plot_mesh(res_perf.vtk_file)
    if path_m: builder.add_figure("fig_malha", path_m, "Malha original do cilindro (MEF)")
    
    path_b = plotter.plot_buckling_mode(res_perf.vtk_file)
    if path_b: builder.add_figure("fig_modo_flambagem", path_b, "Primeiro modo de flambagem")
    
    # Sec 4
    builder.build_section_4(rm)
    
    # Sec 5 e 6
    builder.build_section_5_6(X_data, Y_data, rsm, r2, rmse, emr)
    
    y_doe_pred = rsm.predict(X_data)
    path_rsm = plotter.plot_rsm_validation(Y_data, y_doe_pred, y_val_mef, y_val_pred)
    builder.add_figure("fig_scatter_rsm", path_rsm, "Validação da Superfície de Resposta")
    
    # ---------------------------------------------------------
    # FORM e Monte Carlo
    # ---------------------------------------------------------
    t_start_form = time.time()
    form = FORM(random_model=rm, rsm=rsm, load_var_name='P', rsm_var_names=rsm_vars)
    beta, pf_form, u_star, x_star, beta_history = form.run(max_iter=50, tol=1e-4, verbose=False)
    t_form = time.time() - t_start_form
    
    t_start_mc = time.time()
    mc = MonteCarlo(random_model=rm, rsm=rsm, load_var_name='P', rsm_var_names=rsm_vars)
    num_mc_samples = 1_000_000
    pf_mc, pcr_samples, g_samples = mc.run(num_samples=num_mc_samples)
    t_mc = time.time() - t_start_mc
    
    builder.build_section_7_8_9(beta, pf_form, x_star, u_star, form.alpha_star, form.var_names, rm)
    
    path_i = plotter.plot_importance_factors(form.alpha_star, form.var_names)
    builder.add_figure("fig_importancia", path_i, "Fatores de Importância")
    
    path_cd = plotter.plot_capacity_demand(pcr_samples, rm.get_variable('P').sample(num_mc_samples))
    builder.add_figure("fig_capacidade_demanda", path_cd, "Capacidade vs Demanda")
    
    path_ls = plotter.plot_limit_state(g_samples)
    builder.add_figure("fig_estado_limite", path_ls, "Distribuição do Estado Limite")
    
    path_fc = plotter.plot_form_convergence(beta_history)
    builder.add_figure("fig_form", path_fc, "Convergência do FORM")
    
    path_3d = plotter.plot_rsm_3d(rsm, X_data, Y_data)
    builder.add_figure("fig_rsm_3d", path_3d, "Superfície de Resposta 3D")
    
    builder.build_section_10_11(pf_mc, num_mc_samples, beta, pf_form)
    
    # ---------------------------------------------------------
    # Análise de Sensibilidade
    # ---------------------------------------------------------
    print("\nExecutando Estudo Paramétrico de Sensibilidade (FORM)...")
    sa = SensitivityAnalysis(form)
    variations = [-20, -10, -5, 5, 10, 20]
    beta_hist = sa.run_study(rsm_vars, variations_pct=variations)
    path_s = plotter.plot_sensitivity(variations, beta_hist)
    builder.add_figure("fig_sensibilidade", path_s, "Sensibilidade do Índice Beta")
    
    # Discussão automática e exportação
    importance_dict = {name: val**2 for name, val in zip(form.var_names, form.alpha_star)}
    builder.generate_discussion(r2, beta if beta is not None else 0.0, importance_dict, pf_mc, pf_form)
    
    t_total = time.time() - t_start_total
    times = {
        "DOE (Amostragem)": t_doe,
        "MEF (Soluções de Eigenbuckling)": t_mef,
        "RSM (Treinamento OLS)": t_rsm,
        "FORM (Otimização HLRF)": t_form,
        "Monte Carlo (1M Amostras)": t_mc,
        "Tempo Total": t_total
    }
    
    builder.build_performance_table(times)
    builder.build_math_background()
    builder.build_num_config(base_model)
    builder.build_abstract(r2, beta if beta is not None else 0.0, pf_form, np.mean(pcr_samples))
    
    path_flow = plotter.plot_flowchart()
    builder.add_figure("fig_fluxograma", path_flow, "Fluxograma Metodológico")
    
    print("\nExportando Relatório para Markdown e DOCX...")
    builder.export()
    print("Relatório Científico salvo no diretório: ", out_dir)

if __name__ == "__main__":
    run_reliability_analysis()
