# Guide de déploiement Geodraft

## Déploiement en développement

### Prérequis

- Docker 20.10+
- Docker Compose 1.29+
- 4 Go RAM minimum
- 10 Go espace disque

### Installation rapide

```bash
# Cloner le dépôt
git clone https://github.com/Maredius/geodraft.git
cd geodraft

# Lancer les services
docker-compose up -d

# Attendre que les services démarrent (environ 2 minutes)
docker-compose logs -f django

# Créer les migrations
docker-compose exec django python manage.py makemigrations versioned_editing
docker-compose exec django python manage.py migrate

# Collecter les fichiers statiques
docker-compose exec django python manage.py collectstatic --noinput

# Créer un superutilisateur
docker-compose exec django python manage.py createsuperuser

# Charger les données de démo (optionnel)
docker-compose exec django python manage.py loaddata fixtures/demo_data.json
```

### Accès

- **GeoNode** : http://localhost:8000
- **GeoServer** : http://localhost:8080/geoserver (admin/geoserver)
- **API Versioned Editing** : http://localhost:8000/versioned-editing/api/
- **Admin Django** : http://localhost:8000/admin/
- **Admin Versioned Editing** : http://localhost:8000/versioned-editing/admin/

## Configuration initiale

### 1. Créer les groupes de travail

```bash
# Via l'interface web
# http://localhost:8000/groups/create/

# Ou via Django shell
docker-compose exec django python manage.py shell
```

```python
from geonode.groups.models import GroupProfile
from django.contrib.auth import get_user_model

User = get_user_model()

# Créer un groupe
group = GroupProfile.objects.create(
    title="Équipe Urbanisme",
    description="Groupe responsable des données d'urbanisme",
    access="public"
)
```

### 2. Assigner des rôles

```python
from versioned_editing.models import UserRole
from versioned_editing.permissions import PermissionManager

# Obtenir un utilisateur
user = User.objects.get(username='john')

# Assigner le rôle de validator
admin = User.objects.get(is_superuser=True)
PermissionManager.assign_role(
    admin_user=admin,
    target_user=user,
    group=group,
    role='validator'
)
```

### 3. Importer des données vectorielles

Via GeoNode :
1. Aller sur http://localhost:8000/layers/upload
2. Uploader un fichier Shapefile, GeoJSON, ou GeoPackage
3. Le système créera automatiquement une branche "master"

## Déploiement en production

### Configuration Docker Compose pour production

Créer un fichier `docker-compose.prod.yml` :

```yaml
version: '3.9'

services:
  db:
    image: geonode/postgis:15
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      GEONODE_DATABASE: ${DB_NAME}
      GEONODE_DATABASE_PASSWORD: ${DB_PASSWORD}
      GEONODE_GEODATABASE: ${GEODATABASE_NAME}
      GEONODE_GEODATABASE_PASSWORD: ${GEODATABASE_PASSWORD}
    volumes:
      - db_data:/var/lib/postgresql/data
      - db_backups:/pg_backups
    networks:
      - geodraft-network

  geoserver:
    image: geonode/geoserver:2.23.0
    restart: always
    environment:
      GEOSERVER_ADMIN_USER: ${GEOSERVER_ADMIN_USER}
      GEOSERVER_ADMIN_PASSWORD: ${GEOSERVER_ADMIN_PASSWORD}
      GEOSERVER_LOCATION: http://geoserver:8080/geoserver/
      PUBLIC_LOCATION: ${SITEURL}/geoserver/
      INITIAL_MEMORY: 2G
      MAXIMUM_MEMORY: 4G
    volumes:
      - geoserver_data:/geoserver_data/data
    networks:
      - geodraft-network

  django:
    build: .
    restart: always
    environment:
      DJANGO_SETTINGS_MODULE: geodraft.settings
      SECRET_KEY: ${SECRET_KEY}
      DEBUG: 'False'
      ALLOWED_HOSTS: ${ALLOWED_HOSTS}
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      GEODATABASE_URL: postgis://${DB_USER}:${GEODATABASE_PASSWORD}@db:5432/${GEODATABASE_NAME}
      GEOSERVER_LOCATION: http://geoserver:8080/geoserver/
      GEOSERVER_PUBLIC_LOCATION: ${SITEURL}/geoserver/
      GEOSERVER_ADMIN_USER: ${GEOSERVER_ADMIN_USER}
      GEOSERVER_ADMIN_PASSWORD: ${GEOSERVER_ADMIN_PASSWORD}
      SITEURL: ${SITEURL}
    volumes:
      - static_files:/mnt/volumes/statics
      - media_files:/mnt/volumes/media
    command: uwsgi --ini /usr/src/geodraft/uwsgi.ini
    networks:
      - geodraft-network

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/conf.d/default.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - static_files:/mnt/volumes/statics:ro
      - media_files:/mnt/volumes/media:ro
    networks:
      - geodraft-network
    depends_on:
      - django
      - geoserver

volumes:
  db_data:
  db_backups:
  geoserver_data:
  static_files:
  media_files:

networks:
  geodraft-network:
    driver: bridge
```

### Fichier .env pour la production

```bash
# Database
DB_USER=geodraft_prod
DB_PASSWORD=CHANGEME_STRONG_PASSWORD
DB_NAME=geodraft_prod
GEODATABASE_NAME=geodraft_data_prod
GEODATABASE_PASSWORD=CHANGEME_STRONG_PASSWORD

# Django
SECRET_KEY=CHANGEME_GENERATE_RANDOM_KEY
ALLOWED_HOSTS=geodraft.example.com,www.geodraft.example.com
SITEURL=https://geodraft.example.com/

# GeoServer
GEOSERVER_ADMIN_USER=admin
GEOSERVER_ADMIN_PASSWORD=CHANGEME_STRONG_PASSWORD
```

### Configuration Nginx avec SSL

Créer `nginx.prod.conf` :

```nginx
# Redirection HTTP vers HTTPS
server {
    listen 80;
    server_name geodraft.example.com;
    return 301 https://$server_name$request_uri;
}

# Configuration HTTPS
server {
    listen 443 ssl http2;
    server_name geodraft.example.com;
    
    # SSL
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    client_max_body_size 500M;
    client_body_buffer_size 256K;
    large_client_header_buffers 4 64k;

    # Logs
    access_log /var/log/nginx/geodraft_access.log;
    error_log /var/log/nginx/geodraft_error.log;

    # Static files
    location /static/ {
        alias /mnt/volumes/statics/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /mnt/volumes/media/;
        expires 7d;
    }

    # GeoServer
    location /geoserver/ {
        proxy_pass http://geoserver:8080/geoserver/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # Django application
    location / {
        proxy_pass http://django:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
```

### Déploiement

```bash
# Générer un SECRET_KEY
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Éditer .env avec les valeurs de production

# Lancer en production
docker-compose -f docker-compose.prod.yml up -d

# Migrations
docker-compose -f docker-compose.prod.yml exec django python manage.py migrate

# Collecter les statiques
docker-compose -f docker-compose.prod.yml exec django python manage.py collectstatic --noinput

# Créer superutilisateur
docker-compose -f docker-compose.prod.yml exec django python manage.py createsuperuser
```

## Sauvegardes

### Base de données

```bash
# Sauvegarde manuelle
docker-compose exec db pg_dump -U postgres geodraft > backup_$(date +%Y%m%d).sql

# Restauration
docker-compose exec -T db psql -U postgres geodraft < backup_20231115.sql

# Sauvegarde automatique (cron)
0 2 * * * cd /path/to/geodraft && docker-compose exec db pg_dump -U postgres geodraft | gzip > /backups/geodraft_$(date +\%Y\%m\%d).sql.gz
```

### Fichiers media et data

```bash
# Sauvegarde des volumes Docker
docker run --rm \
  -v geodraft_media_files:/data \
  -v /backups:/backup \
  alpine tar czf /backup/media_$(date +%Y%m%d).tar.gz /data

# Restauration
docker run --rm \
  -v geodraft_media_files:/data \
  -v /backups:/backup \
  alpine tar xzf /backup/media_20231115.tar.gz -C /
```

## Monitoring

### Logs

```bash
# Voir les logs en temps réel
docker-compose logs -f django

# Logs d'une période spécifique
docker-compose logs --since 2023-11-15T00:00:00 django

# Logs d'erreur uniquement
docker-compose logs django | grep ERROR
```

### Métriques

Ajouter au docker-compose :

```yaml
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## Maintenance

### Mise à jour

```bash
# Pull des nouvelles images
docker-compose pull

# Redémarrer les services
docker-compose up -d

# Appliquer les migrations
docker-compose exec django python manage.py migrate
```

### Nettoyage

```bash
# Supprimer les branches mergées anciennes (> 90 jours)
docker-compose exec django python manage.py shell
```

```python
from django.utils import timezone
from datetime import timedelta
from versioned_editing.models import EditBranch

old_date = timezone.now() - timedelta(days=90)
EditBranch.objects.filter(
    status='merged',
    merged_at__lt=old_date
).update(status='deleted')
```

### Optimisation de la base de données

```bash
# Vacuum de la base
docker-compose exec db psql -U postgres -d geodraft -c "VACUUM ANALYZE;"

# Reindex
docker-compose exec db psql -U postgres -d geodraft -c "REINDEX DATABASE geodraft;"
```

## Résolution de problèmes

### Les services ne démarrent pas

```bash
# Vérifier les logs
docker-compose logs

# Vérifier l'état des conteneurs
docker-compose ps

# Redémarrer complètement
docker-compose down
docker-compose up -d
```

### Erreur de migration

```bash
# Vérifier les migrations
docker-compose exec django python manage.py showmigrations

# Fake une migration si nécessaire
docker-compose exec django python manage.py migrate --fake versioned_editing 0001

# Recréer les migrations
docker-compose exec django python manage.py makemigrations versioned_editing
docker-compose exec django python manage.py migrate
```

### GeoServer ne répond pas

```bash
# Redémarrer GeoServer
docker-compose restart geoserver

# Vérifier les logs
docker-compose logs geoserver

# Augmenter la mémoire si nécessaire
# Éditer docker-compose.yml:
# INITIAL_MEMORY: 4G
# MAXIMUM_MEMORY: 8G
```

## Checklist de déploiement

- [ ] Modifier tous les mots de passe par défaut
- [ ] Générer un SECRET_KEY unique
- [ ] Configurer ALLOWED_HOSTS
- [ ] Activer HTTPS avec certificat SSL valide
- [ ] Configurer les sauvegardes automatiques
- [ ] Mettre en place le monitoring
- [ ] Tester la restauration depuis une sauvegarde
- [ ] Configurer les limites de ressources (CPU, RAM)
- [ ] Documenter la procédure de mise à jour
- [ ] Former les administrateurs
- [ ] Tester les permissions des utilisateurs
- [ ] Vérifier les logs d'erreur
- [ ] Configurer les alertes pour les erreurs critiques
