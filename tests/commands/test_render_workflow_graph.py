import os
import tempfile
from pathlib import Path

import pytest
from django.core.management import call_command

pytest.importorskip("graphviz")


def test_call_no_args():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command("render_workflow_graph", "-d", tmp_dir)
    assert os.path.exists(str(tmp_dir / "testapp_simpleworkflow.svg"))
    assert os.path.exists(str(tmp_dir / "testapp_simpleworkflow"))


def test_call_cleanup():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command("render_workflow_graph", "-d", tmp_dir, "-c")
    assert os.path.exists(str(tmp_dir / "testapp_simpleworkflow.svg"))
    assert not os.path.exists(str(tmp_dir / "testapp_simpleworkflow"))


def test_call_format_pdf():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command("render_workflow_graph", "-d", tmp_dir, "-f", "pdf")
    assert os.path.exists(str(tmp_dir / "testapp_simpleworkflow.pdf"))


def test_call_format_png():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command("render_workflow_graph", "-d", tmp_dir, "-f", "png")
    assert os.path.exists(str(tmp_dir / "testapp_simpleworkflow.png"))


def test_call_explicit_workflow():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command(
        "render_workflow_graph",
        "-d",
        tmp_dir,
        "testapp.loopworkflow",
        "testapp.splitjoinworkflow",
    )
    assert not os.path.exists(str(tmp_dir / "testapp_simpleworkflow.svg"))
    assert os.path.exists(str(tmp_dir / "testapp_loopworkflow.svg"))
    assert os.path.exists(str(tmp_dir / "testapp_splitjoinworkflow.svg"))


def test_call_explicit_workflow_invalid():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command(
        "render_workflow_graph", "-d", tmp_dir, "auth.user", "testapp.splitjoinworkflow"
    )
    assert not os.path.exists(str(tmp_dir / "testapp_simpleworkflow.svg"))
    assert not os.path.exists(str(tmp_dir / "auth_user.svg"))
    assert os.path.exists(str(tmp_dir / "testapp_splitjoinworkflow.svg"))
