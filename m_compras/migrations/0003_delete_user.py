# Generated by Django 5.0 on 2023-12-31 02:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('m_compras', '0002_user'),
    ]

    operations = [
        migrations.DeleteModel(
            name='User',
        ),
    ]