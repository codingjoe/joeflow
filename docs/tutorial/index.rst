.. _tutorial:

Tutorial
========

The following tutorial should give you a quick overview on how to write a
workflow, integrate it into your Django application and write robust and
automated tests.

Before we get started make sure you have the package installed. Simply install
the PyPi package…

.. code:: shell

    python3 -m pip install "joeflow[reversion,graphviz]"

…and add ``joeflow`` to the ``INSTALLED_APPS`` setting.

Machine tasks are executed asynchronously with `Django Tasks`_. Configure a
task backend in the ``TASKS`` setting and make sure the queue of the
``JOEFLOW_TASK_QUEUE_NAME`` setting is part of its ``QUEUES``.

.. seealso::
    If you don't have a task backend setup yet, follow the `Django Tasks`_
    documentation.

.. _Django Tasks: https://docs.djangoproject.com/en/stable/topics/tasks/

Once the setup is completed you can get started writing your first workflow!

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   workflow
   templates
   testing
