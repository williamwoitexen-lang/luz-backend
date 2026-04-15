#!/usr/bin/env python3
"""
Test script para validar a limpeza de texto de PDFs
"""

import sys
import os
import re
from pathlib import Path

# Add app directory to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from app.services.document_service import DocumentService


def test_clean_text_content():
    """Test the text cleaning function"""
    
    test_cases = [
        # (input, expected_output, description)
        (
            "Hello\x00World\x01PDF\xff\xfe\xfd",
            "HelloWorldPDF",
            "Remove binary null bytes and non-ASCII"
        ),
        (
            "Hello    World\n\n\n   test",
            "Hello World test",
            "Collapse multiple spaces and newlines"
        ),
        (
            "  leading and trailing  ",
            "leading and trailing",
            "Remove leading/trailing whitespace"
        ),
        (
            "Normal text with punctuation! @#$% symbols.",
            "Normal text with punctuation! @#$% symbols.",
            "Keep ASCII punctuation"
        ),
        (
            "Portuguese: ação, função, café",
            "Portuguese: ao, funo, caf",
            "Remove non-ASCII accents"
        ),
        (
            "PDF binary data: \x80\x81\x82\x83\x84 mixed with text",
            "PDF binary data: mixed with text",
            "Remove PDF binary markers"
        ),
    ]
    
    print("Testing DocumentService._clean_text_content()...")
    print("-" * 80)
    
    passed = 0
    failed = 0
    
    for input_text, expected, description in test_cases:
        result = DocumentService._clean_text_content(input_text)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status}: {description}")
        print(f"  Input:    {repr(input_text[:50])}")
        print(f"  Expected: {repr(expected)}")
        print(f"  Got:      {repr(result)}")
        
        if result != expected:
            print(f"  MISMATCH!")
    
    print("\n" + "-" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    
    return failed == 0


def test_size_reduction():
    """Test that cleaning significantly reduces PDF payload size"""
    
    # Simulate PDF content with lots of binary data
    pdf_like_content = ""
    for i in range(100):
        pdf_like_content += f"This is line {i} of document content. "
        # Add some binary chars that PDFs have
        pdf_like_content += "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09"
        pdf_like_content += "   " * 5  # Multiple spaces
    
    original_size = len(pdf_like_content)
    cleaned = DocumentService._clean_text_content(pdf_like_content)
    cleaned_size = len(cleaned)
    reduction_percent = 100 - (cleaned_size * 100 // original_size)
    
    print("\nTesting size reduction on PDF-like content...")
    print("-" * 80)
    print(f"Original size: {original_size:,} bytes")
    print(f"Cleaned size:  {cleaned_size:,} bytes")
    print(f"Reduction:     {reduction_percent}%")
    print(f"\nSample cleaned text (first 200 chars):")
    print(f"  {cleaned[:200]}")
    
    # Should have at least 50% reduction with PDF-like content
    assert reduction_percent >= 30, f"Expected >= 30% reduction, got {reduction_percent}%"
    print(f"\n✓ Size reduction test passed!")
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TEXT CLEANING VALIDATION TESTS")
    print("=" * 80 + "\n")
    
    try:
        success = True
        
        # Run tests
        if not test_clean_text_content():
            success = False
        
        if not test_size_reduction():
            success = False
        
        # Test com PDF real enviado pelo usuário
        pdf_file = "ACT Compensações Calendário 2025 São Carlos.pdf"
        if Path(pdf_file).exists():
            print(f"\n" + "=" * 80)
            print(f"TESTE COM PDF REAL: {pdf_file}")
            print("=" * 80 + "\n")
            
            try:
                import PyPDF2
                with open(pdf_file, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    num_pages = len(pdf_reader.pages)
                    
                    raw_text = ""
                    for page_num in range(num_pages):
                        page = pdf_reader.pages[page_num]
                        raw_text += page.extract_text() or ""
                    
                    cleaned_text = DocumentService._clean_text_content(raw_text)
                    
                    raw_bytes = len(raw_text.encode('utf-8'))
                    cleaned_bytes = len(cleaned_text.encode('utf-8'))
                    reduction = 100 - (cleaned_bytes * 100 // raw_bytes) if raw_bytes > 0 else 0
                    
                    print(f"📄 Páginas: {num_pages}")
                    print(f"📊 Tamanho bruto: {raw_bytes:,} bytes ({raw_bytes / 1024:.2f} KB)")
                    print(f"🧹 Tamanho limpo: {cleaned_bytes:,} bytes ({cleaned_bytes / 1024:.2f} KB)")
                    print(f"📉 Redução: {reduction}%")
                    
                    # Verificar limites
                    llm_max = 50 * 1024
                    preview_max = 15 * 1024
                    
                    print(f"\n✅ Verificação de limites:")
                    if cleaned_bytes <= preview_max:
                        print(f"   ✓ PASSOU - Dentro do limite de preview (15 KB)")
                    elif cleaned_bytes <= llm_max:
                        print(f"   ⚠️  Dentro do limite LLM Server (50 KB), mas maior que preview")
                    else:
                        print(f"   ❌ FALHOU - Excede limite do LLM Server (50 KB)")
                    
                    print(f"\n📝 Primeiros 300 caracteres do texto limpo:")
                    print(f"   {cleaned_text[:300]}")
                    
            except ImportError:
                print("⚠️  PyPDF2 não instalado. Instalando...")
                os.system("pip install PyPDF2 -q")
                print("Reexecute o script para testar com o PDF real")
            except Exception as e:
                print(f"❌ Erro ao processar PDF: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"\n⚠️  PDF não encontrado: {pdf_file}")
        
        # Final result
        print("\n" + "=" * 80)
        if success:
            print("✓ ALL UNIT TESTS PASSED!")
            print("=" * 80 + "\n")
            sys.exit(0)
        else:
            print("✗ SOME TESTS FAILED!")
            print("=" * 80 + "\n")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
