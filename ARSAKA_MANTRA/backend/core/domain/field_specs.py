"""
MANTRA Decision Field Specifications

Spesifikasi lengkap untuk setiap field dalam MCPDecision.
Digunakan oleh AI untuk mengisi field dengan benar.

Setiap field memiliki:
- description: Penjelasan field
- purpose: Tujuan field ini ada
- format: Format yang diharapkan
- guidelines: Panduan penulisan
- examples: Contoh baik dan buruk
- validation: Aturan validasi
- source: Siapa yang bisa mengisi
"""

from dataclasses import dataclass, field as dc_field
from typing import List, Dict, Any, Optional
from enum import Enum


class FieldSource(Enum):
    """Sumber nilai field."""
    SYSTEM = "system"           # Auto-generated (decision_id, timestamps)
    FORMULA = "formula"         # Calculated dari field lain
    AI_SUGGEST = "ai_suggest"   # AI suggest, human HARUS approve/edit
    AI_FILL = "ai_fill"         # AI bisa isi langsung, tetap perlu approval
    HUMAN_ONLY = "human_only"   # HANYA human yang bisa isi


@dataclass
class FieldExample:
    """Contoh untuk field."""
    value: Any
    is_good: bool
    explanation: str


@dataclass
class FieldSpec:
    """Spesifikasi lengkap untuk satu field."""
    name: str
    display_name: str
    description: str
    purpose: str
    source: FieldSource
    required: bool

    # Format
    data_type: str  # "string", "list", "dict", "int", "enum"
    format_pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_values: Optional[List[str]] = None

    # Guidelines
    guidelines: List[str] = dc_field(default_factory=list)
    writing_tips: List[str] = dc_field(default_factory=list)
    common_mistakes: List[str] = dc_field(default_factory=list)

    # Examples
    good_examples: List[FieldExample] = dc_field(default_factory=list)
    bad_examples: List[FieldExample] = dc_field(default_factory=list)

    # Validation
    validation_rules: List[str] = dc_field(default_factory=list)

    # AI Prompt (untuk AI saat generate)
    ai_prompt: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "purpose": self.purpose,
            "source": self.source.value,
            "required": self.required,
            "data_type": self.data_type,
            "format_pattern": self.format_pattern,
            "min_length": self.min_length,
            "max_length": self.max_length,
            "allowed_values": self.allowed_values,
            "guidelines": self.guidelines,
            "writing_tips": self.writing_tips,
            "common_mistakes": self.common_mistakes,
            "validation_rules": self.validation_rules,
            "ai_prompt": self.ai_prompt,
        }


# ============================================================================
# FIELD SPECIFICATIONS
# ============================================================================

FIELD_SPECS: Dict[str, FieldSpec] = {

    # =========================================================================
    # IDENTITY FIELDS (System Generated)
    # =========================================================================

    "decision_id": FieldSpec(
        name="decision_id",
        display_name="Decision ID",
        description="Unique identifier untuk decision",
        purpose="Identifikasi unik setiap decision dalam sistem",
        source=FieldSource.SYSTEM,
        required=True,
        data_type="string",
        format_pattern=r"^(INT|ARCH|CTL|EVO)-F\d{2}-\d{3}$",
        guidelines=[
            "Format: {DOMAIN}-F{ASPECT}-{SEQUENCE}",
            "DOMAIN: INT, ARCH, CTL, atau EVO",
            "ASPECT: 01-16 (sesuai domain)",
            "SEQUENCE: 001-999",
        ],
        good_examples=[
            FieldExample("INT-F01-001", True, "Vision decision pertama"),
            FieldExample("CTL-F10-042", True, "Security decision ke-42"),
        ],
        bad_examples=[
            FieldExample("DEC-001", False, "Format salah, tidak ada domain"),
            FieldExample("ARCH-F99-001", False, "F99 tidak valid (max F16)"),
        ],
    ),

    "version": FieldSpec(
        name="version",
        display_name="Version",
        description="Nomor versi decision",
        purpose="Track perubahan decision (via supersedes)",
        source=FieldSource.SYSTEM,
        required=True,
        data_type="int",
        guidelines=[
            "Dimulai dari 1",
            "Increment saat ada supersedes",
            "Tidak bisa di-edit manual",
        ],
    ),

    "created_at": FieldSpec(
        name="created_at",
        display_name="Created At",
        description="Timestamp pembuatan decision",
        purpose="Audit trail kapan decision dibuat",
        source=FieldSource.SYSTEM,
        required=True,
        data_type="string",
        format_pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        guidelines=["Format ISO 8601", "Timezone UTC"],
    ),

    # =========================================================================
    # CORE CONTENT FIELDS (AI Suggest, Human Approve)
    # =========================================================================

    "title": FieldSpec(
        name="title",
        display_name="Title",
        description="Judul singkat dan deskriptif untuk decision",
        purpose="Identifikasi cepat apa yang diputuskan",
        source=FieldSource.AI_SUGGEST,
        required=True,
        data_type="string",
        min_length=10,
        max_length=100,
        guidelines=[
            "Singkat tapi deskriptif (10-100 karakter)",
            "Mulai dengan kata kerja atau noun",
            "Hindari kata-kata generic seperti 'Decision about...'",
            "Spesifik tentang APA yang diputuskan",
        ],
        writing_tips=[
            "Bayangkan judul ini muncul di list - apakah jelas?",
            "Sertakan context domain jika perlu",
            "Gunakan technical terms yang tepat",
        ],
        common_mistakes=[
            "Terlalu panjang dan bertele-tele",
            "Terlalu generic: 'API Decision'",
            "Tidak menjelaskan apa yang diputuskan",
        ],
        good_examples=[
            FieldExample(
                "API Rate Limiting: 100 req/min per User",
                True,
                "Spesifik, ada angka, jelas apa yang dibatasi"
            ),
            FieldExample(
                "JWT Token Expiry: 24 Hours for Web, 30 Days for Mobile",
                True,
                "Spesifik per platform, ada durasi"
            ),
        ],
        bad_examples=[
            FieldExample(
                "API Decision",
                False,
                "Terlalu generic, tidak jelas apa yang diputuskan"
            ),
            FieldExample(
                "We decided to implement rate limiting for our API endpoints to prevent abuse",
                False,
                "Terlalu panjang, seperti kalimat bukan judul"
            ),
        ],
        validation_rules=[
            "Tidak boleh kosong",
            "Minimal 10 karakter",
            "Maksimal 100 karakter",
            "Tidak boleh hanya angka atau simbol",
        ],
        ai_prompt="""Generate a concise, descriptive title for this decision.
        - Be specific about WHAT is being decided
        - Include key parameters if applicable (numbers, limits)
        - Use technical terms appropriately
        - 10-100 characters""",
    ),

    "statement": FieldSpec(
        name="statement",
        display_name="Statement",
        description="Pernyataan inti dari decision - APA yang diputuskan",
        purpose="Definisi jelas dan actionable tentang keputusan",
        source=FieldSource.AI_SUGGEST,
        required=True,
        data_type="string",
        min_length=20,
        max_length=500,
        guidelines=[
            "Jelas dan tidak ambigu",
            "Actionable - bisa langsung diimplementasi",
            "Satu decision per statement",
            "Gunakan 'MUST', 'SHALL', 'SHOULD' sesuai RFC 2119",
            "Hindari kata-kata samar seperti 'mungkin', 'bisa jadi'",
        ],
        writing_tips=[
            "Mulai dengan subject yang jelas",
            "Gunakan present tense",
            "Sertakan scope jika perlu",
            "Bisa dipahami tanpa membaca rationale",
        ],
        common_mistakes=[
            "Terlalu panjang dengan banyak kondisi",
            "Ambigu: 'API harus cepat' (seberapa cepat?)",
            "Menggabungkan multiple decisions",
            "Menjelaskan 'why' bukan 'what'",
        ],
        good_examples=[
            FieldExample(
                "All public API endpoints MUST implement rate limiting of 100 requests per minute per authenticated user. Unauthenticated requests are limited to 10 requests per minute per IP.",
                True,
                "Jelas, ada angka spesifik, ada pembedaan authenticated/unauthenticated"
            ),
            FieldExample(
                "Database connections MUST use connection pooling with minimum 5 and maximum 20 connections per service instance.",
                True,
                "Spesifik, ada range, per instance"
            ),
        ],
        bad_examples=[
            FieldExample(
                "We should probably implement rate limiting.",
                False,
                "Tidak spesifik, menggunakan 'probably'"
            ),
            FieldExample(
                "The API needs to be faster and more secure and also we need to add caching and improve the database queries.",
                False,
                "Multiple decisions digabung, tidak actionable"
            ),
        ],
        validation_rules=[
            "Tidak boleh kosong",
            "Minimal 20 karakter",
            "Maksimal 500 karakter",
            "Harus mengandung actionable verb",
        ],
        ai_prompt="""Generate a clear, actionable decision statement.
        - State WHAT is being decided (not why)
        - Use RFC 2119 keywords (MUST, SHALL, SHOULD)
        - Include specific parameters/limits
        - One decision only
        - 20-500 characters""",
    ),

    "rationale": FieldSpec(
        name="rationale",
        display_name="Rationale",
        description="Alasan dan justifikasi MENGAPA decision ini dibuat",
        purpose="Dokumentasi reasoning untuk future reference",
        source=FieldSource.AI_SUGGEST,
        required=True,
        data_type="string",
        min_length=50,
        max_length=1000,
        guidelines=[
            "Jelaskan MENGAPA, bukan APA",
            "Sertakan context yang memicu decision",
            "Sebutkan alternatives yang dipertimbangkan",
            "Jelaskan trade-offs",
            "Referensi ke standards atau best practices jika ada",
        ],
        writing_tips=[
            "Bayangkan orang baru bergabung 1 tahun lagi - apakah mereka paham?",
            "Sertakan data/evidence jika ada",
            "Jelaskan apa yang terjadi jika decision ini tidak diambil",
        ],
        common_mistakes=[
            "Mengulang statement tanpa menjelaskan why",
            "Terlalu singkat tanpa context",
            "Tidak menyebutkan alternatives",
            "Tidak ada justifikasi bisnis/teknis",
        ],
        good_examples=[
            FieldExample(
                "Rate limiting is implemented to prevent API abuse and ensure fair resource allocation. "
                "Without limits, a single user could overwhelm the system affecting all users. "
                "The 100 req/min limit is based on 95th percentile usage analysis showing normal users "
                "average 20 req/min. We considered token bucket (complex) and sliding window (simpler) "
                "algorithms; chose sliding window for operational simplicity.",
                True,
                "Ada context, data, alternatives, dan trade-off"
            ),
        ],
        bad_examples=[
            FieldExample(
                "We need rate limiting because it's important.",
                False,
                "Tidak menjelaskan WHY, terlalu generic"
            ),
            FieldExample(
                "All API endpoints must implement rate limiting of 100 requests per minute.",
                False,
                "Ini statement, bukan rationale - menjelaskan WHAT bukan WHY"
            ),
        ],
        validation_rules=[
            "Tidak boleh kosong",
            "Minimal 50 karakter",
            "Maksimal 1000 karakter",
            "Tidak boleh sama dengan statement",
        ],
        ai_prompt="""Generate a comprehensive rationale explaining WHY this decision is made.
        - Explain the context/trigger
        - Mention alternatives considered
        - Explain trade-offs
        - Include data/evidence if available
        - Reference standards/best practices
        - 50-1000 characters""",
    ),

    # =========================================================================
    # CLASSIFICATION FIELDS (AI Detect, Human Approve)
    # =========================================================================

    "domain_id": FieldSpec(
        name="domain_id",
        display_name="Domain",
        description="Domain classification dari decision (4 groups)",
        purpose="Kategorisasi untuk navigasi dan filtering",
        source=FieldSource.AI_SUGGEST,
        required=True,
        data_type="enum",
        allowed_values=["INT", "ARCH", "CTL", "EVO"],
        guidelines=[
            "INT (Intent): Vision, goals, objectives, stakeholders",
            "ARCH (Architecture): Structure, components, interfaces, patterns",
            "CTL (Control): Policies, security, compliance, risk",
            "EVO (Evolution): Implementation, deployment, migration, maintenance",
        ],
        writing_tips=[
            "Lihat keywords dalam statement/rationale",
            "INT: 'goal', 'vision', 'objective', 'purpose'",
            "ARCH: 'component', 'layer', 'interface', 'pattern'",
            "CTL: 'security', 'policy', 'rule', 'compliance'",
            "EVO: 'deploy', 'release', 'migrate', 'implement'",
        ],
        common_mistakes=[
            "Memilih ARCH untuk security decision (seharusnya CTL)",
            "Memilih EVO untuk architectural decision",
        ],
        good_examples=[
            FieldExample("CTL", True, "Rate limiting = security/control"),
            FieldExample("ARCH", True, "Database schema = architecture"),
            FieldExample("INT", True, "Product vision = intent"),
            FieldExample("EVO", True, "Deployment strategy = evolution"),
        ],
        validation_rules=[
            "Harus salah satu dari: INT, ARCH, CTL, EVO",
        ],
        ai_prompt="""Determine the domain based on the decision content:
        - INT: Goals, vision, objectives, stakeholders
        - ARCH: Structure, components, interfaces
        - CTL: Security, policies, compliance, risk
        - EVO: Implementation, deployment, migration
        Return only the code: INT, ARCH, CTL, or EVO""",
    ),

    "aspect_id": FieldSpec(
        name="aspect_id",
        display_name="Aspect",
        description="Aspect classification (16 aspects, 4 per domain)",
        purpose="Sub-kategorisasi lebih detail",
        source=FieldSource.AI_SUGGEST,
        required=True,
        data_type="enum",
        allowed_values=[f"A{str(i).zfill(2)}" for i in range(1, 17)],
        guidelines=[
            "INT Domain:",
            "  A01: Vision & Purpose - North star, why we exist",
            "  A02: Objectives & Goals - Measurable outcomes, KPIs",
            "  A03: Scope & Boundaries - What's in/out of scope",
            "  A04: Stakeholders - Users, personas, audiences",
            "",
            "ARCH Domain:",
            "  A05: Layers & Tiers - Separation, abstraction levels",
            "  A06: Components & Modules - Services, microservices",
            "  A07: Interfaces & Contracts - APIs, protocols",
            "  A08: Patterns & Standards - Idioms, conventions",
            "",
            "CTL Domain:",
            "  A09: Policies & Rules - Constraints, invariants",
            "  A10: Security & Auth - Permissions, RBAC, access",
            "  A11: Compliance & Audit - Governance, regulations",
            "  A12: Risk & Mitigation - Contingency, fallback",
            "",
            "EVO Domain:",
            "  A13: Implementation - Coding, development",
            "  A14: Deployment & Release - CI/CD, rollout",
            "  A15: Migration & Upgrade - Transitions, backwards compat",
            "  A16: Maintenance & Support - Monitoring, observability",
        ],
        common_mistakes=[
            "Memilih aspect dari domain yang salah",
            "A10 untuk non-security decision",
        ],
        good_examples=[
            FieldExample("A10", True, "Rate limiting = Security (A10)"),
            FieldExample("A07", True, "API contract = Interfaces (A07)"),
            FieldExample("A14", True, "CI/CD pipeline = Deployment (A14)"),
        ],
        validation_rules=[
            "Harus A01-A16",
            "Harus sesuai dengan domain_id",
            "INT: A01-A04, ARCH: A05-A08, CTL: A09-A12, EVO: A13-A16",
        ],
        ai_prompt="""Determine the aspect based on domain and content:
        For CTL domain: A09 (Policy), A10 (Security), A11 (Compliance), A12 (Risk)
        Match the most specific aspect to the decision content.
        Return only the code: A01 to A16""",
    ),

    # =========================================================================
    # IMPACT FIELDS (Formula/AI, Human Approve)
    # =========================================================================

    "blast_radius": FieldSpec(
        name="blast_radius",
        display_name="Blast Radius",
        description="Impact level dari decision (1-5)",
        purpose="Prioritization dan risk assessment",
        source=FieldSource.FORMULA,
        required=True,
        data_type="int",
        allowed_values=["1", "2", "3", "4", "5"],
        guidelines=[
            "1 - Minimal: Satu fitur/modul, mudah di-rollback",
            "2 - Low: Beberapa fitur, satu team affected",
            "3 - Medium: Satu domain/service, multiple teams",
            "4 - High: Cross-domain, significant rework jika salah",
            "5 - Critical: System-wide, tidak bisa di-rollback",
        ],
        writing_tips=[
            "Pertimbangkan: berapa banyak code yang berubah?",
            "Pertimbangkan: berapa team yang affected?",
            "Pertimbangkan: seberapa sulit rollback?",
            "Pertimbangkan: apa impact jika decision salah?",
        ],
        good_examples=[
            FieldExample(4, True, "Rate limiting API-wide = High impact"),
            FieldExample(2, True, "Logging format change = Low impact"),
            FieldExample(5, True, "Database schema migration = Critical"),
        ],
        validation_rules=[
            "Harus 1-5",
            "Harus integer",
        ],
        ai_prompt="""Calculate blast radius based on:
        - Scope of change (1 file vs system-wide)
        - Number of teams affected
        - Rollback difficulty
        - Business impact if wrong
        Return integer 1-5""",
    ),

    "scope": FieldSpec(
        name="scope",
        display_name="Scope",
        description="Cakupan decision - modules dan severity",
        purpose="Define boundaries dan applicability",
        source=FieldSource.AI_SUGGEST,
        required=True,
        data_type="dict",
        guidelines=[
            "modules: List of affected modules/services",
            "severity: low, medium, high, critical",
            "Bisa include 'teams', 'environments', dll",
        ],
        good_examples=[
            FieldExample(
                {"modules": ["api", "auth"], "severity": "high"},
                True,
                "Jelas modules dan severity"
            ),
            FieldExample(
                {"modules": ["backend"], "severity": "medium", "environments": ["production", "staging"]},
                True,
                "Dengan environment specification"
            ),
        ],
        validation_rules=[
            "Harus object/dict",
            "Harus ada 'modules' (list) dan 'severity' (string)",
        ],
        ai_prompt="""Determine scope with:
        - modules: list of affected modules/services
        - severity: "low", "medium", "high", or "critical"
        Return as JSON object""",
    ),

    # =========================================================================
    # CONSTRAINT FIELDS (AI Suggest, Human Approve)
    # =========================================================================

    "constraints": FieldSpec(
        name="constraints",
        display_name="Constraints",
        description="Batasan yang harus diikuti saat implementasi",
        purpose="Guardrails untuk implementasi",
        source=FieldSource.AI_SUGGEST,
        required=False,
        data_type="list",
        guidelines=[
            "Setiap constraint harus actionable",
            "Gunakan 'MUST', 'MUST NOT'",
            "Spesifik dan measurable jika memungkinkan",
            "Max 5-7 constraints per decision",
        ],
        writing_tips=[
            "Fokus pada DO's dan DON'Ts",
            "Setiap constraint bisa di-verify",
            "Jangan duplikasi dengan statement",
        ],
        good_examples=[
            FieldExample(
                [
                    "Rate limit response MUST include X-RateLimit-Remaining header",
                    "Rate limit MUST NOT apply to health check endpoints",
                    "Rate limit bypass MUST require admin approval",
                ],
                True,
                "Specific, actionable, verifiable"
            ),
        ],
        bad_examples=[
            FieldExample(
                ["Be careful", "Test properly"],
                False,
                "Tidak actionable, tidak specific"
            ),
        ],
        validation_rules=[
            "Harus array of strings",
            "Setiap item minimal 10 karakter",
        ],
        ai_prompt="""Generate implementation constraints:
        - Use MUST/MUST NOT
        - Be specific and verifiable
        - Max 5-7 constraints
        Return as list of strings""",
    ),

    "invariants": FieldSpec(
        name="invariants",
        display_name="Invariants",
        description="Kondisi yang harus SELALU benar",
        purpose="System guarantees yang tidak boleh dilanggar",
        source=FieldSource.AI_SUGGEST,
        required=False,
        data_type="list",
        guidelines=[
            "Invariant = SELALU true, tidak ada exception",
            "Jika dilanggar = system error/bug",
            "Biasanya tentang data consistency",
            "Max 3-5 invariants per decision",
        ],
        good_examples=[
            FieldExample(
                [
                    "Rate limit counter MUST reset exactly at window boundary",
                    "User rate limit MUST be isolated from other users",
                ],
                True,
                "Clear conditions that must always hold"
            ),
        ],
        validation_rules=[
            "Harus array of strings",
            "Setiap item minimal 10 karakter",
        ],
        ai_prompt="""Generate invariants - conditions that MUST always be true:
        - These are system guarantees
        - Violation = bug/error
        - Focus on data consistency
        Return as list of strings""",
    ),

    # =========================================================================
    # ENRICHMENT FIELDS (AI Fill, Human Approve)
    # =========================================================================

    "trigger_event": FieldSpec(
        name="trigger_event",
        display_name="Trigger Event",
        description="Apa yang memicu pembuatan decision ini",
        purpose="Context untuk understanding 'why now'",
        source=FieldSource.AI_FILL,
        required=False,
        data_type="string",
        max_length=200,
        guidelines=[
            "Jelaskan event/situation yang memicu",
            "Bisa berupa: incident, feature request, audit finding, dll",
        ],
        good_examples=[
            FieldExample(
                "Security audit finding: API vulnerable to DDoS",
                True,
                "Specific trigger"
            ),
            FieldExample(
                "User request via Claude CLI for API security improvement",
                True,
                "Request context"
            ),
        ],
        ai_prompt="""Capture what triggered this decision:
        - Security audit finding?
        - User request?
        - Incident?
        - Technical debt?
        Keep concise, max 200 chars""",
    ),

    "code_artifacts": FieldSpec(
        name="code_artifacts",
        display_name="Code Artifacts",
        description="File/path code yang related dengan decision",
        purpose="Traceability ke implementation",
        source=FieldSource.AI_FILL,
        required=False,
        data_type="list",
        guidelines=[
            "List file paths yang akan diubah/dibuat",
            "Gunakan relative path dari project root",
            "Include existing files yang affected",
        ],
        good_examples=[
            FieldExample(
                ["src/api/middleware/rate_limit.py", "src/api/routes.py", "tests/test_rate_limit.py"],
                True,
                "Specific files"
            ),
        ],
        ai_prompt="""List related code files:
        - Files to be created/modified
        - Related test files
        - Configuration files
        Use relative paths""",
    ),

    # =========================================================================
    # AUTHORSHIP FIELDS (Human Only / System)
    # =========================================================================

    "author_id": FieldSpec(
        name="author_id",
        display_name="Author",
        description="Human yang membuat decision",
        purpose="Accountability dan ownership",
        source=FieldSource.HUMAN_ONLY,
        required=True,
        data_type="string",
        format_pattern=r"^(human:|user:)",
        guidelines=[
            "HARUS human identifier",
            "TIDAK BOLEH dimulai dengan 'ai:'",
            "Format: human:email@domain.com atau user:username",
        ],
        validation_rules=[
            "Tidak boleh kosong",
            "Tidak boleh dimulai dengan 'ai:'",
            "Harus format human: atau user:",
        ],
    ),

    "approved_by": FieldSpec(
        name="approved_by",
        display_name="Approved By",
        description="Human yang approve decision (MANTRA §6)",
        purpose="Final authority - MUST be human",
        source=FieldSource.HUMAN_ONLY,
        required=True,
        data_type="string",
        format_pattern=r"^(human:|user:)",
        guidelines=[
            "WAJIB human - MANTRA-LAW-001 §6",
            "AI TIDAK BISA approve",
            "Set saat finalize",
        ],
        validation_rules=[
            "HARUS human identifier",
            "TIDAK BOLEH 'ai:' - MANTRA §6 violation",
        ],
    ),
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_field_spec(field_name: str) -> Optional[FieldSpec]:
    """Get spec for a field."""
    return FIELD_SPECS.get(field_name)


def get_ai_prompt(field_name: str) -> Optional[str]:
    """Get AI prompt for a field."""
    spec = FIELD_SPECS.get(field_name)
    return spec.ai_prompt if spec else None


def get_validation_rules(field_name: str) -> List[str]:
    """Get validation rules for a field."""
    spec = FIELD_SPECS.get(field_name)
    return spec.validation_rules if spec else []


def get_guidelines(field_name: str) -> List[str]:
    """Get guidelines for a field."""
    spec = FIELD_SPECS.get(field_name)
    return spec.guidelines if spec else []


def get_all_specs() -> Dict[str, Dict]:
    """Get all field specs as dict."""
    return {name: spec.to_dict() for name, spec in FIELD_SPECS.items()}


def get_field_source_info() -> Dict[str, str]:
    """Get source info for all fields."""
    return {
        name: spec.source.value
        for name, spec in FIELD_SPECS.items()
    }


def format_spec_for_display(field_name: str) -> str:
    """Format spec for display in UI or logs."""
    spec = FIELD_SPECS.get(field_name)
    if not spec:
        return f"No spec for: {field_name}"

    lines = [
        f"=== {spec.display_name} ({spec.name}) ===",
        f"",
        f"Description: {spec.description}",
        f"Purpose: {spec.purpose}",
        f"Source: {spec.source.value}",
        f"Required: {spec.required}",
        f"Type: {spec.data_type}",
    ]

    if spec.guidelines:
        lines.append("")
        lines.append("Guidelines:")
        for g in spec.guidelines:
            lines.append(f"  - {g}")

    if spec.writing_tips:
        lines.append("")
        lines.append("Writing Tips:")
        for t in spec.writing_tips:
            lines.append(f"  - {t}")

    if spec.common_mistakes:
        lines.append("")
        lines.append("Common Mistakes:")
        for m in spec.common_mistakes:
            lines.append(f"  - {m}")

    if spec.good_examples:
        lines.append("")
        lines.append("Good Examples:")
        for ex in spec.good_examples:
            lines.append(f"  [OK] {ex.value}")
            lines.append(f"       {ex.explanation}")

    if spec.bad_examples:
        lines.append("")
        lines.append("Bad Examples:")
        for ex in spec.bad_examples:
            lines.append(f"  [X] {ex.value}")
            lines.append(f"      {ex.explanation}")

    if spec.validation_rules:
        lines.append("")
        lines.append("Validation Rules:")
        for r in spec.validation_rules:
            lines.append(f"  - {r}")

    return "\n".join(lines)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "FieldSpec",
    "FieldSource",
    "FieldExample",
    "FIELD_SPECS",
    "get_field_spec",
    "get_ai_prompt",
    "get_validation_rules",
    "get_guidelines",
    "get_all_specs",
    "get_field_source_info",
    "format_spec_for_display",
]
