# Generated by Django 3.2 on 2021-04-22 13:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('individuals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlantImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(blank=True, upload_to='pictures/PlantImages', verbose_name='image')),
                ('comment', models.CharField(blank=True, max_length=200, verbose_name='comment')),
                ('individual', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='individuals.individual')),
            ],
            options={
                'verbose_name': 'image',
                'verbose_name_plural': 'images',
            },
        ),
    ]
