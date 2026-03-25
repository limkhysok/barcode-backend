"""
Migration: fix productid db_column

The database already has the primary key column named 'id'.
This migration updates Django's migration state to recognise it as
'productid' (with db_column='id') without touching the database.
"""

import products.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0005_alter_product_barcode'),
    ]

    operations = [
        # Use SeparateDatabaseAndState so Django's state is updated
        # (id → productid with db_column='id') without running any SQL
        # that would conflict with the inventory FK constraint.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='product',
                    name='id',
                ),
                migrations.AddField(
                    model_name='product',
                    name='productid',
                    field=models.BigAutoField(db_column='id', primary_key=True, serialize=False),
                ),
            ],
            database_operations=[],
        ),
        # The barcode max_length changed from 15 → 20; apply that normally.
        migrations.AlterField(
            model_name='product',
            name='barcode',
            field=models.CharField(
                default=products.models.generate_barcode,
                help_text='Barcode format: SN-XXXXXX (Randomly generated)',
                max_length=20,
                unique=True,
            ),
        ),
    ]
