import numpy as np
from typing import Dict, Any, Union

def calculate_scalar_metrics(mef_val: float, ref_val: float) -> Dict[str, float]:
    """
    Computes standard error metrics for two scalar quantities.
    """
    abs_err = abs(mef_val - ref_val)
    rel_err = abs_err / abs(ref_val) if abs(ref_val) > 1e-15 else 0.0
    return {
        "mef_value": mef_val,
        "reference_value": ref_val,
        "absolute_error": abs_err,
        "relative_error_percent": rel_err * 100.0
    }

def calculate_field_metrics(mef_arr: np.ndarray, ref_arr: np.ndarray) -> Dict[str, Any]:
    """
    Computes spatial field error metrics between custom solver and Abaqus reference fields.
    """
    mef = np.asarray(mef_arr)
    ref = np.asarray(ref_arr)
    
    if mef.shape != ref.shape:
        return {
            "error_msg": f"Shape mismatch: solver shape {mef.shape} vs. reference shape {ref.shape}"
        }
        
    n = mef.size
    if n == 0:
        return {"error_msg": "Arrays are empty"}
        
    diff = mef - ref
    
    abs_diff = np.abs(diff)
    abs_ref = np.abs(ref)
    
    mae = np.mean(abs_diff)
    rmse = np.sqrt(np.mean(diff ** 2))
    
    # Norms
    norm_l2_diff = np.linalg.norm(diff.ravel())
    norm_l2_ref = np.linalg.norm(ref.ravel())
    rel_l2_error = norm_l2_diff / norm_l2_ref if norm_l2_ref > 1e-15 else 0.0
    
    norm_linf_diff = np.max(abs_diff)
    norm_linf_ref = np.max(abs_ref)
    rel_linf_error = norm_linf_diff / norm_linf_ref if norm_linf_ref > 1e-15 else 0.0
    
    # Peak error
    mef_max = np.max(np.abs(mef))
    ref_max = np.max(np.abs(ref))
    peak_relative_error = abs(mef_max - ref_max) / ref_max if ref_max > 1e-15 else 0.0
    
    # Pearson Correlation Coefficient (r)
    std_mef = np.std(mef)
    std_ref = np.std(ref)
    if std_mef > 1e-15 and std_ref > 1e-15:
        r = np.corrcoef(mef.ravel(), ref.ravel())[0, 1]
    else:
        r = 1.0 if np.allclose(mef, ref) else 0.0
        
    # R² Coefficient
    ss_res = np.sum(diff ** 2)
    ref_mean = np.mean(ref)
    ss_tot = np.sum((ref - ref_mean) ** 2)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-15 else 1.0
    
    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "relative_l2_error": float(rel_l2_error),
        "relative_l2_error_percent": float(rel_l2_error * 100.0),
        "relative_linf_error": float(rel_linf_error),
        "relative_linf_error_percent": float(rel_linf_error * 100.0),
        "peak_relative_error_percent": float(peak_relative_error * 100.0),
        "pearson_correlation": float(r),
        "r2_coefficient": float(r2)
    }
