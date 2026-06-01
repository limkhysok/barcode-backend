from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_add_api_action_choices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useractivity',
            name='action',
            field=models.CharField(
                choices=[
                    ('login', 'Login'),
                    ('logout', 'Logout'),
                    ('login_failed', 'Login Failed'),
                    ('register', 'Register'),
                    ('profile_update', 'Profile Update'),
                    ('password_change', 'Password Change'),
                    ('user_created', 'User Created'),
                    ('user_updated', 'User Updated'),
                    ('user_deleted', 'User Deleted'),
                    ('product_created', 'Product Created'),
                    ('product_updated', 'Product Updated'),
                    ('product_deleted', 'Product Deleted'),
                    ('inventory_created', 'Inventory Created'),
                    ('inventory_updated', 'Inventory Updated'),
                    ('inventory_deleted', 'Inventory Deleted'),
                    ('transaction_created', 'Transaction Created'),
                    ('transaction_deleted', 'Transaction Deleted'),
                    ('transaction_exported', 'Transaction Exported'),
                ],
                max_length=50,
            ),
        ),
    ]
