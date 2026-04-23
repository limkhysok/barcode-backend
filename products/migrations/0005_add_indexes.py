from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_alter_product_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='product_name',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(
                choices=[('Fasteners', 'Fasteners'), ('Accessories', 'Accessories')],
                db_index=True,
                default='Fasteners',
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='supplier',
            field=models.CharField(db_index=True, max_length=255),
        ),
    ]
