# Architecture de Geodraft

## Vue d'ensemble

Geodraft est construit comme une **extension de GeoNode**, pas comme une application séparée. Le système d'édition versionnée s'intègre naturellement dans l'écosystème GeoNode existant.

## Stack technique

### Composants principaux

1. **GeoNode 4.1.3** (Cœur de l'application)
   - Framework Django pour la gestion des données spatiales
   - Interface utilisateur pour la découverte et visualisation des données
   - Système de permissions et groupes natif

2. **PostgreSQL + PostGIS** (Base de données)
   - Stockage des métadonnées GeoNode
   - Stockage des versions de features avec géométries
   - Support des index spatiaux pour les performances

3. **GeoServer 2.23.0** (Serveur cartographique)
   - Publication des couches WMS/WFS
   - Intégration avec les données PostGIS

4. **Django REST Framework** (API)
   - API RESTful pour l'édition collaborative
   - Sérialiseurs GeoJSON pour les données spatiales

5. **OpenLayers 8.2** (Client cartographique)
   - Outils d'édition vectorielle
   - Visualisation des branches et versions

6. **Nginx** (Reverse proxy)
   - Routage des requêtes vers Django et GeoServer
   - Gestion des fichiers statiques

## Architecture des données

### Modèle de données

```
┌─────────────────────────────────────────────────────────────┐
│                      GEONODE (Base)                          │
├─────────────────────────────────────────────────────────────┤
│  - Dataset (Layers)                                          │
│  - User (Django Auth)                                        │
│  - GroupProfile (Groupes GeoNode)                            │
│  - ResourceBase (Permissions)                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              VERSIONED EDITING (Extension)                   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │ UserRole                                              │   │
│  │ - user → User                                         │   │
│  │ - group → GroupProfile                                │   │
│  │ - role (admin/validator/editor)                       │   │
│  │ - can_approve_merges                                  │   │
│  │ - can_manage_branches                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                              ↓                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ EditBranch                                            │   │
│  │ - layer → Dataset                                     │   │
│  │ - group → GroupProfile                                │   │
│  │ - parent_branch → EditBranch (self)                   │   │
│  │ - created_by → User                                   │   │
│  │ - status (active/merged/closed/deleted)               │   │
│  └──────────────────────────────────────────────────────┘   │
│                              ↓                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ FeatureVersion                                        │   │
│  │ - branch → EditBranch                                 │   │
│  │ - feature_id (UUID stable)                            │   │
│  │ - version (integer)                                   │   │
│  │ - geometry (PostGIS)                                  │   │
│  │ - properties (JSONB)                                  │   │
│  │ - operation (CREATE/UPDATE/DELETE/MERGE)              │   │
│  │ - created_by → User                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                              ↓                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ MergeRequest                                          │   │
│  │ - source_branch → EditBranch                          │   │
│  │ - target_branch → EditBranch                          │   │
│  │ - status (pending/approved/rejected/merged/conflicts) │   │
│  │ - created_by → User                                   │   │
│  │ - reviewed_by → User                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                              ↓                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ MergeConflict                                         │   │
│  │ - merge_request → MergeRequest                        │   │
│  │ - feature_id                                          │   │
│  │ - conflict_type (GEOMETRY/PROPERTIES/BOTH/DELETE)     │   │
│  │ - source_version → FeatureVersion                     │   │
│  │ - target_version → FeatureVersion                     │   │
│  │ - resolved (boolean)                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                              ↓                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ AuditLog                                              │   │
│  │ - user → User                                         │   │
│  │ - action (CREATE_BRANCH/UPDATE_FEATURE/etc.)          │   │
│  │ - entity_type                                         │   │
│  │ - entity_id                                           │   │
│  │ - details (JSONB)                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Flux de travail

### 1. Édition collaborative

```
┌─────────────┐
│ Utilisateur │
│  (Editor)   │
└──────┬──────┘
       │
       ↓
┌──────────────────────────────────────────┐
│ 1. Accède à un layer vectoriel GeoNode   │
│    - Clique sur "Edit (Versioned)"       │
└──────────────┬───────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│ 2. Créer une branche d'édition           │
│    - Nom: "feature/ajout-batiments"      │
│    - Parent: master                      │
│    - Groupe: son groupe de travail       │
└──────────────┬───────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│ 3. Édite les données spatiales            │
│    - Dessine de nouvelles géométries     │
│    - Modifie des features existantes     │
│    - Chaque modification = nouvelle       │
│      version de FeatureVersion           │
└──────────────┬───────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│ 4. Soumet une Merge Request              │
│    - Source: sa branche                  │
│    - Target: master                      │
│    - Titre et description                │
└──────────────┬───────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│ Système détecte automatiquement          │
│ les conflits avec target branch          │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────┐
│   Validator     │
│  (du groupe)    │
└────────┬────────┘
         │
         ↓
┌──────────────────────────────────────────┐
│ 5. Examine la Merge Request              │
│    - Visualise les changements           │
│    - Résout les conflits si nécessaire   │
│    - Approuve ou rejette                 │
└──────────────┬───────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│ 6. Si approuvé: Merge automatique        │
│    - Les FeatureVersion sont copiées     │
│      vers la branche master              │
│    - La branche source est marquée       │
│      "merged"                            │
│    - Audit log enregistré                │
└──────────────────────────────────────────┘
```

### 2. Système de permissions

```
┌─────────────────────────────────────────────────────┐
│                      ADMIN                          │
├─────────────────────────────────────────────────────┤
│ Permissions:                                        │
│ - Gestion complète bibliothèque de données          │
│ - Création/suppression de groupes                   │
│ - Ajout/retrait d'utilisateurs                      │
│ - Attribution de rôles                              │
│ - Validation de toutes les MR                       │
│ - Accès à tout                                      │
└─────────────────────────────────────────────────────┘
                      ↓ délègue à
┌─────────────────────────────────────────────────────┐
│                   VALIDATOR                         │
├─────────────────────────────────────────────────────┤
│ Permissions (dans son/ses groupe(s)):               │
│ - Validation des MR des editors                     │
│ - can_approve_merges = True                         │
│ - Édition des données (comme editor)                │
│ - Résolution de conflits                            │
│ - Création de branches                              │
└─────────────────────────────────────────────────────┘
                      ↓ valide
┌─────────────────────────────────────────────────────┐
│                    EDITOR                           │
├─────────────────────────────────────────────────────┤
│ Permissions (dans son/ses groupe(s)):               │
│ - Édition des données vectorielles                  │
│ - Création de branches                              │
│ - Soumission de MR                                  │
│ - can_approve_merges = False                        │
└─────────────────────────────────────────────────────┘
```

### 3. Vérification des permissions

Le système vérifie les permissions à plusieurs niveaux :

```python
# Exemple: Peut-on créer une branche ?
def can_create_branch(user, layer):
    # 1. Est admin global ?
    if user.is_superuser:
        return True
    
    # 2. A-t-on un rôle admin dans un groupe ?
    if UserRole.objects.filter(user=user, role='admin').exists():
        return True
    
    # 3. Le layer appartient-il à un groupe où on est editor+ ?
    if layer.group:
        return UserRole.objects.filter(
            user=user,
            group=layer.group,
            role__in=['editor', 'validator', 'admin']
        ).exists()
    
    # 4. A-t-on la permission GeoNode ?
    return user.has_perm('change_resourcebase', layer.get_self_resource())
```

## Intégration avec GeoNode

### Points d'extension

1. **Dans les templates de layer detail** :
   ```django
   {% load versioned_editing_tags %}
   {% show_edit_button layer %}
   ```
   Ajoute le bouton "Edit (Versioned)" pour les layers vectoriels

2. **Dans les URLs** :
   ```python
   # geodraft/urls.py
   urlpatterns = [
       path('versioned-editing/', include('versioned_editing.urls')),
   ] + geonode_urlpatterns
   ```

3. **Dans les settings** :
   ```python
   INSTALLED_APPS += ('versioned_editing',)
   ```

4. **Signaux Django** :
   - Création automatique de la branche "master" quand un layer vectoriel est créé
   - Enregistrement dans l'audit log

## API REST

### Endpoints principaux

#### Branches
```
GET    /versioned-editing/api/branches/
POST   /versioned-editing/api/branches/
GET    /versioned-editing/api/branches/{id}/
DELETE /versioned-editing/api/branches/{id}/soft_delete/
```

#### Features
```
GET    /versioned-editing/api/features/
POST   /versioned-editing/api/features/
GET    /versioned-editing/api/features/{id}/
PUT    /versioned-editing/api/features/{id}/
DELETE /versioned-editing/api/features/{id}/soft_delete/
GET    /versioned-editing/api/features/history/?feature_id={id}
```

#### Merge Requests
```
GET    /versioned-editing/api/merge-requests/
POST   /versioned-editing/api/merge-requests/
GET    /versioned-editing/api/merge-requests/{id}/
POST   /versioned-editing/api/merge-requests/{id}/approve/
POST   /versioned-editing/api/merge-requests/{id}/reject/
GET    /versioned-editing/api/merge-requests/{id}/conflicts/
```

### Exemple d'utilisation

```javascript
// Créer une branche
const response = await fetch('/versioned-editing/api/branches/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
        name: 'feature/new-buildings',
        description: 'Adding new buildings',
        layer: layerId,
        group: groupId
    })
});

// Créer une feature
const feature = await fetch('/versioned-editing/api/features/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify({
        branch: branchId,
        geometry: {
            type: 'Point',
            coordinates: [2.3522, 48.8566]
        },
        properties: {
            name: 'Eiffel Tower',
            type: 'monument'
        }
    })
});
```

## Sécurité

### Protections mises en place

1. **Authentication** : Django session auth + permissions GeoNode
2. **CSRF Protection** : Tokens CSRF sur toutes les requêtes POST
3. **Permission checks** : À chaque niveau (view, API, service)
4. **Audit logging** : Toutes les actions sont tracées
5. **Soft deletes** : Les données ne sont jamais vraiment supprimées
6. **Versioning** : Historique complet, pas de perte de données

### Bonnes pratiques

- Les mots de passe doivent être changés en production (GeoServer, Django, DB)
- Utiliser HTTPS en production
- Limiter les origines CORS
- Configurer les ALLOWED_HOSTS correctement
- Sauvegarder régulièrement la base de données

## Performance

### Optimisations

1. **Index database** :
   - Index sur `feature_id` + `version`
   - Index spatial sur les géométries
   - Index sur les foreign keys

2. **Query optimization** :
   - `select_related()` pour les foreign keys
   - `prefetch_related()` pour les relations many-to-many
   - Pagination par défaut (50 items)

3. **Caching** :
   - Cache des permissions par utilisateur/groupe
   - Cache des branches actives

## Évolutions futures

### Fonctionnalités potentielles

1. **Notifications** : Alertes par email pour les validators
2. **Comments** : Commentaires sur les MR et features
3. **Labels/Tags** : Catégorisation des MR
4. **Webhooks** : Intégration avec systèmes externes
5. **Rapports** : Statistiques sur les contributions
6. **Mobile app** : Application mobile pour édition terrain
7. **Offline editing** : Édition hors ligne avec synchronisation
8. **3D support** : Support des géométries 3D

## Tests

### Structure de tests recommandée

```python
tests/
├── test_models.py           # Tests des modèles
├── test_permissions.py      # Tests des permissions
├── test_api.py             # Tests de l'API REST
├── test_services.py        # Tests de la logique métier
├── test_merge.py           # Tests du merge
└── test_conflicts.py       # Tests de détection de conflits
```

### Commandes de test

```bash
# Tous les tests
docker-compose exec django python manage.py test versioned_editing

# Tests spécifiques
docker-compose exec django python manage.py test versioned_editing.tests.test_permissions

# Avec coverage
docker-compose exec django coverage run --source='.' manage.py test versioned_editing
docker-compose exec django coverage report
```
