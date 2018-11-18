import os
import tempfile
from pathlib import Path

from django.core.management import call_command


def test_call_no_args():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command('render_process_graph', '-d', tmp_dir)
    assert os.path.exists(str(tmp_dir / 'testapp_simpleprocess.svg'))
    assert os.path.exists(str(tmp_dir / 'testapp_simpleprocess'))


def test_call_cleanup():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command('render_process_graph', '-d', tmp_dir, '-c')
    assert os.path.exists(str(tmp_dir / 'testapp_simpleprocess.svg'))
    assert not os.path.exists(str(tmp_dir / 'testapp_simpleprocess'))


def test_call_format_pdf():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command('render_process_graph', '-d', tmp_dir, '-f', 'pdf')
    assert os.path.exists(str(tmp_dir / 'testapp_simpleprocess.pdf'))


def test_call_format_png():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command('render_process_graph', '-d', tmp_dir, '-f', 'png')
    assert os.path.exists(str(tmp_dir / 'testapp_simpleprocess.png'))


def test_call_explicit_processes():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command('render_process_graph', '-d', tmp_dir, 'testapp.loopprocess', 'testapp.splitjoinprocess')
    assert not os.path.exists(str(tmp_dir / 'testapp_simpleprocess.svg'))
    assert os.path.exists(str(tmp_dir / 'testapp_loopprocess.svg'))
    assert os.path.exists(str(tmp_dir / 'testapp_splitjoinprocess.svg'))


def test_call_explicit_processes_invalid():
    tmp_dir = Path(tempfile.mkdtemp())
    call_command('render_process_graph', '-d', tmp_dir, 'auth.user', 'testapp.splitjoinprocess')
    assert not os.path.exists(str(tmp_dir / 'testapp_simpleprocess.svg'))
    assert not os.path.exists(str(tmp_dir / 'auth_user.svg'))
    assert os.path.exists(str(tmp_dir / 'testapp_splitjoinprocess.svg'))
