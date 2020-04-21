#!/usr/bin/env python3
#
# gptconv.py
# streaming-capable conversion of gptid to device name
#
# Version: 1.0 (2020-04-19)
#
# This is only intended to work on FreeNAS / TrueNAS CORE.
# Probably needs to be run with elevated privileges, due to diskinfo calls,
# when -d is used.
# This tool is not provided, sponsored, endorsed, or supported by iXsystems.
#
# Suggested usages:
# $ zpool status | gptconv.py
#   pool: knat
#  state: ONLINE
#   scan: none requested
# config:
#
#         NAME                                       STATE     READ WRITE CKSUM
#         knat                                       ONLINE       0     0     0
#           mirror-0                                 ONLINE       0     0     0
#             ada0p2                                 ONLINE       0     0     0
#             ada1p2                                 ONLINE       0     0     0
#
# errors: No known data errors
#
# $ zpool status | gptconv.py -d
#   pool: knat
#  state: ONLINE
#   scan: none requested
# config:
#
#         NAME                                       STATE     READ WRITE CKSUM
#         knat                                       ONLINE       0     0     0
#           mirror-0                                 ONLINE       0     0     0
#             ada0p2 (WDC WD100EMAZ-00WJTA0)         ONLINE       0     0     0
#             ada1p2 (WDC WD100EMAZ-00WJTA0)         ONLINE       0     0     0
#
# errors: No known data errors
#
# Copyright 2020 Nick Principe <nick@princi.pe>
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import argparse
import re
import signal
import subprocess
import sys

GPTID_RE = re.compile('(gptid/[0-9A-Fa-f-]+(?:\.eli)?)(\s*)')

def ctrlc_handler(sig, frame):
    sys.exit(0)

class DiskDesc:
    NAME_RE = re.compile('(.*?)(p[0-9]+)?$')
    DESCR_RE = re.compile('(.*?)(# Disk descr.)$')
    UNKNOWN_STR = 'UNKNOWN'
    def __init__(self):
        self.desc_dict = dict()

    def _fetch_desc(self, devname):
        disk_desc = DiskDesc.UNKNOWN_STR
        diskinfo_cp = subprocess.run(['diskinfo', '-v', f'/dev/{devname}'],
                                     capture_output=True,
                                     check=False,
                                     text=True)
        if diskinfo_cp.returncode == 0:
            for line in diskinfo_cp.stdout.splitlines():
                desc_match = DiskDesc.DESCR_RE.match(line)
                if desc_match is not None:
                    disk_desc = desc_match.group(1).strip()
        return disk_desc

    def get_desc(self, name):
        try:
            devname = DiskDesc.NAME_RE.match(name).group(1)
        except AttributeError:
            return DiskDesc.UNKNOWN_STR
        if devname not in self.desc_dict:
            self.desc_dict[devname] = self._fetch_desc(devname)
        return self.desc_dict[devname]

def build_gpt_label_dict():
    glabel_dict = dict()
    glabel_cp = subprocess.run(['glabel', 'status'],
                               capture_output=True,
                               check=True,
                               text=True)
    for line in glabel_cp.stdout.splitlines():
        fields = re.split('\s+', line.strip())
        gptid = GPTID_RE.match(fields[0])
        if gptid is not None:
            glabel_dict[gptid.group(1)] = fields[2]
    return glabel_dict

def gptconv():
    parser = argparse.ArgumentParser(
                description='convert gptid to device name')
    parser.add_argument('-d', action='store_true',
                        help='Insert disk description')
    parser.add_argument('-p', action='store_false',
                        help='Do not try to fix padding on output')
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin)
    parser.add_argument('-o', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout, metavar='outfile',
                        help='Output file (omit for stdout)')
    args = parser.parse_args()
    glabel_dict = build_gpt_label_dict()
    dd = DiskDesc()
    for line in args.infile:
        gpt_to_rep = GPTID_RE.findall(line)
        for gptid,ws in gpt_to_rep:
            repl_str = glabel_dict[gptid.replace('.eli','')]
            if args.d:
                desc = dd.get_desc(repl_str)
                repl_str = f'{repl_str} ({desc})'
            if args.p:
                repl_str = repl_str.ljust(len(gptid) + len(ws))
            line = line.replace(f'{gptid}{ws}', repl_str, 1)
        print(line, end='', file=args.o)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, ctrlc_handler)
    gptconv()
