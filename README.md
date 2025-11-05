# Geodraft

Geodraft est une plateforme SDI (Spatial Data Infrastructure) basée sur GeoNode, enrichie d'un système d'édition versionnée et de validation collaborative pour les données spatiales.

## Fonctionnalités principales

### Architecture

- **Coeur** : GeoNode 4.1.3
- **Base de données** : PostgreSQL avec extension PostGIS
- **Backend** : Django (intégré à GeoNode)
- **Frontend** : OpenLayers pour l'édition cartographique
- **Serveur cartographique** : GeoServer

### Système d'édition versionnée

Geodraft ajoute un système de versionnement de type Git pour les données spatiales vectorielles :

- **Branches d'édition** : Chaque utilisateur peut créer des branches pour éditer les données
- **Historique complet** : Toutes les modifications sont versionnées et tracées
- **Merge requests** : Fusion des modifications avec validation collaborative
- **Détection de conflits** : Gestion automatique des conflits géométriques et attributaires
- **Audit log** : Journal complet de toutes les actions

### Système de rôles et permissions

Geodraft implémente un système de rôles à 3 niveaux basé sur les groupes GeoNode :

#### 1. **Admin** (Administrateur)
- Gestion complète de la bibliothèque de données
- Création et suppression de jeux de données
- Gestion des utilisateurs (ajout, suppression, modification)
- Gestion des groupes (création, suppression)
- Attribution et révocation des rôles
- Validation de toutes les merge requests
- Accès à toutes les fonctionnalités

#### 2. **Validator** (Validateur)
- Validation des modifications faites par les editors de son/ses groupe(s)
- Approbation ou rejet des merge requests
- Édition des données de son/ses groupe(s)
- Création de branches
- Gestion de conflits

#### 3. **Editor** (Éditeur)
- Édition des données vectorielles de son/ses groupe(s)
- Création de branches d'édition
- Soumission de merge requests
- Modification de géométries et attributs

**Note importante** : Un utilisateur peut appartenir à plusieurs groupes avec des rôles différents dans chaque groupe.

## Installation

### Prérequis

- Docker et Docker Compose
- 4 Go de RAM minimum
- 10 Go d'espace disque

### Déploiement avec Docker

1. Cloner le dépôt :
```bash
git clone https://github.com/Maredius/geodraft.git
cd geodraft
```

2. Lancer les services :
```bash
docker-compose up -d
```

3. Créer un superutilisateur :
```bash
docker-compose exec django python manage.py createsuperuser
```

4. Accéder à l'application :
- GeoNode : http://localhost:8000
- GeoServer : http://localhost:8080/geoserver
- API Versioned Editing : http://localhost:8000/versioned-editing/api/

## Utilisation

### Pour les éditeurs (Editors)

1. **Accéder à un jeu de données vectoriel** dans GeoNode
2. **Cliquer sur le bouton "Edit (Versioned)"** pour lancer l'éditeur collaboratif
3. **Créer une branche** pour vos modifications :
   - Cliquer sur "New Branch"
   - Donner un nom et une description
4. **Éditer les données** :
   - Utiliser les outils de dessin (point, ligne, polygone)
   - Modifier les géométries existantes
   - Éditer les attributs
5. **Soumettre une merge request** :
   - Une fois les modifications terminées
   - Remplir le titre et la description
   - Assigner aux validators du groupe

### Pour les validateurs (Validators)

1. **Consulter les merge requests** en attente
2. **Examiner les modifications** :
   - Visualiser les changements sur la carte
   - Vérifier les attributs modifiés
   - Consulter l'historique des versions
3. **Gérer les conflits** si nécessaire :
   - Choisir la version à conserver
   - Ou résoudre manuellement
4. **Approuver ou rejeter** la merge request :
   - Approuver : les modifications sont fusionnées dans la branche master
   - Rejeter : l'éditeur doit revoir ses modifications

### Pour les administrateurs (Admins)

1. **Gestion des utilisateurs** :
   - Accéder à `/versioned-editing/admin/users/`
   - Assigner des rôles dans les groupes
   - Modifier les permissions

2. **Gestion des groupes** :
   - Accéder à `/versioned-editing/admin/groups/`
   - Créer des groupes de travail
   - Ajouter/retirer des membres
   - Définir les rôles de chaque membre

3. **Gestion de la bibliothèque** :
   - Ajouter des jeux de données vectorielles
   - Configurer les permissions par groupe
   - Activer l'édition versionnée

## API REST

L'API REST est disponible à `/versioned-editing/api/` avec les endpoints suivants :

### Branches
- `GET /api/branches/` - Liste des branches
- `POST /api/branches/` - Créer une branche
- `GET /api/branches/{id}/` - Détails d'une branche
- `DELETE /api/branches/{id}/soft_delete/` - Supprimer une branche

### Features (données spatiales)
- `GET /api/features/` - Liste des features
- `POST /api/features/` - Créer une feature
- `GET /api/features/{id}/` - Détails d'une feature
- `PUT /api/features/{id}/` - Modifier une feature (crée une nouvelle version)
- `DELETE /api/features/{id}/soft_delete/` - Supprimer une feature
- `GET /api/features/history/?feature_id={id}` - Historique d'une feature

### Merge Requests
- `GET /api/merge-requests/` - Liste des merge requests
- `POST /api/merge-requests/` - Créer une merge request
- `GET /api/merge-requests/{id}/` - Détails d'une merge request
- `POST /api/merge-requests/{id}/approve/` - Approuver
- `POST /api/merge-requests/{id}/reject/` - Rejeter
- `GET /api/merge-requests/{id}/conflicts/` - Conflits

## Configuration

Les paramètres de Geodraft peuvent être personnalisés dans `geodraft/settings.py` :

```python
VERSIONED_EDITING = {
    'ENABLE_AUTO_VERSIONING': True,
    'MAX_VERSIONS_PER_FEATURE': 100,
    'DEFAULT_BRANCH_NAME': 'master',
    'MERGE_STRATEGIES': ['auto', 'manual', 'theirs', 'ours'],
    'ENABLE_CONFLICT_DETECTION': True,
    'AUDIT_LOG_ENABLED': True,
}
```

## Architecture technique

```
geodraft/
├── docker-compose.yml          # Configuration Docker
├── Dockerfile                  # Image Django/GeoNode
├── nginx.conf                  # Configuration Nginx
└── geodraft/                   # Projet Django
    ├── settings.py            # Configuration principale
    ├── urls.py                # Routes principales
    └── versioned_editing/     # Application d'édition versionnée
        ├── models.py          # Modèles de données
        ├── views.py           # Vues web
        ├── api_views.py       # API REST
        ├── admin_views.py     # Vues d'administration
        ├── permissions.py     # Gestion des permissions
        ├── services.py        # Logique métier (merge, conflits)
        ├── serializers.py     # Sérialiseurs REST
        └── templates/         # Templates HTML
```

## Contribution

Les contributions sont les bienvenues ! Veuillez :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence [préciser la licence].

## Support

Pour toute question ou problème :
- Ouvrir une issue sur GitHub
- Consulter la documentation de GeoNode : https://docs.geonode.org/