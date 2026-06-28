import os
import numpy as np
import matplotlib.pyplot as plt
import pyvista as pv

class ReportPlotter:
    """
    Isola a geração gráfica do projeto, garantindo que todas as figuras do 
    relatório sejam consistentes e off-screen.
    """
    def __init__(self, output_dir: str):
        self.out_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def plot_mesh(self, vtk_file: str) -> str:
        if not os.path.exists(vtk_file): return ""
        mesh = pv.read(vtk_file)
        pl = pv.Plotter(off_screen=True)
        pl.add_mesh(mesh, show_edges=True, color='lightblue', edge_color='black')
        pl.view_isometric()
        path = os.path.join(self.out_dir, "fig_malha.png")
        pl.screenshot(path)
        return path
        
    def plot_buckling_mode(self, vtk_file: str) -> str:
        if not os.path.exists(vtk_file): return ""
        mesh = pv.read(vtk_file)
        pl = pv.Plotter(off_screen=True)
        
        # Warp by Vector se 'Displacement' ou 'Eigenvector' estiver presente
        vectors = None
        for name in mesh.point_data.keys():
            if name.lower() in ['displacement', 'eigenvector']:
                vectors = name
                break
                
        if vectors:
            mesh.set_active_vectors(vectors)
            warped = mesh.warp_by_vector(factor=5.0) # Fator visual
            pl.add_mesh(warped, scalars=vectors, show_edges=True, cmap='jet')
        else:
            pl.add_mesh(mesh, show_edges=True, color='red')
            
        pl.view_isometric()
        path = os.path.join(self.out_dir, "fig_modo_flambagem.png")
        pl.screenshot(path)
        return path
        
    def plot_importance_factors(self, alpha_vector: np.ndarray, var_names: list) -> str:
        plt.figure(figsize=(6, 4))
        # Importância é alfa^2
        importance = alpha_vector**2
        plt.bar(var_names, importance, color='royalblue')
        plt.title(r'Fatores de Importância ($\alpha_i^2$)')
        plt.ylabel('Importância Relativa')
        plt.ylim(0, 1.1)
        for i, val in enumerate(importance):
            plt.text(i, val + 0.05, f"{val:.2f}", ha='center')
        path = os.path.join(self.out_dir, "fig_importancia.png")
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        return path
        
    def plot_sensitivity(self, variations: list, beta_history: dict) -> str:
        plt.figure(figsize=(8, 5))
        for var_name, betas in beta_history.items():
            plt.plot(variations, betas, marker='o', label=var_name)
        plt.title('Estudo Paramétrico de Sensibilidade')
        plt.xlabel('Variação Relativa da Média (%)')
        plt.ylabel(r'Índice de Confiabilidade ($\beta$)')
        plt.legend()
        plt.grid(True, alpha=0.4)
        path = os.path.join(self.out_dir, "fig_sensibilidade.png")
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        return path
        
    def plot_capacity_demand(self, pcr_samples, demand_samples) -> str:
        plt.figure(figsize=(8, 5))
        plt.hist(pcr_samples, bins=100, density=True, alpha=0.6, color='blue', label='Capacidade $P_{cr}$ (RSM)')
        plt.hist(demand_samples, bins=100, density=True, alpha=0.6, color='red', label='Demanda $P$')
        plt.title('Interferência Estatística: Capacidade vs Demanda')
        plt.xlabel('Força Axial (N)')
        plt.ylabel('Densidade')
        plt.legend()
        plt.grid(True, alpha=0.3)
        path = os.path.join(self.out_dir, "fig_capacidade_demanda.png")
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        return path
        
    def plot_limit_state(self, g_samples) -> str:
        plt.figure(figsize=(8, 5))
        plt.hist(g_samples, bins=100, density=True, alpha=0.7, color='purple', label='$g(X) = P_{cr} - P$')
        plt.axvline(x=0, color='red', linestyle='-', linewidth=2, label='Fronteira de Falha ($g=0$)')
        plt.fill_betweenx([0, plt.ylim()[1]], plt.xlim()[0], 0, color='red', alpha=0.1)
        plt.title('Distribuição da Função de Estado Limite')
        plt.xlabel('Margem de Segurança $g(X)$ (N)')
        plt.ylabel('Densidade')
        plt.legend()
        plt.grid(True, alpha=0.3)
        path = os.path.join(self.out_dir, "fig_estado_limite.png")
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        return path
        
    def plot_rsm_validation(self, y_true_train, y_pred_train, y_true_test, y_pred_test) -> str:
        plt.figure(figsize=(6, 6))
        plt.scatter(y_true_train, y_pred_train, color='blue', label='Dados de Treino (DOE)', s=50)
        plt.scatter(y_true_test, y_pred_test, color='red', marker='x', label='Hold-Out (Teste)', s=70)
        
        # Reta identidade
        min_val = min(np.min(y_true_train), np.min(y_true_test)) * 0.95
        max_val = max(np.max(y_true_train), np.max(y_true_test)) * 1.05
        plt.plot([min_val, max_val], [min_val, max_val], 'k--', label='Exato (y=x)')
        plt.title('Validação da Superfície de Resposta')
        plt.xlabel('$P_{cr}$ (Avaliação Direta no MEF)')
        plt.ylabel('$P_{cr}$ (Predição do RSM)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        path = os.path.join(self.out_dir, "fig_scatter_rsm.png")
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        return path
        
    def plot_form_convergence(self, beta_history) -> str:
        if not beta_history: return ""
        plt.figure(figsize=(8, 5))
        plt.plot(range(1, len(beta_history) + 1), beta_history, marker='o', linestyle='-', color='green')
        plt.title('Convergência do Índice de Confiabilidade (FORM)')
        plt.xlabel('Iteração (Algoritmo HLRF)')
        plt.ylabel(r'Índice de Confiabilidade ($\beta$)')
        plt.grid(True, alpha=0.3)
        path = os.path.join(self.out_dir, "fig_convergencia_form.png")
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        return path
        
    def plot_rsm_3d(self, rsm, X_data, Y_data) -> str:
        from mpl_toolkits.mplot3d import Axes3D
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        t_range = np.linspace(X_data[:, 0].min(), X_data[:, 0].max(), 30)
        a_range = np.linspace(X_data[:, 1].min(), X_data[:, 1].max(), 30)
        T_mesh, A_mesh = np.meshgrid(t_range, a_range)
        
        X_grid = np.column_stack((T_mesh.flatten(), A_mesh.flatten()))
        P_pred = rsm.predict(X_grid).reshape(T_mesh.shape)
        
        surf = ax.plot_surface(T_mesh, A_mesh, P_pred, cmap='viridis', alpha=0.8, edgecolor='none')
        ax.scatter(X_data[:, 0], X_data[:, 1], Y_data, color='red', s=50, label='Pontos do DOE')
        
        ax.set_title('Superfície de Resposta Quadrática Completa')
        ax.set_xlabel('Espessura $t$ (mm)')
        ax.set_ylabel('Amplitude $A$ (mm)')
        ax.set_zlabel('Carga Crítica $P_{cr}$ (N)')
        fig.colorbar(surf, shrink=0.5, aspect=5)
        path = os.path.join(self.out_dir, "fig_rsm_3d.png")
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        return path
        
    def plot_flowchart(self) -> str:
        fig, ax = plt.subplots(figsize=(6, 8))
        ax.axis('off')
        
        steps = [
            "Modelo Estrutural",
            "Avaliação Numérica (MEF)",
            "Design of Experiments (DOE)",
            "Banco de Respostas Estocástico",
            "Superfície de Resposta (RSM)",
            "Algoritmo Analítico (FORM)",
            "Simulação Numérica (Monte Carlo)",
            "Relatório Científico Final"
        ]
        
        y_pos = np.linspace(0.9, 0.1, len(steps))
        
        for i, (step, y) in enumerate(zip(steps, y_pos)):
            ax.text(0.5, y, step, ha='center', va='center', fontsize=12, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.8", fc="#e0f2fe", ec="#0369a1", lw=2))
            
            if i < len(steps) - 1:
                ax.annotate('', xy=(0.5, y_pos[i+1]+0.04), xytext=(0.5, y-0.04),
                            arrowprops=dict(arrowstyle="->", lw=2, color="#0369a1"))
                
        path = os.path.join(self.out_dir, "fig_fluxograma.png")
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        return path
