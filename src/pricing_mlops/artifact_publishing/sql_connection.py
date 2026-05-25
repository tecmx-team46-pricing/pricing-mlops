from __future__ import annotations

import os
import struct
from dataclasses import dataclass
from typing import Any


SQL_COPT_SS_ACCESS_TOKEN = 1256
AZURE_SQL_SCOPE = "https://database.windows.net/.default"


@dataclass(frozen=True)
class AzureSqlSettings:
    server: str
    database: str
    driver: str = "ODBC Driver 18 for SQL Server"
    timeout_seconds: int = 30

    @classmethod
    def from_env(cls) -> AzureSqlSettings:
        server = os.getenv("MLOPS_SQL_SERVER", "").strip()
        database = os.getenv("MLOPS_SQL_DATABASE", "").strip()
        if not server or not database:
            raise ValueError("MLOPS_SQL_SERVER and MLOPS_SQL_DATABASE are required for sql_metadata sink")
        return cls(
            server=server,
            database=database,
            driver=os.getenv("MLOPS_SQL_ODBC_DRIVER", "ODBC Driver 18 for SQL Server"),
            timeout_seconds=int(os.getenv("MLOPS_SQL_TIMEOUT_SECONDS", "30")),
        )

    def connection_string(self) -> str:
        server_name = self.server
        if not server_name.startswith("tcp:"):
            server_name = f"tcp:{server_name}"
        if ".database.windows.net" not in server_name:
            server_name = f"{server_name}.database.windows.net"
        return (
            f"Driver={{{self.driver}}};"
            f"Server={server_name},1433;"
            f"Database={self.database};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            f"Connection Timeout={self.timeout_seconds};"
        )


def connect_azure_sql_with_entra_token(credential: Any, settings: AzureSqlSettings | None = None):
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError("pyodbc is required for the sql_metadata sink; install pricing-mlops[sql]") from exc

    resolved = settings or AzureSqlSettings.from_env()
    access_token = credential.get_token(AZURE_SQL_SCOPE).token.encode("utf-16-le")
    token_struct = struct.pack(f"<I{len(access_token)}s", len(access_token), access_token)
    return pyodbc.connect(
        resolved.connection_string(),
        attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct},
    )
