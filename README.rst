django-pgtree
=============

A generic model for storing heirachial data in trees, using `PostgreSQL's built-in ltree data type <ltree_>`_, plus a ltree field for you to use on your own models.

Supports Django 2.0+ on Python 3.5+.

.. _ltree: https://www.postgresql.org/docs/current/static/ltree.html

.. code-block:: python
    :caption: models.py

    from django.db import models
    from django_pgtree.models import TreeNode

    class Organism(TreeNode):
        name = models.CharField()

.. code-block:: python

    >>> animal = Organism.objects.create(name="Animal")
    >>> mammal = Organism.objects.create(name="Mammal", parent=animal)
    >>> dog = Organism.objects.create(name="Dog", parent=mammal)
    >>> cat = Organism.objects.create(name="Cat", parent=mammal)

    >>> mammal.children
    [<Organism: Dog>, <Organism: Cat>]
    >>> dog.ancestors
    [<Organism: Animal>, <Organism: Mammal>]
    >>> cat.siblings
    [<Organism: Dog>]
