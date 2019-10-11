# Generated by Django 2.1.3 on 2018-11-29 15:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import joeflow.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Process',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
            ],
            options={
                'permissions': (('override', 'Can override a process.'),),
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('name', models.TextField(db_index=True, editable=False)),
                ('type', models.TextField(choices=[('human', 'human'), ('machine', 'machine')], db_index=True, editable=False)),
                ('status', models.TextField(choices=[('failed', 'failed'), ('succeeded', 'succeeded'), ('scheduled', 'scheduled'), ('canceled', 'canceled')], db_index=True, default='scheduled', editable=False)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, db_index=True)),
                ('completed', models.DateTimeField(blank=True, db_index=True, editable=False, null=True)),
                ('exception', models.TextField(blank=True)),
                ('stacktrace', models.TextField(blank=True)),
                ('_process', models.ForeignKey(db_column='process_id', editable=False, on_delete=django.db.models.deletion.CASCADE, to='joeflow.Process')),
                ('assignees', models.ManyToManyField(related_name='joeflow_assignee_task_set', to=settings.AUTH_USER_MODEL, verbose_name='assignees')),
                ('completed_by_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='joeflow_completed_by_task_set', to=settings.AUTH_USER_MODEL, verbose_name='completed by')),
                ('content_type', models.ForeignKey(editable=False, limit_choices_to=joeflow.models.process_subclasses, on_delete=django.db.models.deletion.CASCADE, related_name='joeflow_task_set', to='contenttypes.ContentType')),
                ('parent_task_set', models.ManyToManyField(editable=False, related_name='child_task_set', to='joeflow.Task')),
            ],
            options={
                'get_latest_by': ('created',),
                'permissions': (('rerun', 'Can rerun failed tasks.'), ('cancel', 'Can cancel failed tasks.')),
                'ordering': ('-completed', '-created'),
                'default_manager_name': 'objects',
            },
        ),
    ]
