# Generated by Django 5.1.4 on 2025-01-08 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transit', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='transaction_id',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]
