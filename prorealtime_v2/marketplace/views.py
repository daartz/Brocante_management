import csv
from decimal import Decimal
from io import TextIOWrapper

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, ListView, UpdateView, View

from .forms import EventForm, ReservationForm, SpotCSVImportForm, SpotMapFormSet
from .models import Event, Organizer, Reservation, Spot, SubscriptionPlan, Zone
from .services import confirm_reservation_payment, create_checkout_session


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
        context['plans'] = SubscriptionPlan.objects.all()
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
            reservation.status = Reservation.PENDING
            reservation.save()
            locked_spot.status = Spot.RESERVED
            locked_spot.save(update_fields=['status'])
        session = create_checkout_session(request, reservation)
        if session:
            return redirect(session.url)
        return redirect(reverse('reservation_success', kwargs={'pk': reservation.pk}))

    def render(self, request, event, spot, form):
        from django.shortcuts import render

        return render(request, self.template_name, {'event': event, 'spot': spot, 'form': form})


class PaymentSuccessView(DetailView):
    template_name = 'marketplace/payment_success.html'
    model = Reservation
    context_object_name = 'reservation'

    def get_queryset(self):
        return Reservation.objects.select_related('event', 'spot', 'spot__zone', 'payment')

    def get(self, request, *args, **kwargs):
        reservation = self.get_object()
        if reservation.status != Reservation.CONFIRMED:
            reference = getattr(reservation.payment, 'provider_reference', '') or f'DEMO-{reservation.pk:06d}'
            confirm_reservation_payment(reservation, reference)
        return redirect(reverse('reservation_success', kwargs={'pk': reservation.pk}))


class ReservationSuccessView(DetailView):
    template_name = 'marketplace/reservation_success.html'
    model = Reservation
    context_object_name = 'reservation'

    def get_queryset(self):
        return Reservation.objects.select_related('event', 'spot', 'spot__zone', 'payment')


class OrganizerDashboardView(LoginRequiredMixin, DetailView):
    template_name = 'marketplace/organizer_dashboard.html'
    model = Organizer
    context_object_name = 'organizer'

    def get_queryset(self):
        return Organizer.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        events = self.object.events.annotate(
            reservation_count=Count('reservations'),
            revenue=Sum('reservations__total_amount'),
        ).prefetch_related('spots')
        context['events'] = events
        context['total_revenue'] = sum((event.revenue or Decimal('0.00')) for event in events)
        return context


class OrganizerEventUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'marketplace/organizer_event_form.html'
    model = Event
    form_class = EventForm

    def get_queryset(self):
        return Event.objects.filter(organizer__owner=self.request.user)

    def get_success_url(self):
        messages.success(self.request, 'Événement mis à jour.')
        return reverse('organizer_dashboard', kwargs={'pk': self.object.organizer_id})


class SpotCSVImportView(LoginRequiredMixin, FormView):
    template_name = 'marketplace/spot_import.html'
    form_class = SpotCSVImportForm

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, pk=kwargs['event_id'], organizer__owner=request.user)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        imported = 0
        if form.cleaned_data['replace_existing']:
            self.event.spots.all().delete()
        wrapper = TextIOWrapper(form.cleaned_data['csv_file'].file, encoding='utf-8-sig')
        for row in csv.DictReader(wrapper):
            zone, _ = Zone.objects.get_or_create(
                event=self.event,
                name=row.get('zone') or 'Zone importée',
                defaults={'color': '#0f766e'},
            )
            Spot.objects.update_or_create(
                event=self.event,
                number=row['number'],
                defaults={
                    'zone': zone,
                    'price': Decimal(row.get('price') or '0'),
                    'x': Decimal(row.get('x') or '0'),
                    'y': Decimal(row.get('y') or '0'),
                    'map_width': Decimal(row.get('width') or '8'),
                    'map_height': Decimal(row.get('height') or '5'),
                    'width_m': Decimal(row.get('width_m') or '3'),
                    'depth_m': Decimal(row.get('depth_m') or '2'),
                    'status': row.get('status') or Spot.AVAILABLE,
                    'electricity': (row.get('electricity') or '').lower() in {'1', 'true', 'oui', 'yes'},
                    'vehicle_allowed': (row.get('vehicle_allowed') or 'true').lower() in {'1', 'true', 'oui', 'yes'},
                },
            )
            imported += 1
        messages.success(self.request, f'{imported} emplacements importés.')
        return redirect(reverse('map_editor', kwargs={'event_id': self.event.pk}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.event
        context['help_text'] = self.form_class.help_text
        return context


class MapEditorView(LoginRequiredMixin, View):
    template_name = 'marketplace/map_editor.html'

    def get_event(self, request, event_id):
        return get_object_or_404(Event, pk=event_id, organizer__owner=request.user)

    def get(self, request, event_id):
        event = self.get_event(request, event_id)
        formset = SpotMapFormSet(queryset=event.spots.select_related('zone').order_by('number'))
        return self.render(request, event, formset)

    def post(self, request, event_id):
        event = self.get_event(request, event_id)
        formset = SpotMapFormSet(request.POST, queryset=event.spots.select_related('zone').order_by('number'))
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Carte mise à jour.')
            return redirect(reverse('map_editor', kwargs={'event_id': event.pk}))
        return self.render(request, event, formset)

    def render(self, request, event, formset):
        from django.shortcuts import render

        return render(request, self.template_name, {'event': event, 'formset': formset, 'spots': event.spots.select_related('zone')})
