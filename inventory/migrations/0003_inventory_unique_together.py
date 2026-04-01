# Generated manually on 2026-03-31

from django.db import migrations


def remove_duplicate_inventory(apps, schema_editor):
    """
    Before adding the unique_together constraint, remove duplicate
    (product, site, location) rows. For each group of duplicates we
    keep the record with the highest quantity_on_hand (latest meaningful
    state). Ties are broken by keeping the highest id (most recently created).
    """
    inventory_model = apps.get_model('inventory', 'Inventory')

    seen = {}
    # Order so the record we want to KEEP comes last in each group.
    for inv in inventory_model.objects.order_by('product_id', 'site', 'location', 'quantity_on_hand', 'id'):
        key = (inv.product_id, inv.site, inv.location)
        if key in seen:
            # Delete the earlier/lower-quantity duplicate
            inventory_model.objects.filter(id=seen[key]).delete()
        seen[key] = inv.id


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_remove_inventory_order_date_and_more'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_inventory, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='inventory',
            unique_together={('product', 'site', 'location')},
        ),
    ]
