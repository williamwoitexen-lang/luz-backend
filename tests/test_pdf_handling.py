#!/usr/bin/env python3
"""
Test PDF extraction with actual PDF-like binary content
"""
import sys
sys.path.insert(0, '/workspaces/Embeddings')

from app.providers.format_converter import FormatConverter

def test_pdf_like_binary():
    """Test handling of PDF-like binary content (with metadata noise)"""
    print("\n" + "="*60)
    print("TEST: PDF-like binary content with metadata")
    print("="*60)
    
    # Simular conteúdo PDF com ruído binário e texto legível
    pdf_like_content = b"""
%PDF-1.7
%\xE2\xE3\xCF\xD3
1 0 obj
<</Type/Catalog/Pages 2 0 R>>
endobj
2 0 obj
<</Type/Pages/Count 1/Kids[3 0 R]>>
endobj
3 0 obj
<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]
/Contents 4 0 R>>
endobj
4 0 obj
<</Length 500>>
stream
BT
/F1 12 Tf
100 700 Td
(Benef\xFCcios de Sa\xFAde) Tj
0 -20 Td
(S\xE3o Carlos - SP) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000200 00000 n 
trailer
<</Size 5/Root 1 0 R>>
startxref
500
%%EOF
"""
    
    print(f"Input size: {len(pdf_like_content)} bytes (simulated PDF with binary noise)")
    print(f"Input preview: {repr(pdf_like_content[:100])}...")
    
    try:
        result = FormatConverter._handle_pdf(pdf_like_content)
        lines = result.strip().split('\n')
        print(f"\nConversion successful!")
        print(f"Output lines: {len(lines)}")
        print(f"Output:\n{result}")
    except Exception as e:
        print(f"Error: {e}")


def test_text_from_pdf_extraction():
    """Test what happens when PDF extraction falls back to text"""
    print("\n" + "="*60)
    print("TEST: PDF fallback to text extraction")
    print("="*60)
    
    # Simular texto extraído de PDF (com metadata)
    pdf_text_content = """
%PDF-1.7
/Creator (Microsoft Word)
/Producer (Adobe)
/Author (John Doe)

Conteúdo do documento:

Benefícios de Saúde
São Carlos, SP

Texto importante aqui!

uuid:12345678-90ab-cdef-1234-567890abcdef

Mais conteúdo...
""".encode('utf-8')
    
    print(f"Input size: {len(pdf_text_content)} bytes")
    print(f"Input preview:\n{pdf_text_content.decode('utf-8')[:200]}...")
    
    try:
        result = FormatConverter._handle_pdf(pdf_text_content)
        print(f"\nConversion successful!")
        print(f"Output:\n{result}")
    except Exception as e:
        print(f"Error: {e}")


def test_bytes_vs_string():
    """Test that both bytes and string inputs work"""
    print("\n" + "="*60)
    print("TEST: Bytes vs String input handling")
    print("="*60)
    
    text_content = "Benefícios de Saúde\nSão Carlos"
    
    # Test with string
    print("Testing with STRING input:")
    try:
        result_str = FormatConverter.convert_to_csv(text_content, "test.txt")
        print(f"String input: Success")
        print(f"   Output lines: {len(result_str[0].strip().split(chr(10)))}")
    except Exception as e:
        print(f"String input failed: {e}")
    
    # Test with bytes
    print("\nTesting with BYTES input:")
    try:
        result_bytes = FormatConverter.convert_to_csv(text_content.encode('utf-8'), "test.txt")
        print(f"Bytes input: Success")
        print(f"   Output lines: {len(result_bytes[0].strip().split(chr(10)))}")
    except Exception as e:
        print(f"Bytes input failed: {e}")


if __name__ == "__main__":
    test_pdf_like_binary()
    test_text_from_pdf_extraction()
    test_bytes_vs_string()
    
    print("\n" + "="*60)
    print("PDF-LIKE TESTS COMPLETED")
    print("="*60)
