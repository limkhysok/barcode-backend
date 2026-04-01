import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
        ('transactions', '0002_transaction_total_value'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Remove old single-item fields from Transaction
        migrations.RemoveField(model_name='transaction', name='inventory'),
        migrations.RemoveField(model_name='transaction', name='quantity'),
        migrations.RemoveField(model_name='transaction', name='total_value'),

        # Remove choices constraint on transaction_type (validation now in serializer)
        migrations.AlterField(
            model_name='transaction',
            name='transaction_type',
            field=models.CharField(max_length=10),
        ),

        # Create TransactionItem table
        migrations.CreateModel(
            name='TransactionItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                ('cost_per_unit', models.DecimalField(decimal_places=2, max_digits=10)),
                ('transaction', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items',
                    to='transactions.transaction',
                )),
                ('inventory', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='inventory.inventory',
                )),
            ],
        ),
    ]
