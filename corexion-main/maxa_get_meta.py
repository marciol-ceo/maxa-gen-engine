



import os
import numpy as np
from typing import List, Dict, Optional
from pinecone import Pinecone
import random  # <-- ajouté



def get_random_metadata_from_each_namespace(
    index_name: str,
    pinecone_api_key: Optional[str] = None,
    dimension: int = 1536
) -> List[Dict]:
    """
    Sélectionne aléatoirement un exercice dans chaque namespace et retourne TOUS ses chunks.
    
    Returns:
        Liste de dictionnaires avec:
        - chunk_text: le texte du chunk
        - chunk_index: le numéro du chunk
        - exercice: le numéro de l'exercice
        - epreuve: le nom de l'épreuve
        - date: la date de l'examen
    """
    api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)
    
    stats = index.describe_index_stats()
    namespaces = list(stats.get('namespaces', {}).keys())
    
    results = []
    
    for namespace in namespaces:
        # Première requête: sélectionner un chunk aléatoire
        random_vector = np.random.randn(dimension).tolist()
        
        query_result = index.query(
            vector=random_vector,
            namespace=namespace,
            top_k=1,
            include_metadata=True
        )
        
        if query_result['matches']:
            match = query_result['matches'][0]
            metadata = match['metadata']
            
            # Extraire l'identifiant de l'exercice
            exercice_id = metadata.get('exercice')
            ecole = metadata.get('ecole')
            date = metadata.get('date')
            epreuve = metadata.get('epreuve')
            total_chunks = metadata.get('total_chunks', 1)
            
            # Deuxième requête: récupérer TOUS les chunks de cet exercice
            all_chunks_query = index.query(
                vector=random_vector,
                namespace=namespace,
                filter={
                    "exercice": {"$eq": exercice_id},
                    "ecole": {"$eq": ecole},
                    "date": {"$eq": date},
                    "epreuve": {"$eq": epreuve}
                },
                top_k=total_chunks,
                include_metadata=True
            )
            
            # Ajouter tous les chunks avec les champs demandés
            for chunk_match in all_chunks_query['matches']:
                meta = chunk_match['metadata']
                results.append({
                    'chunk_text': meta.get('chunk_text', ''),
                    'chunk_index': meta.get('chunk_index', 0),
                    'exercice': meta.get('exercice', ''),
                    'epreuve': meta.get('epreuve', ''),
                    'date': meta.get('date', '')
                })
    
    # Trier par exercice puis par chunk_index
    results.sort(key=lambda x: (str(x['exercice']), x['chunk_index']))
    
    return results



def get_random_metadata_from_one_random_namespace(
    index_name: str,
    pinecone_api_key: Optional[str] = None,
    dimension: int = 1536
) -> List[Dict]:
    """
    Sélectionne aléatoirement UN namespace, puis un exercice aléatoire dans ce namespace,
    et retourne TOUS les chunks de cet exercice.
    
    Returns:
        Liste de dictionnaires avec:
        - chunk_text: le texte du chunk
        - chunk_index: le numéro du chunk
        - exercice: le numéro de l'exercice
        - epreuve: le nom de l'épreuve
        - date: la date de l'examen
    """
    api_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)
    
    stats = index.describe_index_stats()
    namespaces = list(stats.get('namespaces', {}).keys())
    
    if not namespaces:
        return []  # Aucun namespace trouvé
    
    # 🔁 Choisir un namespace au hasard
    selected_namespace = random.choice(namespaces)
    print(f"Namespace sélectionné aléatoirement : {selected_namespace}")
    
    results = []
    
    # Première requête: sélectionner un chunk aléatoire dans ce namespace
    random_vector = np.random.randn(dimension).tolist()
    
    query_result = index.query(
        vector=random_vector,
        namespace=selected_namespace,
        top_k=1,
        include_metadata=True
    )
    
    if not query_result['matches']:
        return []  # Aucun chunk trouvé dans ce namespace
    
    match = query_result['matches'][0]
    metadata = match['metadata']
    
    # Extraire les identifiants uniques de l'exercice
    exercice_id = metadata.get('exercice')
    ecole = metadata.get('ecole')
    date = metadata.get('date')
    epreuve = metadata.get('epreuve')
    total_chunks = metadata.get('total_chunks', 1)
    
    if exercice_id is None:
        return []  # Impossible d'identifier l'exercice

    # Deuxième requête: récupérer TOUS les chunks de cet exercice dans le même namespace
    all_chunks_query = index.query(
        vector=random_vector,  # peu importe le vecteur ici, on filtre
        namespace=selected_namespace,
        filter={
            "exercice": {"$eq": exercice_id},
            "ecole": {"$eq": ecole},
            "date": {"$eq": date},
            "epreuve": {"$eq": epreuve}
        },
        top_k=total_chunks,
        include_metadata=True
    )
    
    # Ajouter tous les chunks avec les champs demandés
    for chunk_match in all_chunks_query['matches']:
        meta = chunk_match['metadata']
        results.append({
            'chunk_text': meta.get('chunk_text', ''),
            'chunk_index': meta.get('chunk_index', 0),
            'exercice': meta.get('exercice', ''),
            'epreuve': meta.get('epreuve', ''),
            'date': meta.get('date', '')
        })
    
    # Trier par chunk_index
    results.sort(key=lambda x: x['chunk_index'])
    
    return results
