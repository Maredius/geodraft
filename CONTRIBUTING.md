# Contribuer à Geodraft

Merci de votre intérêt pour contribuer à Geodraft ! Ce document fournit des lignes directrices pour contribuer au projet.

## Code de conduite

En participant à ce projet, vous vous engagez à maintenir un environnement respectueux et inclusif pour tous.

## Comment contribuer

### Signaler un bug

Si vous trouvez un bug, veuillez ouvrir une issue avec :
- Un titre clair et descriptif
- Les étapes pour reproduire le problème
- Le comportement attendu vs le comportement observé
- Des captures d'écran si applicable
- Votre environnement (OS, version de Docker, etc.)

### Proposer une nouvelle fonctionnalité

Pour proposer une nouvelle fonctionnalité :
1. Ouvrez une issue pour discuter de l'idée
2. Attendez les retours avant de commencer le développement
3. Suivez les guidelines de développement ci-dessous

### Soumettre des modifications

1. **Forkez le projet**
   ```bash
   git clone https://github.com/votre-username/geodraft.git
   cd geodraft
   ```

2. **Créez une branche pour votre fonctionnalité**
   ```bash
   git checkout -b feature/ma-nouvelle-fonctionnalite
   ```

3. **Faites vos modifications**
   - Suivez les conventions de code (voir ci-dessous)
   - Ajoutez des tests si applicable
   - Mettez à jour la documentation

4. **Commitez vos changements**
   ```bash
   git add .
   git commit -m "Add: Description claire de la fonctionnalité"
   ```
   
   Conventions de commit :
   - `Add:` pour une nouvelle fonctionnalité
   - `Fix:` pour une correction de bug
   - `Update:` pour une mise à jour
   - `Refactor:` pour une refactorisation
   - `Docs:` pour la documentation
   - `Test:` pour les tests

5. **Poussez vers votre fork**
   ```bash
   git push origin feature/ma-nouvelle-fonctionnalite
   ```

6. **Ouvrez une Pull Request**
   - Décrivez clairement les changements
   - Référencez les issues liées
   - Incluez des captures d'écran si UI

## Standards de code

### Python / Django

Suivez [PEP 8](https://pep8.org/) :

```python
# Bon
def create_branch(user, layer, name, description=None):
    """
    Create a new edit branch for a layer.
    
    Args:
        user: User creating the branch
        layer: Dataset to create branch for
        name: Branch name
        description: Optional description
    
    Returns:
        EditBranch: Created branch instance
    """
    branch = EditBranch.objects.create(
        name=name,
        layer=layer,
        created_by=user,
        description=description
    )
    return branch

# Mauvais
def createBranch(u,l,n,d=None):
    b=EditBranch.objects.create(name=n,layer=l,created_by=u,description=d)
    return b
```

### JavaScript

Utilisez ES6+ et des noms descriptifs :

```javascript
// Bon
const createFeature = async (branchId, geometry, properties) => {
    const response = await fetch('/api/features/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ branchId, geometry, properties })
    });
    return response.json();
};

// Mauvais
function cf(b,g,p){return fetch('/api/features/',{method:'POST',body:JSON.stringify({branchId:b,geometry:g,properties:p})}).then(r=>r.json())}
```

### Documentation

- Documentez toutes les fonctions publiques
- Utilisez des docstrings Google style pour Python
- Commentez le code complexe
- Mettez à jour README.md si nécessaire

## Tests

### Exécuter les tests

```bash
# Tous les tests
docker-compose exec django python manage.py test versioned_editing

# Tests spécifiques
docker-compose exec django python manage.py test versioned_editing.tests.test_permissions

# Avec coverage
docker-compose exec django coverage run --source='versioned_editing' manage.py test versioned_editing
docker-compose exec django coverage report
```

### Écrire des tests

Chaque nouvelle fonctionnalité doit inclure des tests :

```python
from django.test import TestCase
from django.contrib.auth import get_user_model
from versioned_editing.models import EditBranch
from geonode.layers.models import Dataset

User = get_user_model()

class EditBranchTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.layer = Dataset.objects.create(
            name='test_layer',
            owner=self.user
        )
    
    def test_create_branch(self):
        """Test creating a new branch"""
        branch = EditBranch.objects.create(
            name='test_branch',
            layer=self.layer,
            created_by=self.user
        )
        self.assertEqual(branch.name, 'test_branch')
        self.assertEqual(branch.status, 'active')
    
    def test_is_master(self):
        """Test master branch detection"""
        master = EditBranch.objects.create(
            name='master',
            layer=self.layer,
            created_by=self.user,
            parent_branch=None
        )
        self.assertTrue(master.is_master())
```

## Structure du projet

```
geodraft/
├── geodraft/                      # Projet Django principal
│   ├── settings.py               # Configuration
│   ├── urls.py                   # Routes principales
│   └── versioned_editing/        # Application d'édition versionnée
│       ├── models.py             # Modèles de données
│       ├── views.py              # Vues web
│       ├── api_views.py          # API REST
│       ├── admin_views.py        # Administration
│       ├── permissions.py        # Gestion des permissions
│       ├── services.py           # Logique métier
│       ├── serializers.py        # Sérialiseurs API
│       ├── forms.py              # Formulaires Django
│       ├── urls.py               # Routes de l'app
│       ├── signals.py            # Signaux Django
│       ├── admin.py              # Config Django admin
│       ├── apps.py               # Config de l'app
│       ├── templates/            # Templates HTML
│       ├── static/               # CSS, JS, images
│       ├── templatetags/         # Tags de template personnalisés
│       └── tests/                # Tests unitaires
├── docker-compose.yml            # Configuration Docker
├── Dockerfile                    # Image Docker
├── requirements.txt              # Dépendances Python
├── README.md                     # Documentation principale
├── ARCHITECTURE.md               # Documentation technique
├── DEPLOYMENT.md                 # Guide de déploiement
└── CONTRIBUTING.md               # Ce fichier
```

## Processus de review

Toutes les Pull Requests seront reviewées par les mainteneurs. Le processus inclut :

1. **Code Review** : Vérification de la qualité du code
2. **Tests** : Les tests doivent passer
3. **Documentation** : La documentation doit être à jour
4. **Fonctionnalité** : La fonctionnalité doit correspondre aux specs

## Questions?

Si vous avez des questions :
- Ouvrez une issue avec le tag `question`
- Contactez les mainteneurs
- Consultez la documentation existante

## Licence

En contribuant à Geodraft, vous acceptez que vos contributions soient sous la même licence que le projet.

## Remerciements

Merci à tous les contributeurs qui aident à améliorer Geodraft ! 🎉
