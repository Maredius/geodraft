# Changelog

Tous les changements notables de ce projet seront documentés dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [1.0.0] - 2025-11-05

### Ajouté

#### Système d'édition versionnée
- Système de branches d'édition type Git pour les données spatiales vectorielles
- Versioning automatique des modifications (FeatureVersion)
- Merge requests pour validation collaborative
- Détection automatique des conflits géométriques et attributaires
- Résolution de conflits (source, target, ou manuelle)
- Historique complet des versions par feature

#### Système de rôles et permissions
- 3 niveaux d'utilisateurs : Admin, Validator, Editor
- UserRole : attribution de rôles par groupe
- Support multi-groupes par utilisateur
- Permissions granulaires (can_approve_merges, can_manage_branches)
- Intégration avec les groupes GeoNode natifs
- Gestion des permissions au niveau branche et merge request

#### API REST
- Endpoints pour branches (CRUD + soft delete)
- Endpoints pour features (CRUD + historique + soft delete)
- Endpoints pour merge requests (CRUD + approve/reject + conflicts)
- Sérialiseurs GeoJSON pour les données spatiales
- Authentification Django intégrée
- Pagination automatique (50 items/page)

#### Interface d'administration
- Dashboard admin pour gestion utilisateurs/groupes
- Interface de gestion des rôles
- Attribution de permissions par utilisateur/groupe
- Ajout/retrait d'utilisateurs dans les groupes
- Recherche d'utilisateurs (API)

#### Intégration GeoNode
- Bouton "Edit (Versioned)" sur les pages de détail des layers vectoriels
- Template tags personnalisés (show_edit_button)
- Signaux Django pour création automatique de branche master
- Utilisation des modèles GeoNode natifs (Dataset, GroupProfile, User)
- Respect des permissions GeoNode existantes

#### Audit et traçabilité
- AuditLog pour toutes les actions importantes
- Enregistrement de l'utilisateur, action, entité, et détails
- Soft delete (pas de suppression réelle de données)
- Historique complet consultable

#### Infrastructure
- Configuration Docker Compose (GeoNode, PostGIS, GeoServer, Nginx)
- Dockerfile optimisé basé sur geonode/geonode:4.1.3
- Configuration Nginx avec reverse proxy
- Configuration uWSGI pour Django
- Script de démarrage rapide (quickstart.sh)
- Fichier .env.example pour configuration

#### Documentation
- README.md complet avec guide d'utilisation
- ARCHITECTURE.md avec détails techniques
- DEPLOYMENT.md avec guide de déploiement production
- CONTRIBUTING.md pour les contributeurs
- CHANGELOG.md (ce fichier)
- Commentaires et docstrings dans le code

### Services métier
- ConflictDetector : détection intelligente des conflits
- MergeService : fusion de branches avec gestion des versions
- ConflictResolver : résolution de conflits multiples stratégies
- PermissionManager : gestion centralisée des permissions

### Modèles de données
- UserRole : rôles d'utilisateurs dans les groupes
- EditBranch : branches d'édition avec hiérarchie
- FeatureVersion : versions de features avec géométrie PostGIS
- MergeRequest : demandes de fusion avec workflow
- MergeConflict : conflits détectés et leur résolution
- AuditLog : journal d'audit complet

### À venir dans les prochaines versions

#### v1.1.0 (prévu)
- Templates HTML complets pour l'éditeur cartographique
- JavaScript OpenLayers pour édition interactive
- Interface de gestion des conflits en temps réel
- Notifications par email pour les validators

#### v1.2.0 (prévu)
- Tests unitaires et d'intégration complets
- Tests de performance et optimisations
- Cache des permissions
- Compression des anciennes versions

#### v2.0.0 (futur)
- Support des rasters versionnés
- Édition collaborative en temps réel
- Commentaires sur les merge requests
- Webhooks pour intégration externe
- Application mobile pour édition terrain
- Support édition hors ligne

## Types de changements

- `Ajouté` pour les nouvelles fonctionnalités
- `Modifié` pour les modifications de fonctionnalités existantes
- `Déprécié` pour les fonctionnalités bientôt supprimées
- `Supprimé` pour les fonctionnalités supprimées
- `Corrigé` pour les corrections de bugs
- `Sécurité` pour les vulnérabilités

## Liens

- [Repository GitHub](https://github.com/Maredius/geodraft)
- [Documentation](https://github.com/Maredius/geodraft/blob/main/README.md)
- [GeoNode](https://geonode.org/)
