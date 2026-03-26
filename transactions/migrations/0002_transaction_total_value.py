from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='total_value',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=12),
        ),
    ]
