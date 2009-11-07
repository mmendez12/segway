#!/usr/bin/env python
from __future__ import division

__version__ = "$Revision$"

# Copyright 2009 Michael M. Hoffman <mmh1@washington.edu>

from os import environ
import sys

from path import path

from .._configparser import OneSectionRawConfigParser
from .._util import ceildiv
from .common import _JobTemplateFactory, make_native_spec

# use SI prefixes. I can't find any documentation for this but Tim
# Cutts seems to assume this is how it works
KB = 10**3
MB = 10**6
GB = 10**9
TB = 10**12
PB = 10**15
EB = 10**18

SIZE_UNITS = dict((unit, globals()[unit])
                  for unit in ["KB", "MB", "GB", "TB", "PB", "EB"])

LSF_CONF_BASENAME = "lsf.conf"
LSF_CONF_FILEPATH = path(environ["LSF_ENVDIR"]) / LSF_CONF_BASENAME

# XXX: this can be more robustly handled with the LSLIB function
# ls_readconfenv() and ctypes instead
LSF_CONF = OneSectionRawConfigParser(dict(LSF_UNIT_FOR_LIMITS="KB"))
LSF_CONF.read(LSF_CONF_FILEPATH)

UNIT_FOR_LIMITS = LSF_CONF.get("LSF_UNIT_FOR_LIMITS")
DIVISOR_FOR_LIMITS = SIZE_UNITS[UNIT_FOR_LIMITS]

CORE_FILE_SIZE_LIMIT = 0

class JobTemplateFactory(_JobTemplateFactory):
    def __init__(self, template, *args, **kwargs):
        # eliminate default overwrite behavior for DRMAA/LSF, go to
        # append which is default for DRMAA/SGE
        self.output_path = template.outputPath.lstrip(":")
        self.error_path = template.errorPath.lstrip(":")

        template.outputPath = ""
        template.errorPath = ""

        return _JobTemplateFactory.__init__(self, template, *args, **kwargs)

    def make_res_req(self, mem_usage):
        mem_usage_mb = ceildiv(mem_usage, MB)

        # return a quoted string
        return '"select[mem>%s] rusage[mem=%s]"' % (mem_usage_mb, mem_usage_mb)

    def make_native_spec(self):
        mem_limit_spec = ceildiv(self.mem_limit, DIVISOR_FOR_LIMITS)

        # bsub -R: resource requirement
        # bsub -M: per-process memory limit
        # bsub -v: hard virtual memory limit for all processes
        # bsub -C: core file size limit
        res_spec = make_native_spec(R=self.res_req, M=mem_limit_spec,
                                    v=mem_limit_spec, o=self.output_path,
                                    e=self.error_path)

        # XXX: -C does not work with DRMAA for LSF 1.03
        # wait for upstream fix:
        # https://sourceforge.net/tracker/?func=detail&aid=2882034&group_id=206321&atid=997191
        #                            C=CORE_FILE_SIZE_LIMIT)

        return " ".join([self.native_spec, res_spec])

def main(args=sys.argv[1:]):
    pass

if __name__ == "__main__":
    sys.exit(main())
