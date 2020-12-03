#! /usr/bin/env python
''' print in tabular form line metrics from multiple ttf fonts'''


# from __future__ import print_function
# from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from glob import glob
import csv
import sys

hheafields = ('ascent', 'descent', 'lineGap')
os2fields = ('sTypoAscender','sTypoDescender','sTypoLineGap',
             'usWinAscent', 'usWinDescent',
             'ySubscriptXSize', 'ySubscriptYSize', 'ySubscriptXOffset', 'ySubscriptYOffset',
             'ySuperscriptXSize', 'ySuperscriptYSize', 'ySuperscriptXOffset', 'ySuperscriptYOffset',
             'yStrikeoutSize', 'yStrikeoutPosition')
postfields = ('underlinePosition', 'underlineThickness')

if len(sys.argv) < 2:
	print("usage: showLineMetrics.py fontfile*.ttf ...")
	sys.exit(1)

with open('metrics.csv', 'wb') as csvfile:
    csvwriter = csv.writer(csvfile)

    fonts = []
    header = ['','']

    for arg in sys.argv[1:]:
        for fontfile in glob(arg):
            fonts.append(TTFont(fontfile))
            header.append(fontfile)
    csvwriter.writerow(header)

    def doRow(tablename,fieldname):
        if doRow.prevtable != tablename:
            row = [tablename,fieldname]
            doRow.prevtable = tablename
        else:
            row = ['',fieldname]
        for f in fonts:
            row.append(f[tablename].__getattribute__(fieldname))
        csvwriter.writerow(row)

    doRow.prevtable = ''
    for tableName,fieldList in (('hhea', hheafields),('OS/2', os2fields),('post', postfields)):
        for fieldname in fieldList:
            doRow(tableName, fieldname)

    for f in fonts:
        f.close()
