"""
ARSAKA_PANDAWA Backend - Centralized API Routes Definition
Follows CORE-STD-01 standards
"""


class APIRoutes:
    """Centralized API route definitions for all modules"""

    # API prefix
    PREFIX = "/api/v1"

    # Authentication & Authorization (Core Services)
    AUTH = f"{PREFIX}/auth"
    AUTH_LOGIN = f"{AUTH}/login"
    AUTH_REGISTER = f"{AUTH}/register"
    AUTH_REFRESH = f"{AUTH}/refresh"
    AUTH_LOGOUT = f"{AUTH}/logout"
    AUTH_ME = f"{AUTH}/me"

    # User Management (Core Services)
    USERS = f"{PREFIX}/users"
    USER_PROFILE = f"{USERS}/profile"
    USER_ROLES = f"{USERS}/roles"

    # Organization Management (Core Services)
    ORGANIZATIONS = f"{PREFIX}/organizations"
    ORG_MEMBERS = f"{ORGANIZATIONS}/members"
    ORG_SETTINGS = f"{ORGANIZATIONS}/settings"

    # PMS Module Routes (Phase 2+)
    PMS = f"{PREFIX}/pms"
    PMS_RESERVATIONS = f"{PMS}/reservations"
    PMS_ROOMS = f"{PMS}/rooms"
    PMS_ROOM_TYPES = f"{PMS}/room-types"
    PMS_GUESTS = f"{PMS}/guests"

    # POS Module Routes (Phase 3+)
    POS = f"{PREFIX}/pos"
    POS_ORDERS = f"{POS}/orders"
    POS_PRODUCTS = f"{POS}/products"
    POS_CATEGORIES = f"{POS}/categories"

    # Accounting Module Routes (Phase 4+)
    ACCOUNTING = f"{PREFIX}/accounting"
    ACC_INVOICES = f"{ACCOUNTING}/invoices"
    ACC_PAYMENTS = f"{ACCOUNTING}/payments"
    ACC_JOURNAL = f"{ACCOUNTING}/journal"

    # HRM Module Routes (Phase 5+)
    HRM = f"{PREFIX}/hrm"
    HRM_EMPLOYEES = f"{HRM}/employees"
    HRM_ATTENDANCE = f"{HRM}/attendance"
    HRM_PAYROLL = f"{HRM}/payroll"

    # Inventory Module Routes (Phase 6+)
    INVENTORY = f"{PREFIX}/inventory"
    INV_ITEMS = f"{INVENTORY}/items"
    INV_STOCK = f"{INVENTORY}/stock"
    INV_MOVEMENTS = f"{INVENTORY}/movements"


routes = APIRoutes()
