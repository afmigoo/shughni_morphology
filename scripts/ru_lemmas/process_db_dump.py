from pathlib import Path
from typing import Dict, List
import subprocess
from tqdm import tqdm
import csv
import re
import os

input_dump = Path(__file__).parent.joinpath('dump.csv')
output_dir = Path(__file__).parent.joinpath('pos')
cyr2lat_translit = Path(__file__).parent.parent.parent.joinpath('translit/cyr2lat.hfst')

if not cyr2lat_translit.is_file:
    raise FileNotFoundError(f'Transliterator not found: {cyr2lat_translit}')

pos_tags = {
    'гл.': '<v>',
    'сущ.': '<n>',
    'прил.': '<adj>',
    'мест.': '<pron>',
}
cyr_stem_fixes = {
    'ғ̌': 'ғ',
}

def cyr2lat(cyr_stems: List[str]) -> str:
    inp_str = '\n'.join(cyr_stems)
    for a, b in cyr_stem_fixes.items():
        inp_str.replace(a, b)
    translit = subprocess.Popen(["hfst-lookup", "-q", cyr2lat_translit],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
    res = translit.communicate(input=bytes(inp_str, encoding='utf8'))[0].decode()
    return [x.split('\t')[1] for x in res.split('\n\n') if x]

def meaning_to_lemma(meaning: str) -> str:
    lemma = meaning.lower()
    lemma = lemma.replace('\n', '')
    # remove everythihg inside ()
    lemma = re.sub(r'\(.*\)', '', lemma)
    # take first substring before ; or ,
    lemma = re.split(r',|;', lemma, maxsplit=1)[0]
    # take last substring if : is present
    if ':' in lemma:
        lemma = re.split(r':', lemma)[-1]
    # take first substring if it has 'a) walk b) run' format
    if re.findall(r'.\)', lemma):
        lemma = re.split(r'.\)', lemma)[1]
    # clear from characters
    lemma = re.sub(r'[^а-яa-z ]', '', lemma)
    lemma = re.sub(r' +', '_', lemma.strip())
    return lemma

def lexd_str(stem: str, tag: str, lemma: str) -> str:
    return f'{stem}{tag}:{lemma}{tag}\n'

def main():
    pos_lists: Dict[str, list] = {}
    for ru_tag, fst_tag in pos_tags.items():
        pos_lists[ru_tag] = list()

    with open(input_dump, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)

        skipped_tags = set()
        # loading dump
        for cyr_stem, ru_tag, meaning in tqdm(reader):
            if not ru_tag in pos_tags:
                skipped_tags.add(ru_tag)
                continue
            if re.findall(r' |\.|\(|\)', cyr_stem) or cyr_stem.startswith('-'):
                continue

            pos_lists[ru_tag].append((
                cyr_stem, pos_tags[ru_tag], meaning_to_lemma(meaning),
            ))

    # creating latin stems from cyrillic
    for ru_tag, data in tqdm(pos_lists.items()):
        lat_stems = cyr2lat([x[0] for x in data])
        if '(каузатив+?' in lat_stems:
            print('b')
        assert len(lat_stems) == len(data)
        for i in range(len(data)):
            data[i] = (lat_stems[i], *data[i])
    
    # converting to lexd format strings and writing to files
    for ru_tag, data in tqdm(pos_lists.items()):
        tag = re.sub(r'<|>', '', pos_tags[ru_tag])
        file_name = output_dir.joinpath(f"{tag}.lexd")
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(f'LEXICON RuLemmas{tag.capitalize()}\n')
            for line in data:
                # cyrillic stem version
                f.write(lexd_str(line[0], line[2], line[3]))
                # latin stem version
                f.write(lexd_str(line[1], line[2], line[3]))
            f.write('\n\n')

    print('Skipped tags:', *skipped_tags)

if __name__ == '__main__':
    main()
