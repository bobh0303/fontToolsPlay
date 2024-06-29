#!/usr/bin/python3
'''
Shake a font to remove unneeded glyphs.

In the process of converting a font from UFO sources to TTF, some glyphs 
used only as components in other glyphs may, due to composite flattening 
or decomposition, become "unreachable" and thus act simply to enlarge the 
font and cause warnings in fontbakery.

Given a component glyph naming convention (e.g., they all start with '_'), 
this tool can remove unreachable component glyphs that match that convention.
'''
# A work in progress

import sys
import re
from pathlib import Path
import argparse  
from fontTools.ttLib import TTFont
from fontTools import subset
from glob import glob
import logging

def ftshake(f, componentNameRE, outpath):
    logger = logging.getLogger('glyphShaker')
    
    gnames = set(f.getGlyphSet().keys())
    allComponents = set(filter(componentNameRE.search, gnames))
    neededComponents = set()
    gtable = f['glyf']

    # In case nested composites haven't yet been flattened, use
    # recursion to make sure all components that are actually 
    # needed are identified
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

    # copied from nototools.subset
    opt = subset.Options()
    opt.name_IDs = ["*"]
    opt.name_legacy = True
    opt.name_languages = ["*"]
    opt.layout_features = ["*"]
    opt.notdef_outline = True
    opt.recalc_bounds = False       # was True
    opt.recalc_timestamp = True
    opt.canonical_order = True

    # Added for glyphshaker:
    opt.layout_features = ["*"]
    opt.layout_scripts = ["*"]
    opt.drop_tables = []
    opt.passthrough_tables = True

    opt.glyph_names = True
    opt.legacy_cmap = True
    opt.recalc_timestamp = True
    opt.prune_unicode_ranges = False
    opt.prune_codepage_ranges = False

    # Invoke the subsetter!
    subsetter = subset.Subsetter(options=opt)
    subsetter.populate(glyphs=toKeep)
    subsetter.subset(f)
    subset.save_font(f, outpath, opt)
    f.close()
    logger.info('Subsetting complete.')
    logger.info('Of %d glyphs, found %d matching components but can remove %d, leaving %d.', len(gnames), len(allComponents), len(toDelete), len(gnames)-len(toDelete))


if __name__ == '__main__':

    parser=argparse.ArgumentParser(
        description=__doc__, 
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog = '''\
If the infonts argument(s) evaluate to a single font file to shake, 
then the OUTFONT option may be used to provide the desired name of 
the output font file.

If the infonts argument evaluates to multiple font files to shake or 
OUTFONT is omitted, then the output fonts will have the same name as 
the input fonts and be stored in the folder named by OUTDIR.

Note: This program uses the fontTools subsetter, and might remove things you 
wanted to keep, such as TypeTuner-only lookups. Suggest the tool be used 
before adding OpenType, Graphite or TypeTuner smarts.
''')
    parser.add_argument("infonts", help="Path to input font file(s). Can be repeated; can contain wildcards", nargs='+')
    outputoptions = parser.add_mutually_exclusive_group()
    outputoptions.add_argument("-d", "--outdir", help="Output folder. Will be created if needed (default: shakenfonts/)", nargs='?', default="shakenfonts/")
    outputoptions.add_argument("-o", "--outfont", help="name of output font file")
    parser.add_argument("-c", "--compregex", metavar="RegEx", help="RegEx to recognize names of component-only glyphs (default: ^_)", 
                        default=r'^_')
    parser.add_argument("-q", "--quiet", action="store_true", help="Set Logging level to ERROR (default: False)")
    parser.add_argument("-L","--loglevel",default="WARN",help="Logging level (default: WARN)", choices=("DEBUG", "INFO", "WARN", "ERROR"))
    parser.add_argument("--logfile",help="Pathname of logfile to create")
    args = parser.parse_args()

    # Compile RE that will identify (by name) candidate component glyphs to delete
    compRE = re.compile(args.compregex)

    # Set up logging
    loglevel = 'ERROR' if args.quiet else args.loglevel
    logger = logging.getLogger('glyphShaker')
    logging.basicConfig(filename=args.logfile, level=loglevel.upper())

    # get a single list of font files to shake
    fileList = []
    for files in args.infonts:
        fonts = list(glob(files))
        if not fonts:
            logger.warning('commandline parameter "%s" did not match any existing filenames', files)
        fileList.extend(fonts)
    if not fileList:
        logger.error('input files found')
        sys.exit(1)
    
    # Decide whether we're using OUTDIR or not and, if so, create it.
    if len(fileList)>1 and args.outfont:
            logger.warning('Multiple font files detected; OUTFONT option will be ignored and fonts will keep the same name and be placed in %s.', args.outdir)

    useOutfont = len(fileList) == 1 and args.outfont

    if not useOutfont:
        # Create output directory (equivalent of mkdir -p)
        outdir = Path(args.outdir)
        outdir.mkdir(parents=True, exist_ok=True) 

    # Finally, loop through all the fonts and shake out those unwanted glyphs!
    for infontname in fileList:
        try:
            infont = TTFont(infontname)
        except:
            logger.warning("Couldn't open %s as a TTF font; parameter skipped", infontname)
            continue

        if useOutfont:
            outpath = args.outfont
        else:
            basename= Path(infontname).name
            outpath = outdir / basename
        logger.info('\nProcessing %s --> %s', infontname, outpath)
        ftshake(infont, compRE, outpath)

# done!