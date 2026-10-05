# Research: Replacing Presidio with a Lightweight PII Detection Stack

- Date: 2026-09-25
- Status: Research / proposal (input for a future ADR)
- Scope: PII **detection** only. The `PIIProvider` port, `EntityResolver`,
  `TokenAnonymizer`, persistence and the API stay the same.

---

## 1. Summary

1. **Presidio is not what makes the install large.** `presidio_analyzer` itself
   is about 2 MB. The size comes from what it pulls in (spaCy, four spaCy models,
   `phonenumbers`), and most of all from **`lingua`, which is 304 MB and has
   nothing to do with Presidio.**
2. We can remove Presidio without losing any current behaviour. The only thing
   it does for us today is run regex patterns with context words (the Swiss
   recognizers) and use spaCy NER for names and locations. We can rebuild the
   regex part ourselves in about 150 lines, using the existing `PIIProvider` port.
3. **Recommended target:** use a *layered provider stack*:
   - **Layer 1: rules.** Our own regex, checksum and context engine (no ML).
     Handles everything structured (EMAIL, CH_AHV, CH_IBAN, CH_UID, CH_PHONE,
     cards, IPs, URLs).
   - **Layer 2: NER.** One pluggable provider for names, locations and
     organisations. Default: **one multilingual ONNX model** run with
     `onnxruntime` (no PyTorch, no spaCy). Keep a spaCy-only adapter as a
     fallback option.
   - **Language detection:** swap `lingua` (304 MB) for `fast-langdetect`
     (fastText `lid.176.ftz`, about 1 MB model).
4. Expected result: **about 475 MB → about 5 MB with rules only, or about
   200–270 MB with rules + multilingual NER**. Quality should be equal or better
   for structured PII because checksums cut false positives. Quality for names
   has to be proven with our own evaluation set (see §7) before we commit.

---

## 2. What we have today (measured)

Current wiring (`src/privacy_engine/api/dependencies.py`):

```
CompositePIIProvider(
    RegexPIIProvider()                       # EMAIL
    PresidioPIIProvider(AnalyzerEngine(      # built-ins + Swiss recognizers
        spaCy: en_core_web_sm, de_core_news_sm, fr_core_news_sm, it_core_news_sm
    ))
)
LanguageResolver(LinguaLanguageDetector())   # de / fr / it / en
```

Installed size in `.venv` (measured with `du`, macOS, Python 3.13):

| Component | Size | Why it is there |
|---|---:|---|
| **lingua** | **304 MB** | language detection (the wheel ships models for ~75 languages, even though we only use 4) |
| 4 × spaCy `*_sm` models | 77 MB | Presidio NLP engine (PERSON / LOCATION / ORG) |
| spacy + thinc + blis + srsly + small deps | ~45 MB | spaCy runtime |
| phonenumbers | 23 MB | Presidio phone recognizer dependency |
| numpy | 23 MB | spaCy / thinc (would also be needed by onnxruntime) |
| presidio_analyzer | 2 MB | the analyzer itself |
| **Total detection stack** | **≈ 475 MB** | |

Conclusion: **about 65% of the size is lingua, not Presidio.** Replacing
lingua alone is the biggest and cheapest win, and it does not change the
architecture.

What Presidio actually gives us today:

- a regex + context-word scoring engine (`PatternRecognizer`), which our Swiss
  recognizers use;
- built-in recognizers (credit card with Luhn check, IP, URL, email, phone, and others);
- spaCy-backed NER for PERSON / LOCATION / NRP / ORG.

The evaluation dataset (`tests/evaluation/pii_detection_cases.json`) only
covers EMAIL, CH_AHV, CH_IBAN, CH_UID and CH_PHONE right now. **No test covers
names**, so the NER part has no measured quality yet.

---

## 3. Options looked at

### 3.1 Language detection (replacing lingua)

| Option | Size | Notes |
|---|---:|---|
| lingua, restricted to 4 languages | 304 MB on disk | Memory drops with low-accuracy mode or fewer languages, but the **wheel still ships every model**, so disk size does not change. |
| **fast-langdetect** (fastText `lid.176.ftz`) | wheel 0.8 MB (model 0.9 MB bundled) + `fasttext-predict` | 176 languages, very fast, fine for de/fr/it/en on sentence-length text. The model licence is CC BY-SA 3.0, so check it with legal. |
| py3langid | ~2–3 MB | Pure Python and numpy, weaker on very short text. |

**Recommendation:** `fast-langdetect`, wrapped in a new
`FastTextLanguageDetector` behind the existing `LanguageDetector` protocol.
Keep the `LanguageResolver` rule that an explicit `language` from the caller
wins over detection. Short or ambiguous text should still raise
`InvalidInputError` when confidence is too low.

### 3.2 Structured PII (replacing Presidio's pattern engine)

| Option | Size | Notes |
|---|---:|---|
| Presidio `PatternRecognizer` | pulls the whole stack | what we use now |
| scrubadub | small | mostly English-centric, little support for Swiss formats, low activity |
| DataFog | small | fast regex, but less control over scoring and context |
| **Own `RuleBasedPIIProvider` + `python-stdnum`** | stdnum wheel 1.2 MB, pure Python | Full control. `stdnum.iban`, `stdnum.ch.ssn` (AHV/AVS), `stdnum.ch.uid` and `stdnum.luhn` give **checksum validation**, which Presidio's Swiss regexes do not have today. |

**Recommendation:** build our own. The logic is small and fits our domain
better than any library:

```
Rule(entity_type, regex, base_score, validator | None, context_words[lang])
score = base_score
      + context_boost    if a context word appears within N tokens before the match
      → dropped          if validator exists and fails
```

This maps one-to-one onto `swiss_recognizers.py`, so the context words we
already maintain carry over unchanged.

Validation also raises precision. For example, `756.1234.5678.97` in the
dataset has a valid EAN-13 check digit. A random 13-digit number starting
with 756 would now be rejected instead of anonymized.

`phonenumbers` (23 MB) is optional. Our Swiss phone regex already covers the
CH case. Only add `phonenumbers` if international numbers are a requirement.

### 3.3 Unstructured PII: names, locations, organisations (the hard part)

This is the only part that needs ML. Candidates, all runnable **without
PyTorch** through ONNX Runtime:

| Candidate | Params / size | de/fr/it/en | Licence | Notes |
|---|---|---|---|---|
| spaCy `*_sm` × 4 (direct, without Presidio) | 77 MB + ~45 MB runtime | yes (4 models) | MIT | What we have. Small, but `sm` NER is weak on names outside news-style text. Needs 4 models. |
| **Multilingual distilled token-classifier NER**, e.g. `Davlan/distilbert-base-multilingual-cased-ner-hrl`, exported to ONNX int8 | ~135M params → ~135 MB int8 (estimate) | yes (one model) | check model card | PER/ORG/LOC only, which is exactly what rules cannot do. Simple BIO decoding. |
| **GLiNER PII (Knowledgator)**, edge/small/base | base: 197 MB UINT8 ONNX | English-focused | Apache 2.0 | F1 ≈ 0.77 (small) / 0.81 (base) as reported. Zero-shot labels. |
| **GLiNER2-PII multi** (`fastino/gliner2-privacy-filter-PII-multi`) | 205M params | en, fr, de, it, es, pt, nl | CC-BY-4.0 | 42 PII types. The model card reports **low precision (0.35–0.37)** and training on synthetic data only. ONNX runner (`gliner2-onnx`) is experimental. |
| Piiranha v1 (mDeBERTa-v3-base) | 280M params | en, fr, de, it, es, nl | **sources disagree: verify** | High reported token accuracy. 256-token context, so needs chunking. |
| OpenAI Privacy Filter | 1.5B total / 50M active (MoE) | English best, others weaker | Apache 2.0 | Strong in English (F1 ~96% on PII-Masking-300k), but the weights are large on disk and non-English quality is lower by the model card's own statement. **Not lightweight for us.** |

Measured runtime wheels (linux x86_64, Python 3.12):
`onnxruntime` 23.6 MB, `tokenizers` 3.4 MB. `numpy` is already present.

**Recommendation:**

- **Default NER provider:** one multilingual token-classification model in
  ONNX int8, run with `onnxruntime` + `tokenizers`. One model replaces four
  spaCy models, handles de/fr/it/en, and does not need PyTorch or spaCy.
- **Shortlist for the bake-off (§7):** the distilled multilingual NER model
  (lightest), GLiNER2-PII multi (widest label set), and spaCy `sm` direct
  (baseline and fallback).
- Do **not** use a zero-shot or LLM-style model as the only layer. Rules must
  always run first for structured IDs, because they are deterministic and
  auditable.

---

## 4. Proposed architecture

The design needs no changes to the domain. `PIIProvider` (ADR-002) and
`CompositePIIProvider` already support this layout:

```
                     LanguageResolver ── FastTextLanguageDetector   (was Lingua)
                              │ language
                              ▼
CompositePIIProvider(
    RuleBasedPIIProvider(rules=default_rules() + swiss_rules())     # Layer 1, ~0 MB
    OnnxNerPIIProvider(model_path, labels_map, min_score)           # Layer 2, optional
)
        │
        ▼
EntityResolver → TokenAnonymizer   (unchanged)
```

New or changed modules (all in `infrastructure`, none in `domain`):

| Module | Replaces | Notes |
|---|---|---|
| `infrastructure/providers/rules/engine.py` | Presidio `PatternRecognizer` | `Rule` dataclass, context-window scoring, validators |
| `infrastructure/providers/rules/swiss.py` | `swiss_recognizers.py` | same regexes and context words, plus stdnum validators |
| `infrastructure/providers/rules/generic.py` | Presidio built-ins | EMAIL (moved from `RegexPIIProvider`), CREDIT_CARD (Luhn), IP, URL |
| `infrastructure/providers/onnx_ner_provider.py` | spaCy NER via Presidio | loads model once (`lru_cache`, same as today), chunks long text, maps labels → `PERSON`/`LOCATION`/`ORGANIZATION` |
| `infrastructure/language/fasttext_detector.py` | `lingua_detector.py` | same `LanguageDetection` result |
| `api/dependencies.py` | Presidio wiring | configuration picks the profile |

Deployment profiles, selected through configuration (`pydantic-settings`):

| Profile | Contents | Approx. size | Use when |
|---|---|---:|---|
| `rules` | Layer 1 + fastText lang-id | **~5 MB** | structured data, logs, or where names are not in scope |
| `rules+ner` (default) | + onnxruntime + tokenizers + int8 NER model | **~200–270 MB** (model-dependent, to be measured) | general free text sent to LLMs |

Model weights should **not** go into the wheel or the git repo. Download them
at image build time (or from an internal artifact store), pin them by hash,
and point to them with a config path. This keeps the Python package tiny and
makes model upgrades a config change.

---

## 5. Honest trade-offs

- **Removing Presidio alone saves only about 25 MB** (Presidio + phonenumbers).
  The big savings come from **dropping lingua (−304 MB)** and **replacing four
  spaCy models + spaCy runtime (−120 MB)**. A transformer NER model adds
  about 150–250 MB back, so `rules+ner` is roughly half the current size, not
  a tenth. Only the `rules` profile is truly tiny.
- A multilingual transformer NER model is usually **more accurate on names**
  than spaCy `sm`, but it is **slower on CPU** (tens of ms per paragraph
  instead of a few ms). Batch or chunk it, and measure p95 latency in the
  bake-off.
- Our own rule engine means **we own the maintenance**: new ID formats,
  context words, and tests. Given what we already do in
  `swiss_recognizers.py`, this is small and gives more control than Presidio did.
- Model licences vary (Apache-2.0 / MIT / CC-BY / possibly non-commercial).
  **Legal must approve the chosen model before use.**
- No detector is perfect, including Presidio. The anonymization contract
  should still be treated as best-effort and backed by the evaluation dataset.

---

## 6. Rejected or not recommended

| Option | Reason |
|---|---|
| Keep Presidio and trim it (use `en_core_web_sm` only) | Breaks de/fr/it NER. Lingua stays, so the size problem is not solved. |
| Presidio with a transformers NLP engine | Pulls in PyTorch (~0.7–2.6 GB). Heavier than today. |
| OpenAI Privacy Filter as main detector | Large weights, English-first. Worth watching as an optional "high-accuracy" provider later. |
| Cloud PII APIs (Azure AI Language, AWS Comprehend, Google DLP) | Sends the raw PII to a third party before anonymizing it, which defeats the product's purpose. |
| LLM-based detection (small local LLM) | Slow, not deterministic, hard to audit offsets. Too heavy. |

---

## 7. How we choose the NER model: a bake-off with our own harness

We already have `tests/evaluation/` (dataset + evaluator + metrics tests). Extend it before deciding:

1. **Extend the dataset** with at least 20–30 cases per language (de, fr, it, en) containing
   PERSON / LOCATION / ORGANIZATION, including Swiss names and places (e.g. "Frau Müller aus Zürich",
   "M. Rochat habite à Lausanne", "il signor Bernasconi di Lugano"), plus negative cases
   (street-name-looking words, product names, capitalised common nouns in German).
2. Run each candidate provider through the **same evaluator** and record:
   precision, recall, F1 per entity type and language, p50/p95 latency per 1 000 chars on CPU,
   RSS memory after load, installed size.
3. Decision rule (proposal): pick the smallest candidate whose **recall on PERSON ≥ current Presidio/spaCy
   baseline** and whose precision does not drop more than 5 points. Recall matters most here,
   because a missed name leaks to the LLM.

---

## 8. Suggested implementation slices (following AGENTS.md workflow)

1. **ADR-013**: replace Presidio with a layered rule + pluggable-NER stack (this document → decision).
2. **SLICE: fastText language detector.** New adapter + unit tests, swap wiring, remove `lingua`.
   (Independent. Delivers −304 MB on its own.)
3. **SLICE: rule engine.** `Rule`, context scoring, validators + unit tests.
4. **SLICE: Swiss + generic rules on the rule engine.** Port `swiss_recognizers.py`, add stdnum checksum
   validation. Existing evaluation cases must stay green.
5. **SLICE: extend evaluation dataset with names/locations** (de/fr/it/en) and record the Presidio baseline.
6. **SLICE: ONNX NER provider.** Adapter, label mapping, chunking, lazy model loading + tests with a fake
   session, integration test gated on the model being present.
7. **SLICE: bake-off + pick model.** Record results in the ADR.
8. **SLICE: remove Presidio/spaCy.** Delete `presidio_provider.py`, its tests, and the dependencies in
   `pyproject.toml`. Add deployment profiles.

Slices 2–4 can ship before any ML decision is made, and they already remove most of the size.

---

## Sources

- GLiNER2-PII paper: https://arxiv.org/abs/2605.09973
- GLiNER2-PII multi model card: https://huggingface.co/fastino/gliner2-privacy-filter-PII-multi
- Knowledgator GLiNER-PII: https://huggingface.co/knowledgator/gliner-pii-base-v1.0
- GLiNER2 ONNX runtime (experimental): https://github.com/lmoe/gliner2-onnx
- GLiNER: https://github.com/urchade/GLiNER
- OpenAI Privacy Filter: https://huggingface.co/openai/privacy-filter ,
  https://openai.com/index/introducing-openai-privacy-filter/
- Piiranha v1: https://www.marktechpost.com/2024/09/14/piiranha-v1-released-a-280m-small-encoder-open-model-for-pii-detection-with-98-27-token-detection-accuracy-supporting-6-languages-and-17-pii-types-released-under-mit-license/
- Open-source PII model overview: https://grepture.com/blog/best-open-source-models-pii-redaction
- Lightweight lang-id with fastText: https://github.com/LlmKira/fast-langdetect
- lingua memory modes: https://pypi.org/project/lingua-language-detector/
- python-stdnum (IBAN, ch.ssn, ch.uid, Luhn): https://github.com/arthurdejong/python-stdnum
- Presidio alternatives overview: https://anonde.io/blog/anonde-vs-presidio/ ,
  https://techhorizonconsulting.com/blog/detecting-and-redacting-pii--microsoft-presidio---scrubadub
