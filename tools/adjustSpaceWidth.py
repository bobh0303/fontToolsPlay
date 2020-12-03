#!/bin/python3
''' create derived fonts with alternate space widths

usage: adjustSpaceWidth spacewidths ttffile(s) ...

spacewidths = comma-separated list of 1 or 2 integer values to serve as space widths
     First integer is desired width of 'space', second, if supplied is of 'space.arab'

ttffile(s) = one or more file patterns specifying input ttf files

output font names and font filenames are constructed from the input by appending info from the spacewidths parameter.

examples:
    # set width of space glyph to 300 and write font named 'Zork-300 Regular' to Zork-Regular-300.ttf:
    adjustSpaceWidth 300 Zork-Regular.ttf

    # set space to 300, space.arab to 210, and write font named 'Zork-300-210' Regular to to Zork-Regular-300-210.ttf
    adjustSpaceWidth 300,210 Zork-Regular.ttf

    # Similar to above but process all ttfs in folder:
    adjustSpaceWidth 300,210 *.ttf
'''
from fontTools.ttLib import TTFont
from glob import glob
import re
from os.path import splitext
import sys

if len(sys.argv) < 3:
    sys.stderr.write('insufficient arguments.\n')
    sys.stderr.write('usage: usage: adjustSpaceWidth spacewidths ttffile(s) ...\n')
    exit(1)

m = re.match('(\d+)(?:,(\d+))?',sys.argv[1])
if not m:
    sys.stderr.write("1st arg must be comma-separated list of one or two positive integer values to use as widths\n")
    exit(1)

spacewidth = int(m.group(1))
suffix = f'-{spacewidth}'

arabwidth = m.group(2)
if arabwidth is not None:
    arabwidth = int(arabwidth)
    suffix += f'-{arabwidth}'

for arg in sys.argv[2:]:
    for fontfile in glob(arg):
        try:
            ttfont = TTFont(fontfile)
        except Exception as e:
            sys.stderr.write(f'"{fontfile}" doesn\'t appear to be a ttf: {e}\n')
            continue
        base, ext = splitext(fontfile)
        outfont = f'{base}{suffix}{ext}'

        print(f'processing {fontfile}  --> {outfont}')

        # update hmtx:
        metrics = ttfont['hmtx'].metrics
        if 'space' in metrics:
            metrics['space'] = (spacewidth, metrics['space'][1])
        else:
            sys.stderr.write(f'glyph "space" not found in fontfile; font ignored')
            ttfont.close()
            continue
        if arabwidth is not None:
            if 'space.arab' in metrics:
                metrics['space.arab'] = (arabwidth, metrics['space.arab'][1])
            else:
                sys.stderr.write(f'glyph "space.arab" not found in fontfile; glyph ignored')

        # Append suffix to font-name
        namelist = ttfont['name'].names
        # Find stylename:
        style = next(str(record) for record in namelist if record.nameID == 2)
        fontname = next(str(record) for record in namelist if record.nameID == 1)
        psfontname = fontname.replace(' ','')
        newfontname = f'{fontname}{suffix}'

        # Now change all names:
        for record in namelist:
            if record.nameID == 6:  # postscriptname
                record.string = str(record).replace(psfontname, f'{psfontname}{suffix}')
            else:
                record.string = str(record).replace(fontname, newfontname)

        # Write the font
        try:
            ttfont.save(outfont)
        except Exception as e:
            sys.stderr.write(f'trouble saving "{outfont}": {e}')
        ttfont.close()