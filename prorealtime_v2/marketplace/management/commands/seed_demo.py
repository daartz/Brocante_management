from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from marketplace.models import Event, Organizer, OrganizerSubscription, Spot, SubscriptionPlan, Zone


class Command(BaseCommand):
    help = 'Crée une brocante de démonstration premium avec zones, emplacements et admin.'

    def handle(self, *args, **options):
        User = get_user_model()
        admin, created = User.objects.get_or_create(
            username='admin@brocante.test',
            defaults={'email': 'admin@brocante.test', 'is_staff': True, 'is_superuser': True},
        )
        if created:
            admin.set_password('BrocantePremium2026!')
            admin.save()


        starter, _ = SubscriptionPlan.objects.update_or_create(
            code=SubscriptionPlan.STARTER,
            defaults={
                'name': 'Starter',
                'monthly_price': Decimal('29.00'),
                'max_events': 1,
                'max_spots_per_event': 120,
                'features': 'Réservation en ligne\nPlan image simplifié\nEmails de confirmation',
                'stripe_price_id': '',
            },
        )
        pro, _ = SubscriptionPlan.objects.update_or_create(
            code=SubscriptionPlan.PRO,
            defaults={
                'name': 'Pro',
                'monthly_price': Decimal('79.00'),
                'max_events': 5,
                'max_spots_per_event': 500,
                'features': 'Cartes interactives\nImport CSV\nDashboard organisateur\nPaiement Stripe',
                'stripe_price_id': '',
                'highlighted': True,
            },
        )
        SubscriptionPlan.objects.update_or_create(
            code=SubscriptionPlan.PREMIUM,
            defaults={
                'name': 'Premium',
                'monthly_price': Decimal('149.00'),
                'max_events': 20,
                'max_spots_per_event': 2000,
                'features': 'Carte géographique\nMulti-organisateurs\nSupport prioritaire\nExports comptables',
                'stripe_price_id': '',
            },
        )

        organizer, _ = Organizer.objects.get_or_create(
            owner=admin,
            name='Association Les Puces du Canal',
            defaults={'email': 'contact@brocante.test', 'phone': '01 23 45 67 89'},
        )

        OrganizerSubscription.objects.update_or_create(
            organizer=organizer,
            defaults={'plan': pro, 'status': OrganizerSubscription.TRIALING},
        )

        event, _ = Event.objects.update_or_create(
            slug='grande-brocante-demo',
            defaults={
                'organizer': organizer,
                'name': 'Grande Brocante Premium Démo',
                'status': Event.PUBLISHED,
                'description': 'Une démonstration complète avec réservation immédiate, zones thématiques et trois modes de carte.',
                'venue_name': 'Place du Marché',
                'address': '1 place du Marché, 75000 Paris',
                'starts_at': timezone.now() + timezone.timedelta(days=45),
                'ends_at': timezone.now() + timezone.timedelta(days=45, hours=9),
                'reservation_deadline': timezone.now() + timezone.timedelta(days=30),
                'default_map_mode': Event.MAP_CANVAS,
                'terms': 'Installation à partir de 6h30. Aucun véhicule ne reste sur site après 8h00 hors zone autorisée.',
            },
        )
        zones = [
            Zone.objects.update_or_create(event=event, name='Allée centrale', defaults={'color': '#0f766e', 'order': 1})[0],
            Zone.objects.update_or_create(event=event, name='Vintage & déco', defaults={'color': '#7c3aed', 'order': 2})[0],
            Zone.objects.update_or_create(event=event, name='Famille', defaults={'color': '#f59e0b', 'order': 3})[0],
        ]
        for row in range(4):
            for col in range(8):
                index = row * 8 + col + 1
                zone = zones[row % len(zones)]
                status = Spot.BLOCKED if index in (7, 18) else Spot.AVAILABLE
                if index in (3, 12, 24):
                    status = Spot.PAID
                Spot.objects.update_or_create(
                    event=event,
                    number=f'{index:02d}',
                    defaults={
                        'zone': zone,
                        'label': f'Stand {index:02d}',
                        'width_m': Decimal('3.00'),
                        'depth_m': Decimal('2.50'),
                        'price': Decimal('28.00') + Decimal(row * 6),
                        'status': status,
                        'x': Decimal(6 + col * 11),
                        'y': Decimal(10 + row * 20),
                        'map_width': Decimal('8.50'),
                        'map_height': Decimal('10.00'),
                        'latitude': Decimal('48.856600') + Decimal(row) / Decimal('1000'),
                        'longitude': Decimal('2.352200') + Decimal(col) / Decimal('1000'),
                        'electricity': row == 0,
                        'vehicle_allowed': row >= 2,
                    },
                )
        self.stdout.write(self.style.SUCCESS('Démo créée : admin@brocante.test / BrocantePremium2026!'))
