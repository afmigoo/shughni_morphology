from __future__ import annotations
import pympi
import pympi.Elan
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Union, Tuple
import re

@dataclass
class TierItem:
    id: str
    content: str
    parent: Union[TierItem, str]
    prev: Union[TierItem, str]
    source_file: str
    tier: str
    children: List[TierItem] = field(default_factory=list)

    def __str__(self):
        inheritance = f'{self.id}>{[x.id for x in self.children]}'
        return f'{self.content} {inheritance} {self.tier}'
    
    def __repr__(self):
        return f'{self.content}'

@dataclass
class TaggedWord:
    wordform: str
    stem: str
    pos: str
    gloss_stem: List[str]
    gloss_suffix: List[List[str]]
    gloss_prefix: List[List[str]]
    source_file: Path

    def tagged(self) -> str:
        pos = f'<{self.pos}>'
        stem_gloss_str = ''
        pref_gloss_str = ''
        suff_gloss_str = ''
        if self.gloss_stem:
            stem_gloss_str = ''.join(f'<{x}>' for x in self.gloss_stem)
        if self.gloss_suffix and self.gloss_suffix[0]:
            suff_gloss_str = '>' + '>'.join([''.join(f'<{x}>' for x in morph) for morph in self.gloss_suffix])
        if self.gloss_prefix and self.gloss_prefix[0]:
            pref_gloss_str = '>'.join([''.join(f'<{x}>' for x in morph) for morph in self.gloss_prefix]) + '>'
        return f'{pref_gloss_str}{self.stem}{pos}{stem_gloss_str}{suff_gloss_str}'.lower()

    def __str__(self):
        return f'{self.tagged()}:{self.wordform.lower()}'
    
    def __repr__(self):
        return str(self)

def get_tiers(elan_file: Path) -> Dict[str, List[TierItem]]:
    """Read elan file and return TierItem lists

    Args:
        elan_file (Path): elan file (.eaf)

    Returns:
        Dict[str, List[TierItem]]: keys are tier names, lists contain items from said tiers
    """
    eaf = pympi.Elan.Eaf(elan_file)
    tiers: Dict[str, List[TierItem]] = {}
    ids: Dict[str, TierItem] = {}
    # create all TierItems and save it to their tiers
    for tier_name in eaf.tiers.keys():
        tiers[tier_name] = []
        for k, v in eaf.tiers[tier_name][1].items():
            tiers[tier_name].append(TierItem(content=v[1].strip(), id=k,
                                             parent=v[0], prev=v[2],
                                             source_file=elan_file,
                                             tier=tier_name))
            ids[k] = tiers[tier_name][-1]
    # when everything is inited link all items by their ids
    for k, it in ids.items():
        if it.parent in ids: 
            it.parent = ids[it.parent]
            it.parent.children.append(it)
        if it.prev in ids: 
            it.prev = ids[it.prev]
    return tiers

def get_all_children(item: TierItem, children: list = None) -> List[TierItem]:
    if children is None:
        children = []
    if len(item.children) == 0:
        return children
    for child in item.children:
        children.append(child)
    for child in item.children:
        get_all_children(child, children)
    return children

def get_morphs(word: TierItem) -> List[List[TierItem]]:
    morphs: List[List[TierItem]] = []
    for m in word.children:
        morphs.append([m, *get_all_children(m)])
    return morphs

def is_upper(s: str) -> bool:
    return s.upper() == s

def clean_segment(s: str) -> str:
    s = s.lower()
    return re.sub(r'=|,|^\.|\.$|^-|-$', '', s)

def resolve_pos(morphs: List[List[TierItem]]) -> str:
    # some words have multiple POS... I will think that the first one is the one
    for parts in morphs:
        for m in parts:
            if 'pos' in m.tier or 'msa' in m.tier:
                return m.content.lower()

def resolve_stem(morphs: List[List[TierItem]]) -> str:
    # stem is the one that has tagged POS
    for parts in morphs:
        m_stem = None
        m_pos = None
        for m in parts:
            if 'pos' in m.tier:
                m_pos = m.content.lower()
            elif 'morph' in m.tier and 'txt' in m.tier:
                m_stem = m.content.lower()
        if m_pos and m_stem:
            return clean_segment(m_stem)
    # if POS is tagged on word level, then stem is the first morph
    return clean_segment(morphs[0][0].content)

def resolve_tags(morphs: List[List[TierItem]], stem: str) -> dict:
    # all other morphs but stem
    tags_prefix: List[List[str]] = []
    tags_stem: List[str] = []
    tags_suffix: List[List[str]] = []
    stem_passed = False
    for parts in morphs:
        new_tags = []
        is_stem = False
        for m in parts:
            if clean_segment(m.content) == stem:
                is_stem = stem_passed = True
            if 'gls' in m.tier or 'glos' in m.tier:
                if m.content:
                    new_tags.extend(t for t in m.content.split('.') if t)
        if not new_tags:
            continue
        if is_stem:
            tags_stem.extend(new_tags)
        elif stem_passed:
            tags_suffix.extend([new_tags])
        else:
            tags_prefix.extend([new_tags])
    return {
        'prefix': tags_prefix,
        'stem': tags_stem,
        'suffix': tags_suffix
    }

def remove_lemma_glosses(word: TaggedWord):
    # lemma glosses are english semantic labels like 'go' in NEG-go.PST
    # this functions tries to filter them out since we are using Shughni stem instead
    def is_lemma_gloss(g: str) -> bool:
        if g.lower() == g: # lemma glosses are mostly lowercase
            return True
        return False
    word.gloss_stem = [g for g in word.gloss_stem if not is_lemma_gloss(g)]

def get_word_pairs(elan_file: Path) -> List[TaggedWord]:
    """Reads elan file and returns tagged words

    Args:
        elan_file (Path): elan file

    Returns:
        List[TaggedWord]: a list of tagged words
    """
    words: List[TaggedWord] = []
    all_tiers = get_tiers(elan_file)
    for word in all_tiers['A_word-txt-sgh']:
        if len(word.children) == 0:
            continue
        wordform = clean_segment(word.content)
        morphs = get_morphs(word)
        stem = resolve_stem(morphs)
        pos = resolve_pos(morphs)
        glosses = resolve_tags(morphs, stem)
        if stem and pos:
            words.append(TaggedWord(
                wordform=wordform, 
                stem=stem, pos=pos,
                gloss_stem=glosses['stem'],
                gloss_suffix=glosses['suffix'],
                gloss_prefix=glosses['prefix'],
                source_file=elan_file
            ))
    for w in words:
        remove_lemma_glosses(w)
    return words
