import numpy as np
from .base import ResponseSurface

class LinearRSM(ResponseSurface):
    def _build_design_matrix(self, X: np.ndarray) -> np.ndarray:
        if X.ndim == 1:
            X = X.reshape(1, -1)
        n_samples, n_vars = X.shape
        # Coluna de 1s para o intercepto + as próprias variáveis
        return np.hstack((np.ones((n_samples, 1)), X))
        
    def fit(self, X: np.ndarray, Y: np.ndarray):
        D = self._build_design_matrix(X)
        self.coefficients, _, _, _ = np.linalg.lstsq(D, Y, rcond=None)
        self.is_fitted = True
        
    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("O modelo ainda não foi ajustado (chame fit primeiro).")
        D = self._build_design_matrix(X)
        return D @ self.coefficients
        
    def gradient(self, X: np.ndarray) -> np.ndarray:
        # y = b0 + b1*x1 + b2*x2
        # dy/dx = [b1, b2]
        return self.coefficients[1:]

class QuadraticPureRSM(LinearRSM):
    def _build_design_matrix(self, X: np.ndarray) -> np.ndarray:
        if X.ndim == 1:
            X = X.reshape(1, -1)
        n_samples, n_vars = X.shape
        
        linear_part = np.hstack((np.ones((n_samples, 1)), X))
        quad_part = X**2
        return np.hstack((linear_part, quad_part))
        
    def gradient(self, X: np.ndarray) -> np.ndarray:
        if X.ndim == 2 and X.shape[0] == 1:
            X = X[0]
        n_vars = len(X)
        # coeffs = [b0, b1, b2, c1, c2, ...]
        b = self.coefficients[1 : 1 + n_vars]
        c = self.coefficients[1 + n_vars : 1 + 2 * n_vars]
        # dy/dx_i = b_i + 2 * c_i * x_i
        return b + 2.0 * c * X

class QuadraticFullRSM(QuadraticPureRSM):
    def _build_design_matrix(self, X: np.ndarray) -> np.ndarray:
        if X.ndim == 1:
            X = X.reshape(1, -1)
        n_samples, n_vars = X.shape
        
        D_pure = super()._build_design_matrix(X)
        
        cross_terms = []
        for i in range(n_vars):
            for j in range(i + 1, n_vars):
                cross_terms.append(X[:, i] * X[:, j])
                
        if cross_terms:
            cross_matrix = np.column_stack(cross_terms)
            return np.hstack((D_pure, cross_matrix))
        return D_pure
        
    def gradient(self, X: np.ndarray) -> np.ndarray:
        if X.ndim == 2 and X.shape[0] == 1:
            X = X.flatten()
        n_vars = len(X)
        
        grad = super().gradient(X)
        
        # Cross terms coefficients start after pure quadratic
        cross_start = 1 + 2 * n_vars
        cross_coeffs = self.coefficients[cross_start:]
        
        idx = 0
        for i in range(n_vars):
            for j in range(i + 1, n_vars):
                coeff = cross_coeffs[idx]
                grad[i] += coeff * X[j]
                grad[j] += coeff * X[i]
                idx += 1
                
        return grad
