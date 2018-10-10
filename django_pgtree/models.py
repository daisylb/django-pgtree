from django.contrib.postgres.indexes import GistIndex
from django.db import models
from django.db.transaction import atomic
from django.utils.crypto import get_random_string

from .fields import LtreeField


class LtreeConcat(models.Func):
    arg_joiner = '||'
    template = '%(expressions)s'


class Subpath(models.Func):
    function = 'subpath'


class TreeNode(models.Model):
    __old_tree_path = None
    tree_path = LtreeField()

    class Meta:
        abstract = True
        indexes = (GistIndex(fields=['tree_path'], name='tree_path_idx'),)

    def __init__(self, *args, parent=None, **kwargs):
        if parent is not None:
            kwargs['tree_path'] = [*parent.tree_path,
                                   get_random_string(length=32)]
        super().__init__(*args, **kwargs)

    @property
    def parent(self):
        parent_path = self.tree_path[:-
                                     1]  # pylint: disable=unsubscriptable-object
        print(parent_path)
        return self.__class__.objects.get(tree_path=parent_path)

    @parent.setter
    def __set_parent(self, new_parent):
        if new_parent.tree_path is None:
            raise ValueError(
                "Parent node must be saved before receiving children")
        # Replace our tree_path with a new one that has our new parent's
        self.__old_tree_path = self.tree_path
        self.tree_path = [*new_parent.tree_path, get_random_string(length=32)]

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        if not self.tree_path:
            # Ensure that we have a tree_path set. We set a random one at this point,
            # because we don't know whether this node will become the parent of other
            # nodes down the track.
            self.tree_path = [get_random_string(length=32)]

        # If we haven't changed the parent, save as normal.
        if self.__old_tree_path is None:
            return super().save(*args, **kwargs)

        # If we have, use a transaction to avoid other contexts seeing the intermediate
        # state where our descendants aren't connected to us.
        with atomic():
            rv = super().save(*args, **kwargs)
            # Move all of our descendants along with us, by substituting our old ltree
            # prefix with our new one, in every descendant that has that prefix.
            self.__class__.objects.filter(
                tree_path__descendant_of=self.__old_tree_path
            ).update(
                tree_path=LtreeConcat(
                    '.'.join(self.tree_path),
                    Subpath(models.F('tree_path'), len(self.__old_tree_path)),
                )
            )
            return rv

    @property
    def ancestors(self):
        return self.__class__.objects.filter(tree_path__ancestor_of=self.tree_path).exclude(pk=self.pk)

    @property
    def descendants(self):
        return self.__class__.objects.filter(tree_path__descendant_of=self.tree_path).exclude(pk=self.pk)

    @property
    def children(self):
        return self.__class__.objects.filter(tree_path__matches_lquery=[*self.tree_path, '*{1}'])

    @property
    def family(self):
        return self.__class__.objects.filter(
            models.Q(tree_path__ancestor_of=self.tree_path) |
            models.Q(tree_path__descendant_of=self.tree_path)
        )

    @property
    def siblings(self):
        return self.__class__.objects.filter(tree_path__matches_lquery=[*self.tree_path[:-1], '*{1}']).exclude(pk=self.pk)
