#! /usr/bin/env python
''' print in tabular form glyph metrics from multiple ttf fonts'''


# from __future__ import print_function
# from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
from glob import glob
import csv
import sys

headfields = ('xMin','yMin','xMax', 'xMin')

if len(sys.argv) != 2:
	print("usage: showGlyphMetrics.py fontfile*.ttf")
	sys.exit(1)

with open('glyphMetrics.csv', 'wb') as csvfile:
    csvwriter = csv.writer(csvfile)

    fonts = []
    header = ['','']
    for fontfile in glob(sys.argv[1]):
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
    for tableName,fieldList in (('head', headfields),):
        for fieldname in fieldList:
            doRow(tableName, fieldname)


    for f in fonts:
        f.close()
