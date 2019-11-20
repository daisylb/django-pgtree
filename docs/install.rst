Installing django-pgtree
========================

Install the ``django-pgtree`` package from PyPI using your package manager of choice:

.. code-block:: sh

    $ pip install django-pgtree
    # or
    $ poetry add django-pgtree
    # or
    $ pipenv install django-pgtree


Then, add ``django_pgtree`` to ``INSTALLED_APPS``.

On your development database and when you first deploy, you'll also need to run the following SQL command on any database that's going to use django-pgtree fields or models:

.. code-block:: sql

    CREATE EXTENSION ltree;

This command needs to be run by the database superuser (usually the ``postgres`` user). If you know that your migrations will be run by this user, you can use our ``LtreeExtension`` migration operation (see more in :doc:`model`), but in most cases you'll need to do this when you create the database.

.. tip::

    If you know you'll be using the ltree extension on a lot of databases on the same machine, or you don't mind having it around unused sometimes, you can also run the above command on the ``template1`` database, and it will be automatically created on every new database on that machine from that point onwards.
