# Brocante Manager Premium

Application Django autonome pour commercialiser des emplacements de brocante avec réservation en ligne, back-office organisateur, paiement Stripe-ready, confirmations PDF, exports comptables, facturation SaaS et choix entre trois niveaux de carte.

## Positionnement produit

Brocante Manager Premium est pensée comme une base SaaS prête à vendre : l’organisateur publie un événement, dessine ses zones, importe ou ajuste ses emplacements, ouvre les réservations et laisse les exposants réserver sur une interface ultra simple.

Fonctionnalités principales :

- page commerciale responsive pour présenter les brocantes publiées ;
- back-office Django pour gérer organisateurs, événements, zones, emplacements, réservations, paiements et plans SaaS ;
- espace organisateur authentifié avec dashboard, édition d’événement, import CSV, exports comptables et éditeur drag-and-drop ;
- trois modes de carte dans la même application : plan image simplifié, plan interactif premium et carte géographique ;
- réservation transactionnelle d’un emplacement pour éviter les doubles ventes ;
- Stripe Checkout pour les réservations avec confirmation stricte par webhook signé en production ;
- Stripe Billing pour les plans SaaS récurrents ;
- email transactionnel avec PDF de confirmation joint ;
- commande de génération de données de démonstration ;
- tests automatisés du parcours public et des protections organisateur.

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

## Espace organisateur

Après connexion, l’organisateur dispose d’un dashboard privé :

- suivi des recettes et du taux de remplissage ;
- modification des informations publiques de l’événement ;
- import CSV des emplacements ;
- éditeur drag-and-drop pour déplacer les stands sur le plan ;
- exports comptables CSV et PDF ;
- accès au rendu public de la carte.

Format CSV minimal :

```csv
zone,number,price,x,y,width,height,width_m,depth_m,status,electricity,vehicle_allowed
Allée A,A01,35,10,12,8,6,3,2.5,available,yes,yes
```

## Paiement et facturation Stripe

Deux flux Stripe sont préparés :

1. **Réservation exposant** : `create_checkout_session` crée un paiement ponctuel Stripe Checkout. En production stricte, la page de retour Stripe ne confirme pas seule la réservation : seul le webhook signé `stripe/webhook/` passe la réservation en confirmée/payée.
2. **Abonnement organisateur** : chaque `SubscriptionPlan` peut recevoir un `stripe_price_id` pour lancer Stripe Billing en mode `subscription`. Sans clé Stripe, le plan est activé en mode démo.

Variables Stripe importantes :

```bash
STRIPE_PUBLIC_KEY=pk_live_xxx
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRICT_STRIPE_WEBHOOKS=True
```

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
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRICT_STRIPE_WEBHOOKS=True
BROKANTE_PLATFORM_FEE_RATE=0.035
DEFAULT_FROM_EMAIL=reservations@brocante.example.com
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

La stack inclut WhiteNoise pour les fichiers statiques, `dj-database-url` pour PostgreSQL, Gunicorn pour un déploiement PaaS classique, Stripe pour l’encaissement et ReportLab pour les PDF.

## Modèle métier

- `Organizer` : structure organisatrice et paramètres de marque ;
- `Event` : brocante publiée, dates, lieu, mode de carte par défaut et conditions exposant ;
- `Zone` : quartier logique de la brocante avec couleur ;
- `Spot` : emplacement réservable, coordonnées sur carte, prix, dimensions et options ;
- `Reservation` : informations exposant, statut et frais plateforme ;
- `Payment` : trace de paiement simulée ou Stripe ;
- `SubscriptionPlan` : plan SaaS avec limites, fonctionnalités et `stripe_price_id` Stripe Billing ;
- `OrganizerSubscription` : abonnement actif ou en essai pour chaque organisateur.

## État des étapes commerciales

- Webhook Stripe signé : intégré pour confirmer les paiements côté serveur en production stricte.
- Éditeur drag-and-drop : intégré dans l’espace organisateur avec synchronisation automatique des coordonnées.
- Exports comptables CSV/PDF : intégrés depuis le dashboard organisateur.
- Facturation récurrente Stripe Billing : intégrée via les plans SaaS et `stripe_price_id`.
- Emails transactionnels : intégrés avec PDF de confirmation joint.
- Import CSV : intégré depuis l’espace organisateur.
