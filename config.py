"""
config.py - Configuração Centralizada da Aplicação ContratoSeguro AI

Este módulo gerencia todas as constantes, variáveis de ambiente, logging
e validações da aplicação. Fornece uma interface única para acessar
configurações em toda a aplicação.

Exemplo de uso:
    from config import load_env_config, setup_logging, check_dependencies

    # Carregar configurações
    config = load_env_config()
    logger = setup_logging()

    # Validar dependências
    check_dependencies()
    check_api_keys()

    # Acessar configurações
    max_file_size = config['MAX_FILE_SIZE']
    gemini_model = config['GEMINI_MODEL']
"""

import hashlib
import importlib.util
import logging
import logging.handlers
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

# ==================== CONSTANTES CENTRALIZADAS ====================

# Limites de arquivo e texto
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MIN_TEXT_LENGTH = 10  # Mínimo de caracteres para análise

# Modelos de IA
GEMINI_MODEL = "gemini-2.5-flash"  # v1beta - Validado pelo usuário

# URLs e endpoints
GEMINI_API_VERSION = "v1beta"  # Versão validada

# Timeouts (em segundos)
REQUEST_TIMEOUT = 60  # Aumentado para evitar 504
ANALYSIS_TIMEOUT = 300

# Retries
MAX_RETRIES = 3
RETRY_DELAY = 5  # segundos (aumentado)

# Diretórios
BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / "cache"
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"

# Extensões aceitas
ACCEPTED_EXTENSIONS = {".pdf", ".txt"}

# Limites de cache
MAX_CACHE_SIZE = 100  # Número máximo de análises em cache
CACHE_EXPIRY_HOURS = 24

# Configurações específicas do Gemini
GEMINI_REQUEST_TIMEOUT = 90  # Timeout para requisições Gemini (mais longo)

# Configurações de logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB por arquivo de log
LOG_BACKUP_COUNT = 5  # Número de backups a manter

# Nota: Para resolver erros 504, aumentamos:
# - REQUEST_TIMEOUT: 30s → 60s
# - RETRY_DELAY: 2s → 5s
# - GEMINI_REQUEST_TIMEOUT: 90s (novo)


# ==================== DEPENDÊNCIAS NECESSÁRIAS ====================

# Pacote google-generativeai: mantido aqui para check_dependencies() compatibilidade
REQUIRED_PACKAGES = {
    "streamlit": "streamlit",
    "pymupdf": "fitz",
    "python-dotenv": "dotenv",
    "google-generativeai": "google.generativeai",
}

OPTIONAL_PACKAGES = {
    "requests": "requests",
    "pandas": "pandas",
}


# ==================== FUNÇÕES DE VALIDAÇÃO ====================


def _module_exists(module_name: str) -> bool:
    """
    Verifica se um módulo Python está instalado.

    Args:
        module_name: Nome do módulo a verificar

    Returns:
        True se o módulo existe, False caso contrário

    Example:
        >>> _module_exists("streamlit")
        True
    """
    spec = importlib.util.find_spec(module_name)
    return spec is not None


def check_dependencies(
    raise_error: bool = True, verbose: bool = True
) -> Dict[str, bool]:
    """
    Verifica se todas as bibliotecas necessárias estão instaladas.

    Valida tanto pacotes obrigatórios quanto opcionais. Para pacotes
    obrigatórios, pode gerar um erro se algum estiver faltando.

    Args:
        raise_error: Se True, lança exceção se pacotes obrigatórios
                    faltarem. Default: True
        verbose: Se True, exibe mensagens sobre as dependências.
                Default: True

    Returns:
        Dict mapeando nome do pacote -> bool (instalado ou não)

    Raises:
        ImportError: Se pacotes obrigatórios estão faltando
                    e raise_error=True

    Example:
        >>> deps = check_dependencies(verbose=True)
        >>> if deps.get('streamlit'):
        ...     print("Streamlit está instalado!")
    """
    missing_required = []
    missing_optional = []
    all_status = {}

    # Verificar pacotes obrigatórios
    for package_name, import_name in REQUIRED_PACKAGES.items():
        is_installed = _module_exists(import_name)
        all_status[package_name] = is_installed

        if not is_installed:
            missing_required.append(package_name)
            if verbose:
                print(f"❌ Pacote obrigatório faltando: {package_name}")
        elif verbose:
            print(f"✅ Pacote instalado: {package_name}")

    # Verificar pacotes opcionais
    for package_name, import_name in OPTIONAL_PACKAGES.items():
        is_installed = _module_exists(import_name)
        all_status[f"{package_name} (opcional)"] = is_installed

        if not is_installed and verbose:
            print(f"⚠️  Pacote opcional não instalado: {package_name}")
        elif verbose:
            print(f"✅ Pacote opcional instalado: {package_name}")

    # Gerar erro se necessário
    if missing_required and raise_error:
        missing_str = ", ".join(missing_required)
        raise ImportError(
            f"Pacotes obrigatórios faltando: {missing_str}\n"
            f"Execute: pip install -r requirements.txt"
        )

    if verbose and not missing_required:
        print("\n✅ Todas as dependências obrigatórias estão instaladas!")

    return all_status


def check_api_keys(verbose: bool = True) -> Dict[str, bool]:
    """
    Valida se as chaves de API necessárias estão configuradas.

    Verifica variáveis de ambiente para chaves de API do Gemini e
    outras integrações necessárias.

    Args:
        verbose: Se True, exibe mensagens sobre as chaves de API.
                Default: True

    Returns:
        Dict mapeando nome da chave -> bool (configurada ou não)

    Example:
        >>> keys = check_api_keys()
        >>> if not keys['GEMINI_API_KEY']:
        ...     print("Configure GEMINI_API_KEY no arquivo .env")
    """
    api_keys_status = {}

    # Chaves obrigatórias
    required_keys = ["GEMINI_API_KEY"]

    # Chaves opcionais
    optional_keys = []

    # Verificar chaves obrigatórias
    for key in required_keys:
        is_set = bool(os.getenv(key))
        api_keys_status[key] = is_set

        if not is_set and verbose:
            print(f"❌ Chave de API faltando: {key}")
            print(f"   Configure no arquivo .env: {key}=seu_valor_aqui")
        elif verbose:
            print(f"✅ Chave de API configurada: {key}")

    # Verificar chaves opcionais
    for key in optional_keys:
        is_set = bool(os.getenv(key))
        api_keys_status[f"{key} (opcional)"] = is_set

        if not is_set and verbose:
            print(f"⚠️  Chave de API opcional não configurada: {key}")
        elif verbose:
            print(f"✅ Chave de API opcional configurada: {key}")

    return api_keys_status


def _create_directories() -> None:
    """
    Cria os diretórios necessários da aplicação.

    Cria automaticamente CACHE_DIR, TEMP_DIR e LOGS_DIR se não existirem.
    """
    for directory in [CACHE_DIR, TEMP_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def _validate_directories() -> Dict[str, bool]:
    """
    Valida se todos os diretórios necessários existem e são acessíveis.

    Returns:
        Dict mapeando nome do diretório -> bool (acessível ou não)
    """
    directories = {
        "CACHE_DIR": CACHE_DIR,
        "TEMP_DIR": TEMP_DIR,
        "LOGS_DIR": LOGS_DIR,
    }

    status = {}
    for name, path in directories.items():
        exists = path.exists()
        is_writable = os.access(path, os.W_OK) if exists else False
        status[name] = exists and is_writable

    return status


# ==================== FUNÇÕES DE CARREGAMENTO DE CONFIGURAÇÃO ====================


def load_env_config(
    env_file: Optional[str] = None, validate: bool = True, verbose: bool = True
) -> Dict[str, Any]:
    """
    Carrega e valida todas as variáveis de configuração da aplicação.

    Carrega as configurações do arquivo .env (se existir) e variáveis
    de ambiente, retornando um dicionário com todas as configs centralizadas.

    Args:
        env_file: Caminho para o arquivo .env. Se None, procura por
                 .env no diretório da aplicação. Default: None
        validate: Se True, valida todas as configurações. Default: True
        verbose: Se True, exibe mensagens de carregamento. Default: True

    Returns:
        Dict contendo todas as configurações da aplicação

    Raises:
        ValueError: Se há configurações inválidas e validate=True

    Example:
        >>> config = load_env_config()
        >>> print(config['GEMINI_MODEL'])
        'gemini-2.0-flash'

        >>> config = load_env_config(env_file='/custom/.env', verbose=False)
    """
    from dotenv import load_dotenv

    # Definir caminho do arquivo .env
    if env_file is None:
        env_file = BASE_DIR / ".env"
    else:
        env_file = Path(env_file)

    # Carregar variáveis do arquivo .env
    if env_file.exists():
        load_dotenv(env_file, override=True)
        if verbose:
            print(f"✅ Arquivo .env carregado: {env_file}")
    elif verbose:
        print(f"⚠️  Arquivo .env não encontrado: {env_file}")
        print("   Usando apenas variáveis de ambiente do sistema")

    # Criar diretórios necessários
    _create_directories()

    # Construir dicionário de configuração
    config = {
        # Limites
        "MAX_FILE_SIZE": int(os.getenv("MAX_FILE_SIZE", MAX_FILE_SIZE)),
        "MIN_TEXT_LENGTH": int(os.getenv("MIN_TEXT_LENGTH", MIN_TEXT_LENGTH)),
        # Modelos
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL", GEMINI_MODEL),
        # Timeouts
        "REQUEST_TIMEOUT": int(os.getenv("REQUEST_TIMEOUT", REQUEST_TIMEOUT)),
        "ANALYSIS_TIMEOUT": int(os.getenv("ANALYSIS_TIMEOUT", ANALYSIS_TIMEOUT)),
        # Retries
        "MAX_RETRIES": int(os.getenv("MAX_RETRIES", MAX_RETRIES)),
        "RETRY_DELAY": int(os.getenv("RETRY_DELAY", RETRY_DELAY)),
        # Diretórios
        "CACHE_DIR": Path(os.getenv("CACHE_DIR", CACHE_DIR)),
        "TEMP_DIR": Path(os.getenv("TEMP_DIR", TEMP_DIR)),
        "LOGS_DIR": Path(os.getenv("LOGS_DIR", LOGS_DIR)),
        # API Keys
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        # Log
        "LOG_LEVEL": os.getenv("LOG_LEVEL", LOG_LEVEL),
        # Cache
        "MAX_CACHE_SIZE": int(os.getenv("MAX_CACHE_SIZE", MAX_CACHE_SIZE)),
        "CACHE_EXPIRY_HOURS": int(os.getenv("CACHE_EXPIRY_HOURS", CACHE_EXPIRY_HOURS)),
    }

    # Validar configurações
    if validate:
        _validate_config(config, verbose)

    if verbose:
        print("\n✅ Configurações carregadas com sucesso!")

    return config


def _validate_config(config: Dict[str, Any], verbose: bool = True) -> None:
    """
    Valida as configurações carregadas.

    Verifica se os valores fazem sentido e são válidos.

    Args:
        config: Dicionário de configuração a validar
        verbose: Se True, exibe mensagens de validação

    Raises:
        ValueError: Se há valores inválidos
    """
    errors = []

    # Validar tamanho máximo de arquivo
    if config["MAX_FILE_SIZE"] <= 0:
        errors.append("MAX_FILE_SIZE deve ser maior que 0")

    # Validar comprimento mínimo de texto
    if config["MIN_TEXT_LENGTH"] < 0:
        errors.append("MIN_TEXT_LENGTH não pode ser negativo")

    # Validar timeouts
    if config["REQUEST_TIMEOUT"] <= 0:
        errors.append("REQUEST_TIMEOUT deve ser maior que 0")

    if config["ANALYSIS_TIMEOUT"] <= 0:
        errors.append("ANALYSIS_TIMEOUT deve ser maior que 0")

    # Validar retries
    if config["MAX_RETRIES"] < 0:
        errors.append("MAX_RETRIES não pode ser negativo")

    # Validar cache
    if config["MAX_CACHE_SIZE"] < 0:
        errors.append("MAX_CACHE_SIZE não pode ser negativo")

    # Validar diretórios
    for dir_key in ["CACHE_DIR", "TEMP_DIR", "LOGS_DIR"]:
        if not config[dir_key].exists():
            errors.append(f"{dir_key} não existe: {config[dir_key]}")

    if errors:
        error_msg = "\n".join(f"  • {error}" for error in errors)
        raise ValueError(f"Erros na validação de configuração:\n{error_msg}")

    if verbose:
        print("✅ Configurações validadas com sucesso!")


# ==================== LOGGING ====================


@lru_cache(maxsize=1)
def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    verbose: bool = True,
) -> logging.Logger:
    """
    Configura o sistema de logging estruturado da aplicação no root logger.

    Cria um logger centralizado com saída para arquivo e console.
    Usa RotatingFileHandler para limitar o tamanho dos logs.
    Todos os módulos que usam logging.getLogger(__name__) herdam
    automaticamente esta configuração.

    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  Se None, usa LOG_LEVEL. Default: None
        log_file: Caminho do arquivo de log. Se None, usa LOGS_DIR.
                 Default: None
        verbose: Se True, exibe mensagens de setup. Default: True

    Returns:
        Root logger configurado pronto para uso

    Example:
        >>> logger = setup_logging()
        >>> logger.info("Aplicação iniciada")
    """
    _create_directories()

    if log_level is None:
        log_level = LOG_LEVEL

    log_level = getattr(logging, log_level.upper(), logging.INFO)

    if log_file is None:
        log_file = LOGS_DIR / "contrato_seguro.log"
    else:
        log_file = Path(log_file)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if root_logger.handlers:
        return root_logger

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if verbose:
        root_logger.info(f"Logging configurado - Nível: {logging.getLevelName(log_level)}")
        root_logger.info(f"Arquivo de log: {log_file}")

    return root_logger


# ==================== UTILITÁRIOS COMPARTILHADOS ====================


def compute_hash(texto: str) -> str:
    """
    Calcula o hash SHA256 de um texto, compartilhado por todos os serviços.

    Args:
        texto: Texto a ser hasheado

    Returns:
        Hash SHA256 em formato hexadecimal

    Example:
        >>> compute_hash("contrato de teste")
        'a1b2c3d4...'
    """
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# ==================== SUMMARY E UTILITY ====================


def print_config_summary(config: Dict[str, Any]) -> None:
    """
    Exibe um resumo das configurações carregadas.

    Args:
        config: Dicionário de configuração

    Example:
        >>> config = load_env_config()
        >>> print_config_summary(config)
    """
    print("\n" + "=" * 60)
    print("📋 RESUMO DE CONFIGURAÇÕES")
    print("=" * 60)

    print("\n📊 Limites:")
    print(f"  • MAX_FILE_SIZE: {config['MAX_FILE_SIZE'] / (1024 * 1024):.1f} MB")
    print(f"  • MIN_TEXT_LENGTH: {config['MIN_TEXT_LENGTH']} caracteres")

    print("\n🤖 Modelos:")
    print(f"  • GEMINI_MODEL: {config['GEMINI_MODEL']}")

    print("\n⏱️  Timeouts:")
    print(f"  • REQUEST_TIMEOUT: {config['REQUEST_TIMEOUT']}s")
    print(f"  • ANALYSIS_TIMEOUT: {config['ANALYSIS_TIMEOUT']}s")

    print("\n🔄 Retries:")
    print(f"  • MAX_RETRIES: {config['MAX_RETRIES']}")
    print(f"  • RETRY_DELAY: {config['RETRY_DELAY']}s")

    print("\n📁 Diretórios:")
    print(f"  • CACHE_DIR: {config['CACHE_DIR']}")
    print(f"  • TEMP_DIR: {config['TEMP_DIR']}")
    print(f"  • LOGS_DIR: {config['LOGS_DIR']}")

    print("\n💾 Cache:")
    print(f"  • MAX_CACHE_SIZE: {config['MAX_CACHE_SIZE']} análises")
    print(f"  • CACHE_EXPIRY_HOURS: {config['CACHE_EXPIRY_HOURS']} horas")

    print("\n" + "=" * 60 + "\n")


# ==================== INICIALIZAÇÃO E TESTE ====================

if __name__ == "__main__":
    """
    Script de teste para validar a configuração.

    Execute com:
        python config.py
    """
    print("🔍 Testando Configurações do ContratoSeguro AI\n")

    try:
        # Verificar dependências
        print("1️⃣  Verificando dependências...")
        check_dependencies(verbose=True)
        print()

        # Verificar chaves de API
        print("2️⃣  Verificando chaves de API...")
        api_keys = check_api_keys(verbose=True)
        print()

        # Carregar configurações
        print("3️⃣  Carregando configurações...")
        config = load_env_config(verbose=True)
        print()

        # Configurar logging
        print("4️⃣  Configurando logging...")
        logger = setup_logging(verbose=True)
        print()

        # Exibir resumo
        print_config_summary(config)

        # Teste de logging
        logger.info("✅ Todos os testes passaram com sucesso!")

    except Exception as e:
        print(f"\n❌ Erro durante a inicialização: {str(e)}")
        sys.exit(1)
