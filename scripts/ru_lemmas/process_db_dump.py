from pathlib import Path
from typing import Dict, List
import subprocess
from tqdm import tqdm
import csv
import re

input_dump = Path(__file__).parent.joinpath('dump.csv')
output_dir = Path(__file__).parent.parent.parent.joinpath('lexd/ru_lemmas')
main_lexd_dir = Path(__file__).parent.parent.parent.joinpath('lexd')

cyr2lat_translit = Path(__file__).parent.parent.parent.joinpath('translit/cyr2lat.hfst')

# if lexicons should include transliterated latin stems
INCLUDE_LATIN = False

if INCLUDE_LATIN and not cyr2lat_translit.is_file:
    raise FileNotFoundError(f'Transliterator not found: {cyr2lat_translit}')

pos_tags = {
    'гл.': '<v>',
    'сущ.': '<n>',
    'прил.': '<adj>',
    'мест.': '<pron>',
}
cyr_stem_fixes = {
    #'ғ̌': 'ғ',
    '/': '',
    'х̆': 'х̌',
}

def get_tag_name(tag: str) -> str:
    """ '<tagname>' -> 'tagname' """
    return re.sub(r'<|>', '', tag)

def get_lexicon_name(tag: str) -> str:
    """ '<tagname>' -> 'RuLemmasTagname' """
    return f'RuLemmas{get_tag_name(tag).capitalize()}'

def generate_rules():
    print('Generating rules...')
    main_lexd_files = [f for f in main_lexd_dir.iterdir() 
                       if f.is_file() and f.name.endswith('.lexd')]
    # get all <tags> from main rules files
    all_tags = set()
    for lexd in tqdm(main_lexd_files, desc='lexd files'):
        with open(lexd, 'r', encoding='utf-8') as f:
            for l in f:
                all_tags.update(re.findall(r'<[^<>]*>', l))
    # remove all pos tags, they are present alr near stems
    for pos in pos_tags.values():
        if pos in all_tags:
            all_tags.remove(pos)
    
    with open(output_dir.joinpath('0_rules.lexd'), 'w', encoding='utf-8') as f:
        f.write(f'PATTERNS\n')
        for pos in pos_tags.values():
            f.write(f"{get_lexicon_name(pos)} {get_lexicon_name('Tags')}*\n")
        f.write('\n')
        f.write(f"LEXICON {get_lexicon_name('Tags')}\n")
        f.write('>:>\n')
        for tag in sorted(all_tags):
            f.write(f'{tag}:{tag}\n')
        f.write('\n\n')

def cyr2lat(cyr_stems: List[str]) -> List[str]:
    """Transliterate cyr shughni to lating shugni using hfst

    Args:
        cyr_stems (List[str]): list of cyr shughni strings

    Returns:
        str: list of transliterated lating shughni strings
    """
    inp_str = '\n'.join(cyr_stems)
    translit = subprocess.Popen(["hfst-lookup", "-q", cyr2lat_translit],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
    res = translit.communicate(input=bytes(inp_str, encoding='utf8'))[0].decode()
    return [x.split('\t')[1] for x in res.split('\n\n') if x]

def meaning_to_lemma(meaning: str) -> str:
    """clears meaning string to a lemma string

    Args:
        meaning (str): meaning description, ex: 'a hand, a door handle, a key (to a mystery)'

    Returns:
        str: lemma string, ex: 'hand'
    """
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
    return f'{stem.lower()}{tag}:{lemma.lower()}{tag}\n'

def generate_lexicons():
    print('Generating lexicons...')
    pos_lists: Dict[str, list] = {}
    for ru_tag, fst_tag in pos_tags.items():
        pos_lists[ru_tag] = list()

    with open(input_dump, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)

        skipped_tags = set()
        # loading dump
        for cyr_stem, ru_tag, meaning in tqdm(reader, desc='Reading dump'):
            if not ru_tag in pos_tags:
                skipped_tags.add(ru_tag)
                continue
            if re.findall(r' |\.|\(|\)|=|\?', cyr_stem) or cyr_stem.startswith('-'):
                continue
            for a, b in cyr_stem_fixes.items():
                cyr_stem = cyr_stem.replace(a, b)

            pos_lists[ru_tag].append((
                cyr_stem, pos_tags[ru_tag], meaning_to_lemma(meaning),
            ))

    if INCLUDE_LATIN:
        # creating latin stems from cyrillic
        for ru_tag, data in tqdm(pos_lists.items(), desc='Generating latin stems'):
            lat_stems = cyr2lat([x[0] for x in data])
            if '(каузатив+?' in lat_stems:
                print('b')
            assert len(lat_stems) == len(data)
            for i in range(len(data)):
                data[i] = (*data[i], lat_stems[i])
    
    # converting to lexd format strings and writing to files
    for ru_tag, data in tqdm(pos_lists.items(), desc='Making lexd'):
        tag = get_tag_name(pos_tags[ru_tag])
        file_name = output_dir.joinpath(f"{tag}.lexd")
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(f'LEXICON {get_lexicon_name(pos_tags[ru_tag])}\n')
            for line in data:
                # cyrillic stem version
                f.write(lexd_str(line[0], line[1], line[2]))
                # latin stem version
                if INCLUDE_LATIN and not '+?' in line[0]: # not recognized
                    f.write(lexd_str(line[3], line[1], line[2]))
            f.write('\n\n')

    print('Skipped tags:', *skipped_tags)

def main():
    generate_rules()
    generate_lexicons()    

if __name__ == '__main__':
    main()
