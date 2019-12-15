#!/usr/bin/env python
#
# A prototype for indigo.
#
# Input is newlines delimited JSON.
#
# TODO(martin):
#
# 1. Have counters for each key encountered (.top => 23, top.nested => 2, ...)
# 2. For each key, reservoir sample values (e.g. 1000).
# 3. For each field value sample, run type inference (string, int, float, date, ...).
#
# Create some post-processable representation, e.g. JSON or dataframe.

import argparse
import collections
import fileinput
import json
import random

class Reservoir:
    """
    Map keys to multiple values, where values are reservoir sampled.
    """
    def __init__(self, size=1024):
        self.size = size
        self.storage = collections.defaultdict(list) # A sample (with duplicates).
        self.uniq = collections.defaultdict(set) # Just some unique examples.
        self.counter = collections.Counter()

    def add(self, key, value):
        self.counter[key] += 1
        if len(self.uniq[key]) < self.size:
            if isinstance(value, (str, int, float, bool)):
                self.uniq[key].add(value)
        if len(self.storage[key]) < self.size:
            self.storage[key].append(value)
        else:
            m = random.randint(0, self.counter[key])
            if m < self.size:
                self.storage[key][m] = value

    def __str__(self):
        return '<Reservoir with {} keys, size={}>'.format(len(self.storage), self.size)

def count_keys(doc, counters=None, samples=None, prefix=''):
    """
    Given a document, update counters with names of keys, optionally prefixed by a key.
    """
    if counters is None:
        counters = collections.Counter()
    if samples is None:
        samples = Reservoir()

    for k, v in doc.items():
        key = '{}{}'.format(prefix, k)
        counters[key] += 1
        if isinstance(v, dict):
            prefix = '{}.'.format(key)
            count_keys(v, counters=counters, samples=samples, prefix=prefix)
        else:
            samples.add(key, v)

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('files', metavar='FILE', nargs='*', help='files to read, if empty, stdin is used')
    args = parser.parse_args()

    # Flat counter with dotted notation.
    counters = collections.Counter()

    # A reservoir for examples.
    samples = Reservoir(size=64)

    # If you would call fileinput.input() without files it would try to process all arguments.
    # We pass '-' as only file when argparse got no files which will cause fileinput to read from stdin
    for line in fileinput.input(files=args.files if len(args.files) > 0 else ('-', )):
        line = line.strip()
        doc = json.loads(line)
        count_keys(doc, counters=counters, samples=samples)

    print(json.dumps(counters))
    print(json.dumps(samples.storage))

if __name__ == '__main__':
    main()
