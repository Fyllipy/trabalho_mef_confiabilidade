import numpy as np

def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred)**2)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    if ss_tot == 0.0:
        return 1.0
    return 1.0 - (ss_res / ss_tot)

def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return np.sqrt(np.mean((y_true - y_pred)**2))

def calculate_mre(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    # Prevenção de divisão por zero
    y_true_safe = np.where(y_true == 0, 1e-12, y_true)
    return np.mean(np.abs((y_true - y_pred) / y_true_safe)) * 100.0

def validate_rsm(y_true: np.ndarray, y_pred: np.ndarray):
    """
    Calcula e imprime as métricas de qualidade do ajuste (R², RMSE, EMR).
    """
    r2 = calculate_r2(y_true, y_pred)
    rmse = calculate_rmse(y_true, y_pred)
    mre = calculate_mre(y_true, y_pred)
    
    print("\n" + "="*45)
    print("VALIDAÇÃO DA SUPERFÍCIE DE RESPOSTA (RSM)")
    print("="*45)
    print(f"R² (Coef. de Determinação): {r2:.4f}")
    print(f"RMSE (Erro Quadrático Médio): {rmse:.4e}")
    print(f"EMR (Erro Médio Relativo):  {mre:.2f}%")
    print("="*45 + "\n")
    
    return r2, rmse, mre
