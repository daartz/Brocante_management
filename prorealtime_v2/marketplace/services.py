import csv
from decimal import Decimal
from io import BytesIO, StringIO

import stripe
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .models import OrganizerSubscription, Payment, Reservation, Spot


def build_confirmation_pdf(reservation):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    pdf.setTitle(f'Reservation {reservation.pk}')
    pdf.setFont('Helvetica-Bold', 18)
    pdf.drawString(50, height - 70, 'Confirmation de reservation brocante')
    pdf.setFont('Helvetica', 11)
    lines = [
        f'Evenement : {reservation.event.name}',
        f'Lieu : {reservation.event.venue_name} - {reservation.event.address}',
        f'Date : {reservation.event.starts_at:%d/%m/%Y %H:%M}',
        f'Exposant : {reservation.exhibitor_first_name} {reservation.exhibitor_last_name}',
        f'Email : {reservation.exhibitor_email}',
        f'Emplacement : {reservation.spot.number} / Zone {reservation.spot.zone.name}',
        f'Dimensions : {reservation.spot.width_m} m x {reservation.spot.depth_m} m',
        f'Montant : {reservation.total_amount} EUR',
        f'Statut : {reservation.get_status_display()}',
    ]
    y = height - 120
    for line in lines:
        pdf.drawString(50, y, line)
        y -= 24
    pdf.setFont('Helvetica-Oblique', 9)
    pdf.drawString(50, 70, 'Document genere automatiquement par Brocante Manager Premium.')
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.read()


def build_accounting_csv(event):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['date', 'reservation', 'exposant', 'email', 'emplacement', 'statut', 'montant', 'frais_plateforme', 'paiement'])
    for reservation in event.reservations.select_related('spot', 'payment').order_by('created_at'):
        writer.writerow([
            reservation.created_at.strftime('%Y-%m-%d %H:%M'),
            reservation.pk,
            f'{reservation.exhibitor_first_name} {reservation.exhibitor_last_name}',
            reservation.exhibitor_email,
            reservation.spot.number,
            reservation.get_status_display(),
            reservation.total_amount,
            reservation.platform_fee,
            getattr(reservation.payment, 'provider_reference', ''),
        ])
    return output.getvalue()


def build_accounting_pdf(event):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    pdf.setTitle(f'Export comptable {event.name}')
    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawString(40, height - 50, f'Export comptable - {event.name}')
    pdf.setFont('Helvetica', 9)
    y = height - 85
    total = Decimal('0.00')
    for reservation in event.reservations.select_related('spot').order_by('created_at'):
        if y < 60:
            pdf.showPage()
            y = height - 50
            pdf.setFont('Helvetica', 9)
        total += reservation.total_amount
        line = f'#{reservation.pk} | {reservation.created_at:%d/%m/%Y} | Stand {reservation.spot.number} | {reservation.exhibitor_last_name} | {reservation.total_amount} EUR'
        pdf.drawString(40, y, line[:115])
        y -= 16
    pdf.setFont('Helvetica-Bold', 11)
    pdf.drawString(40, y - 16, f'Total encaisse : {total} EUR')
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.read()


def send_reservation_confirmation(reservation):
    subject = f'Confirmation emplacement {reservation.spot.number} - {reservation.event.name}'
    text = (
        f'Bonjour {reservation.exhibitor_first_name},\n\n'
        f'Votre emplacement {reservation.spot.number} pour {reservation.event.name} est confirme.\n'
        f'Le PDF de confirmation est joint a cet email.\n\n'
        'Merci pour votre reservation.'
    )
    email = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[reservation.exhibitor_email],
        reply_to=[reservation.event.organizer.email],
    )
    email.attach(f'confirmation-{reservation.pk}.pdf', build_confirmation_pdf(reservation), 'application/pdf')
    email.send(fail_silently=False)


def confirm_reservation_payment(reservation, provider_reference):
    if reservation.status == Reservation.CONFIRMED and reservation.spot.status == Spot.PAID:
        return reservation.payment
    reservation.status = Reservation.CONFIRMED
    reservation.save(update_fields=['status'])
    reservation.spot.status = Spot.PAID
    reservation.spot.save(update_fields=['status'])
    payment, _ = Payment.objects.update_or_create(
        reservation=reservation,
        defaults={
            'amount': reservation.total_amount,
            'provider': Payment.STRIPE if provider_reference.startswith('cs_') or provider_reference.startswith('pi_') else Payment.SIMULATED,
            'status': Payment.SUCCEEDED,
            'provider_reference': provider_reference,
        },
    )
    send_reservation_confirmation(reservation)
    return payment


def create_checkout_session(request, reservation):
    success_url = request.build_absolute_uri(reverse('payment_success', kwargs={'pk': reservation.pk}))
    cancel_url = request.build_absolute_uri(reservation.event.get_absolute_url())
    if not settings.STRIPE_SECRET_KEY:
        confirm_reservation_payment(reservation, f'DEMO-{reservation.pk:06d}')
        return None
    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.create(
        mode='payment',
        payment_method_types=['card'],
        customer_email=reservation.exhibitor_email,
        line_items=[{
            'quantity': 1,
            'price_data': {
                'currency': 'eur',
                'unit_amount': int(reservation.total_amount * Decimal('100')),
                'product_data': {'name': f'{reservation.event.name} - emplacement {reservation.spot.number}'},
            },
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={'reservation_id': str(reservation.pk)},
    )
    Payment.objects.update_or_create(
        reservation=reservation,
        defaults={
            'amount': reservation.total_amount,
            'provider': Payment.STRIPE,
            'status': Payment.CREATED,
            'provider_reference': session.id,
        },
    )
    return session


def activate_subscription(organizer, plan, customer_id='', subscription_id=''):
    subscription, _ = OrganizerSubscription.objects.update_or_create(
        organizer=organizer,
        defaults={
            'plan': plan,
            'status': OrganizerSubscription.ACTIVE,
            'stripe_customer_id': customer_id,
            'stripe_subscription_id': subscription_id,
        },
    )
    return subscription


def create_billing_checkout_session(request, organizer, plan):
    if not settings.STRIPE_SECRET_KEY:
        activate_subscription(organizer, plan)
        return None
    if not plan.stripe_price_id:
        raise ValueError('Le plan SaaS doit avoir un stripe_price_id pour Stripe Billing.')
    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.create(
        mode='subscription',
        payment_method_types=['card'],
        customer_email=organizer.email,
        line_items=[{'price': plan.stripe_price_id, 'quantity': 1}],
        success_url=request.build_absolute_uri(reverse('organizer_dashboard', kwargs={'pk': organizer.pk})),
        cancel_url=request.build_absolute_uri(reverse('home')),
        metadata={'organizer_id': str(organizer.pk), 'plan_id': str(plan.pk), 'purpose': 'saas_subscription'},
        subscription_data={'metadata': {'organizer_id': str(organizer.pk), 'plan_id': str(plan.pk)}},
    )
    return session
