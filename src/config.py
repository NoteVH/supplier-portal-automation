"""
Módulo de configuração.

Carrega variáveis sensíveis (URL, usuário, senha) a partir de um arquivo .env,
evitando que credenciais fiquem expostas no código-fonte.
"""

import os

from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env localizado na raiz do projeto
load_dotenv()

# --- Credenciais e URL do portal (lidas do .env) ---
PORTAL_URL = os.getenv("PORTAL_URL", "")
PORTAL_USER = os.getenv("PORTAL_USER", "")
PORTAL_PASSWORD = os.getenv("PORTAL_PASSWORD", "")

# --- Configurações do WebDriver ---
IMPLICIT_WAIT = int(os.getenv("IMPLICIT_WAIT", "50"))
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "10"))

# --- Mapeamento de contas (CGs da empresa - valores fictícios) ---
CONTAS = {
    "supplier_a_contract_1": "29",
    "supplier_b_contract_2": "30",
    "internal_resources": "31",
}

# --- Fornecedores disponíveis no sistema ---
FORNECEDORES = {
    "1": "MINISTERIO DA FAZENDA  -",
    "2": "MINISTERIO DO TRABALHO  -",
    "3": "Todos",
}


def validate_config() -> None:
    """Garante que as variáveis obrigatórias foram definidas no .env."""
    missing = []
    if not PORTAL_URL:
        missing.append("PORTAL_URL")
    if not PORTAL_USER:
        missing.append("PORTAL_USER")
    if not PORTAL_PASSWORD:
        missing.append("PORTAL_PASSWORD")

    if missing:
        raise EnvironmentError(
            "Variáveis de ambiente ausentes no arquivo .env: "
            + ", ".join(missing)
            + ". Copie o .env.example para .env e preencha os valores."
        )