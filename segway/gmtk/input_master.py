#!/usr/bin/env python
from collections import OrderedDict

import numpy
from numpy import array, ndarray

DENSE_CPT_KIND = "DENSE_CPT"
MEAN_KIND = "MEAN"
COVAR_KIND = "COVAR"
DPMF_KIND = "DPMF"
NAME_COLLECTION_KIND = "NAME_COLLECTION"
DETERMINISTIC_CPT_KIND = "DETERMINISTIC_CPT"

INLINE_TMPL = "{}_IN_FILE inline\n\n"

def array2text(a):
    ndim = a.ndim
    if ndim == 1:
        return " ".join(map(str, a))
    else:
        delimiter = "\n" * (ndim - 1)
        return delimiter.join(array2text(row) for row in a)

class InputMaster(list):
    """
    Master class which contains a list of all sections present in the input
    master and is able to responsible for creating their string representation.
    """
    def __init__(self, *args, **kwargs):
        for item in args:
            if not isinstance(item, Section):
                raise ValueError("Only Section objects may be saved to an "
                                 "InputMaster object")
        super().__init__([*args], **kwargs)

    def __str__(self):
        return "\n".join([str(item) for item in self])

    def append(self, item):
        if not isinstance(item, Section):
            raise ValueError("Only Section objects may be saved to an "
                             "InputMaster object")
        list.append(self, item)


class Section(OrderedDict):
    """
    Defines a section, which contains gmtk objects of all the same type and
    supports writing them to file. This is a subclass of OrderedDict, where the
    keys are set to represent the object names, while their values will be a
    subclass of object.
    """
    def __init__(self, *args, **kwargs):
        kind = None
        for item in args:
            if (not type(item) is tuple or
                not len(item) == 2 or
                not type(item[0]) is str):
                raise ValueError("Section arguments must be tuple of length 2 "
                                 "with a str object name as the first")
            if not kind:
                kind = item[1].kind
            else:
                if not item[1].kind == kind:
                    raise ValueError("Object has incorrect kind")
        super().__init__([*args], **kwargs)

    def __str__(self):
        section_objects = []
        section_objects.append(str(len(self)))
        for index, object_name in enumerate(self):
            section_objects = section_objects + \
                list(map(str, [index, object_name, self[object_name]]))

        return "\n".join(section_objects)

    def kind(self):
        section_kind = None
        # Ensure all members of the section are the same kind
        for obj in self.values():
            if not section_kind:
                section_kind = obj.kind
            else:
                assert section_kind == obj.kind
        return section_kind

    def update(self, new_object):
        for item in new_object:
            if item[1].kind != self.kind():
                raise ValueError("Object has incorrect kind")
        super().update(new_object)


class InlineSection(Section):
    def __str__(self):
        header = INLINE_TMPL.format(self.kind())
        return "".join([header, Section.__str__(self)])


class FileSection(Section):
    def __init__(self, filename, items):
        raise NotImplementedError("Reading from file is not yet supported")


class Object(str):
    def __new__(cls, content, kind = None):
        return str.__new__(cls, content)

    def __init__(self, content, kind):
        self.kind = kind


class DeterministicCPT(list):
    """
    This object will use DT to specify the deterministic relationship between
    parent(s) DT object(s) and their child random variable

    input is a list in the following order:
    [num_parents, [parent_card, ...], self_card, child_name]

    For cardinalities and number of parents, object supports str or int
    The child name must be a str.

    TODO: If possible, ensure child is in fact a DT object. Difficult
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kind = DETERMINISTIC_CPT_KIND

        # The first element gives number of parents
        # Check if it is given as int and check list length, otherwise assume
        # It is a variable and pass
        if (self[0] is int and
            len(self) != self[0] + 3):
            raise ValueError("DeterministicCPT has a length of {} when {} was "
                             "expected".format(len(self), self[0] + 3))
        if type(self[-1]) != str:
            raise ValueError("Final list element is the child variable name, "
                             "must be a str")

    def __str__(self):
        output = map(str, self)

        return " ".join(output)


class NameCollection(list):
    """
    Name collections allow for the user to more easily specify large numbers
    of gmtk objects together at once.

    Input is list of all names in the collection
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.kind = NAME_COLLECTION_KIND

    def __str__(self):
        return "\n".join([str(len(self))] + [str(item) for item in self])


class Array(ndarray):
    def __new__(cls, *args, **kwargs):
        return array(*args, **kwargs).view(cls)

    def __str__(self):
        # 1 dimensional str representation covered here
        # Multidimensional vary between kinds and will have to be specified
        # in specific sub classes.
        assert(len(self.shape) <= 1)
        return " ".join([str(self.size), array2text(self)])


class DenseCPT(Array):
    def __array_finalize__(self, obj):
        self.kind = DENSE_CPT_KIND

    def __str__(self):
        # Find the number of parents, their cardinalities and this cardinality
        num_parents = str(len(self.shape)-1)
        shape_list = list(map(str, self.shape))
        shape_list.insert(0, num_parents)

        shape_line = " ".join(shape_list)
        return "\n".join([shape_line, array2text(self)])


class Mean(Array):
    def __array_finalize__(self, obj):
        self.kind = MEAN_KIND
        if obj.ndim != 1:
            raise ValueError("Mean object supplied must be one-dimensional")


class Covar(Array):
    def __array_finalize__(self, obj):
        self.kind = COVAR_KIND
        if obj.ndim != 1:
            raise ValueError("COVAR object supplied must be one-dimensional")
        if numpy.any(obj < 0):
            raise ValueError("Covariance values may not be less than 0")


class DPMF(Array):
    def __array_finalize__(self, obj):
        self.kind = DPMF_KIND
        if obj.ndim != 1:
            raise ValueError("DPMF object supplied must be one-dimensional")
