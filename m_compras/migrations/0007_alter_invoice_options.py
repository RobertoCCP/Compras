# Generated by Django 5.0 on 2024-01-03 01:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('m_compras', '0006_product_alter_invoice_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='invoice',
            options={'managed': False},
        ),
    ]