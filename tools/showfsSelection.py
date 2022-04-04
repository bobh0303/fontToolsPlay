#!/usr/bin/python3
""" print in tabular form fsSelection from multiple ttf fonts"""

from fontTools.ttLib import TTFont
from glob import glob
import csv
import sys
from os.path import getmtime
from time import strftime, localtime

if len(sys.argv) < 2:
    print("usage: showfsSelection.py fontfile*.ttf ...")
    sys.exit(1)

with open('fsSelection.csv', 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)

    bitList = ['Italic', 'Underscore', 'Negative', 'Outlined', 'StrikeOut', 'Bold', 'Regular',
               'UseTypoMetrics', 'WWS', 'Oblique']
    bitMasks = [1 << x for x in range(len(bitList))]

    header = ['font', 'mod year', 'OS/2 ver']
    header.extend(bitList)
    csvwriter.writerow(header)

    for arg in sys.argv[1:]:
        for fontfile in glob(arg):
            try:
                f = TTFont(fontfile)
            except:
                continue
            r = [fontfile, strftime('%Y', localtime(getmtime(fontfile)))]
            try:
                os2 = f['OS/2']
            except KeyError:
                r.append('no OS/2')
                csvwriter.writerow(r)
                f.close()
                continue
            r.append(os2.version)
            r.extend(['X' if os2.fsSelection & mask else '' for mask in bitMasks])
            csvwriter.writerow(r)
            f.close()
