from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Event, OrganizerSubscription, Reservation, Spot, SubscriptionPlan


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

    def test_organizer_accounting_exports_require_login_then_return_files(self):
        event = Event.objects.get(slug='grande-brocante-demo')
        user = event.organizer.owner
        self.client.force_login(user)
        csv_response = self.client.get(reverse('accounting_csv', kwargs={'event_id': event.pk}))
        pdf_response = self.client.get(reverse('accounting_pdf', kwargs={'event_id': event.pk}))
        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(pdf_response.status_code, 200)
        self.assertIn('text/csv', csv_response['Content-Type'])
        self.assertEqual(pdf_response['Content-Type'], 'application/pdf')

    @override_settings(STRIPE_WEBHOOK_SECRET='whsec_test')
    def test_signed_stripe_webhook_confirms_pending_reservation(self):
        event = Event.objects.get(slug='grande-brocante-demo')
        spot = event.spots.filter(status=Spot.AVAILABLE).first()
        reservation = Reservation.objects.create(
            event=event,
            spot=spot,
            exhibitor_first_name='Sam',
            exhibitor_last_name='Durand',
            exhibitor_email='sam@example.com',
            exhibitor_phone='0600000001',
            items_description='Livres',
            status=Reservation.PENDING,
            total_amount=spot.price,
        )
        spot.status = Spot.RESERVED
        spot.save(update_fields=['status'])
        payload = {
            'type': 'checkout.session.completed',
            'data': {'object': {'id': 'cs_test_123', 'metadata': {'reservation_id': str(reservation.pk)}}},
        }
        with patch('marketplace.views.stripe.Webhook.construct_event', return_value=payload):
            response = self.client.post(reverse('stripe_webhook'), data=b'{}', content_type='application/json', HTTP_STRIPE_SIGNATURE='sig')
        reservation.refresh_from_db()
        spot.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(reservation.status, Reservation.CONFIRMED)
        self.assertEqual(spot.status, Spot.PAID)

    def test_billing_demo_activates_plan_for_logged_organizer(self):
        event = Event.objects.get(slug='grande-brocante-demo')
        user = event.organizer.owner
        plan = SubscriptionPlan.objects.get(code=SubscriptionPlan.PREMIUM)
        self.client.force_login(user)
        response = self.client.post(reverse('billing_checkout', kwargs={'plan_code': plan.code}))
        self.assertEqual(response.status_code, 302)
        event.organizer.subscription.refresh_from_db()
        self.assertEqual(event.organizer.subscription.plan, plan)
        self.assertEqual(event.organizer.subscription.status, OrganizerSubscription.ACTIVE)
