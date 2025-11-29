"""
Validateur et correcteur LaTeX robuste pour détecter et corriger :
1. Les formules invalides/coupées
2. Les problèmes d'encodage (accents corrompus)
3. Les commandes LaTeX malformées
"""

import re
import unicodedata
from typing import Tuple, List, Dict


class LaTeXValidator:
    """Validateur et correcteur LaTeX complet."""

    # Patterns de formules LaTeX courantes qui doivent être complètes
    LATEX_COMMANDS = [
        r'\\frac',
        r'\\sqrt',
        r'\\int',
        r'\\sum',
        r'\\lim',
        r'\\left',
        r'\\right',
        r'\\begin',
        r'\\end',
    ]

    # Corrections de caractères accentués corrompus
    ACCENT_FIXES = {
        # Corrections courantes d'encodage Latin-1 → UTF-8
        'Ã©': 'é',
        'Ã¨': 'è',
        'Ãª': 'ê',
        'Ã§': 'ç',
        'Ã ': 'à',
        'Ã¢': 'â',
        'Ã´': 'ô',
        'Ã®': 'î',
        'Ã¹': 'ù',
        'Ã»': 'û',
        'Ã«': 'ë',
        'Ã¯': 'ï',
        'Ã¼': 'ü',
        'Ã‰': 'É',
        'Ãˆ': 'È',
        'ÃŠ': 'Ê',
        'Ã‡': 'Ç',
        'Ã€': 'À',
        'Ã‚': 'Â',
        'Ã"': 'Ô',
        'ÃŽ': 'Î',
        'Ã™': 'Ù',
        'Ã›': 'Û',
        # Corrections de mots coupés dans LaTeX
        r'\\exp ression': 'expression',
        r'\\tan gente': 'tangente',
        r'\\lim ite': 'limite',
        r'\\int ervalle': 'intervalle',
        r'\\sum mation': 'sommation',
        r'\\frac tion': 'fraction',
    }

    @staticmethod
    def detect_incomplete_braces(text: str) -> List[Tuple[int, str]]:
        """
        Détecte les accolades non fermées dans le texte.
        Retourne la liste des positions et contextes problématiques.
        """
        issues = []
        stack = []

        for i, char in enumerate(text):
            if char == '{':
                stack.append(i)
            elif char == '}':
                if not stack:
                    # Accolade fermante sans ouvrante
                    context = text[max(0, i-20):min(len(text), i+20)]
                    issues.append((i, f"Accolade fermante sans ouvrante: ...{context}..."))
                else:
                    stack.pop()

        # Accolades ouvertes non fermées
        for pos in stack:
            context = text[max(0, pos-20):min(len(text), pos+20)]
            issues.append((pos, f"Accolade ouvrante non fermée: ...{context}..."))

        return issues

    @staticmethod
    def detect_incomplete_commands(text: str) -> List[Tuple[int, str]]:
        """
        Détecte les commandes LaTeX incomplètes.
        Ex: \\frac{1} sans le deuxième argument, \\sqrt sans accolades, etc.
        """
        issues = []

        # Vérifier \\frac{...}{...}
        frac_pattern = r'\\frac\{[^}]*\}(?!\{)'
        for match in re.finditer(frac_pattern, text):
            pos = match.start()
            context = text[max(0, pos-10):min(len(text), pos+50)]
            issues.append((pos, f"\\frac incomplet (manque 2e argument): {context}"))

        # Vérifier \\sqrt{...}
        sqrt_pattern = r'\\sqrt(?!\{|\[)'
        for match in re.finditer(sqrt_pattern, text):
            pos = match.start()
            context = text[max(0, pos-10):min(len(text), pos+30)]
            issues.append((pos, f"\\sqrt incomplet (manque accolades): {context}"))

        # Vérifier \\left sans \\right
        left_positions = [m.start() for m in re.finditer(r'\\left[\(\[\{]', text)]
        right_positions = [m.start() for m in re.finditer(r'\\right[\)\]\}]', text)]

        if len(left_positions) != len(right_positions):
            issues.append((0, f"Déséquilibre \\left/\\right: {len(left_positions)} left vs {len(right_positions)} right"))

        # Vérifier \\begin{...} sans \\end{...}
        begin_envs = re.findall(r'\\begin\{(\w+)\}', text)
        end_envs = re.findall(r'\\end\{(\w+)\}', text)

        for env in set(begin_envs):
            if begin_envs.count(env) != end_envs.count(env):
                issues.append((0, f"Déséquilibre \\begin{{'{env}'}}/\\end{{'{env}'}}: {begin_envs.count(env)} begin vs {end_envs.count(env)} end"))

        return issues

    @staticmethod
    def detect_malformed_math_mode(text: str) -> List[Tuple[int, str]]:
        """
        Détecte les modes mathématiques mal formés.
        Ex: $ non fermé, \\[ sans \\], etc.
        """
        issues = []

        # Compter les $ (doivent être pairs)
        dollar_count = text.count('$')
        if dollar_count % 2 != 0:
            issues.append((0, f"Nombre impair de $ ({dollar_count}): mode mathématique non fermé"))

        # Vérifier \\[ ... \\]
        display_open = text.count('\\[')
        display_close = text.count('\\]')
        if display_open != display_close:
            issues.append((0, f"Déséquilibre \\[/\\]: {display_open} ouvertures vs {display_close} fermetures"))

        return issues

    @classmethod
    def validate_latex(cls, text: str) -> Tuple[bool, List[str]]:
        """
        Valide le code LaTeX et retourne (is_valid, list_of_errors).

        Returns:
            (True, []) si valide
            (False, [liste des erreurs]) si invalide
        """
        all_issues = []

        # 1. Vérifier les accolades
        brace_issues = cls.detect_incomplete_braces(text)
        all_issues.extend([msg for _, msg in brace_issues])

        # 2. Vérifier les commandes incomplètes
        cmd_issues = cls.detect_incomplete_commands(text)
        all_issues.extend([msg for _, msg in cmd_issues])

        # 3. Vérifier les modes mathématiques
        math_issues = cls.detect_malformed_math_mode(text)
        all_issues.extend([msg for _, msg in math_issues])

        is_valid = len(all_issues) == 0
        return is_valid, all_issues

    @classmethod
    def fix_encoding(cls, text: str) -> str:
        """
        Corrige les problèmes d'encodage courants (accents corrompus).
        """
        # Normaliser en NFD puis NFC pour gérer les combinaisons Unicode
        try:
            text = unicodedata.normalize('NFC', text)
        except Exception:
            pass

        # Appliquer les corrections de caractères corrompus
        for corrupt, correct in cls.ACCENT_FIXES.items():
            text = text.replace(corrupt, correct)

        return text

    @classmethod
    def fix_latex_commands(cls, text: str) -> str:
        """
        Corrige automatiquement les commandes LaTeX malformées courantes.
        """
        fixes = [
            # Doubles backslashes devant les commandes (sauf \\ pour saut de ligne)
            (r'\\\\([a-zA-Z])', r'\\\1'),

            # Commandes sans backslash
            (r'\bfrac\{', r'\\frac{'),
            (r'\bsqrt\{', r'\\sqrt{'),
            (r'\bint_', r'\\int_'),
            (r'\bsum_', r'\\sum_'),
            (r'\blim_', r'\\lim_'),

            # Fonctions trigonométriques sans backslash
            (r'\bsin\s*\(', r'\\sin('),
            (r'\bcos\s*\(', r'\\cos('),
            (r'\btan\s*\(', r'\\tan('),
            (r'\bln\s*\(', r'\\ln('),
            (r'\bexp\s*\(', r'\\exp('),

            # left/right incomplets
            (r'left\(', r'\\left('),
            (r'right\)', r'\\right)'),
            (r'left\[', r'\\left['),
            (r'right\]', r'\\right]'),
            (r'left\{', r'\\left\\{'),
            (r'right\}', r'\\right\\}'),

            # Symboles mathématiques
            (r'\binfty\b', r'\\infty'),
            (r'\bto\b(?=\s*[\+\-\d])', r'\\to'),
            (r'geq\s', r'\\geq '),
            (r'leq\s', r'\\leq '),
            (r'neq', r'\\neq'),

            # Espaces dans les commandes mathématiques (fracn m → frac{n}{m})
            (r'\\frac\s+(\w+)\s+(\w+)', r'\\frac{\1}{\2}'),
        ]

        for pattern, replacement in fixes:
            text = re.sub(pattern, replacement, text)

        return text

    @classmethod
    def auto_fix_incomplete_frac(cls, text: str) -> str:
        """
        Tente de corriger automatiquement les \\frac incomplets.
        Ex: \\frac{1} 3 → \\frac{1}{3}
        """
        # Pattern: \\frac{...} suivi d'un espace et d'une expression simple
        pattern = r'\\frac\{([^}]+)\}\s+([a-zA-Z0-9\+\-\*]+)'

        def replacer(match):
            numerator = match.group(1)
            denominator = match.group(2)
            return f'\\frac{{{numerator}}}{{{denominator}}}'

        text = re.sub(pattern, replacer, text)
        return text

    @classmethod
    def auto_fix_all(cls, text: str) -> str:
        """
        Applique toutes les corrections automatiques dans l'ordre.
        """
        # 1. Corriger l'encodage
        text = cls.fix_encoding(text)

        # 2. Corriger les commandes LaTeX
        text = cls.fix_latex_commands(text)

        # 3. Corriger les fractions incomplètes
        text = cls.auto_fix_incomplete_frac(text)

        return text

    @classmethod
    def validate_and_fix(cls, text: str, max_attempts: int = 3) -> Tuple[str, bool, List[str]]:
        """
        Valide et tente de corriger le LaTeX automatiquement.

        Returns:
            (corrected_text, is_valid, remaining_errors)
        """
        current_text = text

        for attempt in range(max_attempts):
            # Appliquer les corrections
            current_text = cls.auto_fix_all(current_text)

            # Valider
            is_valid, errors = cls.validate_latex(current_text)

            if is_valid:
                return current_text, True, []

            # Si toujours invalide après max_attempts, retourner le dernier état
            if attempt == max_attempts - 1:
                return current_text, False, errors

        return current_text, False, errors


# ============================================================================
# FONCTION UTILITAIRE POUR L'API
# ============================================================================

def clean_latex_response(latex_text: str, strict: bool = False) -> Dict[str, any]:
    """
    Nettoie et valide une réponse LaTeX de l'API.

    Args:
        latex_text: Le code LaTeX à nettoyer
        strict: Si True, refuse le texte si des erreurs persistent après correction

    Returns:
        Dict avec:
            - "latex": le texte corrigé
            - "is_valid": True si valide
            - "errors": liste des erreurs détectées
            - "was_corrected": True si des corrections ont été appliquées
    """
    original_text = latex_text

    # Appliquer les corrections
    corrected_text, is_valid, errors = LaTeXValidator.validate_and_fix(latex_text)

    was_corrected = (corrected_text != original_text)

    if strict and not is_valid:
        raise ValueError(f"LaTeX invalide après correction: {errors}")

    return {
        "latex": corrected_text,
        "is_valid": is_valid,
        "errors": errors,
        "was_corrected": was_corrected
    }


# ============================================================================
# TESTS
# ============================================================================

if __name__ == "__main__":
    # Tests d'exemple
    print("=== Tests du validateur LaTeX ===\n")

    # Test 1: Accents corrompus
    test1 = "Calculer la dÃ©rivÃ©e de la fonction $f(x) = x^2$"
    print(f"Test 1 (accents): {test1}")
    result1 = clean_latex_response(test1)
    print(f"Résultat: {result1['latex']}")
    print(f"Valide: {result1['is_valid']}, Corrigé: {result1['was_corrected']}\n")

    # Test 2: Commandes malformées
    test2 = r"Soit $frac{1}{2} + sqrt{3}$"
    print(f"Test 2 (commandes): {test2}")
    result2 = clean_latex_response(test2)
    print(f"Résultat: {result2['latex']}")
    print(f"Valide: {result2['is_valid']}, Corrigé: {result2['was_corrected']}\n")

    # Test 3: Frac incomplet
    test3 = r"La fraction \frac{1} 3 est égale à..."
    print(f"Test 3 (frac incomplet): {test3}")
    result3 = clean_latex_response(test3)
    print(f"Résultat: {result3['latex']}")
    print(f"Valide: {result3['is_valid']}, Corrigé: {result3['was_corrected']}\n")

    # Test 4: Accolades non fermées
    test4 = r"Soit $f(x) = \frac{1{2}$"
    print(f"Test 4 (accolades): {test4}")
    result4 = clean_latex_response(test4)
    print(f"Résultat: {result4['latex']}")
    print(f"Valide: {result4['is_valid']}")
    if not result4['is_valid']:
        print(f"Erreurs: {result4['errors']}\n")
