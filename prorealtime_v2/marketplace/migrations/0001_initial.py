# Generated for Brocante Manager Premium
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=180)),
                ('slug', models.SlugField(unique=True)),
                ('status', models.CharField(choices=[('draft', 'Brouillon'), ('published', 'Publié'), ('closed', 'Fermé')], default='draft', max_length=20)),
                ('description', models.TextField()),
                ('venue_name', models.CharField(max_length=180)),
                ('address', models.CharField(max_length=255)),
                ('starts_at', models.DateTimeField()),
                ('ends_at', models.DateTimeField()),
                ('reservation_deadline', models.DateTimeField()),
                ('default_map_mode', models.CharField(choices=[('image', 'Plan image simplifié'), ('canvas', 'Plan interactif premium'), ('geo', 'Carte géographique')], default='canvas', max_length=20)),
                ('plan_image', models.ImageField(blank=True, upload_to='plans/')),
                ('center_latitude', models.DecimalField(decimal_places=6, default=Decimal('48.856600'), max_digits=9)),
                ('center_longitude', models.DecimalField(decimal_places=6, default=Decimal('2.352200'), max_digits=9)),
                ('terms', models.TextField(blank=True, verbose_name='conditions exposant')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'événement', 'verbose_name_plural': 'événements', 'ordering': ['starts_at']},
        ),
        migrations.CreateModel(
            name='Organizer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=160, verbose_name='nom public')),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(blank=True, max_length=40)),
                ('brand_color', models.CharField(default='#155e75', max_length=7)),
                ('stripe_account_id', models.CharField(blank=True, max_length=120)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organizers', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'organisateur', 'verbose_name_plural': 'organisateurs'},
        ),
        migrations.CreateModel(
            name='Zone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('color', models.CharField(default='#0ea5e9', max_length=7)),
                ('order', models.PositiveIntegerField(default=0)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='zones', to='marketplace.event')),
            ],
            options={'verbose_name': 'zone', 'verbose_name_plural': 'zones', 'ordering': ['order', 'name']},
        ),
        migrations.AddField(
            model_name='event',
            name='organizer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='marketplace.organizer'),
        ),
        migrations.CreateModel(
            name='Spot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=30)),
                ('label', models.CharField(blank=True, max_length=100)),
                ('width_m', models.DecimalField(decimal_places=2, default=Decimal('3.00'), max_digits=5)),
                ('depth_m', models.DecimalField(decimal_places=2, default=Decimal('2.00'), max_digits=5)),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('status', models.CharField(choices=[('available', 'Disponible'), ('reserved', 'Réservé'), ('paid', 'Payé'), ('blocked', 'Bloqué')], default='available', max_length=20)),
                ('x', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=6)),
                ('y', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=6)),
                ('map_width', models.DecimalField(decimal_places=2, default=Decimal('8.00'), max_digits=6)),
                ('map_height', models.DecimalField(decimal_places=2, default=Decimal('5.00'), max_digits=6)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('electricity', models.BooleanField(default=False)),
                ('vehicle_allowed', models.BooleanField(default=True)),
                ('notes', models.CharField(blank=True, max_length=255)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='spots', to='marketplace.event')),
                ('zone', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='spots', to='marketplace.zone')),
            ],
            options={'verbose_name': 'emplacement', 'verbose_name_plural': 'emplacements', 'ordering': ['zone__order', 'number'], 'unique_together': {('event', 'number')}},
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('exhibitor_first_name', models.CharField(max_length=80)),
                ('exhibitor_last_name', models.CharField(max_length=80)),
                ('exhibitor_email', models.EmailField(max_length=254)),
                ('exhibitor_phone', models.CharField(max_length=40)),
                ('business_name', models.CharField(blank=True, max_length=160)),
                ('items_description', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('pending', 'À régler'), ('confirmed', 'Confirmée'), ('cancelled', 'Annulée')], default='pending', max_length=20)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=8)),
                ('platform_fee', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=8)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reservations', to='marketplace.event')),
                ('spot', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='reservation', to='marketplace.spot')),
            ],
            options={'verbose_name': 'réservation', 'verbose_name_plural': 'réservations', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(choices=[('simulated', 'Simulation'), ('stripe', 'Stripe')], default='simulated', max_length=20)),
                ('status', models.CharField(choices=[('created', 'Créé'), ('succeeded', 'Réussi'), ('failed', 'Échoué')], default='succeeded', max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=8)),
                ('provider_reference', models.CharField(blank=True, max_length=160)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reservation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment', to='marketplace.reservation')),
            ],
            options={'verbose_name': 'paiement', 'verbose_name_plural': 'paiements'},
        ),
    ]
