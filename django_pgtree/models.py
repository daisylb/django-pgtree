from django.contrib.postgres.indexes import GistIndex
from django.db import models
from django.db.transaction import atomic

from .fields import LtreeField

GAP = 10 ** 9
PAD_LENGTH = 18


class LtreeConcat(models.Func):
    arg_joiner = "||"
    template = "%(expressions)s"


class Subpath(models.Func):
    function = "subpath"


class Text2Ltree(models.Func):
    function = "text2ltree"


class DjPgTreeNext(models.Func):
    function = "djpgtree_next"


class TreeQuerySet(models.QuerySet):
    def roots(self):
        return self.filter(tree_path__matches_lquery=["*{1}"])


class TreeNode(models.Model):
    __new_parent = None
    tree_path = LtreeField(unique=True)

    objects = TreeQuerySet.as_manager()

    class Meta:
        abstract = True
        indexes = (GistIndex(fields=["tree_path"], name="tree_path_idx"),)
        ordering = ("tree_path",)

    def __init__(self, *args, parent=None, **kwargs):
        if parent is not None:
            self.__new_parent = parent
        super().__init__(*args, **kwargs)

    @property
    def parent(self):
        if self.__new_parent is not None:
            return self.__new_parent
        parent_path = self.tree_path[:-1]  # pylint: disable=unsubscriptable-object
        return self.__class__.objects.get(tree_path=parent_path)

    @parent.setter
    def parent(self, new_parent):
        if new_parent.tree_path is None:
            raise ValueError("Parent node must be saved before receiving children")
        # Replace our tree_path with a new one that has our new parent's
        self.__new_parent = new_parent

    def __next_tree_path_qx(self, prefix=()):
        return DjPgTreeNext(
            models.Value(self._meta.db_table),
            models.Value(".".join(prefix)),
            GAP,
            PAD_LENGTH,
        )

    def relocate(self, *, after=None, before=None):
        if after is None and before is None:
            raise ValueError("You must supply at least one of before or after")

        new_prev_child = after
        new_next_child = before

        if new_prev_child is None:
            new_prev_child = (
                new_next_child.siblings.filter(tree_path__lt=new_next_child.tree_path)
                .order_by("tree_path")
                .last()
            )
            # nb: if we are trying to move into the first position, after will be none

        if new_next_child is None:
            new_next_child = (
                new_prev_child.siblings.filter(tree_path__gt=new_prev_child.tree_path)
                .order_by("tree_path")
                .first()
            )
            if new_next_child is None:
                # this is the case where we want to move to the last position
                # we can just (re-)set the parent, since that's its default
                # behaviour
                self.parent = after.parent
                return

        if (
            new_next_child is not None
            and new_prev_child.tree_path[:-1] != new_next_child.tree_path[:-1]
        ):
            raise ValueError("Before and after nodes aren't actually siblings")

        next_v = int(new_next_child.tree_path[-1])
        if new_prev_child is None:
            self.tree_path = new_next_child.tree_path[:-1] + [
                str(next_v // 2).zfill(PAD_LENGTH)
            ]
        else:
            prev_v = int(new_prev_child.tree_path[-1])
            this_v = prev_v + (next_v - prev_v) // 2
            self.tree_path = new_prev_child.tree_path[:-1] + [
                str(this_v).zfill(PAD_LENGTH)
            ]

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        tree_path_needs_refresh = False
        old_tree_path = None

        if self.__new_parent is not None:
            tree_path_needs_refresh = True
            old_tree_path = self.tree_path or None
            self.tree_path = self.__next_tree_path_qx(self.__new_parent.tree_path)
        if not self.tree_path:
            tree_path_needs_refresh = True
            self.tree_path = self.__next_tree_path_qx()

        # If we haven't changed the parent, save as normal.
        if old_tree_path is None:
            rv = super().save(*args, **kwargs)

        # If we have, use a transaction to avoid other contexts seeing the intermediate
        # state where our descendants aren't connected to us.
        else:
            with atomic():
                rv = super().save(*args, **kwargs)
                # Move all of our descendants along with us, by substituting our old
                # ltree prefix with our new one, in every descendant that
                # has that prefix.
                self.refresh_from_db(fields=("tree_path",))
                tree_path_needs_refresh = False
                self.__class__.objects.filter(
                    tree_path__descendant_of=old_tree_path
                ).update(
                    tree_path=LtreeConcat(
                        models.Value(".".join(self.tree_path)),
                        Subpath(models.F("tree_path"), len(old_tree_path)),
                    )
                )

        if tree_path_needs_refresh:
            self.refresh_from_db(fields=("tree_path",))

        print(
            "for object {!r}, old_tree_path is {!r}, tree_path is {!r}".format(
                self, old_tree_path, self.tree_path
            )
        )
        return rv

    @property
    def ancestors(self):
        return self.__class__.objects.filter(
            tree_path__ancestor_of=self.tree_path
        ).exclude(pk=self.pk)

    @property
    def descendants(self):
        return self.__class__.objects.filter(
            tree_path__descendant_of=self.tree_path
        ).exclude(pk=self.pk)

    @property
    def children(self):
        return self.__class__.objects.filter(
            tree_path__matches_lquery=[*self.tree_path, "*{1}"]
        )

    @property
    def family(self):
        return self.__class__.objects.filter(
            models.Q(tree_path__ancestor_of=self.tree_path)
            | models.Q(tree_path__descendant_of=self.tree_path)
        )

    @property
    def siblings(self):
        return self.__class__.objects.filter(
            tree_path__matches_lquery=[*self.tree_path[:-1], "*{1}"]
        ).exclude(pk=self.pk)
