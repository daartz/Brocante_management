# Brocante Manager Premium

Application Django autonome pour commercialiser des emplacements de brocante avec réservation en ligne, back-office organisateur et choix entre trois niveaux de carte.

## Positionnement produit

Brocante Manager Premium est pensée comme une base SaaS prête à vendre : l’organisateur publie un événement, dessine ses zones, ouvre les emplacements et laisse les exposants réserver sur une interface ultra simple.

Fonctionnalités principales :

- page commerciale responsive pour présenter les brocantes publiées ;
- back-office Django pour gérer organisateurs, événements, zones, emplacements, réservations et paiements ;
- trois modes de carte dans la même application : plan image simplifié, plan interactif premium et carte géographique ;
- réservation transactionnelle d’un emplacement pour éviter les doubles ventes ;
- paiement simulé pour la démo et configuration Stripe-ready ;
- commande de génération de données de démonstration ;
- tests automatisés du parcours public.

## Installation rapide

```bash
cd prorealtime_v2
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Puis ouvrir <http://127.0.0.1:8000/>.

## Identifiants de démonstration

- URL admin : <http://127.0.0.1:8000/admin/>
- Utilisateur : `admin@brocante.test`
- Mot de passe : `BrocantePremium2026!`

## Configuration de production

Variables d’environnement recommandées :

```bash
SECRET_KEY=une-cle-secrete-longue
DEBUG=False
ALLOWED_HOSTS=brocante.example.com
CSRF_TRUSTED_ORIGINS=https://brocante.example.com
DATABASE_URL=postgres://user:password@host:5432/brocante
STRIPE_PUBLIC_KEY=pk_live_xxx
STRIPE_SECRET_KEY=sk_live_xxx
BROKANTE_PLATFORM_FEE_RATE=0.035
```

La stack inclut WhiteNoise pour les fichiers statiques, `dj-database-url` pour PostgreSQL et Gunicorn pour un déploiement PaaS classique.

## Modèle métier

- `Organizer` : structure organisatrice et paramètres de marque ;
- `Event` : brocante publiée, dates, lieu, mode de carte par défaut et conditions exposant ;
- `Zone` : quartier logique de la brocante avec couleur ;
- `Spot` : emplacement réservable, coordonnées sur carte, prix, dimensions et options ;
- `Reservation` : informations exposant, statut et frais plateforme ;
- `Payment` : trace de paiement simulée ou Stripe.

## Prochaines étapes commerciales

1. Brancher Stripe Checkout ou Payment Intents à la place du paiement simulé.
2. Ajouter l’envoi d’emails transactionnels avec PDF de confirmation.
3. Ajouter un module d’import CSV des emplacements et un éditeur visuel de carte.
4. Créer un espace organisateur authentifié hors admin Django.
5. Ajouter des plans tarifaires SaaS par nombre d’événements et d’emplacements.
