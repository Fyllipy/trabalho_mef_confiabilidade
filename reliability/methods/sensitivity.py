import numpy as np

class SensitivityAnalysis:
    """
    Roda um estudo paramétrico variando as médias das variáveis aleatórias
    para gerar curvas de sensibilidade do Índice de Confiabilidade (Beta).
    """
    def __init__(self, form_instance):
        self.form = form_instance
        self.rm = form_instance.rm
        
    def run_study(self, var_names: list, variations_pct: list = [-20, -10, -5, 5, 10, 20]):
        """
        Varia a média das variáveis selecionadas em percentuais e avalia o Beta.
        """
        beta_history = {name: [] for name in var_names}
        
        # Armazena as médias originais
        original_means = {name: self.rm.get_variable(name).mean for name in var_names}
        
        # O ponto 0 (sem variação)
        baseline_beta, _, _, _, _ = self.form.run(max_iter=50)
        
        for name in var_names:
            var = self.rm.get_variable(name)
            original = original_means[name]
            
            curve = []
            for pct in variations_pct:
                if pct == 0:
                    curve.append(baseline_beta)
                    continue
                    
                # Aplicar variação
                var.mean = original * (1.0 + pct / 100.0)
                beta, _, _, _, _ = self.form.run(max_iter=50, verbose=False)
                curve.append(beta if beta is not None else 0.0)
                
            # Restaurar original
            var.mean = original
            beta_history[name] = curve
            
        return beta_history
