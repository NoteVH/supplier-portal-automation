"""
[REDIRECT] Arquivo legado - use main.py

Este arquivo foi mantido apenas para compatibilidade.
A lógica refatorada está em:
  - main.py          (ponto de entrada)
  - src/config.py    (configurações e .env)
  - src/utils.py     (funções utilitárias)
  - src/bot.py       (automação do navegador)
"""

import sys
import subprocess

if __name__ == "__main__":
    print("AVISO: Main.py é o arquivo legado. Executando main.py...\n")
    subprocess.run([sys.executable, "main.py"])