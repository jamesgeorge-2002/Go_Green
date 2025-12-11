from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('user_dashboard', '0003_feedback_response'),
    ]

    operations = [
        migrations.AddField(
            model_name='pickuprequest',
            name='waste_weight',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Weight in kg', max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='reward',
            name='total_waste_collected',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='Total waste collected in kg', max_digits=10),
        ),
    ]