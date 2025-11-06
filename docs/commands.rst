===================
Management Commands
===================

.. automodule:: joeflow.management.commands

render_workflow_graph
---------------------

Render workflow graph to file::

    usage: manage.py render_workflow_graph [-h] [-f {svg,pdf,png}] [-d DIRECTORY]
                                          [-c] [model [model ...]]

    Render workflow graph to file.

    positional arguments:
      workflow              List of workflow to render in the form
                            app_label.workflow_name

    optional arguments:
      -h, --help            show this help message and exit
      -f {svg,pdf,png}, --format {svg,pdf,png}
                            Output file format. Default: svg
      -d DIRECTORY, --directory DIRECTORY
                            Output directory. Default is current working
                            directory.
      -c, --cleanup         Remove dot-files after rendering.
