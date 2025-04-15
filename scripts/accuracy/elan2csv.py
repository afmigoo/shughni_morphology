#!/usr/bin/env python3
from pathlib import Path
import csv
import argparse
import logging
import re

from src.elan_reader import get_word_pairs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument('elan_file', help='input elan file to parse')
parser.add_argument('csv_file', help='output csv file')

def rmpunct(s: str) -> str:
    return re.sub(r'"|,', '', s)

def main():
    args = parser.parse_args()
    words = get_word_pairs(Path(args.elan_file))
    with open(args.csv_file, 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(('wordform', 'tagged'))
        for w in words:
            if all((w.pos != '?', w.wordform != '?', w.stem != '?')):
                writer.writerow((rmpunct(w.wordform), w.tagged()))

if __name__ == '__main__':
    main()
