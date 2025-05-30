Shughni language morphological analyzator and generator made with lexd and twol.

# FST binary compilation
### Dependencies:
- [`hfst` tools](https://github.com/hfst/hfst)
- [`lexd` compiler](https://github.com/apertium/lexd)
- `python` (only for testing and metrics scripts, FST binaries are compiled without python)
### Make
Compile all `.hfstol` binaries
```bash
make all
```

Compile any specific FST binary, all possible binaries are listed at the end
```bash
make sgh_analyze_stem_segm_cyr.hfst
```

Compile all `.hfst` binaries
```bash
make all_hfst
```

Run tests (depends on `python`)
```bash
make test
```

Evaluate all metrics (depends on `python`, `requirements.txt` packages)
```bash
make metrics
```

The Makefile was tested on Debian, other platforms are not guaranteed to be compatible. Tested with 
- `hfst 3.16.0`
- `lexd 1.3.1`
- `python 3.11.2`

# FST binaries naming
All files have name with the following format:
```
<direction>_<lemma type>_<segmentation>_<script>
```
Where
- `direction` can be 'gen' or 'analyze'
    - 'gen': `дарйо<n>><pl>:дарйойен`, tagged form -> surface form
    - 'analyze': `дарйойен:дарйо<n>><pl>`, surface form -> tagged form
- `lemma type` can be 'stem' or 'rulem'. It sets tagged form's main word type
    - 'stem': `дарйойен:дарйо<n>><pl>`, a shughni stem will be used as a lemma
    - 'rulem': `дарйойен:река<n>><pl>`, a russian lemma will be used as a lemma
- `segmentation` can be 'segm' or 'word'. It sets surface form morpheme border behavior
    - 'segm': `дарйо<n>><pl>:дарйо>йен`, surface forms are segmented: they have `>` separator between all the morphemes
    - 'word': `дарйо<n>><pl>:дарйойен`, surface forms are not segmented
- `script` can be 'cyr' or 'lat', dictates surface form's script
    - 'cyr': `дарйо<n>><pl>:дарйойен`
    - 'lat': `дарйо<n>><pl>:daryoyen`

A `.hfstol` version is also available for every possible `.hfst` file.

## Full list of available files
|File|Input|Output|
|-|-|-|
|Generators|
|sgh_gen_stem_segm_cyr|`дарйо<n>><pl>`|`дарйо>йен`|
|sgh_gen_stem_word_cyr|`дарйо<n>><pl>`|`дарйойен`|
|sgh_gen_rulem_segm_cyr|`река<n>><pl>`|`дарйо>йен`|
|sgh_gen_rulem_word_cyr|`река<n>><pl>`|`дарйойен`|
|sgh_gen_stem_segm_lat|`дарйо<n>><pl>`|`daryo>yen`|
|sgh_gen_stem_word_lat|`дарйо<n>><pl>`|`daryoyen`|
|sgh_gen_rulem_segm_lat|`река<n>><pl>`|`daryo>yen`|
|sgh_gen_rulem_word_lat|`река<n>><pl>`|`daryoyen`|
|Analyzers|
|sgh_analyze_stem_segm_cyr|`дарйо>йен`|`дарйо<n>><pl>`|
|sgh_analyze_stem_word_cyr|`дарйойен`|`дарйо<n>><pl>`|
|sgh_analyze_rulem_segm_cyr|`дарйо>йен`|`река<n>><pl>`|
|sgh_analyze_rulem_word_cyr|`дарйойен`|`река<n>><pl>`|
|sgh_analyze_stem_segm_lat|`daryo>yen`|`дарйо<n>><pl>`|
|sgh_analyze_stem_word_lat|`daryoyen`|`дарйо<n>><pl>`|
|sgh_analyze_rulem_segm_lat|`daryo>yen`|`река<n>><pl>`|
|sgh_analyze_rulem_word_lat|`daryoyen`|`река<n>><pl>`|


---

**Author**: Elen Kartina (elenkartina@proton.me)  
**Scientific supervisor**: [George Moroz](https://github.com/agricolamz)  
**Advisor**: [Max Melenchenko](https://github.com/maxmerben)  

