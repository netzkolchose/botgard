# Generated by Django 3.2 on 2021-09-14 10:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seedcatalog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='seedcatalog',
            name='title',
            field=models.TextField(default='Botanic Garden', verbose_name='Title of catalog'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='seedcatalog',
            name='title_sub',
            field=models.TextField(null=True, blank=True, verbose_name='Sub-title of catalog', default="https://example.com"),
        ),
    ]
