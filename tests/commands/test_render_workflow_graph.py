import os
import tempfile
from pathlib import Path

from django.core.management import call_command


def test_call_no_args():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command("render_workflow_graph", "-d", tmp_dir)
    assert os.path.exists(str(tmp_dir / "testapp_simpleworkflow.mmd"))


def test_call_format_mermaid():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command("render_workflow_graph", "-d", tmp_dir, "-f", "mermaid")
    assert os.path.exists(str(tmp_dir / "testapp_simpleworkflow.mmd"))


def test_call_explicit_workflow():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command(
        "render_workflow_graph",
        "-d",
        tmp_dir,
        "testapp.loopworkflow",
        "testapp.splitjoinworkflow",
    )
    assert not os.path.exists(str(tmp_dir / "testapp_simpleworkflow.mmd"))
    assert os.path.exists(str(tmp_dir / "testapp_loopworkflow.mmd"))
    assert os.path.exists(str(tmp_dir / "testapp_splitjoinworkflow.mmd"))


def test_call_explicit_workflow_invalid():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command(
        "render_workflow_graph", "-d", tmp_dir, "auth.user", "testapp.splitjoinworkflow"
    )
    assert not os.path.exists(str(tmp_dir / "testapp_simpleworkflow.mmd"))
    assert not os.path.exists(str(tmp_dir / "auth_user.mmd"))
    assert os.path.exists(str(tmp_dir / "testapp_splitjoinworkflow.mmd"))
