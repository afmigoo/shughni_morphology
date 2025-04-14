Shughni language morphological analyzator and generator made with lexd and twol.

# Make hfst files
Make sure you have hfst tools installed at your PATH
```bash
make all
```
Makefile is written for Debian, it was not tested in other enviroments. Look for pre-built .hfst files in releases

# .hfst files names meaning
All files have name with the following format:
```
<direction>_<lemma type>_<surface morph borders>_<script>.hfst
```
Where
- `direction` can be 'gen' or 'analyze'
    - 'gen': `дарйо<n>><pl>:дарйойен`, tagged form -> surface form
    - 'analyze': `дарйойен:дарйо<n>><pl>`, surface form -> tagged form
- `lemma type` can be 'stem' or 'rulem'. It sets tagged form's main word type
    - 'stem': `дарйойен:дарйо<n>><pl>`, a shughni stem will be used as a lemma
    - 'rulem': `дарйойен:река<n>><pl>`, a russian lemma will be used as a lemma
- `surface morph borders` can be 'morph' or 'word'. It sets surface form morpheme border behavior
    - 'morph': `дарйо<n>><pl>:дарйо>йен`, surface forms have `>` separator between all the morphs
    - 'word': `дарйо<n>><pl>:дарйойен`, surface forms are regular words
- `script` can be 'cyr' or 'lat', dictates surface form's script
    - 'cyr': `дарйо<n>><pl>:дарйойен`
    - 'lat': `дарйо<n>><pl>:daryoyen`

## Full list of available files
|File|Input|Output|
|-|-|-|
|Generators|
|gen_stem_morph_cyr.hfst|`дарйо<n>><pl>`|`дарйо>йен`|
|gen_stem_word_cyr.hfst|`дарйо<n>><pl>`|`дарйойен`|
|gen_rulem_morph_cyr.hfst|`река<n>><pl>`|`дарйо>йен`|
|gen_rulem_word_cyr.hfst|`река<n>><pl>`|`дарйойен`|
|gen_stem_morph_lat.hfst|`дарйо<n>><pl>`|`daryo>yen`|
|gen_stem_word_lat.hfst|`дарйо<n>><pl>`|`daryoyen`|
|gen_rulem_morph_lat.hfst|`река<n>><pl>`|`daryo>yen`|
|gen_rulem_word_lat.hfst|`река<n>><pl>`|`daryoyen`|
|Analyzers|
|analyze_stem_morph_cyr.hfst|`дарйо>йен`|`дарйо<n>><pl>`|
|analyze_stem_word_cyr.hfst|`дарйойен`|`дарйо<n>><pl>`|
|analyze_rulem_morph_cyr.hfst|`дарйо>йен`|`река<n>><pl>`|
|analyze_rulem_word_cyr.hfst|`дарйойен`|`река<n>><pl>`|
|analyze_stem_morph_lat.hfst|`daryo>yen`|`дарйо<n>><pl>`|
|analyze_stem_word_lat.hfst|`daryoyen`|`дарйо<n>><pl>`|
|analyze_rulem_morph_lat.hfst|`daryo>yen`|`река<n>><pl>`|
|analyze_rulem_word_lat.hfst|`daryoyen`|`река<n>><pl>`|