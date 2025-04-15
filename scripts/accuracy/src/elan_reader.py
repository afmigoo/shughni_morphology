from __future__ import annotations
import pympi
import pympi.Elan
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Union, Tuple

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

@dataclass
class TaggedWord:
    wordform: str
    stem: str
    pos: str
    tags: List[str]
    source_file: Path

    def tagged(self) -> str:
        tags = f"<{self.pos}>" + "".join([f"<{x}>" for x in self.tags])
        return f'{self.stem}{tags}'

    def __str__(self):
        return f'{self.tagged()}:{self.wordform}'

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

def is_upper(s: str) -> bool:
    return s.upper() == s

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
        wordform = word.content
        pos = stem = '?'
        tags = []
        for ch in get_all_children(word):
            # first morph text child is a stem
            if stem == '?' and 'morph' in ch.tier and 'txt' in ch.tier:
                stem = ch.content
            if pos == '?' and 'pos' in ch.tier:
                pos = ch.content
            if 'morph' in ch.tier and 'gls' in ch.tier:
                if '.' in ch.content:
                    new_tags = [x for x in ch.content.split('.')]
                else:
                    new_tags = [ch.content]
                tags.extend([x.lower() for x in new_tags if is_upper(x)])
        words.append(TaggedWord(
            wordform=wordform.lower(), stem=stem.lower(),
            pos=pos, tags=tags, source_file=elan_file
        ))
    return words
