# Generated by Django 3.2 on 2021-04-22 13:47

import config_tables.admin
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('individuals', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BasicTicket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(db_index=True, max_length=50, verbose_name='titel')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='ticket created')),
                ('due_date', models.DateField(verbose_name='due to')),
                ('ticket_type', models.CharField(choices=[('basic', 'basic'), ('laser', 'laser gravure')], default='basic', editable=False, max_length=10, verbose_name='type')),
                ('current_state', models.CharField(choices=[('N', 'new'), ('C', 'audited'), ('A', 'in progress'), ('F', 'finished'), ('D', 'discarded')], default='N', max_length=2, verbose_name='current state')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='basicticket_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='creator')),
                ('directed_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='basicticket_directed_to_related', to=settings.AUTH_USER_MODEL, verbose_name='receiver')),
            ],
            options={
                'verbose_name': 'basic ticket',
                'verbose_name_plural': 'basic tickets',
            },
            bases=(models.Model, config_tables.admin.Configurable),
        ),
        migrations.CreateModel(
            name='LaserGravurTicket',
            fields=[
                ('basicticket_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='tickets.basicticket')),
            ],
            options={
                'verbose_name': 'laser gravure ticket',
                'verbose_name_plural': 'laser gravure tickets',
            },
            bases=('tickets.basicticket',),
        ),
        migrations.CreateModel(
            name='MyTicket',
            fields=[
            ],
            options={
                'verbose_name': 'ticket for me',
                'verbose_name_plural': 'tickets for me',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('tickets.basicticket',),
        ),
        migrations.CreateModel(
            name='Etikett_Individual',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('etikett_type', models.CharField(db_index=True, max_length=30, verbose_name='label type')),
                ('is_done', models.BooleanField(default=False, editable=False, verbose_name='is done')),
                ('individual', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='individuals.individual', verbose_name='individal')),
                ('LaserGravur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tickets.lasergravurticket')),
            ],
            options={
                'verbose_name': 'individual',
                'verbose_name_plural': 'individuals',
            },
            bases=(models.Model, config_tables.admin.Configurable),
        ),
    ]
