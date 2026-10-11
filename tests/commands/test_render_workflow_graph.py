import tempfile
from pathlib import Path

import pytest
from django.core.management import call_command

pytest.importorskip("graphviz")


def test_call_no_args():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command("render_workflow_graph", "-d", tmp_dir)
    assert (tmp_dir / "testapp_simpleworkflow.svg").exists()
    assert (tmp_dir / "testapp_simpleworkflow").exists()


def test_call_cleanup():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command("render_workflow_graph", "-d", tmp_dir, "-c")
    assert (tmp_dir / "testapp_simpleworkflow.svg").exists()
    assert not (tmp_dir / "testapp_simpleworkflow").exists()


def test_call_format_pdf():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command("render_workflow_graph", "-d", tmp_dir, "-f", "pdf")
    assert (tmp_dir / "testapp_simpleworkflow.pdf").exists()


def test_call_format_png():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command("render_workflow_graph", "-d", tmp_dir, "-f", "png")
    assert (tmp_dir / "testapp_simpleworkflow.png").exists()


def test_call_explicit_workflow():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command(
        "render_workflow_graph",
        "-d",
        tmp_dir,
        "testapp.loopworkflow",
        "testapp.splitjoinworkflow",
    )
    assert not (tmp_dir / "testapp_simpleworkflow.svg").exists()
    assert (tmp_dir / "testapp_loopworkflow.svg").exists()
    assert (tmp_dir / "testapp_splitjoinworkflow.svg").exists()


def test_call_explicit_workflow_invalid():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command(
        "render_workflow_graph", "-d", tmp_dir, "auth.user", "testapp.splitjoinworkflow"
    )
    assert not (tmp_dir / "testapp_simpleworkflow.svg").exists()
    assert not (tmp_dir / "auth_user.svg").exists()
    assert (tmp_dir / "testapp_splitjoinworkflow.svg").exists()
