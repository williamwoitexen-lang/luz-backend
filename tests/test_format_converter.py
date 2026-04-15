#!/usr/bin/env python3
"""
Test format_converter.py to verify text extraction works correctly
"""
import sys
import os
sys.path.insert(0, '/workspaces/Embeddings')

from app.providers.format_converter import FormatConverter

def test_text_handling():
    """Test plain text handling"""
    print("\n" + "="*60)
    print("TEST 1: Plain text handling")
    print("="*60)
    
    # Test with string
    text_str = "Benefícios de Saúde\nSão Carlos, SP\nAçúcar 123"
    print(f"Input (string): {repr(text_str)}")
    result = FormatConverter._handle_text(text_str)
    print(f"Output:\n{result}")
    
    # Test with bytes
    text_bytes = "Benefícios de Saúde\nSão Carlos, SP\nAçúcar 123".encode('utf-8')
    print(f"\nInput (bytes): {repr(text_bytes[:50])}...")
    result = FormatConverter._handle_text(text_bytes)
    print(f"Output:\n{result}")


def test_csv_handling():
    """Test CSV handling"""
    print("\n" + "="*60)
    print("TEST 2: CSV handling")
    print("="*60)
    
    # CSV with header
    csv_with_header = "Name,Value\nJohn,100\nJane,200"
    print(f"Input (with header): {repr(csv_with_header)}")
    result = FormatConverter._handle_csv(csv_with_header)
    print(f"Output:\n{result}")
    
    # CSV without header
    csv_no_header = "100,200,300\n400,500,600"
    print(f"\nInput (no header): {repr(csv_no_header)}")
    result = FormatConverter._handle_csv(csv_no_header)
    print(f"Output:\n{result}")


def test_has_csv_header():
    """Test CSV header detection"""
    print("\n" + "="*60)
    print("TEST 3: CSV header detection")
    print("="*60)
    
    cases = [
        ("Name,Age,City", True, "header-like"),
        ("100,200,300", False, "data"),
        ("id,name", True, "header"),
        ("1,2,3", False, "numeric"),
    ]
    
    for content, expected, desc in cases:
        result = FormatConverter._has_csv_header(content)
        status = "OK" if result == expected else "FAIL"
        print(f"{status} '{content}' ({desc}): {result} (expected {expected})")


def test_text_cleaning():
    """Test text cleaning with accents and metadata"""
    print("\n" + "="*60)
    print("TEST 4: Text cleaning (DocumentService)")
    print("="*60)
    
    from app.services.document_service import DocumentService
    
    test_cases = [
        ("Benefícios de Saúde", "Portuguese accents preserved"),
        ("São Paulo - SP", "City name with tilde"),
        ("Açúcar e Café", "Multiple accents"),
        ("<xmp:Creator>Tool</xmp:Creator>Content", "XML metadata removal"),
        ("uuid:12345678-1234-1234-1234-123456789012 real text", "UUID removal"),
    ]
    
    for text, description in test_cases:
        cleaned = DocumentService._clean_text_content(text)
        print(f"\n{description}")
        print(f"   Input:  {repr(text)}")
        print(f"   Output: {repr(cleaned)}")


def test_convert_to_csv_with_string():
    """Test convert_to_csv with different inputs"""
    print("\n" + "="*60)
    print("TEST 5: convert_to_csv with strings")
    print("="*60)
    
    # Test with plain text
    text_content = "Linha 1: Benefícios\nLinha 2: Saúde\nLinha 3: São Paulo"
    csv_result, format_type = FormatConverter.convert_to_csv(text_content, "test.txt")
    print(f"File: test.txt (detected as {format_type})")
    print(f"Input: {repr(text_content)}")
    print(f"Output:\n{csv_result}")
    
    # Test with CSV content
    csv_content = "ID,Name,City\n1,João,São Paulo\n2,Maria,Brasília"
    csv_result, format_type = FormatConverter.convert_to_csv(csv_content, "test.csv")
    print(f"\nFile: test.csv (detected as {format_type})")
    print(f"Input: {repr(csv_content[:50])}...")
    print(f"Output:\n{csv_result}")


def test_unicode_handling():
    """Test Unicode characters handling"""
    print("\n" + "="*60)
    print("TEST 6: Unicode handling")
    print("="*60)
    
    unicode_texts = [
        ("português: açúcar, café, pão", "Portuguese"),
        ("español: mañana, señor, ñoño", "Spanish"),
        ("Special chars: €, ©, ®, ™", "Special symbols"),
        ("Math: °, §, ¶", "Math symbols"),
    ]
    
    for text, desc in unicode_texts:
        result = FormatConverter._handle_text(text)
        lines = result.strip().split('\n')
        data_line = lines[1] if len(lines) > 1 else "NO DATA"
        print(f"\n{desc}:")
        print(f"  Input:  {repr(text)}")
        print(f"  Output data: {repr(data_line)}")


if __name__ == "__main__":
    test_text_handling()
    test_csv_handling()
    test_has_csv_header()
    test_text_cleaning()
    test_convert_to_csv_with_string()
    test_unicode_handling()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)
