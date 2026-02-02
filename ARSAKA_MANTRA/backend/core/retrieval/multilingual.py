"""
Multilingual Support for MANTRA Retrieval

Supports top 15 most spoken languages:
1. English (en)
2. Mandarin Chinese (zh)
3. Hindi (hi)
4. Spanish (es)
5. French (fr)
6. Arabic (ar)
7. Bengali (bn)
8. Portuguese (pt)
9. Russian (ru)
10. Japanese (ja)
11. German (de)
12. Indonesian (id)
13. Korean (ko)
14. Turkish (tr)
15. Vietnamese (vi)

Usage:
    from core.retrieval.multilingual import MultilingualSupport

    ml = MultilingualSupport()

    # Detect language
    lang = ml.detect_language("database design")  # "en"
    lang = ml.detect_language("desain basis data")  # "id"

    # Get intent patterns for detected language
    patterns = ml.get_intent_patterns("REVIEW", "id")

    # Expand query with multilingual synonyms
    expanded = ml.expand_multilingual("authentication", source_lang="en")
"""

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
import re


@dataclass
class LanguageConfig:
    """Configuration for a language."""
    code: str
    name: str
    native_name: str
    stopwords: Set[str]
    intent_patterns: Dict[str, List[str]]
    tech_synonyms: Dict[str, List[str]]
    domain_terms: Dict[str, List[str]]


# ============================================================================
# STOPWORDS PER LANGUAGE
# ============================================================================

STOPWORDS: Dict[str, Set[str]] = {
    "en": {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "to", "of",
        "in", "for", "on", "with", "at", "by", "from", "as", "into", "through",
        "during", "before", "after", "above", "below", "between", "under",
        "again", "further", "then", "once", "here", "there", "when", "where",
        "why", "how", "all", "each", "few", "more", "most", "other", "some",
        "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
        "very", "just", "also", "now", "and", "or", "but", "if", "this", "that",
        "these", "those", "i", "me", "my", "we", "our", "you", "your", "he",
        "him", "his", "she", "her", "it", "its", "they", "them", "their",
    },
    "zh": {
        "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一",
        "个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有",
        "看", "好", "自己", "这", "那", "里", "后", "多", "什么", "能", "让",
        "可以", "如果", "但是", "因为", "所以", "还", "被", "把", "他", "她",
    },
    "hi": {
        "का", "के", "की", "है", "में", "को", "से", "पर", "और", "एक", "यह",
        "हो", "था", "थी", "थे", "हैं", "इस", "कि", "जो", "तो", "ने", "भी",
        "लिए", "कर", "या", "हुए", "साथ", "वह", "अपने", "बाद", "कुछ", "सकते",
        "होता", "जब", "तक", "होती", "अब", "जाता", "करने", "दो", "बहुत",
    },
    "es": {
        "el", "la", "de", "que", "y", "a", "en", "un", "ser", "se", "no",
        "haber", "por", "con", "su", "para", "como", "estar", "tener", "le",
        "lo", "todo", "pero", "más", "hacer", "o", "poder", "decir", "este",
        "ir", "otro", "ese", "si", "me", "ya", "ver", "porque", "dar", "cuando",
        "muy", "sin", "sobre", "también", "uno", "hasta", "desde", "nos",
    },
    "fr": {
        "le", "la", "de", "et", "est", "en", "un", "une", "que", "les", "du",
        "des", "pour", "dans", "ce", "pas", "qui", "sur", "se", "par", "plus",
        "ou", "son", "ne", "avec", "tout", "faire", "mais", "nous", "comme",
        "être", "aux", "aussi", "cette", "entre", "sous", "même", "elle", "ont",
    },
    "ar": {
        "في", "من", "على", "إلى", "أن", "هذا", "هذه", "التي", "الذي", "كان",
        "لا", "ما", "مع", "عن", "هو", "هي", "قد", "كل", "بين", "عند", "لم",
        "حتى", "إذا", "ثم", "أو", "بعد", "تلك", "ذلك", "أي", "فقط", "كانت",
        "أكثر", "هناك", "نحن", "أنت", "أنا", "لك", "له", "لها", "منذ",
    },
    "bn": {
        "এই", "একটি", "ও", "এবং", "করা", "হয়", "তার", "থেকে", "কিন্তু",
        "যে", "না", "আমি", "তুমি", "সে", "আমরা", "তারা", "এটা", "এর", "জন্য",
        "হতে", "আছে", "করে", "দিয়ে", "নয়", "হবে", "যদি", "তাহলে", "আর",
    },
    "pt": {
        "o", "a", "de", "que", "e", "do", "da", "em", "um", "para", "é", "com",
        "não", "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como",
        "mas", "foi", "ao", "ele", "das", "tem", "à", "seu", "sua", "ou", "ser",
        "quando", "muito", "há", "nos", "já", "está", "eu", "também", "só",
    },
    "ru": {
        "и", "в", "не", "на", "я", "что", "он", "с", "это", "как", "а", "то",
        "все", "она", "так", "его", "но", "да", "ты", "к", "у", "же", "вы",
        "за", "бы", "по", "только", "её", "мне", "было", "вот", "от", "меня",
        "еще", "нет", "о", "из", "ему", "теперь", "когда", "даже", "ну", "вдруг",
    },
    "ja": {
        "の", "に", "は", "を", "た", "が", "で", "て", "と", "し", "れ", "さ",
        "ある", "いる", "も", "する", "から", "な", "こと", "として", "い", "や",
        "など", "なっ", "ない", "この", "ため", "その", "あっ", "よう", "また",
        "もの", "という", "あり", "まで", "られ", "なる", "へ", "か", "だ",
    },
    "de": {
        "der", "die", "und", "in", "den", "von", "zu", "das", "mit", "sich",
        "des", "auf", "für", "ist", "im", "dem", "nicht", "ein", "eine", "als",
        "auch", "es", "an", "werden", "aus", "er", "hat", "dass", "sie", "nach",
        "wird", "bei", "einer", "um", "am", "sind", "noch", "wie", "einem", "über",
    },
    "id": {
        "yang", "dan", "di", "dari", "ini", "untuk", "dengan", "adalah", "ke",
        "pada", "tidak", "itu", "dalam", "akan", "oleh", "juga", "atau", "ada",
        "saya", "aku", "kamu", "dia", "kami", "kita", "mereka", "bisa", "sudah",
        "telah", "belum", "harus", "dapat", "tersebut", "sebagai", "bahwa",
        "seperti", "jika", "maka", "tetapi", "namun", "karena", "sehingga",
    },
    "ko": {
        "이", "그", "저", "것", "수", "등", "들", "및", "에", "의", "가", "을",
        "를", "으로", "는", "은", "도", "와", "과", "하다", "있다", "되다",
        "이다", "않다", "없다", "같다", "보다", "위하다", "대하다", "통하다",
    },
    "tr": {
        "bir", "bu", "ve", "için", "de", "da", "ile", "mi", "mı", "ne", "var",
        "olan", "gibi", "daha", "çok", "en", "kadar", "sonra", "önce", "o",
        "şu", "ancak", "ama", "fakat", "hem", "ya", "veya", "ki", "çünkü",
    },
    "vi": {
        "và", "của", "là", "có", "được", "trong", "cho", "này", "với", "không",
        "những", "một", "đã", "để", "các", "từ", "hay", "như", "khi", "về",
        "đến", "ra", "người", "nào", "còn", "thì", "mà", "sẽ", "bị", "làm",
    },
}


# ============================================================================
# INTENT PATTERNS PER LANGUAGE
# ============================================================================

INTENT_PATTERNS: Dict[str, Dict[str, List[str]]] = {
    # English patterns
    "en": {
        "LIST": [
            r"\blist\b", r"\bshow\s+all\b", r"\benumerate\b",
            r"\bwhat\s+decisions\b", r"\bavailable\b", r"\bbrowse\b",
        ],
        "ENFORCE": [
            r"\bcreate\b", r"\bbuild\b", r"\bimplement\b", r"\bwrite\b",
            r"\bdevelop\b", r"\badd\b", r"\bmake\b",
        ],
        "UNDERSTAND": [
            r"\bwhy\b", r"\bexplain\b", r"\breason\b", r"\bbackground\b",
            r"\bwhat\s+is\s+the\s+reason\b", r"\brationale\b",
        ],
        "REVIEW": [
            r"\breview\b", r"\bcheck\b", r"\bvalidate\b", r"\baudit\b",
            r"\binspect\b", r"\bverify\b", r"\bevaluate\b",
        ],
        "EXPLORE": [
            r"\bhow\b", r"\bwhat\s+about\b", r"\btell\s+me\s+about\b",
            r"\blearn\b", r"\bunderstand\b",
        ],
        "FULL": [
            r"\bfull\b", r"\bdetail\b", r"\bcomplete\b", r"\bcomprehensive\b",
            r"\ball\s+fields\b", r"\beverything\b",
        ],
        "PRD_EXPORT": [
            r"\bexport\b", r"\bdocument\b", r"\bdocumentation\b",
            r"\bprd\b", r"\bspec\b", r"\breport\b", r"\bmarkdown\b",
        ],
    },

    # Mandarin Chinese patterns
    "zh": {
        "LIST": [
            r"列出", r"显示所有", r"查看列表", r"有哪些", r"什么决策",
        ],
        "ENFORCE": [
            r"创建", r"构建", r"实现", r"编写", r"开发", r"添加", r"制作",
        ],
        "UNDERSTAND": [
            r"为什么", r"解释", r"原因", r"背景", r"理由",
        ],
        "REVIEW": [
            r"审查", r"检查", r"验证", r"审核", r"评估", r"核实",
        ],
        "EXPLORE": [
            r"如何", r"怎么", r"关于", r"告诉我", r"了解",
        ],
        "FULL": [
            r"完整", r"详细", r"全部", r"所有字段", r"所有内容",
        ],
        "PRD_EXPORT": [
            r"导出", r"文档", r"文档化", r"规格", r"报告",
        ],
    },

    # Hindi patterns
    "hi": {
        "LIST": [
            r"सूची", r"दिखाओ", r"क्या\s+निर्णय", r"उपलब्ध",
        ],
        "ENFORCE": [
            r"बनाओ", r"निर्माण", r"लागू", r"लिखो", r"विकसित", r"जोड़ो",
        ],
        "UNDERSTAND": [
            r"क्यों", r"समझाओ", r"कारण", r"पृष्ठभूमि",
        ],
        "REVIEW": [
            r"समीक्षा", r"जांच", r"सत्यापित", r"ऑडिट", r"मूल्यांकन",
        ],
        "EXPLORE": [
            r"कैसे", r"के\s+बारे\s+में", r"बताओ", r"सीखो",
        ],
        "FULL": [
            r"पूर्ण", r"विस्तृत", r"संपूर्ण", r"सब\s+कुछ",
        ],
        "PRD_EXPORT": [
            r"निर्यात", r"दस्तावेज़", r"रिपोर्ट", r"विनिर्देश",
        ],
    },

    # Spanish patterns
    "es": {
        "LIST": [
            r"\blistar\b", r"\bmostrar\s+todo\b", r"\bqué\s+decisiones\b",
            r"\bdisponibles\b", r"\bnavegar\b",
        ],
        "ENFORCE": [
            r"\bcrear\b", r"\bconstruir\b", r"\bimplementar\b", r"\bescribir\b",
            r"\bdesarrollar\b", r"\bañadir\b", r"\bhacer\b",
        ],
        "UNDERSTAND": [
            r"\bpor\s+qué\b", r"\bexplicar\b", r"\brazón\b", r"\bfondo\b",
        ],
        "REVIEW": [
            r"\brevisar\b", r"\bcomprobar\b", r"\bvalidar\b", r"\bauditar\b",
            r"\binspeccionar\b", r"\bverificar\b", r"\bevaluar\b",
        ],
        "EXPLORE": [
            r"\bcómo\b", r"\bqué\s+tal\b", r"\bcuéntame\b", r"\baprender\b",
        ],
        "FULL": [
            r"\bcompleto\b", r"\bdetalle\b", r"\btodo\b", r"\bcomprehensivo\b",
        ],
        "PRD_EXPORT": [
            r"\bexportar\b", r"\bdocumento\b", r"\bdocumentación\b",
            r"\bespecificación\b", r"\binforme\b",
        ],
    },

    # French patterns
    "fr": {
        "LIST": [
            r"\blister\b", r"\bafficher\s+tout\b", r"\bquelles\s+décisions\b",
            r"\bdisponibles\b", r"\bparcourir\b",
        ],
        "ENFORCE": [
            r"\bcréer\b", r"\bconstruire\b", r"\bimplémenter\b", r"\bécrire\b",
            r"\bdévelopper\b", r"\bajouter\b", r"\bfaire\b",
        ],
        "UNDERSTAND": [
            r"\bpourquoi\b", r"\bexpliquer\b", r"\braison\b", r"\bcontexte\b",
        ],
        "REVIEW": [
            r"\bexaminer\b", r"\bvérifier\b", r"\bvalider\b", r"\bauditer\b",
            r"\binspecter\b", r"\bévaluer\b",
        ],
        "EXPLORE": [
            r"\bcomment\b", r"\bqu'en\s+est-il\b", r"\bparlez-moi\b", r"\bapprendre\b",
        ],
        "FULL": [
            r"\bcomplet\b", r"\bdétail\b", r"\btout\b", r"\bexhaustif\b",
        ],
        "PRD_EXPORT": [
            r"\bexporter\b", r"\bdocument\b", r"\bdocumentation\b",
            r"\bspécification\b", r"\brapport\b",
        ],
    },

    # Arabic patterns
    "ar": {
        "LIST": [
            r"قائمة", r"عرض\s+الكل", r"ما\s+القرارات", r"متاح",
        ],
        "ENFORCE": [
            r"إنشاء", r"بناء", r"تنفيذ", r"كتابة", r"تطوير", r"إضافة",
        ],
        "UNDERSTAND": [
            r"لماذا", r"اشرح", r"السبب", r"الخلفية",
        ],
        "REVIEW": [
            r"مراجعة", r"تحقق", r"تحقق\s+من", r"تدقيق", r"فحص", r"تقييم",
        ],
        "EXPLORE": [
            r"كيف", r"ماذا\s+عن", r"أخبرني", r"تعلم",
        ],
        "FULL": [
            r"كامل", r"تفصيلي", r"شامل", r"كل\s+شيء",
        ],
        "PRD_EXPORT": [
            r"تصدير", r"وثيقة", r"توثيق", r"مواصفات", r"تقرير",
        ],
    },

    # Portuguese patterns
    "pt": {
        "LIST": [
            r"\blistar\b", r"\bmostrar\s+tudo\b", r"\bquais\s+decisões\b",
            r"\bdisponíveis\b", r"\bnavegar\b",
        ],
        "ENFORCE": [
            r"\bcriar\b", r"\bconstruir\b", r"\bimplementar\b", r"\bescrever\b",
            r"\bdesenvolver\b", r"\badicionar\b", r"\bfazer\b",
        ],
        "UNDERSTAND": [
            r"\bpor\s+que\b", r"\bexplicar\b", r"\brazão\b", r"\bcontexto\b",
        ],
        "REVIEW": [
            r"\brevisar\b", r"\bverificar\b", r"\bvalidar\b", r"\bauditar\b",
            r"\binspecionar\b", r"\bavaliar\b",
        ],
        "EXPLORE": [
            r"\bcomo\b", r"\be\s+sobre\b", r"\bme\s+conte\b", r"\baprender\b",
        ],
        "FULL": [
            r"\bcompleto\b", r"\bdetalhe\b", r"\btudo\b", r"\babrangente\b",
        ],
        "PRD_EXPORT": [
            r"\bexportar\b", r"\bdocumento\b", r"\bdocumentação\b",
            r"\bespecificação\b", r"\brelatório\b",
        ],
    },

    # Russian patterns
    "ru": {
        "LIST": [
            r"список", r"показать\s+все", r"какие\s+решения", r"доступные",
        ],
        "ENFORCE": [
            r"создать", r"построить", r"реализовать", r"написать",
            r"разработать", r"добавить", r"сделать",
        ],
        "UNDERSTAND": [
            r"почему", r"объясни", r"причина", r"контекст",
        ],
        "REVIEW": [
            r"проверить", r"валидировать", r"аудит", r"инспектировать",
            r"оценить", r"ревью",
        ],
        "EXPLORE": [
            r"как", r"что\s+насчет", r"расскажи", r"узнать",
        ],
        "FULL": [
            r"полный", r"подробный", r"все", r"исчерпывающий",
        ],
        "PRD_EXPORT": [
            r"экспорт", r"документ", r"документация", r"спецификация", r"отчет",
        ],
    },

    # Japanese patterns
    "ja": {
        "LIST": [
            r"リスト", r"一覧", r"表示", r"どの決定", r"利用可能",
        ],
        "ENFORCE": [
            r"作成", r"構築", r"実装", r"書く", r"開発", r"追加", r"作る",
        ],
        "UNDERSTAND": [
            r"なぜ", r"説明", r"理由", r"背景",
        ],
        "REVIEW": [
            r"レビュー", r"確認", r"検証", r"監査", r"検査", r"評価",
        ],
        "EXPLORE": [
            r"どうやって", r"について", r"教えて", r"学ぶ",
        ],
        "FULL": [
            r"完全", r"詳細", r"すべて", r"包括的",
        ],
        "PRD_EXPORT": [
            r"エクスポート", r"文書", r"ドキュメント", r"仕様", r"レポート",
        ],
    },

    # German patterns
    "de": {
        "LIST": [
            r"\bliste\b", r"\bzeige\s+alle\b", r"\bwelche\s+entscheidungen\b",
            r"\bverfügbar\b", r"\bdurchsuchen\b",
        ],
        "ENFORCE": [
            r"\berstellen\b", r"\bbauen\b", r"\bimplementieren\b", r"\bschreiben\b",
            r"\bentwickeln\b", r"\bhinzufügen\b", r"\bmachen\b",
        ],
        "UNDERSTAND": [
            r"\bwarum\b", r"\berklären\b", r"\bgrund\b", r"\bhintergrund\b",
        ],
        "REVIEW": [
            r"\büberprüfen\b", r"\bvalidieren\b", r"\bauditieren\b",
            r"\binspizieren\b", r"\bbewerten\b", r"\bprüfen\b",
        ],
        "EXPLORE": [
            r"\bwie\b", r"\bwas\s+ist\s+mit\b", r"\berzähl\s+mir\b", r"\blernen\b",
        ],
        "FULL": [
            r"\bvollständig\b", r"\bdetail\b", r"\balles\b", r"\bumfassend\b",
        ],
        "PRD_EXPORT": [
            r"\bexportieren\b", r"\bdokument\b", r"\bdokumentation\b",
            r"\bspezifikation\b", r"\bbericht\b",
        ],
    },

    # Indonesian patterns
    "id": {
        "LIST": [
            r"\blist\b", r"\bdaftar\b", r"\btampilkan\s+semua\b",
            r"\bapa\s+saja\b", r"\bsebutkan\b", r"\btersedia\b",
        ],
        "ENFORCE": [
            r"\bbuat\b", r"\bbikin\b", r"\bcreate\b", r"\bbangun\b",
            r"\bimplementasi\b", r"\btulis\b", r"\bkembangkan\b", r"\btambah\b",
        ],
        "UNDERSTAND": [
            r"\bkenapa\b", r"\bmengapa\b", r"\bjelaskan\b", r"\balasan\b",
            r"\bdasar\b", r"\blatar\s+belakang\b",
        ],
        "REVIEW": [
            r"\breview\b", r"\bcek\b", r"\bperiksa\b", r"\bvalidasi\b",
            r"\baudit\b", r"\bevaluasi\b", r"\bverifikasi\b",
        ],
        "EXPLORE": [
            r"\bbagaimana\b", r"\bgimana\b", r"\btentang\b", r"\bceritakan\b",
            r"\bpelajari\b",
        ],
        "FULL": [
            r"\blengkap\b", r"\bdetail\b", r"\bsemua\b", r"\bseluruhnya\b",
            r"\bmenyeluruh\b",
        ],
        "PRD_EXPORT": [
            r"\bekspor\b", r"\bdokumen\b", r"\bdokumentasi\b",
            r"\bspesifikasi\b", r"\blaporan\b",
        ],
    },

    # Korean patterns
    "ko": {
        "LIST": [
            r"목록", r"리스트", r"모두\s+표시", r"어떤\s+결정", r"사용\s+가능",
        ],
        "ENFORCE": [
            r"만들다", r"생성", r"구축", r"구현", r"작성", r"개발", r"추가",
        ],
        "UNDERSTAND": [
            r"왜", r"설명", r"이유", r"배경",
        ],
        "REVIEW": [
            r"검토", r"확인", r"검증", r"감사", r"검사", r"평가",
        ],
        "EXPLORE": [
            r"어떻게", r"에\s+대해", r"알려줘", r"배우다",
        ],
        "FULL": [
            r"전체", r"상세", r"모두", r"포괄적",
        ],
        "PRD_EXPORT": [
            r"내보내기", r"문서", r"문서화", r"사양", r"보고서",
        ],
    },

    # Turkish patterns
    "tr": {
        "LIST": [
            r"\blistele\b", r"\btümünü\s+göster\b", r"\bhangi\s+kararlar\b",
            r"\bmevcut\b", r"\bgözat\b",
        ],
        "ENFORCE": [
            r"\boluştur\b", r"\binşa\s+et\b", r"\buygula\b", r"\byaz\b",
            r"\bgeliştir\b", r"\bekle\b", r"\byap\b",
        ],
        "UNDERSTAND": [
            r"\bneden\b", r"\baçıkla\b", r"\bsebep\b", r"\barka\s+plan\b",
        ],
        "REVIEW": [
            r"\bincele\b", r"\bkontrol\s+et\b", r"\bdoğrula\b", r"\bdenetle\b",
            r"\bteftiş\s+et\b", r"\bdeğerlendir\b",
        ],
        "EXPLORE": [
            r"\bnasıl\b", r"\bhakkında\b", r"\banlat\b", r"\böğren\b",
        ],
        "FULL": [
            r"\btam\b", r"\bdetay\b", r"\bhepsi\b", r"\bkapsamlı\b",
        ],
        "PRD_EXPORT": [
            r"\bdışa\s+aktar\b", r"\bbelge\b", r"\bdokümantasyon\b",
            r"\bspesifikasyon\b", r"\brapor\b",
        ],
    },

    # Vietnamese patterns
    "vi": {
        "LIST": [
            r"danh\s+sách", r"liệt\s+kê", r"hiển\s+thị\s+tất\s+cả",
            r"quyết\s+định\s+nào", r"có\s+sẵn",
        ],
        "ENFORCE": [
            r"tạo", r"xây\s+dựng", r"thực\s+hiện", r"viết", r"phát\s+triển",
            r"thêm", r"làm",
        ],
        "UNDERSTAND": [
            r"tại\s+sao", r"giải\s+thích", r"lý\s+do", r"bối\s+cảnh",
        ],
        "REVIEW": [
            r"xem\s+xét", r"kiểm\s+tra", r"xác\s+nhận", r"kiểm\s+toán",
            r"đánh\s+giá",
        ],
        "EXPLORE": [
            r"làm\s+thế\s+nào", r"về", r"cho\s+tôi\s+biết", r"học",
        ],
        "FULL": [
            r"đầy\s+đủ", r"chi\s+tiết", r"tất\s+cả", r"toàn\s+diện",
        ],
        "PRD_EXPORT": [
            r"xuất", r"tài\s+liệu", r"tài\s+liệu\s+hóa", r"đặc\s+tả", r"báo\s+cáo",
        ],
    },

    # Bengali patterns
    "bn": {
        "LIST": [
            r"তালিকা", r"সব\s+দেখাও", r"কি\s+সিদ্ধান্ত", r"উপলব্ধ",
        ],
        "ENFORCE": [
            r"তৈরি", r"নির্মাণ", r"বাস্তবায়ন", r"লেখ", r"উন্নয়ন", r"যোগ",
        ],
        "UNDERSTAND": [
            r"কেন", r"ব্যাখ্যা", r"কারণ", r"পটভূমি",
        ],
        "REVIEW": [
            r"পর্যালোচনা", r"পরীক্ষা", r"যাচাই", r"নিরীক্ষা", r"মূল্যায়ন",
        ],
        "EXPLORE": [
            r"কিভাবে", r"সম্পর্কে", r"বলো", r"শিখ",
        ],
        "FULL": [
            r"সম্পূর্ণ", r"বিস্তারিত", r"সব", r"ব্যাপক",
        ],
        "PRD_EXPORT": [
            r"রপ্তানি", r"নথি", r"ডকুমেন্টেশন", r"স্পেসিফিকেশন", r"রিপোর্ট",
        ],
    },
}


# ============================================================================
# TECHNICAL SYNONYMS PER LANGUAGE
# ============================================================================

TECH_SYNONYMS: Dict[str, Dict[str, List[str]]] = {
    "en": {
        "database": ["db", "data store", "persistence", "PostgreSQL", "schema"],
        "api": ["endpoint", "REST", "interface", "route", "HTTP"],
        "auth": ["authentication", "authorization", "login", "security"],
        "component": ["UI element", "widget", "React component", "view"],
        "service": ["business logic", "use case", "domain service"],
        "test": ["testing", "unit test", "integration test", "spec"],
    },
    "zh": {
        "数据库": ["DB", "数据存储", "持久化", "PostgreSQL", "模式"],
        "接口": ["API", "端点", "REST", "路由", "HTTP"],
        "认证": ["身份验证", "授权", "登录", "安全"],
        "组件": ["UI元素", "控件", "React组件", "视图"],
        "服务": ["业务逻辑", "用例", "领域服务"],
        "测试": ["单元测试", "集成测试", "测试用例"],
    },
    "es": {
        "base de datos": ["BD", "almacén de datos", "persistencia", "PostgreSQL"],
        "api": ["punto final", "REST", "interfaz", "ruta", "HTTP"],
        "autenticación": ["autorización", "inicio de sesión", "seguridad"],
        "componente": ["elemento UI", "widget", "componente React", "vista"],
        "servicio": ["lógica de negocio", "caso de uso", "servicio de dominio"],
        "prueba": ["test", "prueba unitaria", "prueba de integración"],
    },
    "id": {
        "database": ["basis data", "db", "penyimpanan data", "PostgreSQL", "skema"],
        "api": ["endpoint", "REST", "antarmuka", "rute", "HTTP"],
        "autentikasi": ["auth", "otorisasi", "login", "keamanan"],
        "komponen": ["elemen UI", "widget", "komponen React", "tampilan"],
        "layanan": ["service", "logika bisnis", "use case"],
        "pengujian": ["test", "unit test", "integrasi test"],
    },
    "ja": {
        "データベース": ["DB", "データストア", "永続化", "PostgreSQL", "スキーマ"],
        "API": ["エンドポイント", "REST", "インターフェース", "ルート"],
        "認証": ["認可", "ログイン", "セキュリティ"],
        "コンポーネント": ["UI要素", "ウィジェット", "Reactコンポーネント", "ビュー"],
        "サービス": ["ビジネスロジック", "ユースケース", "ドメインサービス"],
        "テスト": ["単体テスト", "結合テスト", "テストケース"],
    },
    "de": {
        "datenbank": ["DB", "Datenspeicher", "Persistenz", "PostgreSQL", "Schema"],
        "api": ["Endpunkt", "REST", "Schnittstelle", "Route", "HTTP"],
        "authentifizierung": ["Autorisierung", "Anmeldung", "Sicherheit"],
        "komponente": ["UI-Element", "Widget", "React-Komponente", "Ansicht"],
        "dienst": ["Geschäftslogik", "Anwendungsfall", "Domänendienst"],
        "test": ["Einheitentest", "Integrationstest", "Testfall"],
    },
    "fr": {
        "base de données": ["BD", "stockage de données", "persistance", "PostgreSQL"],
        "api": ["point de terminaison", "REST", "interface", "route", "HTTP"],
        "authentification": ["autorisation", "connexion", "sécurité"],
        "composant": ["élément UI", "widget", "composant React", "vue"],
        "service": ["logique métier", "cas d'utilisation", "service de domaine"],
        "test": ["test unitaire", "test d'intégration", "cas de test"],
    },
    "pt": {
        "banco de dados": ["BD", "armazenamento de dados", "persistência", "PostgreSQL"],
        "api": ["endpoint", "REST", "interface", "rota", "HTTP"],
        "autenticação": ["autorização", "login", "segurança"],
        "componente": ["elemento UI", "widget", "componente React", "view"],
        "serviço": ["lógica de negócio", "caso de uso", "serviço de domínio"],
        "teste": ["teste unitário", "teste de integração", "caso de teste"],
    },
    "ru": {
        "база данных": ["БД", "хранилище данных", "персистентность", "PostgreSQL"],
        "api": ["конечная точка", "REST", "интерфейс", "маршрут", "HTTP"],
        "аутентификация": ["авторизация", "вход", "безопасность"],
        "компонент": ["UI элемент", "виджет", "React компонент", "представление"],
        "сервис": ["бизнес-логика", "вариант использования", "доменный сервис"],
        "тест": ["модульный тест", "интеграционный тест", "тестовый случай"],
    },
    "ko": {
        "데이터베이스": ["DB", "데이터 저장소", "지속성", "PostgreSQL", "스키마"],
        "API": ["엔드포인트", "REST", "인터페이스", "라우트", "HTTP"],
        "인증": ["권한 부여", "로그인", "보안"],
        "컴포넌트": ["UI 요소", "위젯", "React 컴포넌트", "뷰"],
        "서비스": ["비즈니스 로직", "유스케이스", "도메인 서비스"],
        "테스트": ["단위 테스트", "통합 테스트", "테스트 케이스"],
    },
    "ar": {
        "قاعدة البيانات": ["DB", "مخزن البيانات", "الاستمرارية", "PostgreSQL"],
        "واجهة برمجة التطبيقات": ["نقطة النهاية", "REST", "واجهة", "مسار"],
        "المصادقة": ["التفويض", "تسجيل الدخول", "الأمان"],
        "مكون": ["عنصر واجهة المستخدم", "ودجت", "مكون React", "عرض"],
        "خدمة": ["منطق الأعمال", "حالة الاستخدام", "خدمة المجال"],
        "اختبار": ["اختبار الوحدة", "اختبار التكامل", "حالة اختبار"],
    },
    "tr": {
        "veritabanı": ["DB", "veri deposu", "kalıcılık", "PostgreSQL", "şema"],
        "api": ["son nokta", "REST", "arayüz", "rota", "HTTP"],
        "kimlik doğrulama": ["yetkilendirme", "giriş", "güvenlik"],
        "bileşen": ["UI öğesi", "widget", "React bileşeni", "görünüm"],
        "hizmet": ["iş mantığı", "kullanım durumu", "alan hizmeti"],
        "test": ["birim testi", "entegrasyon testi", "test durumu"],
    },
    "vi": {
        "cơ sở dữ liệu": ["DB", "kho dữ liệu", "lưu trữ", "PostgreSQL", "lược đồ"],
        "api": ["điểm cuối", "REST", "giao diện", "route", "HTTP"],
        "xác thực": ["ủy quyền", "đăng nhập", "bảo mật"],
        "thành phần": ["phần tử UI", "widget", "React component", "view"],
        "dịch vụ": ["logic nghiệp vụ", "use case", "domain service"],
        "kiểm thử": ["unit test", "integration test", "test case"],
    },
    "hi": {
        "डेटाबेस": ["DB", "डेटा स्टोर", "स्थायित्व", "PostgreSQL", "स्कीमा"],
        "एपीआई": ["एंडपॉइंट", "REST", "इंटरफेस", "रूट", "HTTP"],
        "प्रमाणीकरण": ["प्राधिकरण", "लॉगिन", "सुरक्षा"],
        "घटक": ["UI तत्व", "विजेट", "React घटक", "दृश्य"],
        "सेवा": ["व्यापार तर्क", "उपयोग मामला", "डोमेन सेवा"],
        "परीक्षण": ["यूनिट टेस्ट", "इंटीग्रेशन टेस्ट", "टेस्ट केस"],
    },
    "bn": {
        "ডাটাবেস": ["DB", "ডেটা স্টোর", "স্থিরতা", "PostgreSQL", "স্কিমা"],
        "এপিআই": ["এন্ডপয়েন্ট", "REST", "ইন্টারফেস", "রুট", "HTTP"],
        "প্রমাণীকরণ": ["অনুমোদন", "লগইন", "নিরাপত্তা"],
        "কম্পোনেন্ট": ["UI উপাদান", "উইজেট", "React কম্পোনেন্ট", "ভিউ"],
        "সার্ভিস": ["ব্যবসায়িক যুক্তি", "ব্যবহারের ক্ষেত্রে", "ডোমেইন সার্ভিস"],
        "পরীক্ষা": ["ইউনিট টেস্ট", "ইন্টিগ্রেশন টেস্ট", "টেস্ট কেস"],
    },
}


# ============================================================================
# CROSS-LANGUAGE MAPPINGS (for translation expansion)
# ============================================================================

# Map common terms across languages
CROSS_LANGUAGE_TERMS: Dict[str, Dict[str, str]] = {
    "database": {
        "en": "database", "zh": "数据库", "hi": "डेटाबेस", "es": "base de datos",
        "fr": "base de données", "ar": "قاعدة البيانات", "pt": "banco de dados",
        "ru": "база данных", "ja": "データベース", "de": "datenbank",
        "id": "basis data", "ko": "데이터베이스", "tr": "veritabanı",
        "vi": "cơ sở dữ liệu", "bn": "ডাটাবেস",
    },
    "authentication": {
        "en": "authentication", "zh": "认证", "hi": "प्रमाणीकरण", "es": "autenticación",
        "fr": "authentification", "ar": "المصادقة", "pt": "autenticação",
        "ru": "аутентификация", "ja": "認証", "de": "authentifizierung",
        "id": "autentikasi", "ko": "인증", "tr": "kimlik doğrulama",
        "vi": "xác thực", "bn": "প্রমাণীকরণ",
    },
    "api": {
        "en": "api", "zh": "接口", "hi": "एपीआई", "es": "api",
        "fr": "api", "ar": "واجهة برمجة التطبيقات", "pt": "api",
        "ru": "api", "ja": "API", "de": "api",
        "id": "api", "ko": "API", "tr": "api",
        "vi": "api", "bn": "এপিআই",
    },
    "security": {
        "en": "security", "zh": "安全", "hi": "सुरक्षा", "es": "seguridad",
        "fr": "sécurité", "ar": "الأمان", "pt": "segurança",
        "ru": "безопасность", "ja": "セキュリティ", "de": "sicherheit",
        "id": "keamanan", "ko": "보안", "tr": "güvenlik",
        "vi": "bảo mật", "bn": "নিরাপত্তা",
    },
    "component": {
        "en": "component", "zh": "组件", "hi": "घटक", "es": "componente",
        "fr": "composant", "ar": "مكون", "pt": "componente",
        "ru": "компонент", "ja": "コンポーネント", "de": "komponente",
        "id": "komponen", "ko": "컴포넌트", "tr": "bileşen",
        "vi": "thành phần", "bn": "কম্পোনেন্ট",
    },
    "service": {
        "en": "service", "zh": "服务", "hi": "सेवा", "es": "servicio",
        "fr": "service", "ar": "خدمة", "pt": "serviço",
        "ru": "сервис", "ja": "サービス", "de": "dienst",
        "id": "layanan", "ko": "서비스", "tr": "hizmet",
        "vi": "dịch vụ", "bn": "সার্ভিস",
    },
    "test": {
        "en": "test", "zh": "测试", "hi": "परीक्षण", "es": "prueba",
        "fr": "test", "ar": "اختبار", "pt": "teste",
        "ru": "тест", "ja": "テスト", "de": "test",
        "id": "pengujian", "ko": "테스트", "tr": "test",
        "vi": "kiểm thử", "bn": "পরীক্ষা",
    },
}


# ============================================================================
# MULTILINGUAL SUPPORT CLASS
# ============================================================================

class MultilingualSupport:
    """
    Provides multilingual support for MANTRA retrieval.

    Features:
    - Language detection
    - Intent patterns in 15 languages
    - Technical synonyms in multiple languages
    - Cross-language term expansion
    """

    SUPPORTED_LANGUAGES = [
        ("en", "English", "English"),
        ("zh", "Chinese", "中文"),
        ("hi", "Hindi", "हिन्दी"),
        ("es", "Spanish", "Español"),
        ("fr", "French", "Français"),
        ("ar", "Arabic", "العربية"),
        ("bn", "Bengali", "বাংলা"),
        ("pt", "Portuguese", "Português"),
        ("ru", "Russian", "Русский"),
        ("ja", "Japanese", "日本語"),
        ("de", "German", "Deutsch"),
        ("id", "Indonesian", "Bahasa Indonesia"),
        ("ko", "Korean", "한국어"),
        ("tr", "Turkish", "Türkçe"),
        ("vi", "Vietnamese", "Tiếng Việt"),
    ]

    def __init__(self, default_language: str = "en"):
        self.default_language = default_language
        self._build_detection_patterns()

    def _build_detection_patterns(self):
        """Build language detection patterns."""
        # Simple detection based on script/character patterns
        self.script_patterns = {
            "zh": re.compile(r'[\u4e00-\u9fff]'),  # Chinese characters
            "ja": re.compile(r'[\u3040-\u309f\u30a0-\u30ff]'),  # Hiragana/Katakana
            "ko": re.compile(r'[\uac00-\ud7af\u1100-\u11ff]'),  # Korean
            "ar": re.compile(r'[\u0600-\u06ff]'),  # Arabic
            "hi": re.compile(r'[\u0900-\u097f]'),  # Devanagari (Hindi)
            "bn": re.compile(r'[\u0980-\u09ff]'),  # Bengali
            "ru": re.compile(r'[\u0400-\u04ff]'),  # Cyrillic
            "vi": re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', re.IGNORECASE),
        }

        # Word-based detection for Latin scripts
        self.word_patterns = {
            "id": {"yang", "dan", "untuk", "dengan", "adalah", "dari", "ini", "itu", "tidak", "ada", "saya", "bisa"},
            "es": {"que", "para", "por", "como", "pero", "más", "cuando", "también", "sobre", "este", "está", "ser"},
            "fr": {"que", "pour", "dans", "avec", "cette", "sont", "nous", "vous", "être", "avoir", "fait", "plus"},
            "pt": {"que", "para", "como", "mais", "quando", "também", "sobre", "este", "está", "ser", "foram", "isso"},
            "de": {"und", "ist", "das", "die", "den", "für", "nicht", "auf", "mit", "sich", "werden", "wird"},
            "tr": {"için", "bir", "ile", "olan", "gibi", "daha", "çok", "sonra", "önce", "kadar", "ancak"},
        }

    def detect_language(self, text: str) -> str:
        """
        Detect the language of input text.

        Args:
            text: Input text

        Returns:
            ISO 639-1 language code
        """
        if not text or not text.strip():
            return self.default_language

        text_lower = text.lower()

        # Check script-based patterns first
        for lang, pattern in self.script_patterns.items():
            if pattern.search(text):
                return lang

        # Check word-based patterns for Latin scripts
        words = set(re.findall(r'\b\w+\b', text_lower))

        best_match = self.default_language
        best_score = 0

        for lang, keywords in self.word_patterns.items():
            score = len(words & keywords)
            if score > best_score:
                best_score = score
                best_match = lang

        # If score is 0, default to English
        return best_match if best_score > 0 else self.default_language

    def get_intent_patterns(self, intent: str, language: str = None) -> List[str]:
        """
        Get intent patterns for a language.

        Args:
            intent: Intent type (LIST, ENFORCE, etc.)
            language: Language code (auto-detect if None)

        Returns:
            List of regex patterns
        """
        lang = language or self.default_language

        if lang not in INTENT_PATTERNS:
            lang = self.default_language

        patterns = INTENT_PATTERNS.get(lang, {})
        return patterns.get(intent, [])

    def get_all_intent_patterns(self, intent: str) -> Dict[str, List[str]]:
        """
        Get intent patterns for all languages.

        Args:
            intent: Intent type

        Returns:
            Dict of language -> patterns
        """
        return {
            lang: patterns.get(intent, [])
            for lang, patterns in INTENT_PATTERNS.items()
        }

    def get_stopwords(self, language: str = None) -> Set[str]:
        """Get stopwords for a language."""
        lang = language or self.default_language
        return STOPWORDS.get(lang, STOPWORDS["en"])

    def get_tech_synonyms(self, term: str, language: str = None) -> List[str]:
        """
        Get technical synonyms for a term.

        Args:
            term: Technical term
            language: Language code

        Returns:
            List of synonyms
        """
        lang = language or self.default_language

        if lang not in TECH_SYNONYMS:
            lang = self.default_language

        synonyms = TECH_SYNONYMS.get(lang, {})
        return synonyms.get(term.lower(), [])

    def expand_multilingual(
        self,
        term: str,
        source_lang: str = None,
        target_langs: List[str] = None,
    ) -> Dict[str, str]:
        """
        Expand a term to multiple languages.

        Args:
            term: Term to expand
            source_lang: Source language
            target_langs: Target languages (None = all)

        Returns:
            Dict of language -> translated term
        """
        term_lower = term.lower()

        # Find the concept in cross-language terms
        for concept, translations in CROSS_LANGUAGE_TERMS.items():
            # Check if term matches any translation
            for lang, translation in translations.items():
                if translation.lower() == term_lower:
                    if target_langs:
                        return {l: translations.get(l, term) for l in target_langs}
                    return translations

        # No cross-language mapping found
        return {source_lang or self.default_language: term}

    def get_combined_patterns(self, intent: str, languages: List[str] = None) -> List[str]:
        """
        Get combined intent patterns from multiple languages.

        Args:
            intent: Intent type
            languages: List of language codes (None = all)

        Returns:
            Combined list of patterns
        """
        langs = languages or list(INTENT_PATTERNS.keys())
        patterns = []

        for lang in langs:
            lang_patterns = self.get_intent_patterns(intent, lang)
            patterns.extend(lang_patterns)

        return list(set(patterns))

    def filter_stopwords(self, text: str, language: str = None) -> str:
        """
        Remove stopwords from text.

        Args:
            text: Input text
            language: Language code

        Returns:
            Text without stopwords
        """
        lang = language or self.detect_language(text)
        stopwords = self.get_stopwords(lang)

        words = text.split()
        filtered = [w for w in words if w.lower() not in stopwords]

        return " ".join(filtered)

    def get_language_info(self, code: str) -> Optional[Tuple[str, str, str]]:
        """Get language info by code."""
        for lang_code, name, native in self.SUPPORTED_LANGUAGES:
            if lang_code == code:
                return (lang_code, name, native)
        return None

    def list_supported_languages(self) -> List[Tuple[str, str, str]]:
        """List all supported languages."""
        return self.SUPPORTED_LANGUAGES


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "MultilingualSupport",
    "LanguageConfig",
    "STOPWORDS",
    "INTENT_PATTERNS",
    "TECH_SYNONYMS",
    "CROSS_LANGUAGE_TERMS",
]
