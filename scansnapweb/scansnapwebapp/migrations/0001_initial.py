# Generated by Django 5.2 on 2025-05-11 07:37

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Scan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('not_executed', 'Not_executed'), ('success', 'Success'), ('scanning', 'Scanning'), ('failed', 'Failed')], default='not_executed', max_length=16)),
                ('num_scanned_papers', models.IntegerField(default=0)),
                ('paper_width', models.IntegerField(default=0)),
                ('paper_height', models.IntegerField(default=0)),
                ('color', models.CharField(choices=[('color', 'Color'), ('grayscale', 'Grayscale')], default='color', max_length=16)),
                ('starting_page_number', models.IntegerField(default=1)),
                ('sides', models.CharField(choices=[('duplex', 'Duplex'), ('front', 'Front')], default='duplex', max_length=8)),
            ],
        ),
    ]
