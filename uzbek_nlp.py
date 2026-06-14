"""
uzbek_nlp.py
O'zbek tili uchun tokenizatsiya va lemmatizatsiya moduli.
korpus_app.py ga tegmasdan ulash uchun alohida fayl.
"""

import re

# ─────────────────────────────────────────────────────────
#  O'zbek tiliga xos qo'shimchalar ro'yxati
#  (kelishik, ko'plik, egalik, fe'l qo'shimchalari)
#  Uzunroq qo'shimcha avval tekshiriladi (greedy order)
# ─────────────────────────────────────────────────────────
UZ_SUFFIXES = [
    # Ko'plik
    "lar", "lar",
    # Kelishik qo'shimchalari
    "ning", "ga", "ni", "da", "dan", "gача", "gacha",
    # Egalik
    "im", "ing", "i", "imiz", "ingiz",
    "imni", "ingni", "ini",
    "imga", "ingga", "iga",
    "imda", "ingda", "ida",
    "imdan", "ingdan", "idan",
    # Fe'l nisbat / harakat nomi
    "moq", "ish", "lik", "lik",
    # Fe'l zamon qo'shimchalari
    "yapti", "yapman", "yapsan", "yapmiz", "yapsiz", "yaptilar",
    "adi", "aman", "asan", "amiz", "asiz", "adilar",
    "di", "dim", "ding", "dik", "dingiz", "dilar",
    "gan", "gani", "ganini", "ganiga", "ganida",
    "yotgan", "yotir", "yotibdi",
    "ydi", "ydir",
    # Sifat / ravish yasovchi
    "li", "siz", "dosh", "kor", "bon", "par",
    "roq", "gina", "kina", "qina",
    # Bog'lama
    "man", "san", "miz", "siz", "dir", "dirlar",
    # Qo'shimcha ko'plik + kelishik kombinatsiyalari
    "larni", "larga", "lardan", "larda", "larning",
    "larim", "laring", "lari",
    "larimni", "laringni", "larini",
]

# Uzunlikka ko'ra kamayish tartibida (uzun qo'shimcha avval tekshirilsin)
UZ_SUFFIXES = sorted(set(UZ_SUFFIXES), key=len, reverse=True)

# ─────────────────────────────────────────────────────────
#  Minimal so'z uzunligi lemmatizatsiyadan keyin
# ─────────────────────────────────────────────────────────
MIN_ROOT_LEN = 2


# ─────────────────────────────────────────────────────────
#  4-bosqich: Tokenizatsiya (kengaytirilgan)
#  Oldingi oddiy split()dan farqi:
#    - Gaplarni aniqlaydi va saqlab qo'yadi
#    - Har bir token uchun gap raqamini beradi
#    - Apostrof ichidagi so'zlarni butun saqlaydi
# ─────────────────────────────────────────────────────────
SENT_END  = re.compile(r"(?<=[.!?])\s+")
WORD_SPLIT = re.compile(r"[\s,;:()\[\]\"«»\-]+")
PUNCT_STRIP = re.compile(r"^[.,!?;:\-]+|[.,!?;:\-]+$")


def tokenize_sentences(text: str) -> list[str]:
    """Matnni gaplarga ajratadi."""
    sents = SENT_END.split(text.strip())
    return [s.strip() for s in sents if s.strip()]


def tokenize_words(sentence: str) -> list[str]:
    """Gapni so'zlarga ajratadi, apostrof saqlangan holda."""
    tokens = []
    for raw in WORD_SPLIT.split(sentence):
        tok = PUNCT_STRIP.sub("", raw).lower()
        if len(tok) >= 2:
            tokens.append(tok)
    return tokens


def full_tokenize(text: str) -> dict:
    """
    Qaytaradi:
      {
        "sentences"      : ["gap1", "gap2", ...],
        "tokens"         : ["so'z1", "so'z2", ...],
        "token_sent_map" : [0, 0, 1, 1, ...],   # har token qaysi gap
        "sent_count"     : N,
        "token_count"    : M,
      }
    """
    sentences = tokenize_sentences(text)
    all_tokens = []
    sent_map   = []

    for i, sent in enumerate(sentences):
        words = tokenize_words(sent)
        all_tokens.extend(words)
        sent_map.extend([i] * len(words))

    return {
        "sentences"     : sentences,
        "tokens"        : all_tokens,
        "token_sent_map": sent_map,
        "sent_count"    : len(sentences),
        "token_count"   : len(all_tokens),
    }


# ─────────────────────────────────────────────────────────
#  Morfologik tahlil yordamchi: apostrof bilan so'zni bo'lish
#  Misol: "o'qimoqdalar" → ["o'qi", "moq", "da", "lar"]
#         (faqat ma'lumot uchun, lemmatizatsiyada ishlatilmaydi)
# ─────────────────────────────────────────────────────────
def morpheme_split(word: str) -> list[str]:
    """
    So'zni morfemalariga bo'ladi.
    Bu to'liq morfologik analizator emas —
    rekursiv qo'shimcha kesish orqali ishlaydi.
    """
    if len(word) <= MIN_ROOT_LEN:
        return [word]
    for suf in UZ_SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= MIN_ROOT_LEN:
            root = word[: -len(suf)]
            return morpheme_split(root) + [suf]
    return [word]


# ─────────────────────────────────────────────────────────
#  11-bosqich: Lemmatizatsiya
#  So'zning asosiy shaklini (lemmani) topadi.
#  Strategiya: qo'shimchalarni ketma-ket olib tashlash.
# ─────────────────────────────────────────────────────────
def lemmatize(word: str) -> str:
    """
    So'zdan qo'shimchalarni olib, asosiy shaklni qaytaradi.
    Misol:
      kitoblarni  → kitob
      o'qimoqdalar → o'qi   (o'q + i — fe'l asosi)
      talabalar   → talaba
    """
    lemma = word.lower()
    # Bir necha qatlam qo'shimcha kesish (maks 4 qatlam)
    for _ in range(4):
        cut = False
        for suf in UZ_SUFFIXES:
            if lemma.endswith(suf) and len(lemma) - len(suf) >= MIN_ROOT_LEN:
                lemma = lemma[: -len(suf)]
                cut = True
                break
        if not cut:
            break
    return lemma


def lemmatize_tokens(tokens: list[str]) -> list[dict]:
    """
    Har bir token uchun lug'at qaytaradi:
      [{"token": "talabalar", "lemma": "talaba", "morphemes": ["talaba","lar"]}, ...]
    """
    result = []
    for tok in tokens:
        lemma     = lemmatize(tok)
        morphemes = morpheme_split(tok)
        result.append({
            "token"    : tok,
            "lemma"    : lemma,
            "morphemes": morphemes,
            "changed"  : tok != lemma,
        })
    return result


# ─────────────────────────────────────────────────────────
#  Asosiy pipeline: tokenizatsiya + lemmatizatsiya birga
# ─────────────────────────────────────────────────────────
def nlp_pipeline(clean_text: str) -> dict:
    """
    Kirish: tozalangan matn (korpus_app.py dagi clean_text() chiqishi)
    Chiqish:
      {
        "sentences"   : [...],
        "sent_count"  : N,
        "token_count" : M,
        "tokens"      : [...],
        "lemmas"      : [...],          # token bilan parallel
        "lemma_freq"  : {lemma: count}, # lemma chastotasi
        "details"     : [{token, lemma, morphemes, changed}, ...]
      }
    """
    tok_result = full_tokenize(clean_text)
    tokens     = tok_result["tokens"]

    details    = lemmatize_tokens(tokens)
    lemmas     = [d["lemma"] for d in details]

    # Lemma chastotasi (asosiy shakl bo'yicha yig'iladi)
    from collections import Counter
    lemma_freq = dict(Counter(lemmas))

    return {
        "sentences"  : tok_result["sentences"],
        "sent_count" : tok_result["sent_count"],
        "token_count": tok_result["token_count"],
        "tokens"     : tokens,
        "lemmas"     : lemmas,
        "lemma_freq" : lemma_freq,
        "details"    : details,
    }
