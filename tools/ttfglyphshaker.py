#!/usr/bin/python3

# A work in progress

import sys
import re
from pathlib import Path
import argparse  
from fontTools.ttLib import TTFont
from glob import glob
import logging

def ftshake(f, componentNameRE):
    gnames = set(f.getGlyphSet().keys())
    allComponents = set(filter(componentNameRE.search, gnames))
    neededComponents = set()
    gtable = f['glyf']

    # In case nested composites haven't yet been flattened, use
    # recursion to make sure all components are marked as needed
    def markneeded(gname):
        if gname in allComponents:
            neededComponents.add(gname)
        g = gtable[gname]
        if g.isComposite():
            for c in g.components:
                markneeded(c.glyphName)

    for gname in gnames - allComponents:
        markneeded(gname)

    toDelete = allComponents-neededComponents
    toKeep = gnames - toDelete
    breakpoint()
    print(f'found {len(allComponents)} matching components but can remove {len(toDelete)}:\n', '\n'.join(sorted(toDelete)))


if __name__ == '__main__':

    parser=argparse.ArgumentParser()
    parser.add_argument("infonts", help="Path to input font file(s)", nargs='+')
    parser.add_argument("-o", "--outdir", help="Output folder", default="outfonts")
    parser.add_argument("-c", "--compregex", help="RegEx to recognize names of component-only glyphs", 
                        default=r'^_')
    parser.add_argument("-L","--loglevel",default="INFO",help="Logging level [DEBUG, INFO, WARN, ERROR]")
    parser.add_argument("--logfile",help="Log to file")
    args = parser.parse_args()


    # Create output directory (equivalent of mkdir -p)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True) 

    logger = logging.getLogger('glyphShaker')
    logging.basicConfig(filename=args.logfile, level=args.loglevel.upper())

    compRE = re.compile(args.compregex)

    for files in args.infonts:
        fonts = list(glob(files))
        if not fonts:
            logger.warning('commandline parameter "%s" did not match any existing filenames', files)
        for infontname in fonts:
            try:
                infont = TTFont(infontname)
            except:
                logger.warning("Couldn't open %s as a TTF font; parameter skipped", infontname)
                continue

            basename= Path(infontname).name
            outname = outdir / basename
            print(f'\nProcessing {infontname} --> {outname}')

            ftshake(infont, compRE)

            infont.close()
            


