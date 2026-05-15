from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView, TemplateView, View

from .forms import ReservationForm
from .models import Event, Organizer, Payment, Reservation, Spot


class HomeView(ListView):
    template_name = 'marketplace/home.html'
    model = Event
    context_object_name = 'events'

    def get_queryset(self):
        return Event.objects.filter(status=Event.PUBLISHED).select_related('organizer').prefetch_related('spots')[:6]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {
            'events': Event.objects.filter(status=Event.PUBLISHED).count(),
            'spots': Spot.objects.count(),
            'reservations': Reservation.objects.exclude(status=Reservation.CANCELLED).count(),
        }
        return context


class EventDetailView(DetailView):
    template_name = 'marketplace/event_detail.html'
    model = Event
    context_object_name = 'event'

    def get_queryset(self):
        return Event.objects.select_related('organizer').prefetch_related('zones', 'spots')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        requested_mode = self.request.GET.get('mode')
        modes = [choice[0] for choice in Event.MAP_MODE_CHOICES]
        context['map_mode'] = requested_mode if requested_mode in modes else self.object.default_map_mode
        context['map_modes'] = Event.MAP_MODE_CHOICES
        context['spots'] = self.object.spots.select_related('zone').all()
        context['available_count'] = self.object.spots.filter(status=Spot.AVAILABLE).count()
        return context


class ReservationCreateView(View):
    template_name = 'marketplace/reservation_form.html'

    def get_event_and_spot(self, slug, spot_id):
        event = get_object_or_404(Event, slug=slug, status=Event.PUBLISHED)
        spot = get_object_or_404(Spot.objects.select_related('zone', 'event'), pk=spot_id, event=event)
        if not event.is_open:
            raise Http404('Les réservations sont fermées pour cet événement.')
        return event, spot

    def get(self, request, slug, spot_id):
        event, spot = self.get_event_and_spot(slug, spot_id)
        if not spot.is_bookable:
            messages.error(request, 'Cet emplacement n’est plus disponible.')
            return redirect(event.get_absolute_url())
        return self.render(request, event, spot, ReservationForm())

    def post(self, request, slug, spot_id):
        event, spot = self.get_event_and_spot(slug, spot_id)
        form = ReservationForm(request.POST)
        if not form.is_valid():
            return self.render(request, event, spot, form)
        with transaction.atomic():
            locked_spot = Spot.objects.select_for_update().get(pk=spot.pk)
            if not locked_spot.is_bookable:
                messages.error(request, 'Trop tard, cet emplacement vient d’être réservé.')
                return redirect(event.get_absolute_url())
            reservation = form.save(commit=False)
            reservation.event = event
            reservation.spot = locked_spot
            reservation.total_amount = locked_spot.price
            reservation.platform_fee = (locked_spot.price * Decimal(str(settings.BROKANTE_PLATFORM_FEE_RATE))).quantize(Decimal('0.01'))
            reservation.status = Reservation.CONFIRMED
            reservation.save()
            locked_spot.status = Spot.PAID
            locked_spot.save(update_fields=['status'])
            Payment.objects.create(
                reservation=reservation,
                amount=reservation.total_amount,
                provider=Payment.SIMULATED,
                status=Payment.SUCCEEDED,
                provider_reference=f'DEMO-{reservation.pk:06d}',
            )
        return redirect(reverse('reservation_success', kwargs={'pk': reservation.pk}))

    def render(self, request, event, spot, form):
        from django.shortcuts import render

        return render(request, self.template_name, {'event': event, 'spot': spot, 'form': form})


class ReservationSuccessView(DetailView):
    template_name = 'marketplace/reservation_success.html'
    model = Reservation
    context_object_name = 'reservation'

    def get_queryset(self):
        return Reservation.objects.select_related('event', 'spot', 'payment')


class OrganizerDashboardView(DetailView):
    template_name = 'marketplace/organizer_dashboard.html'
    model = Organizer
    context_object_name = 'organizer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        events = self.object.events.annotate(
            reservation_count=Count('reservations'),
            revenue=Sum('reservations__total_amount'),
        ).prefetch_related('spots')
        context['events'] = events
        context['total_revenue'] = sum((event.revenue or Decimal('0.00')) for event in events)
        return context
