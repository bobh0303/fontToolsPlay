#!/usr/bin/python3
""" print in tabular form fsSelection from multiple ttf fonts"""


from fontTools.ttLib import TTFont
from glob import glob
import csv
import sys
from collections import OrderedDict
from os.path import getmtime
from time import strftime, localtime

if len(sys.argv) < 2:
    print("usage: showfsSelection.py fontfile*.ttf ...")
    sys.exit(1)

with open('fsSelection.csv', 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)

    bitList = OrderedDict(zip(['Italic', 'Underscore', 'Negative', 'Outlined', 'StrikeOut', 'Bold', 'Regular',
               'UseTypoMetrics', 'WWS', 'Oblique'], [1 << x for x in range(0, 10)]))

    header = ['font', 'mod year', 'OS/2 ver']
    header.extend(bitList.keys())
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
            r.extend(['X' if os2.fsSelection & mask else '' for mask in bitList.values()])
            csvwriter.writerow(r)
            f.close()
