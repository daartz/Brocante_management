from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('marketplace', '0002_saas_plans')]

    operations = [
        migrations.AddField(
            model_name='subscriptionplan',
            name='stripe_price_id',
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name='organizersubscription',
            name='stripe_customer_id',
            field=models.CharField(blank=True, max_length=160),
        ),
    ]
