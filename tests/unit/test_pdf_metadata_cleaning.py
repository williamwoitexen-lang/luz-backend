#!/usr/bin/env python3
"""
Teste para validar limpeza de metadados XML de PDF
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from app.services.document_service import DocumentService


def test_xml_metadata_removal():
    """Testa remoção de metadata XML de PDF"""
    
    # Exemplo real do problema reportado
    pdf_metadata = '''eator>" "" Microsoft® Word for Microsoft 365
<rdf:Description rdf:about=""  xmlns:xmp="http://ns.adobe.com/xap/1.0/">
<xmp:CreatorTool>Microsoft® Word for Microsoft 365</xmp:CreatorTool>
<xmp:CreateDate>2025-03-26T14:32:56-03:00</xmp:CreateDate>
<xmp:ModifyDate>2025-03-26T14:32:56-03:00</xmp:ModifyDate>
</rdf:Description>
<rdf:Description rdf:about=""  xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/">
<xmpMM:DocumentID>uuid:2CD71D8B-11A5-4005-8F29-7B3F109453CD</xmpMM:DocumentID>
</rdf:Description>
Benefícios de Saúde - São Carlos
CLÁUSULA DÉCIMA SEGUNDA
Compensações - Ação Judicial
'''
    
    cleaned = DocumentService._clean_text_content(pdf_metadata)
    
    print("\n" + "="*80)
    print("TESTE: Remoção de Metadata XML de PDF")
    print("="*80)
    
    print("\n📝 Input (original com metadata):")
    print(pdf_metadata[:200] + "...\n")
    
    print("🧹 Output (após limpeza):")
    print(cleaned)
    print()
    
    # Validações
    tests = [
        ("Preserva 'Benefícios'", "Benefícios" in cleaned),
        ("Preserva 'São Carlos'", "São Carlos" in cleaned),
        ("Preserva 'CLÁUSULA DÉCIMA SEGUNDA'", "CLÁUSULA DÉCIMA SEGUNDA" in cleaned),
        ("Remove tags XML", "<rdf:" not in cleaned and "<xmp:" not in cleaned),
        ("Remove UUIDs", "2CD71D8B-11A5-4005-8F29" not in cleaned),
        ("Remove timestamps", "2025-03-26T14:32:56" not in cleaned),
        ("Remove xmlns", "xmlns:" not in cleaned),
    ]
    
    all_passed = True
    for desc, result in tests:
        status = "✓" if result else "✗"
        print(f"{status} {desc}")
        if not result:
            all_passed = False
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ TODOS OS TESTES PASSARAM!")
        return 0
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        return 1


if __name__ == "__main__":
    exit(test_xml_metadata_removal())
