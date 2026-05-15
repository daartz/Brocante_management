from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Event, Reservation, Spot, SubscriptionPlan


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class MarketplaceFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)

    def test_homepage_loads_published_event_and_plans(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Grande Brocante Premium Démo')
        self.assertContains(response, '3 niveaux de carte')
        self.assertContains(response, 'Plans SaaS commercialisables')
        self.assertEqual(SubscriptionPlan.objects.count(), 3)

    def test_reservation_marks_spot_as_paid_and_sends_pdf_email(self):
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
        reservation = Reservation.objects.get()
        self.assertEqual(spot.status, Spot.PAID)
        self.assertEqual(reservation.status, Reservation.CONFIRMED)
        self.assertEqual(reservation.payment.provider_reference, f'DEMO-{reservation.pk:06d}')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].attachments[0][2], 'application/pdf')

    def test_map_editor_requires_authenticated_organizer(self):
        event = Event.objects.get(slug='grande-brocante-demo')
        response = self.client.get(reverse('map_editor', kwargs={'event_id': event.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])
