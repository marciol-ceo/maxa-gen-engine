
import os
import json
import re
from typing import List, Dict, Optional
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from maxa_get_meta import get_random_metadata_from_one_random_namespace
from maxa_latex_validator import LaTeXValidator, clean_latex_response







def nettoyer_et_formater_latex(texte):
    """
    Nettoie la syntaxe LaTeX et reformate le texte pour ajouter des retours à la ligne
    devant les questions et sous-questions.
    """
    
    # --- ÉTAPE 1 : Corrections de syntaxe (nettoyage brut) ---
    
    # 1. Correction des mots coupés ou faux-amis identifiés
    remplacements_mots = {
        r'\frac{tion': 'fraction',
        r'\limites': 'limites',
        r'\limite': 'limite',
        r'\intervalle': 'intervalle',
        r'\r\right': r'\right',
        # Correction spécifique pour l'exercice 2 où \neq et \sin sont mal formés
        r'\\neq': r'\neq',
        r'\\sin': r'\sin',
        r'\\cos': r'\cos',
        r'\\le': r'\le',
        r'\\ge': r'\ge',
        r'\\sum': r'\sum',
        r'\\int': r'\int',
        r'\\infty': r'\infty',
        r'\\left': r'\left',
        r'\\right': r'\right'
    }
    
    for erreur, correction in remplacements_mots.items():
        texte = texte.replace(erreur, correction)

    # 2. Nettoyage général des doubles backslashes devant les lettres
    # Transforme "\\commande" en "\commande", mais ne touche pas à "\\" (saut de ligne LaTeX)
    texte = re.sub(r'\\\\([a-zA-Z])', r'\\\1', texte)


    # --- ÉTAPE 2 : Mise en forme et retours à la ligne ---

    # 1. Forcer le saut de ligne avant \item
    texte = re.sub(r'\s*\\item', r'\n\\item', texte)

    # 2. Gestion des maths hors-texte \[ ... \]
    # Mettre \[ sur une nouvelle ligne
    texte = re.sub(r'(?<!\n)\\\[', r'\n\\[', texte)
    # Mettre \] sur une nouvelle ligne et forcer le texte suivant à la ligne
    texte = re.sub(r'\\\]\s*', r'\\]\n', texte)

    # 3. Détecter les numérotations manuelles type "1.", "2." etc.
    # On cherche : un espace ou saut de ligne, un chiffre, un point, un espace
    # Le (?<=\s) assure qu'on ne coupe pas un nombre décimal comme 3.14
    texte = re.sub(r'(?<=\s)(\d+\.)\s+', r'\n\1 ', texte)

    # 4. Détecter les sous-questions type "(a)", "(b)", etc.
    # On cherche : espace, parenthèse, lettre, parenthèse
    texte = re.sub(r'\s+(\([a-z]\))\s', r'\n\1 ', texte)

    # 5. Nettoyer les espaces excessifs autour des sections
    texte = re.sub(r'\s*\\section\*', r'\n\n\\section*', texte)
    texte = re.sub(r'\s*\\begin\{enumerate\}', r'\n\\begin{enumerate}', texte)
    texte = re.sub(r'\s*\\end\{enumerate\}', r'\n\\end{enumerate}', texte)

    return texte.strip()



# ============================================================================
# MODÈLES PYDANTIC POUR LA STRUCTURE
# ============================================================================

class ExerciceStructure(BaseModel):
    """Structure analysée d'un exercice"""
    nombre_questions: int = Field(description="Nombre total de questions")
    domaines_mathematiques: List[str] = Field(description="Domaines couverts (analyse, algèbre, probabilités, etc.)")
    types_questions: List[str] = Field(description="Types de questions (calcul, démonstration, résolution, etc.)")
    niveau_difficulte: str = Field(description="Niveau estimé (facile, moyen, difficile)")
    notations_utilisees: List[str] = Field(description="Notations mathématiques spécifiques")
    format_reponses: List[str] = Field(description="Formats attendus pour chaque question")


class NouvelExercice(BaseModel):
    """Exercice généré"""
    titre: str = Field(description="Titre de l'exercice (ex: Exercice n° 1)")
    enonce_complet: str = Field(description="Énoncé complet de l'exercice en LaTeX")
    domaine_principal: str = Field(description="Domaine mathématique principal")
    difficulte: str = Field(description="Niveau de difficulté")


# ============================================================================
# FONCTION 1 : RECONSTITUER L'EXERCICE COMPLET
# ============================================================================

def reconstruct_exercice_from_chunks(chunks_list: List[Dict]) -> Dict:
    """
    Reconstitue l'exercice complet à partir de la liste de chunks.
    
    Args:
        chunks_list: Liste de dicts avec chunk_text, chunk_index, exercice, epreuve, date
        
    Returns:
        Dict avec exercice_number, texte_complet, epreuve, date, nombre_chunks
    """
    if not chunks_list:
        return {}
    
    # Regrouper par exercice
    exercices = {}
    
    for chunk in chunks_list:
        exercice_num = chunk['exercice']
        
        if exercice_num not in exercices:
            exercices[exercice_num] = {
                'exercice': exercice_num,
                'epreuve': chunk['epreuve'],
                'date': chunk['date'],
                'chunks': []
            }
        
        exercices[exercice_num]['chunks'].append({
            'index': chunk['chunk_index'],
            'text': chunk['chunk_text']
        })
    
    # Reconstituer le texte complet pour chaque exercice
    exercices_complets = []
    
    for exercice_num, data in exercices.items():
        # Trier les chunks par index
        sorted_chunks = sorted(data['chunks'], key=lambda x: x['index'])
        
        # Concaténer le texte
        texte_complet = '\n\n'.join([chunk['text'] for chunk in sorted_chunks])
        
        exercices_complets.append({
            'exercice': exercice_num,
            'texte_complet': texte_complet,
            'epreuve': data['epreuve'],
            'date': data['date'],
            'nombre_chunks': len(sorted_chunks)
        })
    
    return exercices_complets


# ============================================================================
# FONCTION 2 : ANALYSER LA STRUCTURE DE L'EXERCICE
# ============================================================================

def analyze_exercice_structure(
    exercice_text: str,
    llm: Optional[ChatOpenAI] = None
) -> ExerciceStructure:
    """
    Analyse la structure d'un exercice pour en extraire les patterns.
    
    Args:
        exercice_text: Texte complet de l'exercice
        llm: Modèle LLM (si None, utilise gpt-4o-mini par défaut)
        
    Returns:
        ExerciceStructure avec l'analyse détaillée
    """
    if llm is None:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    # Prompt système pour l'analyse
    system_prompt = """Tu es un expert en analyse d'exercices de mathématiques pour concours d'ingénieurs statistiques.

Ton rôle est d'analyser en profondeur la STRUCTURE d'un exercice pour identifier :
1. Le nombre exact de questions/sous-questions
2. Les domaines mathématiques couverts (analyse, algèbre, probabilités, géométrie, etc.)
3. Les types de questions (calcul direct, démonstration, résolution d'équation, limite, intégrale, etc.)
4. Le niveau de difficulté global
5. Les notations mathématiques spécifiques utilisées (Ln, lim, intégrales, etc.)
6. Le format attendu des réponses

TU DOIS ABSOLUMENT répondre UNIQUEMENT avec un JSON valide contenant ces champs, sans aucun texte avant ou après.

Exemple de réponse attendue :
{{
  "nombre_questions": 10,
  "domaines_mathematiques": ["Analyse", "Algèbre"],
  "types_questions": ["Calcul de limite", "Résolution d'équation"],
  "niveau_difficulte": "Moyen",
  "notations_utilisees": ["$\\operatorname{{Ln}}$", "$\\lim$"],
  "format_reponses": ["Valeur numérique", "Fraction"]
}}"""

    human_prompt = """Analyse la structure de cet exercice de mathématiques :

{exercice_text}

IMPORTANT : Réponds UNIQUEMENT avec un JSON valide suivant exactement ce format :
{{
  "nombre_questions": <nombre de questions>,
  "domaines_mathematiques": [<liste des domaines en texte simple>],
  "types_questions": [<liste des types de questions en texte simple>],
  "niveau_difficulte": "<facile/moyen/difficile>",
  "notations_utilisees": [<liste des notations EN TEXTE SIMPLE, par exemple "Ln", "limite", "integrale">],
  "format_reponses": [<liste des formats attendus>]
}}

ATTENTION : N'utilise PAS de notations LaTeX (comme $\\operatorname{{Ln}}$) dans le JSON.
Utilise seulement du texte simple (comme "Ln", "limite", "integrale").

NE METS RIEN D'AUTRE QUE LE JSON."""

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        HumanMessagePromptTemplate.from_template(human_prompt)
    ])
    
    # Essayer avec le parser Pydantic
    try:
        parser = PydanticOutputParser(pydantic_object=ExerciceStructure)
        chain = prompt | llm | parser
        result = chain.invoke({
            "exercice_text": exercice_text
        })
        return result
    except Exception as e:
        print(f"   ⚠️  Erreur avec le parser Pydantic, tentative de parsing manuel...")
        
        # Fallback : appeler le LLM directement et parser manuellement
        chain_simple = prompt | llm
        response = chain_simple.invoke({
            "exercice_text": exercice_text
        })
        
        # Extraire le JSON de la réponse
        response_text = response.content
        
        # Essayer de trouver le JSON dans la réponse
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            json_str = json_match.group()
            try:
                # Échapper les backslashes pour les notations LaTeX
                # Remplacer \ par \\ sauf si déjà échappé
                json_str_escaped = json_str.replace('\\', '\\\\')
                # Mais ne pas double-échapper les séquences déjà valides
                json_str_escaped = json_str_escaped.replace('\\\\n', '\\n')
                json_str_escaped = json_str_escaped.replace('\\\\t', '\\t')
                json_str_escaped = json_str_escaped.replace('\\\\r', '\\r')
                
                data = json.loads(json_str_escaped, strict=False)
                return ExerciceStructure(**data)
            except Exception as e2:
                print(f"   ❌ Erreur de parsing JSON : {e2}")
                # Dernier essai : demander au LLM sans LaTeX
                print(f"   🔄 Nouvelle tentative sans LaTeX...")
                # Retourner une structure par défaut
                return ExerciceStructure(
                    nombre_questions=5,
                    domaines_mathematiques=["Mathématiques"],
                    types_questions=["Calcul"],
                    niveau_difficulte="Moyen",
                    notations_utilisees=["LaTeX standard"],
                    format_reponses=["Numérique"]
                )
        else:
            print(f"   ❌ Aucun JSON trouvé dans la réponse")
            return ExerciceStructure(
                nombre_questions=5,
                domaines_mathematiques=["Mathématiques"],
                types_questions=["Calcul"],
                niveau_difficulte="Moyen",
                notations_utilisees=["LaTeX standard"],
                format_reponses=["Numérique"]
            )


# ============================================================================
# FONCTION 3 : FORMATER L'ÉNONCÉ AVEC ENUMERATE
# ============================================================================

def format_enonce_with_enumerate(enonce: str) -> str:
    """
    Formate automatiquement l'énoncé pour utiliser des environnements enumerate LaTeX.
    
    Détecte les patterns de questions comme:
    - 1., 2., 3., etc.
    - a), b), c), etc.
    
    Et les encapsule dans des environnements enumerate appropriés.
    """
    # Nettoyer l'énoncé
    enonce = enonce.strip()
    
    # Séparer par lignes
    lines = enonce.split('\n')
    
    # Détecter le pattern de numérotation
    # Pattern pour 1., 2., 3., etc.
    pattern_numbers = r'^(\d+)\.\s+'
    # Pattern pour a), b), c), etc.
    pattern_letters = r'^([a-z])\)\s+'
    
    # Identifier les lignes qui sont des questions
    question_indices = []
    question_types = []  # 'number' ou 'letter'
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if re.match(pattern_numbers, line_stripped):
            question_indices.append(i)
            question_types.append('number')
        elif re.match(pattern_letters, line_stripped):
            question_indices.append(i)
            question_types.append('letter')
    
    # Si aucune question détectée, retourner l'énoncé tel quel
    if not question_indices:
        return enonce
    
    # Reconstruire l'énoncé avec enumerate
    result_parts = []
    
    # Texte avant la première question (introduction)
    if question_indices[0] > 0:
        intro_lines = lines[:question_indices[0]]
        intro = '\n'.join(intro_lines).strip()
        if intro:
            result_parts.append(intro)
            result_parts.append('')  # Ligne vide
    
    # Déterminer le type dominant de questions
    main_type = 'number' if question_types.count('number') > question_types.count('letter') else 'letter'
    
    # Commencer l'environnement enumerate
    if main_type == 'number':
        result_parts.append('\\begin{enumerate}')
    else:
        result_parts.append('\\begin{enumerate}[label=(\\alph*)]')
    
    # Traiter chaque question
    for idx, q_idx in enumerate(question_indices):
        # Trouver la fin de cette question (début de la suivante ou fin du texte)
        if idx + 1 < len(question_indices):
            end_idx = question_indices[idx + 1]
        else:
            end_idx = len(lines)
        
        # Extraire les lignes de cette question
        question_lines = lines[q_idx:end_idx]
        
        # Nettoyer la première ligne pour enlever la numérotation
        first_line = question_lines[0].strip()
        if main_type == 'number':
            first_line_cleaned = re.sub(pattern_numbers, '', first_line)
        else:
            first_line_cleaned = re.sub(pattern_letters, '', first_line)
        
        # Reconstruire la question
        question_content = [first_line_cleaned] + [line.strip() for line in question_lines[1:]]
        question_text = ' '.join([l for l in question_content if l])
        
        # Ajouter l'item
        result_parts.append(f'\\item {question_text}')
    
    # Fermer l'environnement enumerate
    result_parts.append('\\end{enumerate}')
    
    return '\n'.join(result_parts)


# ============================================================================
# FONCTION 4 : CORRIGER LA SYNTAXE LATEX
# ============================================================================

def fix_latex_syntax(text: str) -> str:
    """
    Corrige automatiquement les erreurs LaTeX courantes.
    """
    import re
    
    # Corriger les sauts de ligne au milieu des formules mathématiques
    # Supprimer les \n qui sont entre des $ ou à l'intérieur d'environnements mathématiques
    text = re.sub(r'\$([^\$]*)\n([^\$]*)\$', r'$\1 \2$', text)  # Dans les formules inline
    
    # Corriger les commandes LaTeX sans backslash
    corrections = [
        (r'\bfrac([0-9a-zA-Z])', r'\\frac{\1'),  # fracn → \frac{n
        (r'\bfrac\s*([0-9])', r'\\frac{\1'),     # frac 1 → \frac{1
        (r'\bsqrt([0-9a-zA-Z])', r'\\sqrt{\1'),  # sqrtb → \sqrt{b
        (r'\bint([0-9a-zA-Z_^{])', r'\\int\1'),  # int0 → \int_0
        (r'\bsum([0-9a-zA-Z_^])', r'\\sum\1'),   # sumn → \sum_n
        (r'\blim([0-9a-zA-Z_])', r'\\lim\1'),    # limx → \lim_x
        (r'\bsin\s*([0-9a-zA-Z(])', r'\\sin \1'), # sinx → \sin x
        (r'\bcos\s*([0-9a-zA-Z(])', r'\\cos \1'), # cosx → \cos x
        (r'\btan\s*([0-9a-zA-Z(])', r'\\tan \1'), # tanx → \tan x
        (r'\bln\s*([0-9a-zA-Z(])', r'\\ln \1'),   # lnx → \ln x
        (r'\bexp\s*([0-9a-zA-Z(])', r'\\exp \1'), # expx → \exp x
        (r'ight\)', r'\\right)'),                 # ight) → \right)
        (r'ight\]', r'\\right]'),                 # ight] → \right]
        (r'ight\}', r'\\right}'),                 # ight} → \right}
        (r'left\(', r'\\left('),                  # left( → \left(
        (r'left\[', r'\\left['),                  # left[ → \left[
        (r'left\{', r'\\left{'),                  # left{ → \left{
        (r'\binfty\b', r'\\infty'),               # infty → \infty
        (r'\bto\b', r'\\to'),                     # to → \to
        (r'geq\s*([0-9])', r'\\geq \1'),         # geq0 → \geq 0
        (r'leq\s*([0-9])', r'\\leq \1'),         # leq0 → \leq 0
        (r'neq', r'\\neq'),                       # neq → \neq
        # Corriger les accolades manquantes dans frac, sqrt, etc.
        (r'\\frac([0-9a-zA-Z])\s*([0-9a-zA-Z])', r'\\frac{\1}{\2}'),  # \fracn m → \frac{n}{m}
    ]
    
    for pattern, replacement in corrections:
        text = re.sub(pattern, replacement, text)
    
    return text


# ============================================================================
# FONCTION 5 : GÉNÉRER UN EXERCICE SIMILAIRE (AMÉLIORÉ)
# ============================================================================

def generate_similar_exercice(
    exercice_original: str,
    structure_analysee: ExerciceStructure,
    metadata: Dict,
    llm: Optional[ChatOpenAI] = None,
    temperature: float = 0.7
) -> NouvelExercice:
    """
    Génère un nouvel exercice ayant la même structure que l'original.
    VERSION AMÉLIORÉE avec meilleur formatage.
    """
    if llm is None:
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=temperature,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    # PROMPT AMÉLIORÉ
    system_prompt = """Tu es un expert en mathématiques. Génère un exercice similaire à l'original.

RÈGLES DE BASE :
- Même structure (même nombre de questions)
- Même niveau de difficulté
- Valeurs et contextes différents

⚠️ FORMATAGE DES QUESTIONS - TRÈS IMPORTANT ⚠️
Chaque question DOIT être sur une ligne séparée et commencer par sa numérotation :
- Si l'exercice original utilise 1., 2., 3., utilise le même format
- Si l'exercice original utilise a), b), c), utilise le même format

EXEMPLE DE FORMATAGE CORRECT :
"Soit la fonction $f$ définie par $f(x) = \\frac{{x^2 + 1}}{{x - 2}}$.

1. Calculer $\\lim_{{x \\to 2^+}} f(x)$.

2. Résoudre l'équation $f(x) = \\sqrt{{5}}$.

3. Calculer $\\int_{{0}}^{{1}} f(x) dx$."

SYNTAXE LaTeX CRITIQUE - TOUJOURS UTILISER LA SYNTAXE COMPLÈTE :
✅ Fractions : \\frac{{1}}{{3}} (avec accolades complètes)
✅ Racines : \\sqrt{{b}} ou \\sqrt[3]{{x}}
✅ Intégrales : \\int_{{0}}^{{1}} f(x) dx
✅ Limites : \\lim_{{x \\to +\\infty}}
✅ Sommes : \\sum_{{n=1}}^{{\\infty}}
✅ Parenthèses : \\left( ... \\right) (toujours par paires)
✅ Fonctions : \\sin, \\cos, \\tan, \\ln, \\exp
✅ Infini : \\infty
✅ Comparaisons : \\leq, \\geq
✅ Systèmes : \\begin{{cases}} ... \\end{{cases}}

❌ JAMAIS : frac13, sqrtb, int0, limx, sinx, ight), infty, pi (sans \\)

DANS LE JSON, DOUBLE TOUS LES BACKSLASHES :
- \\frac → \\\\frac
- \\sqrt → \\\\sqrt  
- \\int → \\\\int
- \\n pour les sauts de ligne entre questions

Réponds UNIQUEMENT avec le JSON (sans ``` ni texte)."""

    human_prompt = """Génère un exercice similaire à celui-ci :

{exercice_original}

Structure : {nombre_questions} questions, domaines : {domaines}, niveau : {niveau_difficulte}

RAPPELS CRITIQUES :
1. Double TOUS les backslashes LaTeX dans le JSON : \\frac → \\\\frac
2. Syntaxe complète : \\\\frac{{{{1}}}}{{{{3}}}} (JAMAIS frac13 ou fracn)
3. Chaque question sur une ligne séparée avec sa numérotation (1., 2., ou a), b))
4. Une ligne vide (\\n\\n) entre chaque question

FORMAT JSON :
{{{{
"titre": "Exercice n° X",
"enonce_complet": "Texte d'introduction.\\n\\n1. Première question.\\n\\n2. Deuxième question.",
"domaine_principal": "Analyse",
"difficulte": "Moyen"
}}}}

Réponds UNIQUEMENT avec le JSON (sans markdown)."""

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        HumanMessagePromptTemplate.from_template(human_prompt)
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({
        "exercice_original": exercice_original[:5000],  # Limiter la taille
        "nombre_questions": structure_analysee.nombre_questions,
        "domaines": ", ".join(structure_analysee.domaines_mathematiques),
        "niveau_difficulte": structure_analysee.niveau_difficulte
    })
    
    response_text = response.content.strip()
    
    # Nettoyer
    response_text = re.sub(r'```json\s*', '', response_text)
    response_text = re.sub(r'```\s*$', '', response_text)
    response_text = re.sub(r'^```\s*', '', response_text)
    response_text = response_text.strip()
    
    # Extraire le JSON
    try:
        # Chercher le premier { et le dernier }
        start = response_text.find('{')
        end = response_text.rfind('}')
        
        if start == -1 or end == -1:
            raise ValueError("Pas de JSON trouvé")
        
        json_str = response_text[start:end+1]
        
        # Parser avec json.loads - le LLM devrait avoir déjà doublé les backslashes
        try:
            data = json.loads(json_str, strict=False)
        except json.JSONDecodeError:
            # Si ça échoue, c'est que les backslashes ne sont pas correctement échappés
            # On va essayer de les corriger automatiquement
            print("   ⚠️  Correction automatique des backslashes...")
            # Ne pas toucher aux séquences d'échappement JSON valides
            json_str_fixed = json_str
            # Remplacer les backslashes simples dans les commandes LaTeX
            # mais préserver les échappements JSON (\n, \", etc.)
            json_str_fixed = json_str_fixed.replace('\\n', '\x00NEWLINE\x00')  # Protéger \n
            json_str_fixed = json_str_fixed.replace('\\"', '\x00QUOTE\x00')    # Protéger \"
            json_str_fixed = json_str_fixed.replace('\\t', '\x00TAB\x00')      # Protéger \t
            json_str_fixed = json_str_fixed.replace('\\r', '\x00RETURN\x00')   # Protéger \r
            json_str_fixed = json_str_fixed.replace('\\', '\\\\')               # Doubler les autres \
            json_str_fixed = json_str_fixed.replace('\x00NEWLINE\x00', '\\n')  # Restaurer \n
            json_str_fixed = json_str_fixed.replace('\x00QUOTE\x00', '\\"')    # Restaurer \"
            json_str_fixed = json_str_fixed.replace('\x00TAB\x00', '\\t')      # Restaurer \t
            json_str_fixed = json_str_fixed.replace('\x00RETURN\x00', '\\r')   # Restaurer \r
            
            data = json.loads(json_str_fixed, strict=False)
        
        # Vérifier les champs requis
        if 'titre' not in data:
            data['titre'] = f"Exercice n° {structure_analysee.nombre_questions}"
        if 'enonce_complet' not in data:
            raise ValueError("Champ enonce_complet manquant")
        if 'domaine_principal' not in data:
            data['domaine_principal'] = structure_analysee.domaines_mathematiques[0] if structure_analysee.domaines_mathematiques else "Mathématiques"
        if 'difficulte' not in data:
            data['difficulte'] = structure_analysee.niveau_difficulte
        
        # CORRECTION AUTOMATIQUE DU LATEX
        data['enonce_complet'] = fix_latex_syntax(data['enonce_complet'])
        
        # FORMATER AVEC ENUMERATE
        data['enonce_complet'] = format_enonce_with_enumerate(data['enonce_complet'])
        
        return NouvelExercice(**data)
        
    except Exception as e:
        raise Exception(f"Erreur parsing: {str(e)[:200]}")


# ============================================================================
# FONCTION 6 : PIPELINE COMPLET (AMÉLIORÉ)
# ============================================================================

def generate_new_epreuve_as_latex_string(
    chunks_list: List[Dict],
    n_variations_per_exercice: int = 1,
    temperature: float = 0.7,
    llm_analysis: Optional[ChatOpenAI] = None,
    llm_generation: Optional[ChatOpenAI] = None,
    return_all_latex: bool = True
) -> str:
    """
    Génère une **nouvelle épreuve complète** (sous forme de string LaTeX)
    composée de variations d'exercices similaires aux originaux.
    
    VERSION AMÉLIORÉE avec meilleur formatage.

    Args:
        chunks_list: Liste de chunks d'exercices (doit contenir plusieurs exercices)
        n_variations_per_exercice: Nombre **maximal de tentatives** de génération
                                   par exercice. La **première réussie** est conservée.
        temperature: Créativité du modèle (0—1)
        llm_analysis: LLM pour l'analyse (par défaut gpt-4o-mini)
        llm_generation: LLM pour la génération (par défaut gpt-4o)
        return_all_latex: Si True, retourne le document complet avec en-tête et footer.
                         Si False, retourne uniquement le corps (exercices uniquement).

    Returns:
        str: Épreuve complète au format LaTeX, prête à compiler.
    """
    from typing import List, Dict, Optional
    import re

    # 1. Reconstituer les exercices originaux
    exercices_complets = reconstruct_exercice_from_chunks(chunks_list)
    if not exercices_complets:
        return "% Aucun exercice à générer\n"

    # 2. Générer **une seule variation valide par exercice**, avec jusqu'à `n_variations_per_exercice` tentatives
    nouveaux_enonces = []
    
    for i, exo_data in enumerate(exercices_complets):
        print(f"🔹 Traitement de l'exercice original n°{exo_data['exercice']}...")
        
        # Analyse (une seule fois, pas besoin de la refaire à chaque tentative)
        structure = analyze_exercice_structure(exo_data['texte_complet'], llm=llm_analysis)
        
        nouveau_exo = None
        max_attempts = max(1, n_variations_per_exercice)  # au moins 1 tentative

        for attempt in range(max_attempts):
            print(f"   ➤ Tentative {attempt + 1}/{max_attempts} de génération...")
            try:
                nouveau_exo = generate_similar_exercice(
                    exercice_original=exo_data['texte_complet'],
                    structure_analysee=structure,
                    metadata=exo_data,
                    llm=llm_generation,
                    temperature=temperature
                )
                print(f"   ✅ Variation réussie à la tentative {attempt + 1}.")
                break  # On arrête dès qu'on en a une bonne
            except Exception as e:
                print(f"   ⚠️ Échec tentative {attempt + 1} : {e}")
                continue  # On réessaie, sauf si c'était la dernière
        
        # 3. Formatage de l'énoncé ou fallback
        if nouveau_exo:
            enonce = nouveau_exo.enonce_complet
            nouveaux_enonces.append(enonce)
        else:
            fallback = f"\\textit{{Échec de génération après {max_attempts} tentative(s).}}"
            nouveaux_enonces.append(fallback)

    # 4. En-tête LaTeX complet (AMÉLIORÉ)
    latex_header = r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[french]{babel}
\usepackage{amsmath,amssymb,amsthm,mathtools}
\usepackage{geometry}
\geometry{margin=2.5cm}
\usepackage{enumitem}
\usepackage{fancyhdr}
\usepackage{xfrac}

% Configuration enumerate pour un espacement optimal
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

    # 5. Assembler les exercices avec meilleur espacement
    exercices_latex = []
    for i, enonce in enumerate(nouveaux_enonces):
        exercice_section = f"\\section*{{Exercice {i+1}}}\n\n{enonce}"
        exercices_latex.append(exercice_section)
    
    corps_latex = "\n\n\\vspace{1.5cm}\n\n".join(exercices_latex)

    # 6. Fin du document
    latex_footer = r"""

\end{document}
"""

    # 7. Retourner selon le paramètre
    if return_all_latex:
        return nettoyer_et_formater_latex(latex_header + corps_latex + latex_footer)
    else:
        return nettoyer_et_formater_latex(corps_latex)
