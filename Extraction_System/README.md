Pseudo Code for Pipeline: 

PROCESS_PDF(pdf):
  text = PDF_TO_TEXT(pdf)
  chunks = CHUNK(text, size=300w, overlap=80w)

  FOR target IN [prep, dopant, doping_method, solvent]:
    scored_chunks = [(c, SCORE(c, target)) for c in chunks]
    top = TOP_K(scored_chunks, k=5)

    cands = []
    FOR c IN top:
      cands += KW_WINDOW(c, target)
      cands += REGEX(c, target)
      cands += DICT_HITS(c, target)
      cands += SPACY_RULES(c, target)

    best = ARGMAX([(x, CONF(x)) for x in cands])
    OUT[target] = best.value IF best.conf >= THRESH[target] ELSE "NOT_FOUND"

  UPDATE_RULE_WEIGHTS(OUT)   # using your verified labels later
  RETURN OUT


SCORE(chunk, target) = section_bonus + keyword_count + proximity_bonus
CONF(candidate) = method_weight * rule_reliability + validation_bonus + context_bonus



======
src/

pipeline.py (orchestrator)

pdf_text.py (pdf to pages, cleaning)

chunking.py (sectioning, windowing)

extractors/

polymer.py

dopant.py

solvent.py

doping_method.py

film_prep.py

scoring.py (candidate scoring, tie break)

normalize.py (canonical names, synonym maps)

validate.py (consistency checks)

evaluate.py (metrics vs gold)

rules/

v001/

polymer_patterns.yml

dopant_patterns.yml

solvent_patterns.yml

method_patterns.yml

film_prep_patterns.yml

synonym_map.yml

stoplists.yml (things to ignore, like “references”, “previous work” cues)

data/

gold/

annotations.jsonl (value + evidence span + page)

runs/

run_2026-01-13_v001/ (outputs, logs, per-pdf debug)

Key idea: rules live in YAML, code loads them. Updating rules never requires editing Python beyond adding new rule types.