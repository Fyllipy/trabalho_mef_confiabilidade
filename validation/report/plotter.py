import os
import numpy as np
import matplotlib
matplotlib.use('Agg') # Set non-interactive backend to run without GUI
import matplotlib.pyplot as plt

def plot_correlation(mef_val: np.ndarray, ref_val: np.ndarray, title: str, xlabel: str, ylabel: str, filename: str):
    """
    Plots a scientific correlation scatter plot between Solver MEF and Abaqus reference values.
    Includes the y = x line (ideal correlation) for comparison.
    """
    m = np.asarray(mef_val).ravel()
    r = np.asarray(ref_val).ravel()
    
    plt.figure(figsize=(6, 5))
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    plt.scatter(r, m, color='#2b5c8f', alpha=0.6, edgecolors='none', label='Nós da Malha')
    
    # 45-degree identity line
    mn = min(r.min(), m.min())
    mx = max(r.max(), m.max())
    lims = [mn - 0.05*abs(mn), mx + 0.05*abs(mx)]
    plt.plot(lims, lims, 'r--', alpha=0.8, linewidth=1.5, label='Correlação Perfeita (y = x)')
    
    plt.xlim(lims)
    plt.ylim(lims)
    plt.xlabel(xlabel, fontsize=10)
    plt.ylabel(ylabel, fontsize=10)
    plt.title(title, fontsize=12, fontweight='bold', pad=15)
    plt.legend(loc='upper left', frameon=True)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    plt.savefig(filename, dpi=300)
    plt.close()

def plot_error_histogram(mef_val: np.ndarray, ref_val: np.ndarray, title: str, filename: str):
    """
    Plots a histogram of relative errors across all nodes/points.
    """
    m = np.asarray(mef_val).ravel()
    r = np.asarray(ref_val).ravel()
    
    denom = np.abs(r)
    mask = denom > 1e-15
    errors = np.zeros_like(r)
    errors[mask] = (np.abs(m[mask] - r[mask]) / denom[mask]) * 100.0
    
    plt.figure(figsize=(6, 4))
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    plt.hist(errors, bins=20, color='#3a86c8', edgecolor='black', alpha=0.7)
    plt.xlabel('Erro Relativo (%)', fontsize=10)
    plt.ylabel('Frequência (Nós)', fontsize=10)
    plt.title(title, fontsize=12, fontweight='bold', pad=15)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    plt.savefig(filename, dpi=300)
    plt.close()

def plot_equilibrium_path(mef_disp: np.ndarray, mef_load: np.ndarray, ref_disp: np.ndarray, ref_load: np.ndarray, title: str, xlabel: str, ylabel: str, filename: str):
    """
    Plots the equilibrium path (Force-Displacement curve) for nonlinear analysis.
    """
    plt.figure(figsize=(7, 5))
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    plt.plot(mef_disp, mef_load, 'b-', label='Solver MEF', linewidth=2.0)
    plt.plot(ref_disp, ref_load, 'r--', label='Abaqus (Referência)', linewidth=2.0)
    
    plt.xlabel(xlabel, fontsize=10)
    plt.ylabel(ylabel, fontsize=10)
    plt.title(title, fontsize=12, fontweight='bold', pad=15)
    plt.legend(loc='best', frameon=True)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    plt.savefig(filename, dpi=300)
    plt.close()

def plot_mesh_3d(nodes: np.ndarray, elements: np.ndarray, filename: str):
    """
    Plots a 3D wireframe of the shell mesh.
    """
    if nodes is None or elements is None:
        return
        
    fig = plt.figure(figsize=(7, 6))
    from mpl_toolkits.mplot3d import Axes3D  # Import for older matplotlib support
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot nodes
    ax.scatter(nodes[:, 0], nodes[:, 1], nodes[:, 2], color='#7f8c8d', s=5, alpha=0.6)
    
    # Plot element edges
    for elem in elements:
        # Loop for boundary drawing
        closed_loop = list(elem[:4]) + [elem[0]] if len(elem) >= 4 else list(elem) + [elem[0]]
        edge_coords = nodes[closed_loop]
        ax.plot(edge_coords[:, 0], edge_coords[:, 1], edge_coords[:, 2], color='#2c3e50', linewidth=0.5, alpha=0.7)
        
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_zlabel('Z (mm)')
    ax.set_title('Malha Discretizada da Casca', fontsize=12, fontweight='bold', pad=15)
    
    try:
        ax.set_box_aspect([np.ptp(nodes[:, 0]), np.ptp(nodes[:, 1]), np.ptp(nodes[:, 2])])
    except:
        pass
        
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    plt.savefig(filename, dpi=300)
    plt.close()
