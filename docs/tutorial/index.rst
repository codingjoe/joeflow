.. _tutorial:

Tutorial
========

The following tutorial should give you a quick overview on how to write a
workflow, integrate it into your Django application and write robust and
automated tests.

Before we get started make you you have the package installed. Simply install
the PyPi package…

.. code:: shell

    python3 -m pip install "joeflow[reversion,dramatiq,celery]"

…and add ``joeflow`` to the ``INSTALLED_APP`` setting. You will also need to have
celery setup.

.. seealso::
    If you don't have celery setup yet, simply follow their setup instructions
    for Django projects.

    https://celery.readthedocs.io/en/latest/django/first-steps-with-django.html

Once the setup is completed you can get started writing your first workflow!

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   workflow
   templates
   testing
