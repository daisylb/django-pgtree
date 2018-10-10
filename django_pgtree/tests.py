import pytest

from testproject.testapp.models import TestModel as T

pytestmark = pytest.mark.django_db


@pytest.fixture
def animal():
    animal = T.objects.create(name='Animal')
    mammal = T.objects.create(name='Mammal', parent=animal)
    T.objects.create(name='Cat', parent=mammal)
    T.objects.create(name='Dog', parent=mammal)
    marsupial = T.objects.create(name='Marsupial', parent=animal)
    T.objects.create(name='Koala', parent=marsupial)
    T.objects.create(name='Kangaroo', parent=marsupial)
    T.objects.create(name='Plant')
    return animal


def test_descendants(animal):
    assert [x.name for x in animal.descendants] == [
        'Mammal', 'Cat', 'Dog', 'Marsupial', 'Koala', 'Kangaroo']


def test_ancestors(animal):
    koala = T.objects.get(name='Koala')
    assert [x.name for x in koala.ancestors] == ['Animal', 'Marsupial']


def test_parent(animal):
    mammal = T.objects.get(name='Mammal')
    assert mammal.parent == animal


def test_children(animal):
    assert [x.name for x in animal.children] == ['Mammal', 'Marsupial']


def test_family(animal):
    mammal = T.objects.get(name='Mammal')
    assert [x.name for x in mammal.family] == ['Animal', 'Mammal', 'Cat', 'Dog']

def test_reparent(animal):
    marsupial = T.objects.get(name='Marsupial')
    mammal = T.objects.get(name='Mammal')
    marsupial.parent = mammal
    marsupial.save()
    assert marsupial.tree_path[:2] == mammal.tree_path
    koala = T.objects.get(name='Koala')
    assert koala.parent == marsupial
    assert koala.tree_path[:2] == mammal.tree_path
    assert mammal in koala.ancestors


def test_top_level_ordering(animal):
    all_l = list(T.objects.all())
    assert all_l[0] == animal
    assert all_l[-1].name == 'Plant'