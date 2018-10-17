import pytest
from testproject.testapp.models import TestModel as T

pytestmark = pytest.mark.django_db


@pytest.fixture
def animal():
    animal = T.objects.create(name="Animal")
    mammal = T.objects.create(name="Mammal", parent=animal)
    T.objects.create(name="Cat", parent=mammal)
    T.objects.create(name="Dog", parent=mammal)
    T.objects.create(name="Seal", parent=mammal)
    T.objects.create(name="Bear", parent=mammal)
    marsupial = T.objects.create(name="Marsupial", parent=animal)
    T.objects.create(name="Koala", parent=marsupial)
    T.objects.create(name="Kangaroo", parent=marsupial)
    T.objects.create(name="Plant")
    return animal


def test_descendants(animal):
    assert [x.name for x in animal.descendants] == [
        "Mammal",
        "Cat",
        "Dog",
        "Seal",
        "Bear",
        "Marsupial",
        "Koala",
        "Kangaroo",
    ]


def test_ancestors(animal):
    koala = T.objects.get(name="Koala")
    assert [x.name for x in koala.ancestors] == ["Animal", "Marsupial"]


def test_parent(animal):
    mammal = T.objects.get(name="Mammal")
    assert mammal.parent == animal


def test_children(animal):
    assert [x.name for x in animal.children] == ["Mammal", "Marsupial"]


def test_family(animal):
    mammal = T.objects.get(name="Mammal")
    assert [x.name for x in mammal.family] == [
        "Animal",
        "Mammal",
        "Cat",
        "Dog",
        "Seal",
        "Bear",
    ]


def test_reparent(animal):
    marsupial = T.objects.get(name="Marsupial")
    mammal = T.objects.get(name="Mammal")

    dog = T.objects.get(name="Dog")
    dog_tree_path = dog.tree_path
    plant = T.objects.get(name="Plant")
    plant_tree_path = plant.tree_path

    marsupial.parent = mammal
    marsupial.save()

    assert marsupial.tree_path[:2] == mammal.tree_path
    koala = T.objects.get(name="Koala")
    assert koala.parent == marsupial
    assert koala.tree_path[:2] == mammal.tree_path
    assert mammal in koala.ancestors

    dog.refresh_from_db()
    assert dog.tree_path == dog_tree_path
    plant.refresh_from_db()
    assert plant.tree_path == plant_tree_path


def test_roots(animal):
    roots = T.objects.roots()
    assert [x.name for x in roots] == ["Animal", "Plant"]


def test_relocate_in_between(animal):
    seal = T.objects.get(name="Seal")
    cat = T.objects.get(name="Cat")
    seal.relocate(after=cat)
    seal.save()
    assert [x.name for x in cat.parent.children] == ["Cat", "Seal", "Dog", "Bear"]
