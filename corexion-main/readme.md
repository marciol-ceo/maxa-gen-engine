# 🎨 Interface UI - Maxa Gen Engine

Interface web complète pour générer des épreuves mathématiques avec votre API.

## 📁 Structure du projet

```
/votre-projet/
├── api_with_ui.py              # API FastAPI avec serveur UI
├── maxa_get_meta.py            # Vos modules
├── maxa_generer_epreuve.py     # Vos modules
├── .env                        # Variables d'environnement
└── static/                     # Fichiers de l'interface
    ├── index.html              # Page principale
    ├── styles.css              # Styles
    └── app.js                  # Logique JavaScript
```

## 🚀 Démarrage rapide

### 1. Installer les dépendances (si nécessaire)

```bash
pip install fastapi uvicorn python-dotenv
```

### 2. Vérifier la structure

Assurez-vous que le dossier `static/` existe avec les 3 fichiers :
- `index.html`
- `styles.css`
- `app.js`

### 3. Lancer le serveur

```bash
python api_with_ui.py
```

### 4. Ouvrir l'interface

Ouvrez votre navigateur et accédez à :

🎨 **Interface UI** : http://localhost:5000/ui

📚 **Documentation API** : http://localhost:5000/docs

## 🎯 Fonctionnalités de l'interface

### 1️⃣ Exercice Unique
- Génère un seul exercice aléatoire
- Paramètres personnalisables (variations, température)
- Téléchargement direct du fichier `.tex`

### 2️⃣ Épreuve Complète (Mixed)
- Génère une épreuve avec des exercices de TOUS les namespaces
- Affiche le nombre d'exercices générés
- Aperçu du code LaTeX

### 3️⃣ Épreuve (Single Namespace)
- Génère une épreuve avec des exercices d'UN SEUL namespace
- Idéal pour des épreuves thématiques

### 4️⃣ Génération Manuelle
- Génère du LaTeX à partir de vos propres chunks JSON
- Contrôle total sur les données d'entrée

## ⚙️ Paramètres de génération

### Nombre de variations (1-20)
- Nombre de versions générées par exercice
- **Défaut** : 5

### Température (0.0 - 1.0)
- Contrôle la créativité du modèle
- **0.0** : Très conservateur, colle aux exemples
- **0.7** : Équilibré (recommandé)
- **1.0** : Très créatif, plus de variations

### Retourner LaTeX complet
- ✅ **Activé** : Document LaTeX complet et compilable
- ❌ **Désactivé** : Uniquement les exercices

## 📥 Téléchargement et Copie

Chaque résultat généré offre deux options :

1. **📥 Télécharger LaTeX** : Télécharge un fichier `.tex` avec timestamp
2. **📋 Copier** : Copie le code dans le presse-papiers

## 🎨 Aperçu visuel

L'interface inclut :
- ✅ Indicateur d'état de l'API en temps réel
- 🎨 Design moderne et responsive
- 📱 Compatible mobile
- 🌈 Thème violet/gradient élégant
- ⚡ Animations fluides
- 🔔 Notifications toast

## 🐛 Dépannage

### L'API ne se connecte pas
```bash
# Vérifier que l'API tourne
curl http://localhost:5000/

# Devrait retourner : {"status": "online", ...}
```

### Les fichiers statiques ne se chargent pas
```bash
# Vérifier la structure
ls -la static/

# Doit contenir : index.html, styles.css, app.js
```

### Erreur CORS (si vous utilisez un autre domaine)
Ajoutez dans `api_with_ui.py` :

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📝 Exemples d'utilisation

### Génération rapide d'un exercice
1. Cliquez sur "🎯 Exercice Unique"
2. Ajustez les paramètres si nécessaire
3. Cliquez sur "🚀 Générer l'exercice"
4. Téléchargez le fichier `.tex` généré

### Génération d'une épreuve complète
1. Cliquez sur "📚 Épreuve Complète (Mixed)"
2. Réglez le nombre de variations (ex: 10)
3. Ajustez la température (ex: 0.8 pour plus de créativité)
4. Générez et téléchargez

### Génération manuelle depuis JSON
1. Cliquez sur "⚙️ Génération Manuelle"
2. Collez votre JSON de chunks
3. Configurez les paramètres
4. Générez

Exemple de JSON :
```json
[
  {
    "id": "chunk-123",
    "namespace": "algebre",
    "text": "Résoudre l'équation...",
    "metadata": {...}
  }
]
```

## 🔧 Personnalisation

### Changer les couleurs
Modifiez les variables CSS dans `static/styles.css` :

```css
:root {
    --primary-color: #2563eb;  /* Couleur principale */
    --success-color: #10b981;  /* Couleur de succès */
    /* ... */
}
```

### Modifier le port
Dans `api_with_ui.py`, ligne finale :

```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # Port 8000 au lieu de 5000
```

## 📊 Monitoring

L'interface vérifie automatiquement l'état de l'API toutes les 30 secondes et affiche :
- 🟢 **API en ligne** : Tout fonctionne
- 🔴 **API hors ligne** : Serveur inaccessible

## 🚀 Déploiement en production

Pour déployer l'interface en production :

1. **Sécuriser les CORS**
2. **Utiliser HTTPS**
3. **Configurer un reverse proxy (nginx)**
4. **Ajouter une authentification si nécessaire**

## 📞 Support

Si vous rencontrez des problèmes :
1. Vérifiez la console du navigateur (F12)
2. Vérifiez les logs du serveur
3. Testez l'API directement : http://localhost:5000/docs

## 🎉 Fonctionnalités à venir

- [ ] Prévisualisation PDF du LaTeX généré
- [ ] Historique des générations
- [ ] Sauvegarde des paramètres favoris
- [ ] Mode sombre
- [ ] Export en plusieurs formats

---

**Version** : 1.2.0  
**Auteur** : Maxa Gen Engine Team  
**License** : MIT