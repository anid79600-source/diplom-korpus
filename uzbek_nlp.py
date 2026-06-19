"""
uzbek_nlp.py
O'zbek tili uchun tokenizatsiya va lemmatizatsiya moduli.
korpus_app.py ga tegmasdan ulash uchun alohida fayl.
"""

import re

# ─────────────────────────────────────────────────────────
#  STOP-SO'ZLAR — jadvalda chiqmasin
# ─────────────────────────────────────────────────────────
UZ_STOPWORDS = {
    # Olmoshlar
    "men", "sen", "u", "biz", "siz", "ular",
    "mening", "sening", "uning", "bizning", "sizning", "ularning",
    "menga", "senga", "unga", "bizga", "sizga", "ularga",
    "meni", "seni", "uni", "bizni", "sizni", "ularni",
    "menda", "senda", "unda", "bizda", "sizda", "ularda",
    "mendan", "sendan", "undan", "bizdan", "sizdan", "ulardan",
    "bu", "shu", "o'sha", "ana", "mana",
    "buni", "shuni", "uni",
    "bunga", "shunga", "unga",
    "bunday", "shunday", "unday",
    "kim", "nima", "qanday", "qaysi", "qachon", "qayer", "nega", "necha",
    # Bog'lovchilar
    "va", "bilan", "ham", "yoki", "lekin", "ammo", "balki",
    "chunki", "agar", "esa", "garchi", "holbuki",
    "ya'ni", "demak", "shuning", "shuningdek",
    # Ko'makchilar
    "uchun", "haqida", "kabi", "singari", "sayin",
    "qadar", "beri", "buyon", "keyin", "oldin",
    "ustida", "ostida", "ichida", "tashqarida",
    "yonida", "oldida", "orqasida", "o'rtasida",
    # Fe'l yordamchilari / bog'lamalar
    "edi", "ekan", "emish", "dir", "dir",
    "bo'ldi", "bo'lgan", "bo'lib", "bo'lsa", "bo'ladi",
    "qildi", "qilgan", "qilib", "qilsa", "qiladi", "qilish",
    "keldi", "ketdi", "oldi", "berdi",
    # Modal so'zlar
    "kerak", "mumkin", "lozim", "darkor", "shart",
    "emas", "yo'q", "bor", "hali", "endi", "faqat",
    "hech", "har", "hamma", "barcha", "hammasi",
    "juda", "eng", "ancha", "biroz", "sal",
    "doim", "hozir", "bugun", "kecha", "ertaga",
    "yana", "yana", "ham", "deb", "deydi",
    "boshqa", "yangi", "katta", "kichik",
    "bir", "ikki", "uch", "to'rt", "besh",
    # Qisqa / ma'nosiz qoldiqlar (lemmatizatsiya xatolari)
    "ldi", "lgan", "lish", "ladi", "lishi",
    "rdi", "rgan", "rish", "radi", "rati", "raman",
    "ng", "ri", "ta", "da", "ga", "ni", "dan",
    "di", "ди",
    # Inglizcha (aralash matnlar uchun)
    "the", "a", "an", "is", "are", "was", "were",
    "to", "of", "and", "in", "for", "on", "with",
    "it", "this", "that", "do", "did", "so", "not",
    # Sizning jadvaldan olingan so'zlar
    "ko", "bo", "tom", "yo", "meri", "so",
    "tomning", "yolg", "narsani", "olmayman",
    "tilida", "tilini", "ingliz",
    "olib", "sotib", "yerda", "ushbu",
    "qila", "qiladi", "qilish",
    "ladi", "ldi", "lgan", "lishi",
    "radi", "raman",
}

# ─────────────────────────────────────────────────────────
#  Token validatsiya — jadvalga kirishi uchun shart
# ─────────────────────────────────────────────────────────
def is_valid_token(word: str) -> bool:
    """
    True qaytaradi agar so'z:
    - stop-so'z emas
    - kamida 3 belgidan iborat
    - faqat raqamdan iborat emas
    - haqiqiy harf bor
    """
    if word in UZ_STOPWORDS:
        return False
    if len(word) < 3:
        return False
    if word.isdigit():
        return False
    if not re.search(r"[a-zA-Z'']", word):
        return False
    return True

# ─────────────────────────────────────────────────────────
#  O'zbek tiliga xos qo'shimchalar ro'yxati
#  (kelishik, ko'plik, egalik, fe'l qo'shimchalari)
#  Uzunroq qo'shimcha avval tekshiriladi (greedy order)
# ─────────────────────────────────────────────────────────
UZ_SUFFIXES = [
    # Ko'plik
    "lar", "lar",
    # Kelishik qo'shimchalari
    "ning", "ga", "ni", "da", "dan", "gаchа", "gacha",
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
MIN_ROOT_LEN = 4


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
def lemmatize(word: str):

    if word.endswith("moq"):
        return word

    lemma = word.lower()

    for _ in range(4):
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
        "token_count" : M,   # stop-so'zlarsiz
        "tokens"      : [...],
        "lemmas"      : [...],
        "lemma_freq"  : {lemma: count},
        "details"     : [{token, lemma, morphemes, changed}, ...]
      }
    """
    from collections import Counter

    tok_result = full_tokenize(clean_text)
    raw_tokens = tok_result["tokens"]

    # ── Stop-so'z va yaroqsiz tokenlarni filtrlash ──
    filtered = [t for t in raw_tokens if is_valid_token(t)]

    details = lemmatize_tokens(filtered)

    # Lemmatizatsiyadan chiqqan qoldiqlarni ham filtrlash
    clean_details = []
    for d in details:
        if is_valid_token(d["lemma"]) and len(d["lemma"]) >= 3:
            clean_details.append(d)

    lemmas     = [d["lemma"] for d in clean_details]
    lemma_freq = dict(Counter(lemmas))

    return {
        "sentences"  : tok_result["sentences"],
        "sent_count" : tok_result["sent_count"],
        "token_count": len(clean_details),
        "tokens"     : [d["token"] for d in clean_details],
        "lemmas"     : lemmas,
        "lemma_freq" : lemma_freq,
        "details"    : clean_details,
    }
