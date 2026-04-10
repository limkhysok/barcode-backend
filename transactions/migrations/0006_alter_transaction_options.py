from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0005_add_indexes'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='transaction',
            options={'ordering': ['-transaction_date', '-id']},
        ),
    ]
