#!/usr/bin/env python

import argparse
import fnmatch
import os
import re


def is_logic_file(path):
    return fnmatch.fnmatch(path, '*.dl')


def extract_predicates(path, keyword='.decl'):
    pattern = '{} (?P<predicate>.*)\\(.*\\)'.format(keyword)

    with open(path, 'r') as logicfile:
        for line in logicfile:
            m = re.search(pattern, line)

            if m is not None:
                yield m.group('predicate')


def generate_output_logic(path, predicates):
    exportdir = os.path.dirname(path)

    for logicfile in [os.path.join(exportdir, f) for f in os.listdir(exportdir)]:
        if logicfile == path:
            continue
        if os.path.isfile(logicfile) and is_logic_file(logicfile):
            for predicate in extract_predicates(logicfile):
                if predicate.startswith('_'):
                    predicates.remove(predicate[1:])

    with open(path, 'w') as out:
        for predicate in sorted(predicates):
            out.write('.output {}\n'.format(predicate))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('logic_dir', metavar='DIR',
                        help='Directory containing Datalog files')
    parser.add_argument('-o', '--output_file', metavar='OUTFILE',
                        help='output file', required=True)
    parser.add_argument('--extra-output-preds', metavar='FILE',
                        help='Extra output predicates', type=argparse.FileType('r'))

    # Parse arguments
    args = parser.parse_args()

    # Predicate sets
    allpreds, inputpreds = set(), set()

    # Traverse logic directory
    for root, dirs, files in os.walk(args.logic_dir):
        for f in files:
            path = os.path.join(root, f)

            if not is_logic_file(path):
                continue

            for predicate in extract_predicates(path):
                allpreds.add(predicate)

            for predicate in extract_predicates(path, keyword='.input'):
                inputpreds.add(predicate)

    # Compute output predicates
    outputpreds = allpreds.difference(inputpreds)

    # Add extra output predicates
    if args.extra_output_preds:
        extra_preds = args.extra_output_preds.read().splitlines()
        for pred in extra_preds:
            if pred in allpreds:
                outputpreds.add(pred)
            else:
                parser.error("Unknown output predicate to be added: {}".format(pred))

    # Create output file
    outputpreds = filter(lambda p: not p.startswith('_'), outputpreds)
    generate_output_logic(args.output_file, outputpreds)


if __name__ == '__main__':
    main()
