# Generated migration for FeeStructure and RoverFee models

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rovers', '0002_notice_fundtransaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeeStructure',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Fee Amount (BDT)')),
                ('frequency', models.CharField(choices=[('WEEKLY', 'Weekly'), ('MONTHLY', 'Monthly')], default='MONTHLY', max_length=10)),
                ('description', models.CharField(blank=True, help_text='e.g., Monthly Rover Fund, Weekly Dues', max_length=255)),
                ('is_active', models.BooleanField(default=True, help_text='Enable/disable fee collection')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Fee Structures',
            },
        ),
        migrations.CreateModel(
            name='RoverFee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('frequency', models.CharField(choices=[('WEEKLY', 'Weekly'), ('MONTHLY', 'Monthly')], max_length=10)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('PAID', 'Paid'), ('OVERDUE', 'Overdue')], default='PENDING', max_length=10)),
                ('due_date', models.DateField()),
                ('paid_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('rover', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fees', to='rovers.roverprofile')),
            ],
            options={
                'ordering': ['-due_date'],
            },
        ),
    ]
