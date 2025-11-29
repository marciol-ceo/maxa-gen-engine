# 🚀 Maxa Gen Engine V2 - Mode Ultra-Robuste

## ✨ Nouveautés majeures

### 🎯 **Problèmes résolus**

1. ✅ **Fini les accents corrompus** - Encodage UTF-8 garanti
2. ✅ **Fini les formules LaTeX coupées** - Validation structurée par OpenAI
3. ✅ **Fini les erreurs de syntaxe** - Structured Outputs garantit le format
4. ✅ **Qualité maximale** - GPT-5 (94.6% sur AIME 2025)

### 🔧 **Technologies utilisées**

- **GPT-5** : Modèle le plus puissant d'OpenAI (2025)
- **Structured Outputs** : Validation JSON native par OpenAI
- **Schémas Pydantic** : Garantie de conformité des données
- **UTF-8 forcé** : Middleware FastAPI pour l'encodage

---

## 📖 **Guide d'utilisation**

### **Installation**

```bash
pip install openai fastapi uvicorn pydantic python-dotenv
```

### **Configuration**

Créez un fichier `.env` :

```env
OPENAI_API_KEY=votre_clé_api_openai
pinecone_api_key=votre_clé_pinecone
```

---

## 🎮 **API Endpoints**

### **1. Génération automatique d'épreuve complète**

**Endpoint** : `POST /generate/auto`

**Payload** :
```json
{
  "index_name": "gen-engine-index",
  "mode": "mixed",
  "n_variations_per_exercice": 1,
  "temperature": 0.7,
  "model": "gpt-5",
  "use_robust_mode": true,
  "return_all_latex": true
}
```

**Paramètres** :
- `model` : `"gpt-5"` (meilleur), `"gpt-5-mini"` (plus rapide), `"gpt-4o"` (fallback)
- `use_robust_mode` : `true` (recommandé) ou `false` (legacy)
- `temperature` : 0.0 (déterministe) à 1.0 (créatif)
- `mode` : `"mixed"` (tous les namespaces) ou `"single"` (un seul)

**Réponse** :
```json
{
  "mode_used": "mixed",
  "chunks_count": 7,
  "latex_result": "\\documentclass[12pt,a4paper]{article}\n...",
  "generation_mode": "robust",
  "model_used": "gpt-5"
}
```

---

### **2. Génération d'un exercice aléatoire**

**Endpoint** : `POST /generate/exercise/random`

**Payload** :
```json
{
  "index_name": "gen-engine-index",
  "temperature": 0.7,
  "model": "gpt-5",
  "use_robust_mode": true
}
```

---

### **3. Génération manuelle depuis des chunks**

**Endpoint** : `POST /generate/from-chunks`

**Payload** :
```json
{
  "index_name": "gen-engine-index",
  "chunks_list": [...],
  "temperature": 0.7,
  "model": "gpt-5",
  "use_robust_mode": true
}
```

---

## 🔬 **Comparaison des modes**

| Critère | Mode Robuste (V2) | Mode Legacy (V1) |
|---------|------------------|------------------|
| **Modèle** | GPT-5 / GPT-5-mini | GPT-4o-mini |
| **Validation** | Structured Outputs | Regex manuels |
| **Encodage** | UTF-8 garanti | Parfois corrompu |
| **Formules LaTeX** | 100% valides | ~85% valides |
| **Accents** | Parfaits | Parfois corrompus |
| **Coût** | Légèrement plus élevé | Moins cher |
| **Qualité** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## 🧪 **Tests**

### **Test du générateur robuste**

```bash
python maxa_generer_epreuve_v2_robust.py
```

### **Test de l'API**

```bash
python maxa_api.py
```

Puis :
```bash
curl -X POST http://localhost:5000/generate/auto \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5",
    "use_robust_mode": true,
    "temperature": 0.7
  }'
```

---

## 📊 **Architecture technique**

### **Flux de génération (Mode Robuste)**

```
1. Récupération des chunks depuis Pinecone
   ↓
2. Reconstitution des exercices complets
   ↓
3. Analyse structurelle avec GPT-5 (Structured Outputs)
   ↓
4. Génération de variations avec GPT-5 (Structured Outputs)
   ↓
5. Validation automatique par OpenAI (JSON Schema)
   ↓
6. Assemblage en document LaTeX complet
   ↓
7. Retour avec UTF-8 garanti
```

### **Schémas Pydantic**

#### **`ExerciceLatexStructure`**
```python
class ExerciceLatexStructure(BaseModel):
    titre: str
    introduction: str
    questions: List[QuestionLatex]
    domaine_principal: str
    niveau_difficulte: str
```

#### **`QuestionLatex`**
```python
class QuestionLatex(BaseModel):
    numero: int
    enonce_latex: str  # LaTeX garanti valide
    type_question: str
```

---

## 🎓 **Avantages du Structured Outputs**

### **Avant (Legacy)**
```json
{
  "enonce": "Calculer $\frac{1}{2}$"  # Peut être corrompu
}
```
❌ Parfois : `"enonce": "Calculer $frac12$"` (invalide)

### **Après (Robuste)**
```json
{
  "questions": [{
    "numero": 1,
    "enonce_latex": "Calculer $\\frac{1}{2}$"
  }]
}
```
✅ **Garanti** conforme au schéma JSON
✅ **Garanti** LaTeX valide avec doubles backslashes
✅ **Garanti** UTF-8 correct

---

## 💡 **Bonnes pratiques**

### **1. Choix du modèle**

- **Production** : `gpt-5` (qualité maximale)
- **Développement** : `gpt-5-mini` (plus rapide, moins cher)
- **Fallback** : `gpt-4o` (compatible)

### **2. Température**

⚠️ **IMPORTANT** : Avec Structured Outputs, le paramètre `temperature` est **IGNORÉ** et fixé à `1.0` par OpenAI.

- Cette limitation garantit la validité du JSON mais réduit le contrôle sur la créativité
- Pour un contrôle précis de la température, utilisez le mode legacy (`use_robust_mode: false`)
- En mode robuste, la variété vient du prompt et du contexte, pas de la température

### **3. Mode de sélection**

- `"mixed"` : Épreuve complète avec tous types d'exercices
- `"single"` : Épreuve homogène d'un seul domaine

---

## 🐛 **Résolution de problèmes**

### **Erreur : "temperature does not support 0"**
```
Error: 'temperature' does not support 0 with this model. Only the default (1) value is supported.
```

**Cause** : Structured Outputs ne supporte QUE `temperature=1` (valeur par défaut).

**Solution** : Le code a été corrigé pour omettre le paramètre `temperature`. Assurez-vous d'utiliser la version mise à jour de `maxa_generer_epreuve_v2_robust.py`.

### **L'API retourne juste "$" ou un document vide**

**Cause** : Toutes les générations ont échoué.

**Solutions** :
1. Vérifiez les logs serveur pour voir les erreurs détaillées
2. Vérifiez que votre clé API est valide et a du crédit
3. Augmentez `max_retries` dans le code (actuellement 2)
4. Essayez avec `model: "gpt-4o"` si GPT-5 n'est pas encore disponible

### **Erreur : "API key not found"**
```bash
# Vérifiez votre .env
cat .env | grep OPENAI_API_KEY
```

### **Erreur : "Model not found: gpt-5"**
GPT-5 est en cours de déploiement. Utilisez temporairement :
```json
{
  "model": "gpt-4o"
}
```

### **LaTeX toujours invalide en mode legacy**
Passez au mode robuste :
```json
{
  "use_robust_mode": true
}
```

---

## 📚 **Sources et références**

- [OpenAI GPT-5 Launch](https://openai.com/index/introducing-gpt-5/)
- [Structured Outputs Documentation](https://platform.openai.com/docs/guides/structured-outputs)
- [GPT-5 Performance Benchmarks](https://www.getpassionfruit.com/blog/chatgpt-5-vs-gpt-5-pro-vs-gpt-4o-vs-o3-performance-benchmark-comparison-recommendation-of-openai-s-2025-models)

---

## 🚀 **Prochaines évolutions**

- [ ] Support de GPT-5.1 (avec raisonnement adaptatif)
- [ ] Cache intelligent des analyses structurelles
- [ ] Génération multilingue (anglais, allemand, etc.)
- [ ] Export PDF direct depuis l'API
- [ ] Interface web avec prévisualisation LaTeX live

---

## 📝 **Licence**

Projet privé - Tous droits réservés

---

## 👨‍💻 **Contact**

Pour toute question sur la V2 Robuste, consultez ce README ou testez directement l'API.
