#!/usr/bin/env python
"""
Runner para todos os testes do ContratoSeguro IA.
Executa: python run_tests.py
"""
import subprocess
import sys
from pathlib import Path

TEST_DIR = Path(__file__).parent / "tests"

TEST_FILES = [
    "test_config.py",
    "test_services.py",
    "test_auth_service.py",
    "test_database_service.py",
    "test_report_service.py",
    "test_tabs.py",
    "test_notification.py",
    "test_pdf_extractor.py",
    "test_run_app.py",
]

def run():
    failed = []
    passed = []
    total = 0

    for test_file in TEST_FILES:
        path = TEST_DIR / test_file
        if not path.exists():
            print(f"[SKIP] {test_file} - arquivo nao encontrado")
            continue

        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent),
        )

        lines = result.stdout.strip().split("\n")
        test_count = len([l for l in lines if "passaram!" in l.lower()]) or 1

        if result.returncode == 0:
            passed.append(test_file)
            total += test_count
            print(f"[PASS] {test_file}")
        else:
            failed.append(test_file)
            print(f"[FAIL] {test_file}")
            print(f"  stdout: {result.stdout[-200:]}")
            print(f"  stderr: {result.stderr[-200:]}")

    print(f"\n{'='*50}")
    print(f"Resultado: {len(passed)} passaram, {len(failed)} falharam")
    print(f"Arquivos: {', '.join(passed)}")
    if failed:
        print(f"Falhas: {', '.join(failed)}")
    print(f"{'='*50}")

    return len(failed) == 0


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
