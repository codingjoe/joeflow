===================
Management Commands
===================

.. automodule:: joeflow.management.commands

render_process_graph
--------------------

Render process graph to file::

    usage: manage.py render_process_graph [-h] [-f {svg,pdf,png}] [-d DIRECTORY]
                                          [-c] [model [model ...]]

    Render process graph to file.

    positional arguments:
      model                 List of models to render in the form
                            app_label.model_name

    optional arguments:
      -h, --help            show this help message and exit
      -f {svg,pdf,png}, --format {svg,pdf,png}
                            Output file format. Default: svg
      -d DIRECTORY, --directory DIRECTORY
                            Output directory. Default is current working
                            directory.
      -c, --cleanup         Remove dot-files after rendering.
