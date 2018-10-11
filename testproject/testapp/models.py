from django.db import models

from django_pgtree.models import TreeNode


class TestModel(TreeNode):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name
