from __future__ import annotations

from typing import Literal

ROLE_ADMIN: Literal["admin"] = "admin"
ROLE_ATENDENTE: Literal["atendente"] = "atendente"
ROLE_LEITOR: Literal["leitor"] = "leitor"

USER_ROLES: tuple[Literal["admin"], Literal["atendente"], Literal["leitor"]] = (
    ROLE_ADMIN,
    ROLE_ATENDENTE,
    ROLE_LEITOR,
)
