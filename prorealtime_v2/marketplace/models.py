from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Organizer(models.Model):
    name = models.CharField('nom public', max_length=160)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organizers')
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    brand_color = models.CharField(max_length=7, default='#155e75')
    stripe_account_id = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'organisateur'
        verbose_name_plural = 'organisateurs'

    def __str__(self):
        return self.name


class Event(models.Model):
    MAP_IMAGE = 'image'
    MAP_CANVAS = 'canvas'
    MAP_GEO = 'geo'
    MAP_MODE_CHOICES = [
        (MAP_IMAGE, 'Plan image simplifié'),
        (MAP_CANVAS, 'Plan interactif premium'),
        (MAP_GEO, 'Carte géographique'),
    ]
    DRAFT = 'draft'
    PUBLISHED = 'published'
    CLOSED = 'closed'
    STATUS_CHOICES = [(DRAFT, 'Brouillon'), (PUBLISHED, 'Publié'), (CLOSED, 'Fermé')]

    organizer = models.ForeignKey(Organizer, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=180)
    slug = models.SlugField(unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    description = models.TextField()
    venue_name = models.CharField(max_length=180)
    address = models.CharField(max_length=255)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    reservation_deadline = models.DateTimeField()
    default_map_mode = models.CharField(max_length=20, choices=MAP_MODE_CHOICES, default=MAP_CANVAS)
    plan_image = models.ImageField(upload_to='plans/', blank=True)
    center_latitude = models.DecimalField(max_digits=9, decimal_places=6, default=Decimal('48.856600'))
    center_longitude = models.DecimalField(max_digits=9, decimal_places=6, default=Decimal('2.352200'))
    terms = models.TextField('conditions exposant', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['starts_at']
        verbose_name = 'événement'
        verbose_name_plural = 'événements'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('event_detail', kwargs={'slug': self.slug})

    @property
    def is_open(self):
        return self.status == self.PUBLISHED and self.reservation_deadline >= timezone.now()

    @property
    def occupancy_rate(self):
        total = self.spots.count()
        if not total:
            return 0
        unavailable = self.spots.exclude(status=Spot.AVAILABLE).count()
        return round(unavailable * 100 / total)


class Zone(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='zones')
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    color = models.CharField(max_length=7, default='#0ea5e9')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'zone'
        verbose_name_plural = 'zones'

    def __str__(self):
        return f'{self.event} · {self.name}'


class Spot(models.Model):
    AVAILABLE = 'available'
    RESERVED = 'reserved'
    PAID = 'paid'
    BLOCKED = 'blocked'
    STATUS_CHOICES = [
        (AVAILABLE, 'Disponible'),
        (RESERVED, 'Réservé'),
        (PAID, 'Payé'),
        (BLOCKED, 'Bloqué'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='spots')
    zone = models.ForeignKey(Zone, on_delete=models.PROTECT, related_name='spots')
    number = models.CharField(max_length=30)
    label = models.CharField(max_length=100, blank=True)
    width_m = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('3.00'))
    depth_m = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('2.00'))
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=AVAILABLE)
    x = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    y = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    map_width = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('8.00'))
    map_height = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('5.00'))
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    electricity = models.BooleanField(default=False)
    vehicle_allowed = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['zone__order', 'number']
        unique_together = [('event', 'number')]
        verbose_name = 'emplacement'
        verbose_name_plural = 'emplacements'

    def __str__(self):
        return f'{self.event} · emplacement {self.number}'

    @property
    def area(self):
        return self.width_m * self.depth_m

    @property
    def is_bookable(self):
        return self.status == self.AVAILABLE and self.event.is_open


class Reservation(models.Model):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [(PENDING, 'À régler'), (CONFIRMED, 'Confirmée'), (CANCELLED, 'Annulée')]

    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name='reservations')
    spot = models.OneToOneField(Spot, on_delete=models.PROTECT, related_name='reservation')
    exhibitor_first_name = models.CharField(max_length=80)
    exhibitor_last_name = models.CharField(max_length=80)
    exhibitor_email = models.EmailField()
    exhibitor_phone = models.CharField(max_length=40)
    business_name = models.CharField(max_length=160, blank=True)
    items_description = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'réservation'
        verbose_name_plural = 'réservations'

    def __str__(self):
        return f'{self.exhibitor_last_name} · {self.event} · {self.spot.number}'


class Payment(models.Model):
    SIMULATED = 'simulated'
    STRIPE = 'stripe'
    PROVIDER_CHOICES = [(SIMULATED, 'Simulation'), (STRIPE, 'Stripe')]
    CREATED = 'created'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    STATUS_CHOICES = [(CREATED, 'Créé'), (SUCCEEDED, 'Réussi'), (FAILED, 'Échoué')]

    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE, related_name='payment')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default=SIMULATED)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SUCCEEDED)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    provider_reference = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'paiement'
        verbose_name_plural = 'paiements'

    def __str__(self):
        return f'{self.get_provider_display()} · {self.amount} €'


class SubscriptionPlan(models.Model):
    STARTER = 'starter'
    PRO = 'pro'
    PREMIUM = 'premium'
    CODE_CHOICES = [(STARTER, 'Starter'), (PRO, 'Pro'), (PREMIUM, 'Premium')]

    code = models.SlugField(max_length=40, unique=True, choices=CODE_CHOICES)
    name = models.CharField(max_length=80)
    monthly_price = models.DecimalField(max_digits=8, decimal_places=2)
    max_events = models.PositiveIntegerField(default=1)
    max_spots_per_event = models.PositiveIntegerField(default=100)
    features = models.TextField(help_text='Une fonctionnalité par ligne')
    highlighted = models.BooleanField(default=False)

    class Meta:
        ordering = ['monthly_price']
        verbose_name = 'plan SaaS'
        verbose_name_plural = 'plans SaaS'

    def __str__(self):
        return self.name

    @property
    def feature_list(self):
        return [line.strip() for line in self.features.splitlines() if line.strip()]


class OrganizerSubscription(models.Model):
    ACTIVE = 'active'
    TRIALING = 'trialing'
    PAST_DUE = 'past_due'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (ACTIVE, 'Actif'),
        (TRIALING, 'Essai'),
        (PAST_DUE, 'Paiement requis'),
        (CANCELLED, 'Annulé'),
    ]

    organizer = models.OneToOneField(Organizer, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=TRIALING)
    current_period_end = models.DateField(null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'abonnement organisateur'
        verbose_name_plural = 'abonnements organisateurs'

    def __str__(self):
        return f'{self.organizer} · {self.plan}'
