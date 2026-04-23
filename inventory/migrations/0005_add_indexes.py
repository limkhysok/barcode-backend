from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_alter_inventory_product_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventory',
            name='site',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='reorder_status',
            field=models.CharField(
                choices=[('Yes', 'Yes'), ('No', 'No')],
                db_index=True,
                default='No',
                max_length=3,
            ),
        ),
    ]
