# Generated by Django 5.0 on 2024-01-02 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('m_compras', '0005_alter_personal_options_alter_personal_email_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('prod_id', models.AutoField(primary_key=True, serialize=False)),
                ('prod_name', models.CharField(max_length=255)),
                ('prod_descripcion', models.CharField(max_length=300)),
                ('prod_cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('prod_pvp', models.DecimalField(decimal_places=2, max_digits=10)),
                ('prod_state', models.BooleanField()),
                ('prod_iva', models.BooleanField()),
            ],
            options={
                'db_table': 'Product',
                'managed': False,
            },
        ),
        migrations.AlterModelOptions(
            name='invoice',
            options={},
        ),
    ]