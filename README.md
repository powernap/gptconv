# gptconv.py
streaming-capable conversion of gptid to device name

```
# ./gptconv.py -h
usage: gptconv.py [-h] [-d] [-s] [-p] [-o [outfile]] [infile]

convert gptid to device name

positional arguments:
  infile

optional arguments:
  -h, --help    show this help message and exit
  -d            Insert disk description
  -s            Insert disk serial number
  -p            Do not try to fix padding on output
  -o [outfile]  Output file (omit for stdout)
```

This is only intended to work on FreeNAS / TrueNAS CORE. It should work on any FreeBSD-based system, though. Probably needs to be run with elevated privileges, due to diskinfo calls, when -d is used.
This tool is not provided, sponsored, endorsed, or supported by iXsystems.

Suggested usage:
```
$ zpool status | gptconv.py
  pool: knat
 state: ONLINE
  scan: none requested
config:

        NAME                                       STATE     READ WRITE CKSUM
        knat                                       ONLINE       0     0     0
          mirror-0                                 ONLINE       0     0     0
            ada0p2                                 ONLINE       0     0     0
            ada1p2                                 ONLINE       0     0     0

errors: No known data errors
```
Or if you'd like the disk descriptions inserted as well:
```
$ zpool status | gptconv.py -d
  pool: knat
 state: ONLINE
  scan: none requested
config:

        NAME                                       STATE     READ WRITE CKSUM
        knat                                       ONLINE       0     0     0
          mirror-0                                 ONLINE       0     0     0
            ada0p2 (WDC WD100EMAZ-00WJTA0)         ONLINE       0     0     0
            ada1p2 (WDC WD100EMAZ-00WJTA0)         ONLINE       0     0     0

errors: No known data errors
```
This should work for converting any text with gptid's to device names with or without the disk descriptions. If the output is not padded, like zpool status, then it may be beneficial to provide the -p flag to suppress attempting to reinstate padding on output.
