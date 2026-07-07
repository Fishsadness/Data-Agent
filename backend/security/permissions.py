"""
企业权限管理系统
JWT 认证 + 角色权限 + 数据脱敏
"""
import hashlib
import hmac
import json
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Role(Enum):
    ADMIN = "admin"         # 管理员 - 全部权限
    ANALYST = "analyst"     # 分析师 - 可查询所有表
    VIEWER = "viewer"       # 查看者 - 只能看聚合数据
    SALES = "sales"         # 销售 - 只能看订单和客户
    FINANCE = "finance"     # 财务 - 只能看利润和成本


@dataclass
class User:
    username: str
    role: Role
    department: str = ""


@dataclass
class Permission:
    """表级权限"""
    allowed_tables: list[str] = field(default_factory=list)
    forbidden_tables: list[str] = field(default_factory=list)
    allowed_columns: dict[str, list[str]] = field(default_factory=dict)  # table -> allowed columns
    require_masking: bool = False


# 角色权限映射
ROLE_PERMISSIONS = {
    Role.ADMIN: Permission(
        allowed_tables=["*"],
        require_masking=False,
    ),
    Role.ANALYST: Permission(
        allowed_tables=["*"],
        require_masking=True,  # 分析师需要脱敏
    ),
    Role.VIEWER: Permission(
        allowed_tables=["orders", "products"],
        forbidden_tables=["users"],  # 不能看用户详情
        require_masking=True,
    ),
    Role.SALES: Permission(
        allowed_tables=["orders", "products"],
        forbidden_tables=["users"],
        allowed_columns={"users": ["id", "city"]},  # 只能看用户的id和城市
        require_masking=True,
    ),
    Role.FINANCE: Permission(
        allowed_tables=["orders", "products"],
        require_masking=True,
    ),
}

# 敏感字段模式
SENSITIVE_PATTERNS = {
    "phone": r"(\d{3})\d{4}(\d{4})",
    "email": r"(.{2}).*(@.*)",
    "id_card": r"(\d{4})\d{10}(\d{4})",
    "name": None,  # 姓名特殊处理
}

# 脱敏规则
MASKING_RULES = {
    "phone": lambda v: re.sub(r"(\d{3})\d{4}(\d{4})", r"\1****\2", str(v)),
    "email": lambda v: re.sub(r"(.{2}).*(@.*)", r"\1***\2", str(v)),
    "id_card": lambda v: re.sub(r"(\d{4})\d{10}(\d{4})", r"\1**********\2", str(v)),
    "name": lambda v: str(v)[0] + "*" * (len(str(v)) - 1) if len(str(v)) > 1 else str(v),
}


class SecurityManager:
    """安全管理器"""

    def __init__(self):
        self._users: dict[str, User] = {
            "admin": User("admin", Role.ADMIN, "技术部"),
            "analyst": User("analyst", Role.ANALYST, "数据部"),
            "viewer": User("viewer", Role.VIEWER, "业务部"),
            "sales": User("sales", Role.SALES, "销售部"),
            "finance": User("finance", Role.FINANCE, "财务部"),
        }

    def get_user(self, username: str) -> Optional[User]:
        return self._users.get(username)

    def get_permission(self, user: User) -> Permission:
        return ROLE_PERMISSIONS.get(user.role, Permission())

    def check_table_access(self, user: User, table_name: str) -> bool:
        """检查用户是否有权访问指定表"""
        perm = self.get_permission(user)

        if "*" in perm.allowed_tables:
            if table_name in perm.forbidden_tables:
                return False
            return True

        return table_name in perm.allowed_tables

    def check_column_access(self, user: User, table_name: str, column_name: str) -> bool:
        """检查用户是否有权访问指定列"""
        perm = self.get_permission(user)

        if table_name in perm.allowed_columns:
            return column_name in perm.allowed_columns[table_name]
        return True

    def filter_sql(self, user: User, sql: str) -> str:
        """根据用户权限过滤 SQL（在安全层之上加权限控制）"""
        perm = self.get_permission(user)

        sql_upper = sql.upper()

        # 检查禁止的表
        for table in perm.forbidden_tables:
            if table.upper() in sql_upper:
                raise PermissionError(f"用户 {user.username} 无权访问表 {table}")

        return sql

    def mask_data(self, user: User, columns: list[str], rows: list[dict]) -> tuple[list[str], list[dict]]:
        """对敏感数据进行脱敏"""
        perm = self.get_permission(user)

        if not perm.require_masking:
            return columns, rows

        # 识别敏感列
        sensitive_cols = set()
        for col in columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ["phone", "mobile", "电话", "手机"]):
                sensitive_cols.add((col, "phone"))
            elif any(keyword in col_lower for keyword in ["email", "mail", "邮箱"]):
                sensitive_cols.add((col, "email"))
            elif any(keyword in col_lower for keyword in ["id_card", "身份证"]):
                sensitive_cols.add((col, "id_card"))
            elif any(keyword in col_lower for keyword in ["name", "姓名", "username"]):
                sensitive_cols.add((col, "name"))

        if not sensitive_cols:
            return columns, rows

        masked_rows = []
        for row in rows:
            masked_row = dict(row)
            for col_name, mask_type in sensitive_cols:
                if col_name in masked_row and masked_row[col_name] is not None:
                    rule = MASKING_RULES.get(mask_type)
                    if rule:
                        masked_row[col_name] = rule(masked_row[col_name])
            masked_rows.append(masked_row)

        return columns, masked_rows


# 全局实例
security = SecurityManager()


# ============ JWT 简易实现 ============

JWT_SECRET = "data-agent-secret-key-change-in-production"


def create_token(username: str) -> str:
    """创建简易 JWT Token"""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400,  # 24小时
    }

    header_b64 = _b64_encode(json.dumps(header))
    payload_b64 = _b64_encode(json.dumps(payload))
    signature = hmac.new(
        JWT_SECRET.encode(),
        f"{header_b64}.{payload_b64}".encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{header_b64}.{payload_b64}.{signature}"


def verify_token(token: str) -> Optional[str]:
    """验证 Token，返回用户名"""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature = parts
        expected = hmac.new(
            JWT_SECRET.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).hexdigest()

        if signature != expected:
            return None

        payload = json.loads(_b64_decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None

        return payload.get("sub")
    except Exception:
        return None


def _b64_encode(data: str) -> str:
    import base64
    return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")


def _b64_decode(data: str) -> str:
    import base64
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data).decode()