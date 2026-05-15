from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Event, Reservation, Spot


class MarketplaceFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)

    def test_homepage_loads_published_event(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Grande Brocante Premium Démo')
        self.assertContains(response, '3 niveaux de carte')

    def test_reservation_marks_spot_as_paid(self):
        event = Event.objects.get(slug='grande-brocante-demo')
        spot = event.spots.filter(status=Spot.AVAILABLE).first()
        response = self.client.post(
            reverse('reserve_spot', kwargs={'slug': event.slug, 'spot_id': spot.id}),
            {
                'exhibitor_first_name': 'Camille',
                'exhibitor_last_name': 'Martin',
                'exhibitor_email': 'camille@example.com',
                'exhibitor_phone': '0600000000',
                'business_name': 'Atelier Camille',
                'items_description': 'Décoration vintage',
                'accept_terms': 'on',
            },
        )
        self.assertEqual(response.status_code, 302)
        spot.refresh_from_db()
        self.assertEqual(spot.status, Spot.PAID)
        self.assertEqual(Reservation.objects.count(), 1)
