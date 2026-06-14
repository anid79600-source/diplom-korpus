"""
O'zbek tili matn korpusini shakllantirish dasturi
Diplom himoyasi uchun minimal ishlaydigan prototip
"""

import streamlit as st
import re
import hashlib
import json
import io
from collections import Counter
from datetime import datetime

# ─────────────────────────────────────────────
#  Sahifa sozlamalari
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="O'zbek Tili Korpusi",
    page_icon="📚",
    layout="wide",
)

# ─────────────────────────────────────────────
#  Session state — korpus saqlanib boradi
# ─────────────────────────────────────────────
if "freq"         not in st.session_state: st.session_state.freq         = {}   # {so'z: chastota}
if "total_tokens" not in st.session_state: st.session_state.total_tokens = 0
if "total_sents"  not in st.session_state: st.session_state.total_sents  = 0
if "files_log"    not in st.session_state: st.session_state.files_log    = []   # [{name, tokens, sents, new, dup, ts}]
if "seen_hashes"  not in st.session_state: st.session_state.seen_hashes  = set()
if "rejected"     not in st.session_state: st.session_state.rejected     = []

# ─────────────────────────────────────────────
#  Kirill → Lotin jadval
# ─────────────────────────────────────────────
KIRILL_LOTIN = {
    'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo',
    'ж':'j','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m',
    'н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u',
    'ф':'f','х':'x','ц':'ts','ч':'ch','ш':'sh','щ':'sh',
    'ъ':"'", 'ы':'i','ь':'','э':'e','ю':'yu','я':'ya',
    'қ':'q','ғ':"g'",'ҳ':'h','ў':"o'","
':'n',
}

def kirill_to_lotin(text: str) -> str:
    result = []
    for ch in text.lower():
        result.append(KIRILL_LOTIN.get(ch, ch))
    return "".join(result)

# ─────────────────────────────────────────────
#  Apostrof standartlashtirish
# ─────────────────────────────────────────────
APOS_VARIANTS = "ʻʼ`''′‛"

def normalize_apostrophe(text: str) -> str:
    for ch in APOS_VARIANTS:
        text = text.replace(ch, "'")
    return text

# ─────────────────────────────────────────────
#  3-bosqich: Matnni tozalash
# ─────────────────────────────────────────────
def clean_text(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw)                       # HTML teglari
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)        # URL
    text = re.sub(r"\S+@\S+\.\S+", " ", text)                 # email
    text = kirill_to_lotin(text)                               # Kirill → Lotin
    text = normalize_apostrophe(text)                          # apostrof
    text = re.sub(r"[^\w\s'.,!?;:\-]", " ", text, flags=re.UNICODE)  # maxsus belgilar
    text = re.sub(r"\s+", " ", text).strip()                  # ortiqcha bo'shliq
    return text

# ─────────────────────────────────────────────
#  4-bosqich: Tokenizatsiya
# ─────────────────────────────────────────────
SENT_SPLIT = re.compile(r"[.!?]+")
TOKEN_SPLIT = re.compile(r"[\s,;:()\[\]\"«»]+")
PUNCT_STRIP = re.compile(r"^[.,!?;:\-]+|[.,!?;:\-]+$")

def tokenize(text: str):
    sents = [s.strip() for s in SENT_SPLIT.split(text) if s.strip()]
    tokens = []
    for sent in sents:
        for raw_tok in TOKEN_SPLIT.split(sent):
            tok = PUNCT_STRIP.sub("", raw_tok).lower()
            if len(tok) >= 2:
                tokens.append(tok)
    return tokens, len(sents)

# ─────────────────────────────────────────────
#  5-bosqich: Dublikat aniqlash (xesh)
# ─────────────────────────────────────────────
def file_hash(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()

# ─────────────────────────────────────────────
#  6-bosqich: Chastotani yangilash
# ─────────────────────────────────────────────
def update_frequency(tokens: list):
    new_words = 0
    dup_words = 0
    for tok in tokens:
        if tok in st.session_state.freq:
            dup_words += 1
        else:
            new_words += 1
        st.session_state.freq[tok] = st.session_state.freq.get(tok, 0) + 1
    return new_words, dup_words

# ─────────────────────────────────────────────
#  Asosiy qayta ishlash funksiyasi
# ─────────────────────────────────────────────
def process_file(uploaded_file):
    raw_bytes = uploaded_file.read()
    h = file_hash(raw_bytes)

    # Dublikat fayl tekshiruvi
    if h in st.session_state.seen_hashes:
        st.session_state.rejected.append({
            "fayl": uploaded_file.name,
            "sabab": "Fayl dublikati (avval yuklangan)",
            "vaqt": datetime.now().strftime("%H:%M:%S"),
        })
        return False, "⚠️ Bu fayl allaqachon yuklangan (dublikat)."

    # UTF-8 o'qish
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            raw_text = raw_bytes.decode("cp1251")
        except Exception:
            st.session_state.rejected.append({
                "fayl": uploaded_file.name,
                "sabab": "Kodlash xatosi",
                "vaqt": datetime.now().strftime("%H:%M:%S"),
            })
            return False, "❌ Fayl kodlashini o'qib bo'lmadi."

    # Minimal uzunlik tekshiruvi
    if len(raw_text.split()) < 20:
        st.session_state.rejected.append({
            "fayl": uploaded_file.name,
            "sabab": "Matn juda qisqa (< 20 so'z)",
            "vaqt": datetime.now().strftime("%H:%M:%S"),
        })
        return False, "❌ Matn juda qisqa (minimal 20 so'z talab qilinadi)."

    # Pipeline
    clean   = clean_text(raw_text)
    tokens, sent_count = tokenize(clean)
    new_w, dup_w = update_frequency(tokens)

    # Statistika yangilash
    st.session_state.total_tokens += len(tokens)
    st.session_state.total_sents  += sent_count
    st.session_state.seen_hashes.add(h)

    st.session_state.files_log.append({
        "fayl"    : uploaded_file.name,
        "tokenlar": len(tokens),
        "gaplar"  : sent_count,
        "yangi"   : new_w,
        "dublikat": dup_w,
        "vaqt"    : datetime.now().strftime("%H:%M:%S"),
    })
    return True, f"✅ **{uploaded_file.name}** — {len(tokens):,} token, {new_w:,} yangi so'z qo'shildi."

# ─────────────────────────────────────────────
#  Eksport yordamchilari
# ─────────────────────────────────────────────
def export_tokens_txt() -> bytes:
    lines = ["so'z\tchastota\tulush%"]
    total = st.session_state.total_tokens or 1
    for word, cnt in sorted(st.session_state.freq.items(), key=lambda x: -x[1]):
        share = cnt / total * 100
        lines.append(f"{word}\t{cnt}\t{share:.2f}")
    return "\n".join(lines).encode("utf-8")

def export_report_txt() -> bytes:
    freq   = st.session_state.freq
    total  = st.session_state.total_tokens
    unique = len(freq)
    sents  = st.session_state.total_sents
    lines  = [
        "=" * 50,
        "O'ZBEK TILI KORPUSI — STATISTIKA HISOBOTI",
        "=" * 50,
        f"Sana: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"Jami tokenlar        : {total:,}",
        f"Noyob so'zlar        : {unique:,}",
        f"Noyob so'zlar ulushi : {unique/total*100:.1f}%" if total else "Noyob so'zlar ulushi : —",
        f"Jami gaplar          : {sents:,}",
        f"O'rtacha gap uzunligi: {total/sents:.1f} so'z" if sents else "O'rtacha gap uzunligi: —",
        f"Yuklangan fayllar    : {len(st.session_state.files_log)}",
        f"Rad etilgan fayllar  : {len(st.session_state.rejected)}",
        "",
        "ENG KO'P ISHLATILADIGAN 20 SO'Z:",
        "-" * 30,
    ]
    top20 = sorted(freq.items(), key=lambda x: -x[1])[:20]
    for i, (w, c) in enumerate(top20, 1):
        lines.append(f"  {i:2}. {w:<20} {c:>6}")
    return "\n".join(lines).encode("utf-8")

def export_corpus_json() -> bytes:
    data = {
        "meta": {
            "jami_token" : st.session_state.total_tokens,
            "noyob_soz"  : len(st.session_state.freq),
            "jami_gap"   : st.session_state.total_sents,
            "fayllar"    : st.session_state.files_log,
        },
        "freq": st.session_state.freq,
    }
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

# ═══════════════════════════════════════════════
#  UI
# ═══════════════════════════════════════════════

st.markdown("""
<h2 style='margin-bottom:2px'>📚 O'zbek Tili Matn Korpusi</h2>
<p style='color:gray;font-size:14px;margin-top:0'>
  Matn korpusini shakllantirish tizimi — diplom himoyasi prototipi
</p>
""", unsafe_allow_html=True)

st.divider()

# ───────── SIDEBAR ─────────
with st.sidebar:
    st.subheader("📁 Fayl yuklash")
    uploaded = st.file_uploader(
        "TXT fayllarni tanlang",
        type=["txt"],
        accept_multiple_files=True,
        help="Bir nechta faylni bir vaqtda tanlash mumkin (Ctrl+Click)",
    )

    if uploaded:
        for f in uploaded:
            already = any(log["fayl"] == f.name for log in st.session_state.files_log)
            if not already:
                ok, msg = process_file(f)
                if ok:
                    st.success(msg)
                else:
                    st.warning(msg)

    st.divider()

    # Fayl logi
    if st.session_state.files_log:
        st.subheader("✅ Qabul qilingan")
        for log in st.session_state.files_log:
            st.markdown(
                f"**{log['fayl']}**  \n"
                f"🕐 {log['vaqt']} · {log['tokenlar']:,} token · {log['yangi']:,} yangi"
            )
        st.divider()

    if st.session_state.rejected:
        st.subheader("❌ Rad etilgan")
        for r in st.session_state.rejected:
            st.markdown(f"~~{r['fayl']}~~  \n_{r['sabab']}_")
        st.divider()

    # Korpusni tozalash
    if st.button("🗑️ Korpusni tozalash", use_container_width=True):
        for key in ["freq","total_tokens","total_sents",
                    "files_log","seen_hashes","rejected"]:
            del st.session_state[key]
        st.rerun()

# ───────── ASOSIY SAHIFA ─────────
freq   = st.session_state.freq
total  = st.session_state.total_tokens
unique = len(freq)
sents  = st.session_state.total_sents

# 7-bosqich: Statistika ko'rsatish
col1, col2, col3, col4 = st.columns(4)
col1.metric("🔢 Jami tokenlar",    f"{total:,}")
col2.metric("🔤 Noyob so'zlar",    f"{unique:,}")
col3.metric("📊 Noyob ulushi",     f"{unique/total*100:.1f}%" if total else "—")
col4.metric("📝 Gaplar soni",      f"{sents:,}")

if st.session_state.files_log:
    col5, col6, col7, col8 = st.columns(4)
    col5.metric("📁 Yuklangan fayllar",  len(st.session_state.files_log))
    col6.metric("❌ Rad etilgan",         len(st.session_state.rejected))
    avg_len = f"{total/sents:.1f}" if sents else "—"
    col7.metric("📏 O'rtacha gap",        f"{avg_len} so'z")
    col8.metric("🏆 Eng ko'p so'z",
        sorted(freq.items(), key=lambda x: -x[1])[0][0] if freq else "—")

st.divider()

# ─── Tablar ───
tab1, tab2, tab3 = st.tabs(["📋 Tokenlar jadvali", "📈 Hisobot", "💾 Eksport"])

# TAB 1: Jadval
with tab1:
    if not freq:
        st.info("Hali fayl yuklanmagan. Chap paneldan TXT fayl tanlang.")
    else:
        # Filtrlash paneli
        fc1, fc2, fc3 = st.columns([2, 1, 1])
        search = fc1.text_input("🔍 So'z qidirish", placeholder="masalan: o'zbek")
        min_freq = fc2.number_input("Minimal chastota", min_value=1, value=1, step=1)
        sort_by  = fc3.selectbox("Tartiblash", ["Chastota ↓", "Chastota ↑", "A → Z", "Z → A"])

        # Filtr qo'llash
        rows = [(w, c, c/total*100) for w, c in freq.items()
                if c >= min_freq and (not search or search.lower() in w)]

        if sort_by == "Chastota ↓":  rows.sort(key=lambda x: -x[1])
        elif sort_by == "Chastota ↑": rows.sort(key=lambda x:  x[1])
        elif sort_by == "A → Z":      rows.sort(key=lambda x:  x[0])
        else:                          rows.sort(key=lambda x: -len(x[0]))

        st.caption(f"Jami **{len(rows):,}** so'z ko'rsatilmoqda")

        # 8-bosqich: Jadval chiqarish
        import pandas as pd
        df = pd.DataFrame(rows, columns=["So'z", "Chastota", "Ulush %"])
        df.index = df.index + 1
        df["Ulush %"] = df["Ulush %"].map("{:.2f}%".format)

        st.dataframe(
            df,
            use_container_width=True,
            height=460,
        )

# TAB 2: Hisobot
with tab2:
    if not freq:
        st.info("Hali fayl yuklanmagan.")
    else:
        st.subheader("Korpus statistikasi")
        import pandas as pd

        # Fayl logi jadvali
        if st.session_state.files_log:
            st.markdown("**Yuklangan fayllar:**")
            log_df = pd.DataFrame(st.session_state.files_log)
            log_df.columns = ["Fayl", "Tokenlar", "Gaplar",
                               "Yangi so'zlar", "Mavjud so'zlar", "Vaqt"]
            st.dataframe(log_df, use_container_width=True)

        st.markdown("---")

        # Top 20 jadval
        st.markdown("**Eng ko'p ishlatiladigan 20 ta so'z:**")
        top20 = sorted(freq.items(), key=lambda x: -x[1])[:20]
        top_df = pd.DataFrame(top20, columns=["So'z", "Chastota"])
        top_df["Ulush %"] = top_df["Chastota"].apply(
            lambda c: f"{c/total*100:.2f}%")
        top_df.index = top_df.index + 1
        st.dataframe(top_df, use_container_width=True)

        # Chiqish grafikasi
        st.markdown("**Chastota taqsimoti (Top 15):**")
        top15_df = pd.DataFrame(top20[:15], columns=["So'z", "Chastota"])
        top15_df = top15_df.set_index("So'z")
        st.bar_chart(top15_df)

# TAB 3: Eksport
with tab3:
    if not freq:
        st.info("Hali fayl yuklanmagan.")
    else:
        st.subheader("💾 Natijalarni yuklash")

        ec1, ec2, ec3 = st.columns(3)

        with ec1:
            st.markdown("**Token ro'yxati (TXT)**")
            st.caption("So'z + chastota + ulush foiz")
            st.download_button(
                label="⬇️ tokenlar.txt",
                data=export_tokens_txt(),
                file_name="tokenlar.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with ec2:
            st.markdown("**Statistika hisoboti (TXT)**")
            st.caption("Umumiy ko'rsatkichlar")
            st.download_button(
                label="⬇️ hisobot.txt",
                data=export_report_txt(),
                file_name="hisobot.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with ec3:
            st.markdown("**To'liq korpus (JSON)**")
            st.caption("Barcha meta-ma'lumot bilan")
            st.download_button(
                label="⬇️ korpus.json",
                data=export_corpus_json(),
                file_name="korpus.json",
                mime="application/json",
                use_container_width=True,
            )

        st.divider()
        st.markdown("**Hisobot ko'rinishi:**")
        st.code(export_report_txt().decode("utf-8"), language="text")
