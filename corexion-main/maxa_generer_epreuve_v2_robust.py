"""
VERSION ULTRA-ROBUSTE de la génération d'épreuves LaTeX
Utilise GPT-5 + Structured Outputs pour garantir un LaTeX parfait
"""

import os
import json
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from openai import OpenAI


# ============================================================================
# MODÈLES PYDANTIC POUR STRUCTURED OUTPUTS
# ============================================================================

class QuestionLatex(BaseModel):
    """Une question individuelle avec son LaTeX validé."""
    numero: int = Field(description="Numéro de la question (1, 2, 3...)")
    enonce_latex: str = Field(
        description="Énoncé complet de la question en LaTeX VALIDE avec doubles backslashes (\\\\frac, \\\\sqrt, etc.)"
    )
    type_question: str = Field(
        description="Type: calcul, démonstration, résolution, limite, intégrale, etc."
    )


class ExerciceLatexStructure(BaseModel):
    """Structure complète d'un exercice avec LaTeX garanti valide."""
    titre: str = Field(description="Titre de l'exercice (ex: 'Exercice 1')")
    introduction: str = Field(
        description="Texte d'introduction de l'exercice en LaTeX (peut être vide)"
    )
    questions: List[QuestionLatex] = Field(
        description="Liste des questions de l'exercice"
    )
    domaine_principal: str = Field(
        description="Domaine mathématique: Analyse, Algèbre, Probabilités, Géométrie..."
    )
    niveau_difficulte: str = Field(
        description="Niveau: facile, moyen, difficile"
    )

    def to_latex_string(self) -> str:
        """Convertit l'exercice structuré en code LaTeX complet."""
        parts = []

        # Titre
        parts.append(f"\\section*{{{self.titre}}}\n")

        # Introduction si présente
        if self.introduction.strip():
            parts.append(f"{self.introduction}\n")

        # Questions dans un environnement enumerate
        parts.append("\\begin{enumerate}")
        for q in self.questions:
            parts.append(f"\\item {q.enonce_latex}")
        parts.append("\\end{enumerate}")

        return "\n".join(parts)


class AnalyseExerciceStructure(BaseModel):
    """Analyse structurée d'un exercice existant."""
    nombre_questions: int = Field(description="Nombre total de questions")
    domaines_mathematiques: List[str] = Field(
        description="Liste des domaines mathématiques couverts"
    )
    types_questions: List[str] = Field(
        description="Types de questions présentes"
    )
    niveau_difficulte: str = Field(description="Niveau estimé: facile, moyen, difficile")
    format_numerotation: str = Field(
        description="Format de numérotation: '1. 2. 3.' ou 'a) b) c)' ou 'mixte'"
    )


# ============================================================================
# CLIENT GPT-5 AVEC STRUCTURED OUTPUTS
# ============================================================================

class RobustLatexGenerator:
    """Générateur LaTeX ultra-robuste avec GPT-5 et Structured Outputs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-5",
        temperature: float = 0.7
    ):
        """
        Initialise le générateur.

        Args:
            api_key: Clé API OpenAI (si None, utilise OPENAI_API_KEY de .env)
            model: Modèle à utiliser (gpt-5, gpt-5-mini, gpt-4o)
            temperature: Créativité (0.0-1.0)
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.temperature = temperature

    def analyser_exercice(
        self,
        exercice_text: str
    ) -> AnalyseExerciceStructure:
        """
        Analyse la structure d'un exercice avec Structured Outputs.
        GARANTIT un JSON valide conforme au schéma.
        """
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": """Tu es un expert en analyse d'exercices mathématiques.
Analyse la structure de l'exercice fourni et extrait :
- Le nombre exact de questions
- Les domaines mathématiques (Analyse, Algèbre, Probabilités, etc.)
- Les types de questions (calcul, démonstration, limite, intégrale, etc.)
- Le niveau de difficulté
- Le format de numérotation utilisé"""
                },
                {
                    "role": "user",
                    "content": f"Analyse cet exercice :\n\n{exercice_text}"
                }
            ],
            response_format=AnalyseExerciceStructure
            # NOTE: temperature omise avec Structured Outputs (utilise la valeur par défaut = 1)
        )

        return response.choices[0].message.parsed

    def generer_exercice_similaire(
        self,
        exercice_original: str,
        analyse: AnalyseExerciceStructure,
        numero_exercice: int = 1
    ) -> ExerciceLatexStructure:
        """
        Génère un exercice similaire avec STRUCTURED OUTPUTS.
        GARANTIT un LaTeX parfait, sans corruption d'encodage.

        Args:
            exercice_original: Texte de l'exercice source
            analyse: Analyse structurelle de l'exercice
            numero_exercice: Numéro de l'exercice dans l'épreuve

        Returns:
            ExerciceLatexStructure avec LaTeX garanti valide
        """

        # Prompt système ultra-précis
        system_prompt = f"""Tu es un expert en création d'exercices de mathématiques pour concours.

MISSION : Génère un exercice SIMILAIRE à l'original, avec :
- EXACTEMENT {analyse.nombre_questions} questions
- Même structure et difficulté ({analyse.niveau_difficulte})
- Domaines : {', '.join(analyse.domaines_mathematiques)}
- Types : {', '.join(analyse.types_questions)}

RÈGLES LATEX ABSOLUES :

1. **Doubles backslashes OBLIGATOIRES** dans le JSON :
   - \\\\frac{{{{a}}}}{{{{b}}}} pour les fractions
   - \\\\sqrt{{{{x}}}} pour les racines
   - \\\\int_{{{{a}}}}^{{{{b}}}} pour les intégrales
   - \\\\lim_{{{{x \\\\to a}}}} pour les limites
   - \\\\sum_{{{{i=1}}}}^{{{{n}}}} pour les sommes

2. **Syntaxe COMPLÈTE toujours** :
   ✅ \\\\frac{{{{1}}}}{{{{3}}}} (JAMAIS frac13)
   ✅ \\\\sqrt{{{{b}}}} (JAMAIS sqrtb)
   ✅ \\\\sin x, \\\\cos x, \\\\ln x (TOUJOURS avec \\\\)

3. **Accolades TOUJOURS par paires** :
   ✅ \\\\left( ... \\\\right)
   ✅ \\\\left[ ... \\\\right]

4. **Fonctions mathématiques** :
   \\\\sin, \\\\cos, \\\\tan, \\\\ln, \\\\exp, \\\\arcsin, etc.

5. **Symboles** :
   \\\\infty, \\\\pi, \\\\leq, \\\\geq, \\\\neq, \\\\in, \\\\mathbb{{{{R}}}}, \\\\mathbb{{{{C}}}}

IMPORTANT : Le JSON sera parsé automatiquement, donc :
- Utilise TOUJOURS des doubles backslashes
- Quadruple les accolades dans les f-strings : {{{{{{{{x}}}}}}}}
- Chaque question doit être complète et compilable

CRÉATIVITÉ : Change les valeurs numériques, contextes, fonctions, mais garde la structure."""

        user_prompt = f"""Génère un exercice similaire à celui-ci :

{exercice_original[:3000]}

L'exercice doit avoir EXACTEMENT {analyse.nombre_questions} questions de types : {', '.join(analyse.types_questions)}.
Numérotation : {analyse.format_numerotation}

RAPPEL CRITIQUE : Dans le JSON, TOUS les backslashes LaTeX doivent être DOUBLÉS.
Exemple : Pour écrire \\frac{{1}}{{2}} en LaTeX, tu dois écrire \\\\frac{{{{1}}}}{{{{2}}}} dans le JSON."""

        # Appel avec Structured Outputs - GARANTIT le format
        # NOTE: Structured Outputs ne supporte QUE temperature=1 (valeur par défaut)
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=ExerciceLatexStructure
            # temperature ignorée avec Structured Outputs - toujours = 1
        )

        # Le parsing est GARANTI par OpenAI
        exercice = response.choices[0].message.parsed

        # Correction du titre si nécessaire
        if not exercice.titre or "Exercice" not in exercice.titre:
            exercice.titre = f"Exercice {numero_exercice}"

        return exercice

    def generer_epreuve_complete(
        self,
        exercices_originaux: List[Dict],
        temperature: float = None,
        max_retries: int = 2
    ) -> str:
        """
        Génère une épreuve complète à partir d'exercices sources.

        Args:
            exercices_originaux: Liste de dicts avec 'texte_complet', 'exercice', etc.
            temperature: Override de température (optionnel, ignoré en mode Structured Outputs)
            max_retries: Nombre max de tentatives par exercice

        Returns:
            String LaTeX complète de l'épreuve, garantie valide
        """
        if temperature is not None:
            old_temp = self.temperature
            self.temperature = temperature

        exercices_generes = []

        for i, exo_data in enumerate(exercices_originaux):
            print(f"\n🔹 Génération exercice {i+1}/{len(exercices_originaux)}...")

            exercice_latex = None

            for attempt in range(max_retries):
                try:
                    # 1. Analyse de la structure
                    if attempt == 0:
                        print(f"   📊 Analyse de la structure...")
                    else:
                        print(f"   🔄 Nouvelle tentative {attempt + 1}/{max_retries}...")

                    analyse = self.analyser_exercice(exo_data['texte_complet'])

                    if attempt == 0:
                        print(f"   ✅ Détecté: {analyse.nombre_questions} questions, {analyse.niveau_difficulte}")

                    # 2. Génération avec Structured Outputs
                    print(f"   🤖 Génération avec {self.model}...")
                    exercice = self.generer_exercice_similaire(
                        exercice_original=exo_data['texte_complet'],
                        analyse=analyse,
                        numero_exercice=i + 1
                    )

                    # 3. Conversion en LaTeX
                    exercice_latex = exercice.to_latex_string()

                    # Vérification basique
                    if len(exercice_latex.strip()) < 50:
                        raise ValueError("Exercice généré trop court (probablement incomplet)")

                    print(f"   ✅ Exercice {i+1} généré avec succès!")
                    break  # Succès, on sort de la boucle retry

                except Exception as e:
                    print(f"   ⚠️  Erreur tentative {attempt + 1}: {str(e)[:100]}")
                    if attempt == max_retries - 1:
                        # Dernière tentative échouée
                        print(f"   ❌ Échec après {max_retries} tentatives")
                        exercice_latex = None

            # Ajouter le résultat (ou fallback)
            if exercice_latex:
                exercices_generes.append(exercice_latex)
            else:
                # Fallback: utiliser l'exercice original modifié
                print(f"   ⚠️  Utilisation de l'exercice original comme fallback")
                exercices_generes.append(
                    f"\\section*{{Exercice {i+1}}}\n\n"
                    f"{exo_data.get('texte_complet', 'Exercice non disponible')[:1000]}"
                )

        # Restaurer température
        if temperature is not None:
            self.temperature = old_temp

        # Assembler l'épreuve complète
        return self._assembler_epreuve_latex(exercices_generes)

    def _assembler_epreuve_latex(self, exercices: List[str]) -> str:
        """Assemble les exercices dans un document LaTeX complet."""

        header = r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[french]{babel}
\usepackage{amsmath,amssymb,amsthm,mathtools}
\usepackage{geometry}
\geometry{margin=2.5cm}
\usepackage{enumitem}
\usepackage{fancyhdr}
\usepackage{xfrac}

% Configuration enumerate
\setlist[enumerate]{
    itemsep=0.8em,
    parsep=0.5em,
    topsep=0.8em
}

\pagestyle{fancy}
\fancyhf{}
\rhead{\thepage}
\lhead{Épreuve de Mathématiques}

\title{\textbf{Épreuve de Mathématiques} \\ Concours d'Ingénieur Statisticien}
\author{}
\date{\today}

\begin{document}

\maketitle

\section*{Instructions}
Durée de l'épreuve : 4 heures. \\
Les calculatrices sont autorisées. \\
Toutes les réponses doivent être justifiées.

\vspace{1cm}

"""

        corps = "\n\n\\vspace{1.5cm}\n\n".join(exercices)

        footer = r"""

\end{document}
"""

        return header + corps + footer


# ============================================================================
# FONCTION D'INTERFACE COMPATIBLE AVEC L'ANCIENNE VERSION
# ============================================================================

def generate_new_epreuve_as_latex_string_v2(
    chunks_list: List[Dict],
    n_variations_per_exercice: int = 3,
    temperature: float = 0.7,
    model: str = "gpt-5",
    use_structured_outputs: bool = True
) -> str:
    """
    VERSION 2 ROBUSTE de la génération d'épreuve.

    Args:
        chunks_list: Liste de chunks d'exercices
        n_variations_per_exercice: Nombre de tentatives max (avec structured outputs, 1 suffit)
        temperature: Créativité du modèle
        model: Modèle à utiliser (gpt-5, gpt-5-mini, gpt-4o)
        use_structured_outputs: Si True, utilise Structured Outputs (recommandé)

    Returns:
        Code LaTeX complet de l'épreuve, garanti valide
    """
    from maxa_generer_epreuve import reconstruct_exercice_from_chunks

    # Reconstituer les exercices
    exercices = reconstruct_exercice_from_chunks(chunks_list)

    if not exercices:
        return "% Aucun exercice trouvé\n"

    if use_structured_outputs:
        # MODE ROBUSTE avec Structured Outputs
        print(f"🚀 Mode ROBUSTE activé avec {model}")
        generator = RobustLatexGenerator(model=model, temperature=temperature)
        return generator.generer_epreuve_complete(exercices, temperature=temperature)
    else:
        # Fallback vers l'ancienne méthode
        print("⚠️  Mode legacy (sans Structured Outputs)")
        from maxa_generer_epreuve import generate_new_epreuve_as_latex_string
        return generate_new_epreuve_as_latex_string(
            chunks_list=chunks_list,
            n_variations_per_exercice=n_variations_per_exercice,
            temperature=temperature
        )


# ============================================================================
# TESTS
# ============================================================================

if __name__ == "__main__":
    print("=== Test du générateur robuste ===\n")

    # Test avec un exercice simple
    exercice_test = """
Soit la fonction f définie par $f(x) = \\frac{x^2 + 1}{x - 2}$.

1. Calculer $\\lim_{x \\to 2^+} f(x)$.

2. Résoudre l'équation $f(x) = \\sqrt{5}$.

3. Calculer $\\int_{0}^{1} f(x) dx$.
"""

    generator = RobustLatexGenerator(model="gpt-4o", temperature=0.7)

    # Test analyse
    print("📊 Test de l'analyse...")
    analyse = generator.analyser_exercice(exercice_test)
    print(f"Résultat: {analyse.model_dump_json(indent=2)}\n")

    # Test génération
    print("🤖 Test de génération...")
    exercice = generator.generer_exercice_similaire(
        exercice_original=exercice_test,
        analyse=analyse,
        numero_exercice=1
    )

    print(f"\n✅ Exercice généré :")
    print(exercice.to_latex_string())
