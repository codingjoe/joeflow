# Generated by Django 2.1.3 on 2018-11-13 14:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import galahad.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Process',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('started', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('completed', models.DateTimeField(blank=True, db_index=True, editable=False, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('node_name', models.TextField(db_index=True, editable=False)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('completed', models.DateTimeField(blank=True, db_index=True, editable=False, null=True)),
                ('failed', models.DateTimeField(blank=True, db_index=True, editable=False, null=True)),
                ('exception', models.TextField(blank=True)),
                ('stacktrace', models.TextField(blank=True)),
                ('_process', models.ForeignKey(db_column='process_id', editable=False, on_delete=django.db.models.deletion.CASCADE, to='galahad.Process')),
                ('assignees', models.ManyToManyField(related_name='galahad_task_set', to=settings.AUTH_USER_MODEL, verbose_name='assignees')),
                ('content_type', models.ForeignKey(editable=False, limit_choices_to=galahad.models.process_subclasses, on_delete=django.db.models.deletion.CASCADE, related_name='galahad_task_set', to='contenttypes.ContentType')),
                ('parent_task_set', models.ManyToManyField(editable=False, related_name='child_task_set', to='galahad.Task')),
            ],
            options={
                'default_manager_name': 'objects',
                'permissions': (('rerun', 'Can rerun failed tasks.'), ('override', 'Can override a process.')),
                'ordering': ('-completed', '-created'),
                'get_latest_by': ('created',),
            },
        ),
    ]
