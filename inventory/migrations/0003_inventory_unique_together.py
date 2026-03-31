# Generated manually on 2026-03-31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_remove_inventory_order_date_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='inventory',
            unique_together={('product', 'site', 'location')},
        ),
    ]
