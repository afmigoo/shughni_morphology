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
sgh_<direction>_<type>_<script>.hfst
```
Where
- `direction` can be 'gen' or 'analyze'
    - 'gen': `дарйо<n>><pl>:дарйойен`
    - 'analyze': `дарйойен:дарйо<n>><pl>`
- `type` can be 'morph' or 'word'
    - 'morph': `дарйо<n>><pl>:дарйо>йен`, surface forms have `>` separator between all the morphs
    - 'word': `дарйо<n>><pl>:дарйойен`, surface forms are regular words
- `script` can be 'cyr' or 'lat'
    - 'cyr': `дарйо<n>><pl>:дарйойен`
    - 'lat': `дарйо<n>><pl>:daryoyen`

## Full list of available files
|File|Input|Output|
|-|-|-|
|sgh_analyze_morph_cyr.hfst|`дарйо>йен`|`дарйо<n>><pl>`|
|sgh_analyze_morph_lat.hfst|`daryo>yen`|`дарйо<n>><pl>`|
|sgh_analyze_word_cyr.hfst|`дарйойен`|`дарйо<n>><pl>`|
|sgh_analyze_word_lat.hfst|`daryoyen`|`дарйо<n>><pl>`|
|sgh_gen_morph_cyr.hfst|`дарйо<n>><pl>`|`дарйо>йен`|
|sgh_gen_morph_lat.hfst|`дарйо<n>><pl>`|`daryo>yen`|
|sgh_gen_word_cyr.hfst|`дарйо<n>><pl>`|`дарйойен`|
|sgh_gen_word_lat.hfst|`дарйо<n>><pl>`|`daryoyen`|