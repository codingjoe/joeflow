# Generated by Django 3.1a1 on 2020-06-28 14:22

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("joeflow", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FailingWorkflowState",
            fields=[
                (
                    "workflow_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="joeflow.workflow",
                    ),
                ),
            ],
            bases=("joeflow.workflow",),
        ),
        migrations.CreateModel(
            name="GatewayWorkflowState",
            fields=[
                (
                    "workflow_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="joeflow.workflow",
                    ),
                ),
            ],
            bases=("joeflow.workflow",),
        ),
        migrations.CreateModel(
            name="LoopWorkflowState",
            fields=[
                (
                    "workflow_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="joeflow.workflow",
                    ),
                ),
                ("counter", models.PositiveIntegerField(default=0)),
            ],
            bases=("joeflow.workflow",),
        ),
        migrations.CreateModel(
            name="Shipment",
            fields=[
                (
                    "workflow_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="joeflow.workflow",
                    ),
                ),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("shipping_address", models.TextField()),
                ("tracking_code", models.TextField()),
            ],
            bases=("joeflow.workflow",),
        ),
        migrations.CreateModel(
            name="SimpleWorkflowState",
            fields=[
                (
                    "workflow_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="joeflow.workflow",
                    ),
                ),
            ],
            bases=("joeflow.workflow",),
        ),
        migrations.CreateModel(
            name="SplitJoinWorkflowState",
            fields=[
                (
                    "workflow_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="joeflow.workflow",
                    ),
                ),
                ("parallel_task_value", models.PositiveIntegerField(default=0)),
            ],
            bases=("joeflow.workflow",),
        ),
        migrations.CreateModel(
            name="TestWorkflowState",
            fields=[
                (
                    "workflow_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="joeflow.workflow",
                    ),
                ),
            ],
            bases=("joeflow.workflow",),
        ),
        migrations.CreateModel(
            name="WaitWorkflowState",
            fields=[
                (
                    "workflow_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="joeflow.workflow",
                    ),
                ),
                ("parallel_task_value", models.PositiveIntegerField(default=0)),
            ],
            bases=("joeflow.workflow",),
        ),
        migrations.CreateModel(
            name="WelcomeWorkflowState",
            fields=[
                (
                    "workflow_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="joeflow.workflow",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            bases=("joeflow.workflow",),
        ),
        migrations.CreateModel(
            name="FailingWorkflow",
            fields=[],
            options={"proxy": True, "indexes": [], "constraints": []},
            bases=("testapp.failingworkflowstate",),
        ),
        migrations.CreateModel(
            name="GatewayWorkflow",
            fields=[],
            options={"proxy": True, "indexes": [], "constraints": []},
            bases=("testapp.gatewayworkflowstate",),
        ),
        migrations.CreateModel(
            name="LoopWorkflow",
            fields=[],
            options={"proxy": True, "indexes": [], "constraints": []},
            bases=("testapp.loopworkflowstate",),
        ),
        migrations.CreateModel(
            name="ShippingWorkflow",
            fields=[],
            options={"proxy": True, "indexes": [], "constraints": []},
            bases=("testapp.shipment",),
        ),
        migrations.CreateModel(
            name="SimpleWorkflow",
            fields=[],
            options={"proxy": True, "indexes": [], "constraints": []},
            bases=("testapp.simpleworkflowstate",),
        ),
        migrations.CreateModel(
            name="SplitJoinWorkflow",
            fields=[],
            options={"proxy": True, "indexes": [], "constraints": []},
            bases=("testapp.splitjoinworkflowstate",),
        ),
        migrations.CreateModel(
            name="TestWorkflow",
            fields=[],
            options={"proxy": True, "indexes": [], "constraints": []},
            bases=("testapp.testworkflowstate",),
        ),
        migrations.CreateModel(
            name="WaitWorkflow",
            fields=[],
            options={"proxy": True, "indexes": [], "constraints": []},
            bases=("testapp.waitworkflowstate",),
        ),
        migrations.CreateModel(
            name="WelcomeWorkflow",
            fields=[],
            options={"proxy": True, "indexes": [], "constraints": []},
            bases=("testapp.welcomeworkflowstate",),
        ),
    ]
