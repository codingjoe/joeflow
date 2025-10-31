===================
Management Commands
===================

.. automodule:: joeflow.management.commands

render_workflow_graph
---------------------

Render workflow graph to file::

    usage: manage.py render_workflow_graph [-h] [-f {mmd,mermaid}] [-d DIRECTORY]
                                          [workflow [workflow ...]]

    Render workflow graph to file in Mermaid format.

    positional arguments:
      workflow              List of workflow to render in the form
                            app_label.workflow_name

    optional arguments:
      -h, --help            show this help message and exit
      -f {mmd,mermaid}, --format {mmd,mermaid}
                            Output file format. Default: mmd (Mermaid markdown)
      -d DIRECTORY, --directory DIRECTORY
                            Output directory. Default is current working
                            directory.
