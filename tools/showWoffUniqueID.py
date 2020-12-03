#!/usr/bin/python3

import sys
from fontTools.ttLib import TTFont
from glob import glob
import xml.etree.ElementTree as ET


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if len(args) < 1:
        print("usage: showWoffUniqueID INPUT.woff", file=sys.stderr)
        return 1

    for arg in args:
        for infile in glob(arg):
            font = TTFont(infile)

            if not font.flavorData or not font.flavorData.metaData:
                print(f"No WOFF metadata in {infile}")
            else:
                root = ET.fromstring(font.flavorData.metaData)
                uniqueid = root.find('uniqueid')
                if 'uniqueid' is not None:
                    print(f'{infile}: {uniqueid.get("id", "Unique ID element has no ID attribute")}')
                else:
                    print(f'{infile}: no unique ID element found')




if __name__ == "__main__":
    sys.exit(main())
