#!/usr/bin/python3
""" print in tabular form line metrics from multiple ttf fonts"""

from fontTools.ttLib import TTFont
from glob import glob
import csv
import sys

headfields = ('unitsPerEm', 'yMax', 'yMin')
hheafields = ('ascent', 'descent', 'lineGap')
os2fields = ('sTypoAscender', 'sTypoDescender', 'sTypoLineGap', 'USE_TYPO_METRICS',
             'usWinAscent', 'usWinDescent',
             'ySubscriptXSize', 'ySubscriptYSize', 'ySubscriptXOffset', 'ySubscriptYOffset',
             'ySuperscriptXSize', 'ySuperscriptYSize', 'ySuperscriptXOffset', 'ySuperscriptYOffset',
             'yStrikeoutSize', 'yStrikeoutPosition')
postfields = ('underlinePosition', 'underlineThickness')

if len(sys.argv) < 2:
    print("usage: showLineMetrics.py fontfile*.ttf ...")
    sys.exit(1)

with open('metrics.csv', 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)

    fonts = []
    header = ['', '']

    for arg in sys.argv[1:]:
        for fontfile in glob(arg):
            fonts.append(TTFont(fontfile))
            header.append(fontfile)
    csvwriter.writerow(header)

    def doRow(tablename,fieldname):
        if doRow.prevtable != tablename:
            row = [tablename, fieldname]
            doRow.prevtable = tablename
        else:
            row = ['', fieldname]
        for f in fonts:
            if fieldname == 'USE_TYPO_METRICS':
                row.append('True' if f[tablename].fsSelection & 0x80 else 'False')
            else:
                row.append(f[tablename].__getattribute__(fieldname))
        csvwriter.writerow(row)

    doRow.prevtable = ''
    for tableName, fieldList in (('head', headfields), ('hhea', hheafields), ('OS/2', os2fields), ('post', postfields)):
        for fieldname in fieldList:
            doRow(tableName, fieldname)

    for f in fonts:
        f.close()
