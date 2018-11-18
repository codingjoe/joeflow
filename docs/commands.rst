===================
Management Commands
===================

.. automodule:: galahad.management.commands

render_process_graph
--------------------

Render process graph to file::

    usage: manage.py render_process_graph [-h] [-f {svg,pdf,png}] [-d DIRECTORY]
                                          [-c] [--version] [-v {0,1,2,3}]
                                          [--settings SETTINGS]
                                          [--pythonpath PYTHONPATH] [--traceback]
                                          [--no-color]
                                          [model [model ...]]

    Render process graph to file.

    positional arguments:
      model

    optional arguments:
      -h, --help            show this help message and exit
      -f {svg,pdf,png}, --format {svg,pdf,png}
                            Output file format. Default: svg
      -d DIRECTORY, --directory DIRECTORY
                            Output directory. Default is current working
                            directory.
      -c, --cleanup         Remove dot-files after rendering.
      --version             show program's version number and exit
      -v {0,1,2,3}, --verbosity {0,1,2,3}
                            Verbosity level; 0=minimal output, 1=normal output,
                            2=verbose output, 3=very verbose output
      --settings SETTINGS   The Python path to a settings module, e.g.
                            "myproject.settings.main". If this isn't provided, the
                            DJANGO_SETTINGS_MODULE environment variable will be
                            used.
      --pythonpath PYTHONPATH
                            A directory to add to the Python path, e.g.
                            "/home/djangoprojects/myproject".
      --traceback           Raise on CommandError exceptions
      --no-color            Don't colorize the command output.
