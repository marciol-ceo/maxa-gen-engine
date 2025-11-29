"""
Script de test pour le mode robuste avec GPT-5 + Structured Outputs
"""

import os
from dotenv import load_dotenv
from maxa_generer_epreuve_v2_robust import RobustLatexGenerator

load_dotenv()

# Exercice de test
EXERCICE_TEST = """
Soit la fonction $f$ définie par $f(x) = \\frac{x^2 + 1}{x - 2}$.

1. Calculer $\\lim_{x \\to 2^+} f(x)$.

2. Résoudre l'équation $f(x) = \\sqrt{5}$.

3. Calculer $\\int_{0}^{1} f(x) dx$.

4. Étudier la convexité de $f$ sur son domaine de définition.
"""

def test_analyse():
    """Test de l'analyse structurelle."""
    print("=" * 60)
    print("TEST 1 : Analyse structurelle avec GPT-5")
    print("=" * 60)

    try:
        generator = RobustLatexGenerator(model="gpt-4o", temperature=0.0)
        print(f"✓ Générateur initialisé avec {generator.model}\n")

        print("📊 Analyse en cours...")
        analyse = generator.analyser_exercice(EXERCICE_TEST)

        print("\n✅ RÉSULTAT DE L'ANALYSE :")
        print(f"   • Nombre de questions : {analyse.nombre_questions}")
        print(f"   • Domaines : {', '.join(analyse.domaines_mathematiques)}")
        print(f"   • Types : {', '.join(analyse.types_questions)}")
        print(f"   • Niveau : {analyse.niveau_difficulte}")
        print(f"   • Format : {analyse.format_numerotation}")

        return analyse

    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        return None


def test_generation(analyse):
    """Test de la génération d'exercice similaire."""
    print("\n" + "=" * 60)
    print("TEST 2 : Génération d'exercice similaire")
    print("=" * 60)

    if not analyse:
        print("⚠️  Analyse non disponible, skip test")
        return None

    try:
        generator = RobustLatexGenerator(model="gpt-4o", temperature=0.7)
        print(f"✓ Générateur initialisé avec {generator.model}\n")

        print("🤖 Génération en cours...")
        exercice = generator.generer_exercice_similaire(
            exercice_original=EXERCICE_TEST,
            analyse=analyse,
            numero_exercice=1
        )

        print("\n✅ EXERCICE GÉNÉRÉ :")
        print(f"   • Titre : {exercice.titre}")
        print(f"   • Introduction : {exercice.introduction[:50]}..." if exercice.introduction else "   • Introduction : (vide)")
        print(f"   • Nombre de questions : {len(exercice.questions)}")
        print(f"   • Domaine : {exercice.domaine_principal}")
        print(f"   • Difficulté : {exercice.niveau_difficulte}")

        print("\n📝 QUESTIONS :")
        for q in exercice.questions:
            preview = q.enonce_latex[:80].replace('\n', ' ')
            print(f"   {q.numero}. {preview}...")

        print("\n📄 CODE LATEX COMPLET :")
        print("-" * 60)
        latex = exercice.to_latex_string()
        print(latex)
        print("-" * 60)

        # Validation basique
        if '\\frac' in latex and '\\frac{' not in latex:
            print("\n⚠️  WARNING : \\frac incomplet détecté")
        if '\\sqrt' in latex and '\\sqrt{' not in latex:
            print("\n⚠️  WARNING : \\sqrt incomplet détecté")
        if latex.count('{') != latex.count('}'):
            print(f"\n⚠️  WARNING : Déséquilibre d'accolades ({latex.count('{')} vs {latex.count('}')})")
        else:
            print("\n✅ Validation basique : OK (accolades équilibrées)")

        return exercice

    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        return None


def test_epreuve_complete():
    """Test de génération d'épreuve complète."""
    print("\n" + "=" * 60)
    print("TEST 3 : Génération d'épreuve complète")
    print("=" * 60)

    try:
        # Simuler des chunks
        chunks_mock = [
            {
                'texte_complet': EXERCICE_TEST,
                'exercice': 1,
                'epreuve': 'Test',
                'date': '2025',
                'chunk_text': EXERCICE_TEST,
                'chunk_index': 0
            },
            {
                'texte_complet': """
On considère la suite $(u_n)$ définie par $u_0 = 1$ et $u_{n+1} = \\frac{u_n + 2}{u_n + 1}$.

1. Montrer que la suite est bornée.

2. Étudier la monotonie de la suite.

3. En déduire que la suite converge et déterminer sa limite.
""",
                'exercice': 2,
                'epreuve': 'Test',
                'date': '2025',
                'chunk_text': '',
                'chunk_index': 0
            }
        ]

        from maxa_generer_epreuve_v2_robust import generate_new_epreuve_as_latex_string_v2

        print("🚀 Génération avec mode robuste...")
        latex_complet = generate_new_epreuve_as_latex_string_v2(
            chunks_list=chunks_mock,
            model="gpt-4o",
            temperature=0.7,
            use_structured_outputs=True
        )

        print(f"\n✅ Épreuve générée ({len(latex_complet)} caractères)")

        # Sauvegarder
        output_path = "test_output_robust.tex"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(latex_complet)

        print(f"✅ Sauvegardé dans : {output_path}")

        # Aperçu
        print("\n📄 APERÇU (200 premiers caractères) :")
        print("-" * 60)
        print(latex_complet[:200] + "...")
        print("-" * 60)

        return True

    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Lance tous les tests."""
    print("\n🧪 SUITE DE TESTS - MODE ROBUSTE")
    print("=" * 60)

    # Vérifier la clé API
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERREUR : OPENAI_API_KEY non trouvée dans .env")
        return

    print(f"✓ Clé API trouvée (commence par : {api_key[:10]}...)")
    print()

    # Test 1
    analyse = test_analyse()

    # Test 2
    if analyse:
        test_generation(analyse)

    # Test 3
    test_epreuve_complete()

    print("\n" + "=" * 60)
    print("✅ TESTS TERMINÉS")
    print("=" * 60)
    print("\nSi GPT-5 n'est pas encore disponible, les tests utilisent GPT-4o.")
    print("Dès que GPT-5 sera disponible, changez 'gpt-4o' par 'gpt-5' dans ce script.")


if __name__ == "__main__":
    main()
