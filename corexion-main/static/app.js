// Configuration
const API_BASE_URL = window.location.origin;

// Variables globales pour stocker les résultats
let currentResults = {
    'result-single': null,
    'result-mixed': null,
    'result-single-ns': null,
    'result-manual': null
};

// ============================================
// INITIALISATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    initializeTemperatureSliders();
    checkApiStatus();
    
    // Vérifier l'état de l'API toutes les 30 secondes
    setInterval(checkApiStatus, 30000);
});

// ============================================
// GESTION DES TABS
// ============================================

function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Désactiver tous les boutons et contenus
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Activer le bon bouton et contenu
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

// ============================================
// GESTION DES SLIDERS DE TEMPÉRATURE
// ============================================

function initializeTemperatureSliders() {
    const sliders = [
        { id: 'single-temperature', valueId: 'single-temp-value' },
        { id: 'mixed-temperature', valueId: 'mixed-temp-value' },
        { id: 'single-ns-temperature', valueId: 'single-ns-temp-value' },
        { id: 'manual-temperature', valueId: 'manual-temp-value' }
    ];
    
    sliders.forEach(slider => {
        const element = document.getElementById(slider.id);
        const valueDisplay = document.getElementById(slider.valueId);
        
        element.addEventListener('input', function() {
            const value = (this.value / 100).toFixed(2);
            valueDisplay.textContent = value;
        });
        
        // Initialiser l'affichage
        const initialValue = (element.value / 100).toFixed(2);
        valueDisplay.textContent = initialValue;
    });
}

// ============================================
// VÉRIFICATION DE L'ÉTAT DE L'API
// ============================================

async function checkApiStatus() {
    const statusIndicator = document.getElementById('apiStatus');
    const statusText = document.getElementById('apiStatusText');
    
    try {
        const response = await fetch(`${API_BASE_URL}/`);
        
        if (response.ok) {
            statusIndicator.classList.add('online');
            statusIndicator.classList.remove('offline');
            statusText.textContent = 'API en ligne';
        } else {
            throw new Error('API non accessible');
        }
    } catch (error) {
        statusIndicator.classList.add('offline');
        statusIndicator.classList.remove('online');
        statusText.textContent = 'API hors ligne';
        showToast('Erreur: Impossible de se connecter à l\'API', 'error');
    }
}

// ============================================
// GÉNÉRATION: EXERCICE UNIQUE
// ============================================

async function generateSingleExercise() {
    const button = event.target.closest('button');
    const btnText = button.querySelector('.btn-text');
    const spinner = button.querySelector('.spinner');
    
    // Récupérer les valeurs
    const indexName = document.getElementById('single-index').value;
    const nVariations = parseInt(document.getElementById('single-variations').value);
    const temperature = parseFloat(document.getElementById('single-temperature').value) / 100;
    const returnLatex = document.getElementById('single-return-latex').checked;
    
    // Préparer le payload
    const payload = {
        index_name: indexName,
        n_variations_per_exercice: nVariations,
        temperature: temperature,
        return_all_latex: returnLatex
    };
    
    try {
        // Désactiver le bouton et afficher le spinner
        button.disabled = true;
        btnText.style.display = 'none';
        spinner.style.display = 'inline';
        
        // Cacher le résultat précédent
        document.getElementById('result-single').style.display = 'none';
        
        const response = await fetch(`${API_BASE_URL}/generate/exercise/random`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors de la génération');
        }
        
        const result = await response.json();
        
        // Stocker le résultat
        currentResults['result-single'] = result.latex_result;
        
        // Afficher le résultat
        document.getElementById('single-chunk-id').textContent = result.source_chunk_id;
        document.getElementById('single-latex-content').textContent = result.latex_result;
        document.getElementById('result-single').style.display = 'block';
        
        // Scroll vers le résultat
        document.getElementById('result-single').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        showToast('✅ Exercice généré avec succès!', 'success');
        
    } catch (error) {
        showToast(`❌ Erreur: ${error.message}`, 'error');
        console.error('Erreur:', error);
    } finally {
        // Réactiver le bouton
        button.disabled = false;
        btnText.style.display = 'inline';
        spinner.style.display = 'none';
    }
}

// ============================================
// GÉNÉRATION: ÉPREUVE COMPLÈTE (MIXED)
// ============================================

async function generateMixedEpreuve() {
    const button = event.target.closest('button');
    const btnText = button.querySelector('.btn-text');
    const spinner = button.querySelector('.spinner');
    
    const indexName = document.getElementById('mixed-index').value;
    const nVariations = parseInt(document.getElementById('mixed-variations').value);
    const temperature = parseFloat(document.getElementById('mixed-temperature').value) / 100;
    const returnLatex = document.getElementById('mixed-return-latex').checked;
    
    const payload = {
        index_name: indexName,
        mode: 'mixed',
        n_variations_per_exercice: nVariations,
        temperature: temperature,
        return_all_latex: returnLatex
    };
    
    try {
        button.disabled = true;
        btnText.style.display = 'none';
        spinner.style.display = 'inline';
        
        document.getElementById('result-mixed').style.display = 'none';
        
        const response = await fetch(`${API_BASE_URL}/generate/auto`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors de la génération');
        }
        
        const result = await response.json();
        
        currentResults['result-mixed'] = result.latex_result;
        
        document.getElementById('mixed-mode').textContent = result.mode_used;
        document.getElementById('mixed-chunks-count').textContent = result.chunks_count;
        document.getElementById('mixed-latex-content').textContent = result.latex_result;
        document.getElementById('result-mixed').style.display = 'block';
        
        document.getElementById('result-mixed').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        showToast('✅ Épreuve générée avec succès!', 'success');
        
    } catch (error) {
        showToast(`❌ Erreur: ${error.message}`, 'error');
        console.error('Erreur:', error);
    } finally {
        button.disabled = false;
        btnText.style.display = 'inline';
        spinner.style.display = 'none';
    }
}

// ============================================
// GÉNÉRATION: ÉPREUVE SINGLE NAMESPACE
// ============================================

async function generateSingleNsEpreuve() {
    const button = event.target.closest('button');
    const btnText = button.querySelector('.btn-text');
    const spinner = button.querySelector('.spinner');
    
    const indexName = document.getElementById('single-ns-index').value;
    const nVariations = parseInt(document.getElementById('single-ns-variations').value);
    const temperature = parseFloat(document.getElementById('single-ns-temperature').value) / 100;
    const returnLatex = document.getElementById('single-ns-return-latex').checked;
    
    const payload = {
        index_name: indexName,
        mode: 'single',
        n_variations_per_exercice: nVariations,
        temperature: temperature,
        return_all_latex: returnLatex
    };
    
    try {
        button.disabled = true;
        btnText.style.display = 'none';
        spinner.style.display = 'inline';
        
        document.getElementById('result-single-ns').style.display = 'none';
        
        const response = await fetch(`${API_BASE_URL}/generate/auto`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors de la génération');
        }
        
        const result = await response.json();
        
        currentResults['result-single-ns'] = result.latex_result;
        
        document.getElementById('single-ns-mode').textContent = result.mode_used;
        document.getElementById('single-ns-chunks-count').textContent = result.chunks_count;
        document.getElementById('single-ns-latex-content').textContent = result.latex_result;
        document.getElementById('result-single-ns').style.display = 'block';
        
        document.getElementById('result-single-ns').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        showToast('✅ Épreuve générée avec succès!', 'success');
        
    } catch (error) {
        showToast(`❌ Erreur: ${error.message}`, 'error');
        console.error('Erreur:', error);
    } finally {
        button.disabled = false;
        btnText.style.display = 'inline';
        spinner.style.display = 'none';
    }
}

// ============================================
// GÉNÉRATION: MANUELLE (DEPUIS CHUNKS)
// ============================================

async function generateManual() {
    const button = event.target.closest('button');
    const btnText = button.querySelector('.btn-text');
    const spinner = button.querySelector('.spinner');
    
    const indexName = document.getElementById('manual-index').value;
    const chunksText = document.getElementById('manual-chunks').value.trim();
    const nVariations = parseInt(document.getElementById('manual-variations').value);
    const temperature = parseFloat(document.getElementById('manual-temperature').value) / 100;
    const returnLatex = document.getElementById('manual-return-latex').checked;
    
    // Valider et parser le JSON
    let chunks;
    try {
        chunks = JSON.parse(chunksText);
        if (!Array.isArray(chunks)) {
            throw new Error('Le JSON doit être un tableau');
        }
    } catch (e) {
        showToast('❌ JSON invalide: Vérifiez le format de vos chunks', 'error');
        return;
    }
    
    const payload = {
        index_name: indexName,
        chunks_list: chunks,
        n_variations_per_exercice: nVariations,
        temperature: temperature,
        return_all_latex: returnLatex
    };
    
    try {
        button.disabled = true;
        btnText.style.display = 'none';
        spinner.style.display = 'inline';
        
        document.getElementById('result-manual').style.display = 'none';
        
        const response = await fetch(`${API_BASE_URL}/generate/from-chunks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors de la génération');
        }
        
        const result = await response.json();
        
        currentResults['result-manual'] = result.latex_result;
        
        document.getElementById('manual-latex-content').textContent = result.latex_result;
        document.getElementById('result-manual').style.display = 'block';
        
        document.getElementById('result-manual').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        showToast('✅ LaTeX généré avec succès!', 'success');
        
    } catch (error) {
        showToast(`❌ Erreur: ${error.message}`, 'error');
        console.error('Erreur:', error);
    } finally {
        button.disabled = false;
        btnText.style.display = 'inline';
        spinner.style.display = 'none';
    }
}

// ============================================
// UTILITAIRES: TÉLÉCHARGEMENT
// ============================================

function downloadLatex(resultId) {
    const latexContent = currentResults[resultId];
    
    if (!latexContent) {
        showToast('❌ Aucun contenu à télécharger', 'error');
        return;
    }
    
    // Créer un nom de fichier avec timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `epreuve_${timestamp}.tex`;
    
    // Créer un blob et télécharger
    const blob = new Blob([latexContent], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    showToast(`✅ Fichier téléchargé: ${filename}`, 'success');
}

// ============================================
// UTILITAIRES: COPIER DANS LE PRESSE-PAPIERS
// ============================================

function copyToClipboard(resultId) {
    const latexContent = currentResults[resultId];
    
    if (!latexContent) {
        showToast('❌ Aucun contenu à copier', 'error');
        return;
    }
    
    navigator.clipboard.writeText(latexContent).then(() => {
        showToast('✅ Code LaTeX copié dans le presse-papiers', 'success');
    }).catch(err => {
        showToast('❌ Erreur lors de la copie', 'error');
        console.error('Erreur de copie:', err);
    });
}

// ============================================
// UTILITAIRES: NOTIFICATIONS TOAST
// ============================================

function showToast(message, type = 'success') {
    // Supprimer les toasts existants
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => toast.remove());
    
    // Créer le nouveau toast
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span style="font-size: 1.5rem;">${type === 'success' ? '✅' : '❌'}</span>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Supprimer après 4 secondes
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Animation de sortie pour le toast
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);