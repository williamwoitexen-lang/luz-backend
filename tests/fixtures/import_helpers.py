"""
Helpers para corrigir imports em testes
Adiciona automaticamente o path correto
"""

import sys
import os
from pathlib import Path

# Adicionar raiz do projeto ao path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Adicionar pasta app
sys.path.insert(0, str(PROJECT_ROOT / "app"))

print(f"✓ Project root added to path: {PROJECT_ROOT}")
