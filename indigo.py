#!/usr/bin/env python
#
# A prototype for indigo.

import argparse
import fileinput


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--dummy', help='dummy argument')
    parser.add_argument('files', metavar='FILE', nargs='*', help='files to read, if empty, stdin is used')
    args = parser.parse_args()

    # If you would call fileinput.input() without files it would try to process all arguments.
    # We pass '-' as only file when argparse got no files which will cause fileinput to read from stdin
    for line in fileinput.input(files=args.files if len(args.files) > 0 else ('-', )):
        line = line.strip()
        print(line)

if __name__ == '__main__':
    main()
