#!/usr/bin/python3
""" trace through fea code"""

from fontTools.ttLib import TTFont
from fontTools.feaLib.parser import Parser
from fontTools.feaLib import ast
import argparse     #, logging, os, gc
import sys
import re

def loc(locationObject):
    """ format an object's location attribute the way we want to see it"""
    return f'line {locationObject.location.line}'

def glyphMatch(glyphName, glyphObject):
    """ return true if glyphname matches the glyphObject (single glyph, class, etc.)"""
    if isinstance(glyphObject, ast.GlyphName):
        return glyphName == glyphObject.glyph
    elif isinstance(glyphObject, ast.GlyphClassName):
        return glyphName in glyphObject.glyphclass.glyphs.glyphs
    elif isinstance(glyphObject, ast.GlyphClass):
        return glyphName in glyphObject.glyphs
    else:
        raise TypeError(f'unhandled glyph object "{glyphObject.asFea()}" -- aborting.')


def traceFea(lkup, glyphs, offset=0):
    """ see if a specific lookup matches a list of glyphs at a specific offset """
    res = []
    for s in lkup.statements:
        # print(s.asFea())
        if isinstance(s, ast.SinglePosStatement) and not s.forceChain:
            # Single Position statement
            for pos in s.pos:
                if glyphMatch(glyphs[offset], pos[0]):
                    # yes we have a winner!
                    masked = '# (MASKED)' if len(res) > 0 else ''
                    res.append(f"{loc(s)} Lookup {lkup.name} SinglePos {glyphs[offset]} --> {pos[1].asFea()}  {masked}")
                    continue

        elif isinstance(s, ast.PairPosStatement):
            # Pair Position statement
            if glyphMatch(glyphs[offset], s.glyphs1) and glyphMatch(glyphs[offset + 1], s.glyphs2):
                # yes we have a winner!
                masked = '# (MASKED)' if len(res) > 0 else ''
                res.append(f"{loc(s)} Lookup {lkup.name} PairPos {glyphs[offset]},{glyphs[offset + 1]} --> {s.asFea()}  {masked}")
            continue

        elif isinstance(s, (ast.ChainContextSubstStatement, ast.ChainContextPosStatement)) or \
                (isinstance(s, ast.SinglePosStatement) and s.forceChain):
            # Contextual
            if len(s.prefix) > 0:
                ## TODO implement support for prefix strings
                raise NotImplementedError
            if len(s.prefix) > offset or offset + (1 if not hasattr(s,'glyphs') else len(s.glyphs)) + len(s.suffix) > len(glyphs):
                continue  # Can't possibly match
            mismatch = False  # assume success
            if isinstance(s, (ast.ChainContextSubstStatement, ast.ChainContextPosStatement)):
                # proper chaining contextual lookup
                for i, g in enumerate(s.glyphs):
                    if not glyphMatch(glyphs[offset+i], g):
                        mismatch = True
                        break
                for i, g in enumerate(s.suffix):
                    if not glyphMatch(glyphs[offset + len(s.glyphs) + i], g):
                        mismatch = True
                        break
            else:
                # a single positioning lookup with forceChain set
                for i, p in enumerate(s.pos):
                    # I'm only guessing how this works
                    if glyphMatch(glyphs[offset], p[0]):
                        break
                    else:
                        mismatch = True
                for i, g in enumerate(s.suffix):
                    if not glyphMatch(glyphs[offset + 1 + i], g):
                        mismatch = True
                        break
            if mismatch:
                continue
            # We have a context match!
            masked = '# (MASKED)' if len(res) > 0 else ''
            res.append(f"{loc(s)} Lookup {lkup.name} Context match --> {s.asFea()}  {masked}")

            # If this is the first matching context, do all the actions:
            if isinstance(s, (ast.ChainContextSubstStatement, ast.ChainContextPosStatement)) and len(res) == 1:
                for i,lkupList in enumerate(s.lookups):
                    if lkupList != None:
                        for l in lkupList:
                            res2 = traceFea(l, glyphs, offset+i)
                            res.extend(res2)
            continue

        else:
            # print(f'Line {s.location.line} is of unimplemented statement type {type(s)}')
            continue

        # print(f"Lookup {lkup.name} did not match at offset {offset}")

    return(res)

if __name__ == '__main__':

    parser=argparse.ArgumentParser()
    parser.add_argument("infile", help="Path to input fea file", metavar='input-fea-file')
    parser.add_argument('glyphs', help='comma-separated glyph sequence to trace', metavar='glyphname(s)')
    parser.add_argument("-f","--font", help="Path to font file")
    parser.add_argument("-l", "--lookup", help="name of lookup to trace", default="mainkern")
    parser.add_argument("-k", "--kern", help="raw grkern2fea data file")
    parser.add_argument("--allpairs", help="test all pairs from glyphs", action='store_true')
    ## parser.add_argument("-o", "--outfile", help="Output file of results")
    ## parser.add_argument("-L","--log",default="INFO",help="Logging level [DEBUG, *INFO*, WARN, ERROR]")
    ## parser.add_argument("--logfile",help="Log to file")
    args = parser.parse_args()

    if args.font:
        font = TTFont(args.font)
        parser = Parser(args.infile, font.getReverseGlyphMap())
    else:
        parser = Parser(args.infile)
    parsetree = parser.parse()

    # Find desired lookup
    lookup = [s for s in parsetree.statements if isinstance(s, ast.LookupBlock) and s.name == args.lookup ]
    if len(lookup) == 0:
        print(f'lookup named "{args.lookup}" not found in file "{args.infile}"')
        sys.exit(1)
    if len(lookup) > 1:
        print(f'more than one lookup named "{args.lookup}" found in file "{args.infile}"')
        sys.exit(1)
    lookup = lookup[0]

    # Split glyphlist:
    glyphs = args.glyphs.split(',')

    # If provided, read the raw kern data to find the actual value
    if args.kern:
        gnameRE = re.compile(r'\[([^]]+)\]')  # regex to extract glyph names from rawKern data
        kernRE = re.compile(r'{([^}]+)}')   # regex to extract kern value from rawKern data
        with open(args.kern, encoding='utf-8') as f:
            for lineno,line in enumerate(f):
                dataGlyphs = gnameRE.findall(line)
                if dataGlyphs == glyphs:
                    # found the record
                    kerns = kernRE.findall(line)
                    if len(kerns) != 1:
                        print(f'raw data line {lineno}: Unexpected count of kern values ({len(kerns)} in kerndata, data ignored: {line}')
                    else:
                        print(f"raw data line {lineno}: Desired kern value = {kerns[0]}")
                        break
            else:
                print('No matching kern value found in kerndata')

    # Trace fea code
    if args.allpairs:
        for g1 in glyphs:
            for g2 in glyphs:
                res = traceFea(lookup, (g1, g2))
                if len(res):
                    print(f"\ntracing pair {g1},{g2}--------------------")
                    for x in res:
                        print(x)

    else:
        for x in traceFea(lookup, glyphs):
            print(x)
