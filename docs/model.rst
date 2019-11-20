Using the abstract model
========================

This functionality is for when you want to model your data as a tree, of which model instances are nodes. All you need to do is subclass your model from :class:`django_pgtree.models.TreeNode`:

.. code-block:: python
    :caption: models.py

    from django.db import models
    from django_pgtree.models import TreeNode

    class Organism(TreeNode):
        name = models.CharField()

If you haven't manually run the SQL query ``CREATE EXTENSION ltree`` before, you can do it in migration script:

.. code-block:: python

    from django_pgtree.dbext import LtreeExtension

    class Migration(migrations.Migration):
        operations = [
            LtreeExtension(),
            # Other migration operations
        ]


You can create root nodes as you would like any other normal model:

.. code-block:: python

    >>> animal = Organism.objects.create(name='Animal')
    >>> plant = Organism()
    >>> plant.name = 'Plant'
    >>> plant.save()

Then, create child nodes by setting another instance of your model as its ``parent``:

.. code-block:: python

    >>> mammal = Organism.objects.create(name='Mammal', parent=animal)
    >>> marsupial = Organism()
    >>> marsupial.name = 'Marsupial'
    >>> marsupial.parent = animal
    >>> marsupial.save()

.. warning::

    The ``parent`` attribute isn't actually a model field that exists in the database; it's a constructor argument and writable property on the model instance. This means that you can assign to it on model instances, and pass it as an argument to your model's constructor or ``.objects.create()`` as we've done above, but you can't use it in calls to methods like ``.filter()``.

Model API reference
-------------------
