.. _tutorial-templates:

Creating templates
==================

Your human tasks, like your `start` view will need a template. The template
name is similar as it is for a
:class:`CreateView<django.views.generic.edit.CreateView>` but with more
options. Default template names are::

    app_name/welcomeworkflow_start.html
    app_name/welcomeworkflow_form.html
    app_name/workflow_form.html

Django will search for a template precisely that order. This allows you to
create a base template for all human tasks but also override override them
individually should that be needed.

Following the example please
create a file named ``app_name/workflow_form.html`` in your template folder.
The ``app_nam`` should be replaced by the application name in which you crated
your Welcome workflow. Now fill the file with a simple form template:

.. code-block:: html

    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>Welcome Workflow</title>
    </head>
    <body>
      <form method="POST">
        {% csrf_token %}
        {{ form }}
        <input type="submit">
      </form>
    </body>
    </html>

Of course you can make it prettier, but this will work.

Besides the tasks a workflow comes with two more views by default. A workflow
detail view and a view to manually override the current workflow state.

The manual override view will also use the ``workflow_form.html`` template
that you have already created. You can of course create a more specific
template. Django will search for templates in the following order::

    app_name/welcomeworkflow_override.html
    app_name/workflow_override.html
    app_name/welcomeworkflow_form.html
    app_name/workflow_form.html

Last but not least you will need a template for the workflow detail view.
You don't really need to add anything here, but lets add a little information
to make your workflow feel more alive.

.. code-block:: html

    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Welcome Workflow</title>
    </head>
    <body>
      {{ object.get_instance_graph_svg }}
      <h1>{{ object }}</h1>
      <table>
        <thead>
        <tr>
          <th>id</th>
          <th>task name</th>
          <th>completed</th>
        </tr>
        </thead>
        <tbody>
        {% for task in object.task_set.all %}
        <tr>
          <td>{{ task.pk }}</td>
          <td>
            {% if task.get_absolute_url %}
            <a href="{{ task.get_absolute_url }}">
              {{ task.name }}
            </a>
            {% else %}
            {{ task.name }}
            {% endif %}
          </td>
          <td>{{ task.completed }}</td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
      <a href="{{ object.get_override_url }}">Override</a>
    </body>
    </html>

You are all set! Spin up your application and play around with it.
Once you are done come back to learn
:ref:`how to write tests in the next part of our tutorial<tutorial-testing>`.
