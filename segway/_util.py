#!/usr/bin/env python
from __future__ import division, with_statement

__version__ = "$Revision$"

# Copyright 2008-2009, 2011, 2012 Michael M. Hoffman <mmh1@washington.edu>

from collections import defaultdict
from contextlib import closing
from functools import partial
from gzip import open as _gzip_open
from itertools import repeat
from math import floor, log10
from os import extsep
import shutil
from string import Template
import sys
import re
from tempfile import mkdtemp

import colorbrewer
from numpy import (append, array, diff, empty, insert, intc, zeros)

from optbuild import Mixin_UseFullProgPath, OptionBuilder_ShortOptWithSpace_TF
from path import path
from pkg_resources import resource_filename, resource_string
from tables import Filters, NoSuchNodeError, openFile

# XXX: check that these are all in use

# these are loaded by other modules indirectly
# ignore PyFlakes warnings here

try:
    # Python 2.6
    PKG = __package__
except NameError:
    PKG = "segway"

PKG_DATA = ".".join([PKG, "data"])

FILTERS_GZIP = Filters(complevel=1)

EXT_BED = "bed"
EXT_LIST = "list"
EXT_INT = "int"
EXT_FLOAT = "float32"
EXT_GZ = "gz"
EXT_MASTER = "master"
EXT_PARAMS = "params"
EXT_TAB = "tab"

SUFFIX_BED = extsep + EXT_BED
SUFFIX_GZ = extsep + EXT_GZ
SUFFIX_TAB = extsep + EXT_TAB

DTYPE_IDENTIFY = intc
DTYPE_OBS_INT = intc
DTYPE_SEG_LEN = intc

DISTRIBUTION_NORM = "norm"
DISTRIBUTION_GAMMA = "gamma"
DISTRIBUTION_ASINH_NORMAL = "asinh_norm"

PREFIX_INPUT = "input"
PREFIX_LIKELIHOOD = "likelihood"
PREFIX_PARAMS = "params"

SUBDIRNAME_LOG = "log"
SUBDIRNAME_PARAMS = "params"

POSTERIOR_SCALE_FACTOR = 100.0

# sentinel values
ISLAND_BASE_NA = 0
ISLAND_LST_NA = 0

SEG_TABLE_WIDTH = 3
OFFSET_START = 0
OFFSET_END = 1
OFFSET_STEP = 2

data_filename = partial(resource_filename, PKG_DATA)
data_string = partial(resource_string, PKG_DATA)

NUM_COLORS = 8
SCHEME = colorbrewer.Dark2[NUM_COLORS]

KB = 2**10
MB = 2**20
GB = 2**30
TB = 2**40
PB = 2**50
EB = 2**60

OptionBuilder_GMTK = (Mixin_UseFullProgPath +
                      OptionBuilder_ShortOptWithSpace_TF)

VITERBI_PROG = OptionBuilder_GMTK("gmtkViterbi")
POSTERIOR_PROG = OptionBuilder_GMTK("gmtkJT")

BED_SCORE = "1000"
BED_STRAND = "."

# use the GMTK MissingFeatureScaledDiagGaussian feature?
USE_MFSDG = False

SUPERVISION_UNSUPERVISED = 0
SUPERVISION_SEMISUPERVISED = 1
SUPERVISION_SUPERVISED = 2

SUPERVISION_LABEL_OFFSET = 1

def extjoin(*args):
    return extsep.join(args)

def extjoin_not_none(*args):
    return extjoin(*[str(arg) for arg in args
                     if arg is not None])

# NamedTemporaryDir is based somewhat on Python 2.5.2
# tempfile._TemporaryFileWrapper
#
# Original Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006 Python
# Software Foundation; All Rights Reserved
#
# License at http://www.python.org/download/releases/2.5.2/license/

# XXX: submit for inclusion in core
# XXX: is this still in use?
class NamedTemporaryDir(object):
    def __init__(self, *args, **kwargs):
        self.name = mkdtemp(*args, **kwargs)
        self.close_called = False
        self.rmtree = shutil.rmtree # want a function, not an unbound method

    def __enter__(self):
        return self

    def close(self):
        if not self.close_called:
            self.close_called = True
            self.rmtree(self.name)

    def __del__(self):
        self.close()

    def __exit__(self, exc, value, tb):
        self.close()

def copy_attrs(src, dst, attrs):
    for attr in attrs:
        setattr(dst, attr, getattr(src, attr))

class Copier(object):
    copy_attrs = []

    def __init__(self, runner):
        # copy copy_attrs from runner to Copier instance
        copy_attrs(runner, self, self.copy_attrs)

class Saver(Copier):
    resource_name = None

    def make_mapping(self):
        """
        override in subclasses
        """
        pass

    def __call__(self, filename, *args, **kwargs):
        return save_template(filename, self.resource_name, self.make_mapping(),
                             *args, **kwargs)

class PassThroughDict(dict):
    def __missing__(self, key):
        return key

def die(msg=""):
    if msg:
        print >>sys.stderr, msg
    sys.exit(1)

def get_col_index(chromosome, trackname):
    return get_tracknames(chromosome).index(trackname)

def get_label_color(label):
    color = SCHEME[label % NUM_COLORS]

    return ",".join(map(str, color))

# XXX: suggest as default
def fill_array(scalar, shape, dtype=None, *args, **kwargs):
    if dtype is None:
        dtype = array(scalar).dtype

    res = empty(shape, dtype, *args, **kwargs)
    res.fill(scalar)

    return res

# XXX: suggest as default
def gzip_open(*args, **kwargs):
    return closing(_gzip_open(*args, **kwargs))

def is_gz_filename(filename):
    return filename.endswith(SUFFIX_GZ)

def maybe_gzip_open(filename, mode="r", *args, **kwargs):
    if filename == "-":
        if mode.startswith("U"):
            raise NotImplementedError("U mode not implemented")
        elif mode.startswith("w") or mode.startswith("a"):
            return sys.stdout
        elif mode.startswith("r"):
            if "+" in mode:
                raise NotImplementedError("+ mode not implemented")
            else:
                return sys.stdin
        else:
            raise ValueError("mode string must begin with one of 'r', 'w', or 'a'")

    if is_gz_filename(filename):
        return gzip_open(filename, mode, *args, **kwargs)

    return open(filename, mode, *args, **kwargs)

def constant(val):
    """
    constant values for defaultdict
    """
    return repeat(val).next

array_factory = constant(array([]))

# XXX: replace with genomedata.Chromosome.tracknames_continuous
def get_tracknames(chromosome):
    return chromosome.root._v_attrs.tracknames.tolist()

def init_num_obs(num_obs, continuous):
    curr_num_obs = continuous.shape[1]
    assert num_obs is None or num_obs == curr_num_obs

    return curr_num_obs

def new_extrema(func, data, extrema):
    curr_extrema = func(data, 0)

    return func([extrema, curr_extrema], 0)

# XXX: replace with iter(genomedata.Chromosome)
def walk_supercontigs(h5file):
    root = h5file.root

    for supercontig in h5file.walkGroups():
        if supercontig == root:
            continue

        yield supercontig

# XXX: replace with genomedata.Chromosome.itercontinuous
def walk_continuous_supercontigs(h5file):
    for supercontig in walk_supercontigs(h5file):
        try:
            yield supercontig, supercontig.continuous
        except NoSuchNodeError:
            continue

# XXX: duplicates bed.py?
def load_coords(filename):
    """
    returns: defaultdict
      keys: chrom
      values: array with one dimension 2 and the other number of coords
      default: array([])
    """
    if not filename:
        return

    coords = defaultdict(list)

    with maybe_gzip_open(filename) as infile:
        for line in infile:
            words = line.rstrip().split()
            chrom = words[0]
            start = int(words[1])
            end = int(words[2])

            coords[chrom].append((start, end))

    return defaultdict(array_factory, ((chrom, array(coords_list))
                       for chrom, coords_list in coords.iteritems()))

def get_chrom_coords(coords, chrom):
    """
    returns empty array if there are no coords on that chromosome
    returns None if there are no coords whatsoever
    """
    if coords:
        return coords[chrom]

def is_empty_array(arr):
    try:
        return arr.shape == (0,)
    except AttributeError:
        return False

def chrom_name(filename):
    return path(filename).namebase

# XXX: replace with stuff from prep_observations()
def iter_chroms_coords(filenames, coords):
    for filename in filenames:
        print >>sys.stderr, filename
        chrom = chrom_name(filename)

        chr_include_coords = get_chrom_coords(coords, chrom)

        if is_empty_array(chr_include_coords):
            continue

        with openFile(filename) as chromosome:
            yield chrom, filename, chromosome, chr_include_coords

def find_segment_starts(data):
    """
    finds the start of each segment

    returns the start positions, and the labels at each position

    returns lists of len num_segments+1, num_segments
    """
    len_data = len(data)

    # unpack tuple, ignore rest
    end_pos, = diff(data).nonzero()

    # add one to get the start positions, and add a 0 at the beginning
    start_pos = insert(end_pos + 1, 0, 0)
    labels = data[start_pos]

    # after generating labels, add an extraneous start position so
    # where_seg+1 doesn't go out of bounds
    start_pos = append(start_pos, len_data)

    return start_pos, labels

def ceildiv(dividend, divisor):
    "integer ceiling division"

    # int(bool) means 0 -> 0, 1+ -> 1
    return (dividend // divisor) + int(bool(dividend % divisor))

re_posterior_entry = re.compile(r"^\d+: (\S+) seg\((\d+)\)=(\d+)$")
def parse_posterior(iterable):
    """
    a generator.
    yields tuples (index, label, prob)

    index: (int) frame index
    label: (int) segment label
    prob: (float) prob value
    """
    # ignores non-matching lines
    for line in iterable:
        m_posterior_entry = re_posterior_entry.match(line.rstrip())

        if m_posterior_entry:
            group = m_posterior_entry.group
            yield (int(group(2)), int(group(3)), float(group(1)))

def read_posterior(infile, num_frames, num_labels):
    """
    returns an array (num_frames, num_labels)
    """
    # XXX: should these be single precision?
    res = zeros((num_frames, num_labels))

    for frame_index, label, prob in parse_posterior(infile):
        if label >= num_labels:
            raise ValueError("saw label %s but num_labels is only %s"
                             % (label, num_labels))

        res[frame_index, label] = prob

    return res

def make_filelistpath(dirpath, ext):
    return dirpath / extjoin(ext, EXT_LIST)

# XXX: these next three functions are spaghetti
def make_default_filename(resource, dirname="WORKDIR", instance_index=None):
    resource_part = resource.rpartition(".tmpl")
    stem = resource_part[0] or resource_part[2]
    stem_part = stem.rpartition(extsep)
    prefix = stem_part[0]
    ext = stem_part[2]

    filebasename = extjoin_not_none(prefix, instance_index, ext)

    return path(dirname) / filebasename

def make_template_filename(filename, resource, dirname=None, clobber=False,
                           instance_index=None):
    """
    returns (filename, is_new)
    """
    if filename:
        if not clobber and path(filename).exists():
            return filename, False
        # else filename is unchanged
    else:
        # filename is None
        filename = make_default_filename(resource, dirname, instance_index)

    return filename, True

def save_template(filename, resource, mapping, dirname=None,
                  clobber=False, instance_index=None):
    """
    creates a temporary file if filename is None or empty
    """
    filename, is_new = make_template_filename(filename, resource, dirname,
                                              clobber, instance_index)

    if is_new:
        with open(filename, "w+") as outfile:
            tmpl = Template(data_string(resource))
            text = tmpl.substitute(mapping)

            outfile.write(text)

    return filename, is_new

class memoized_property(object):
    def __init__(self, fget):
        self.fget = fget
        self.__doc__ = fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__

    def __get__(self, instance, owner):
        res = self.fget(instance or owner)

        # replace this descriptor with the actual value
        setattr(instance, self.__name__, res)
        return res

def resource_substitute(resourcename):
    return Template(data_string(resourcename)).substitute

def make_prefix_fmt(num):
    # make sure there are sufficient leading zeros
    return "%%0%dd." % (int(floor(log10(num))) + 1)

def main(args=sys.argv[1:]):
    pass

if __name__ == "__main__":
    sys.exit(main())
