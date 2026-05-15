from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('marketplace', '0001_initial')]

    operations = [
        migrations.CreateModel(
            name='SubscriptionPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(choices=[('starter', 'Starter'), ('pro', 'Pro'), ('premium', 'Premium')], max_length=40, unique=True)),
                ('name', models.CharField(max_length=80)),
                ('monthly_price', models.DecimalField(decimal_places=2, max_digits=8)),
                ('max_events', models.PositiveIntegerField(default=1)),
                ('max_spots_per_event', models.PositiveIntegerField(default=100)),
                ('features', models.TextField(help_text='Une fonctionnalité par ligne')),
                ('highlighted', models.BooleanField(default=False)),
            ],
            options={'verbose_name': 'plan SaaS', 'verbose_name_plural': 'plans SaaS', 'ordering': ['monthly_price']},
        ),
        migrations.CreateModel(
            name='OrganizerSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('active', 'Actif'), ('trialing', 'Essai'), ('past_due', 'Paiement requis'), ('cancelled', 'Annulé')], default='trialing', max_length=20)),
                ('current_period_end', models.DateField(blank=True, null=True)),
                ('stripe_subscription_id', models.CharField(blank=True, max_length=160)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('organizer', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='marketplace.organizer')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subscriptions', to='marketplace.subscriptionplan')),
            ],
            options={'verbose_name': 'abonnement organisateur', 'verbose_name_plural': 'abonnements organisateurs'},
        ),
    ]
