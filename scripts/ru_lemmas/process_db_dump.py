from typing import Dict, List, Set, Tuple, DefaultDict, Generator
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm
from statistics import mean, median
import subprocess
import csv
import re

import matplotlib.pyplot as plt

input_dump = Path(__file__).parent.joinpath('dump.csv')
output_dir = Path(__file__).parent.parent.parent.joinpath('translate/lexd')
main_lexd_dir = Path(__file__).parent.parent.parent.joinpath('lexd')

cyr2lat_translit = Path(__file__).parent.parent.parent.joinpath('translit/cyr2lat.hfst')

# if lexicons should include transliterated latin stems
INCLUDE_LATIN = False

if INCLUDE_LATIN and not cyr2lat_translit.is_file:
    raise FileNotFoundError(f'Transliterator not found: {cyr2lat_translit}')

pos_alias = {
    'прил.': 'adj',
    'нареч.': 'adv',
    'союз': 'conj',
    'межд.': 'intj',
    'сущ.': 'n',
    'числ.': 'num',
    'предл.': 'prep',
    'мест.': 'pro',
    'част.': 'prt',
    'посл.': 'post',
    'гл.': 'v',
}

extra_variants = {
    'pro': ['pers', 'dem']
}

cyr_stem_fixes = {
    #'ғ̌': 'ғ',
    '/': '',
    'х̆': 'х̌',
    'ӯ̊': 'ӯ', # invalid set of diacritics
    'ҳ̌': 'ҳ',
    'ц̌': 'ч',
    '́': '' # remove stress
}

verb_stem_infl = [
    r'[дт]$',       # past, inf
    r'[дт]оw$',     # inf
    r'оw$',         # inf
    r'[ҷч]$'        # pref
]

def tag(tag: str) -> str:
    """ 'tagname' -> '<tagname>' """
    return re.sub(r'<|>', '', tag)

def get_lexicon_name(tag: str) -> str:
    """ 'tagname' -> 'RuLemmasTagname' """
    return f'RuLemmas{tag.capitalize()}'

def get_lexd_formatted_tags(tag: str) -> str:
    """ 'tagname' -> [<tagname>:<tagname>] """
    if not tag in extra_variants:
        return f'[<{tag}>]'
    all_tags = [tag] + extra_variants[tag]
    return '|'.join(f'[<{t}>]' for t in all_tags)

def verb_forms(verb_form: str) -> List[str]:
    """Backtracks verb stem inflection to generate less inflected verb stems"""
    forms = set([verb_form])
    for pattern in verb_stem_infl:
        forms.add(re.sub(pattern, '', verb_form))
    return list(forms)

def inflate_verb_stems(verbs: Set[Tuple[str, str]]):
    new_stems = set()
    for stem, meaning in verbs:
        new_stems.update((stem_form, meaning) for stem_form in verb_forms(stem))
    verbs.update(new_stems)

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
    
    with open(output_dir.joinpath('0_rules.lexd'), 'w', encoding='utf-8') as f:
        f.write(f'PATTERNS\n')
        f.write('({base}|{tags_lex})+\n\n'.format(
            tags_lex=get_lexicon_name('Tags'),
            base=get_lexicon_name('Base')
        ))
        f.write(f"PATTERN {get_lexicon_name('Base')}\n")
        for pos in pos_alias.values():
            f.write("{pos_lex} {pos_tag}\n".format(
                pos_lex=get_lexicon_name(pos),
                pos_tag=get_lexd_formatted_tags(pos)
            ))
        f.write('\n')
        f.write(f"LEXICON {get_lexicon_name('Tags')}\n")
        f.write('>\n')
        for tag in sorted(all_tags):
            f.write(f'{tag}\n')
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
    # remove everythihg inside () if its not the entire string
    no_brackets = re.sub(r'\(.*\)', '', lemma)
    if no_brackets:
        lemma = no_brackets
    else:
        lemma = re.sub(r'\(|\)', '', lemma)
    # take first substring before ;
    lemma = re.split(r';', lemma, maxsplit=1)[0]
    # take last substring after :
    lemma = re.split(r':', lemma)[-1]
    # take first substring before ,
    lemma = re.split(r',', lemma, maxsplit=1)[0]
    # take first substring if it has 'a) walk b) run' format
    if re.findall(r'.\)', lemma):
        lemma = re.split(r'.\)', lemma)[1]
    # clear from characters
    lemma = re.sub(r'[^а-яa-z ]', '', lemma)
    lemma = re.sub(r' +', '_', lemma.strip())
    return lemma

def lexd_str(stem: str, lemma: str) -> str:
    return f'{stem.lower()}:{lemma.lower()}\n'

def generate_lexicons():
    print('Generating lexicons...')
    pos_lists: Dict[str, List[Tuple]] = {}

    with open(input_dump, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)

        skipped_tags: Set[str] = set()
        unique_pairs: DefaultDict[str, Set[Tuple[str, str]]] = defaultdict(set)
        # loading dump
        for cyr_stem, ru_tag, meaning in tqdm(reader, desc='Reading dump'):
            if not ru_tag in pos_alias:
                skipped_tags.add(ru_tag)
                continue
            if re.findall(r' |\.|\(|\)|=|\?', cyr_stem) or cyr_stem.startswith('-'):
                continue
            for a, b in cyr_stem_fixes.items():
                cyr_stem = cyr_stem.replace(a, b)

            lemma = meaning_to_lemma(meaning)
            if not lemma:
                print(f'Lemma is empty for {cyr_stem}: {meaning}')
                continue
            if cyr_stem.startswith('-') or cyr_stem.endswith('-'):
                continue
            unique_pairs[ru_tag].add((
                cyr_stem, meaning_to_lemma(meaning),
            ))

        inflate_verb_stems(unique_pairs['гл.'])
        for tag, pairs in unique_pairs.items():
            pos_lists[tag] = sorted(list(pairs), key=lambda x: x[0] + x[1])
        del unique_pairs

    if INCLUDE_LATIN:
        # creating latin stems from cyrillic
        for ru_tag, pairs in tqdm(pos_lists.items(), desc='Generating latin stems'):
            # generating latin forms
            lat_stems = cyr2lat([x[0] for x in pairs])
            assert len(lat_stems) == len(pairs)
            for i in range(len(pairs)):
                # adding latin forms to pairs (now they are triplets)
                pairs[i] = (*pairs[i], lat_stems[i])
    
    # converting to lexd format strings and writing to files
    char_lengths = []
    word_lengths = []
    for ru_tag, data in tqdm(pos_lists.items(), desc='Making lexd'):
        file_name = output_dir.joinpath(f"{pos_alias[ru_tag]}.lexd")
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(f'LEXICON {get_lexicon_name(pos_alias[ru_tag])}\n')
            for line in data:
                # cyrillic stem version
                char_lengths.append((len(line[1]), line[1]))
                word_lengths.append((len(line[1].split('_')), line[1]))
                f.write(lexd_str(line[0], line[1]))
                # latin stem version
                if INCLUDE_LATIN and not '+?' in line[0]: # not recognized
                    f.write(lexd_str(line[2], line[1]))
            f.write('\n\n')

    print(sum(1 for x in word_lengths if x[0] <= 4) / len(word_lengths))
    print(f'[Chars] Mean: {mean(x[0] for x in char_lengths):.3f}; median: {median(x[0] for x in char_lengths)} min: {min(char_lengths)} max: {max(char_lengths)}')
    print(f'[Words] Mean: {mean(x[0] for x in word_lengths):.3f}; median: {median(x[0] for x in word_lengths)} min: {min(word_lengths)} max: {max(word_lengths)}')
    #plt.hist([x[0] for x in lemma_lengths], bins=100)
    #plt.savefig("lemma_len.pdf", format="pdf", bbox_inches="tight") 
    print('Skipped tags:', *skipped_tags)

def main():
    generate_rules()
    generate_lexicons()    

if __name__ == '__main__':
    main()
