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
import datetime
import fileinput
import hashlib
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

    def unique_storage(self):
        """
        Return storage array, reduced to unique values.
        """
        us = collections.defaultdict(set)
        for k, v in self.storage.items():
            us[k] = set(v)
        return us

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

    if isinstance(doc, dict):
        for k, v in doc.items():
            key = '{}{}'.format(prefix, k)
            counters[key] += 1
            if isinstance(v, dict):
                count_keys(v, counters=counters, samples=samples, prefix='{}.'.format(key))
            elif isinstance(v, list):
                for item in v:
                    count_keys(item, counters=counters, samples=samples, prefix='{}[].'.format(key))
            else:
                samples.add(key, v)
    else:
        return

class SetEncoder(json.JSONEncoder):
    """
    Helper to encode python sets into JSON lists.
    So you can write something like this:
        json.dumps({"things": set([1, 2, 3])}, cls=SetEncoder)
    """
    def default(self, obj):
        """
        Decorate call to standard implementation.
        """
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('files', metavar='FILE', nargs='*', help='files to read, if empty, stdin is used')
    args = parser.parse_args()

    # Flat counter with dotted notation.
    counters = collections.Counter()

    # A reservoir for examples.
    samples = Reservoir(size=1024)

    # Total number of documents.
    total = 0

    # Checksum as we go.
    sha1 = hashlib.sha1()

    # If you would call fileinput.input() without files it would try to process all arguments.
    # We pass '-' as only file when argparse got no files which will cause fileinput to read from stdin
    for line in fileinput.input(files=args.files if len(args.files) > 0 else ('-', )):
        total += 1
        sha1.update(line.encode('utf-8'))
        doc = json.loads(line)
        count_keys(doc, counters=counters, samples=samples)

    result = {
        'meta': {
            'size': samples.size,
            'date': datetime.datetime.now().isoformat(),
            'total': total,
            'sha1': sha1.hexdigest(),
        },
        'c': counters,
        's': samples.storage,
        'u': samples.unique_storage(),
        'v': samples.uniq,
    }
    print(json.dumps(result, cls=SetEncoder))

if __name__ == '__main__':
    main()
