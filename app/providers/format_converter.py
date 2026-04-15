"""
Format converter: transforms various document formats into CSV with guaranteed headers.
Supported: CSV, Excel, TXT, PDF, DOCX

This module expects BINARY file content (bytes), not decoded text.
It extracts clean text from PDFs, DOCX, etc. and converts to CSV.
"""
import io
import csv
import logging
from typing import Tuple, Union

logger = logging.getLogger(__name__)


class FormatConverter:
    """Convert various document formats to CSV with headers."""
    
    @staticmethod
    def _get_file_format(filename: str) -> str:
        """Detect file format from extension."""
        ext = filename.lower().split('.')[-1]
        if ext in ['txt']:
            return 'txt'
        elif ext in ['pdf']:
            return 'pdf'
        elif ext in ['docx', 'doc']:
            return 'docx'
        elif ext in ['xlsx', 'xls']:
            return 'xlsx'
        elif ext in ['csv']:
            return 'csv'
        else:
            return 'txt'  # Default fallback
    
    @staticmethod
    def _has_csv_header(content: Union[str, bytes]) -> bool:
        """Check if CSV content already has a header row."""
        # Decode if bytes
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        
        lines = content.strip().split('\n')
        if not lines:
            return False
        
        # Simple heuristic: if first line looks like headers (no numbers, reasonable length)
        first_line = lines[0]
        reader = csv.reader(io.StringIO(first_line))
        try:
            headers = next(reader)
            # If any header contains only digits, likely not a header
            for h in headers:
                if h.isdigit():
                    return False
            return True
        except:
            return False
    
    @staticmethod
    def convert_to_csv(file_content: Union[str, bytes], filename: str) -> Tuple[str, str]:
        """
        Convert any format to CSV with guaranteed header.
        
        Args:
            file_content: Can be bytes (binary) or str (text). Binary preferred for PDFs/DOCX.
            filename: Original filename for format detection
        
        Returns:
            Tuple of (csv_content: str, original_format: str)
        """
        file_format = FormatConverter._get_file_format(filename)
        logger.info(f"Converting {filename} ({file_format}) to CSV format")
        logger.info(f"Input type: {type(file_content).__name__}, size: {len(file_content)} {'bytes' if isinstance(file_content, bytes) else 'chars'}")
        
        try:
            if file_format == 'csv':
                csv_content = FormatConverter._handle_csv(file_content)
            elif file_format == 'xlsx':
                # Ensure bytes for Excel processing
                if isinstance(file_content, str):
                    logger.warning("Excel file is string, encoding to bytes...")
                    file_content = file_content.encode('utf-8')
                csv_content = FormatConverter._handle_excel(file_content)
            elif file_format == 'pdf':
                csv_content = FormatConverter._handle_pdf(file_content)
            elif file_format == 'docx':
                csv_content = FormatConverter._handle_docx(file_content)
            else:  # txt and default
                csv_content = FormatConverter._handle_text(file_content)
            
            logger.info(f"Successfully converted {filename} to CSV")
            return csv_content, file_format
            
        except Exception as e:
            logger.error(f"Failed to convert {filename} ({file_format}): {type(e).__name__}: {e}")
            logger.warning(f"Falling back to safe text handling")
            try:
                # Try to safely decode and clean
                return FormatConverter._handle_text(file_content), file_format
            except Exception as fallback_error:
                logger.error(f"Even fallback failed: {fallback_error}")
                # Last resort: return a minimal CSV with error message
                return "error\nFailed to process file\n", file_format
    
    @staticmethod
    def _handle_csv(content: Union[str, bytes]) -> str:
        """Handle CSV: validate and ensure header exists."""
        # Decode if bytes
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')
        
        lines = content.strip().split('\n')
        if not lines:
            return "content\n"
        
        # Check if first line is header
        if FormatConverter._has_csv_header(content):
            # Header exists, return as-is
            return content
        else:
            # No header detected, add generic header
            logger.warning("CSV file missing header, adding 'content' header")
            return "content\n" + content
    
    @staticmethod
    def _handle_excel(file_content: Union[str, bytes]) -> str:
        """
        Handle Excel files (.xlsx, .xls).
        Excel is already structured, just convert to CSV preserving headers.
        """
        try:
            import pandas as pd
            from io import BytesIO
            
            logger.info(f"Processing Excel file with pandas...")
            
            # Convert to BytesIO if needed
            if isinstance(file_content, str):
                logger.warning("Excel content is string, encoding to bytes...")
                file_content = file_content.encode('utf-8')
            
            # Ensure file_content is bytes
            if not isinstance(file_content, bytes):
                logger.error(f"Excel content is {type(file_content)}, expected bytes")
                raise RuntimeError(f"Excel content must be bytes, got {type(file_content)}")
            
            logger.info(f"Excel file size: {len(file_content)} bytes")
            
            # Create fresh BytesIO for reading (don't reuse for multiple reads)
            excel_bytes = BytesIO(file_content)
            
            # Try to read all sheets first to see what we have
            try:
                xls = pd.ExcelFile(excel_bytes, engine='openpyxl')
            except ImportError:
                logger.info("openpyxl not available, trying xlrd engine")
                try:
                    excel_bytes = BytesIO(file_content)  # Fresh copy
                    xls = pd.ExcelFile(excel_bytes, engine='xlrd')
                except Exception as e:
                    logger.error(f"Failed with xlrd: {e}")
                    raise RuntimeError(f"Cannot read Excel file - openpyxl or xlrd required: {e}")
            except Exception as e:
                logger.error(f"Failed to read Excel file: {e}")
                raise RuntimeError(f"Invalid Excel file: {e}")
            
            sheet_names = xls.sheet_names
            logger.info(f"Excel sheets found: {sheet_names}")
            
            if not sheet_names:
                logger.error("Excel file has no sheets")
                raise RuntimeError("Excel file has no sheets")
            
            # Read first sheet (or all sheets and concatenate)
            if len(sheet_names) > 1:
                logger.info(f"Multiple sheets found ({len(sheet_names)}), reading all sheets...")
                dfs = []
                for sheet in sheet_names:
                    try:
                        # Create fresh BytesIO for each sheet read
                        excel_bytes = BytesIO(file_content)
                        df = pd.read_excel(excel_bytes, sheet_name=sheet)
                        logger.info(f"  Sheet '{sheet}': {df.shape[0]} rows x {df.shape[1]} cols")
                        dfs.append(df)
                    except Exception as e:
                        logger.warning(f"  Failed to read sheet '{sheet}': {e}")
                        continue
                
                if not dfs:
                    logger.error("Failed to read any sheet from Excel")
                    raise RuntimeError("Could not read any sheet from Excel file")
                
                # Add sheet name as column to distinguish
                for df, sheet_name in zip(dfs, sheet_names[:len(dfs)]):
                    df.insert(0, '_sheet', sheet_name)
                df = pd.concat(dfs, ignore_index=True)
            else:
                logger.info(f"Reading first sheet: {sheet_names[0]}")
                # Create fresh BytesIO for reading
                excel_bytes = BytesIO(file_content)
                df = pd.read_excel(excel_bytes, sheet_name=0)
                logger.info(f"Sheet shape: {df.shape[0]} rows x {df.shape[1]} cols")
            
            # Handle empty dataframe
            if df.empty:
                logger.warning("Excel sheet is empty, creating minimal CSV")
                csv_buffer = io.StringIO()
                csv_buffer.write("content\n")
                csv_buffer.write("(Empty Excel sheet)\n")
                return csv_buffer.getvalue()
            
            logger.info(f"Excel dataframe shape: {df.shape} (rows, cols)")
            logger.info(f"Excel columns: {list(df.columns)}")
            
            # Convert to CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()
            
            logger.info(f"Successfully converted Excel to CSV: {len(csv_content)} chars")
            return csv_content
            
        except ImportError as e:
            logger.error(f"Missing Excel library: {e}")
            raise RuntimeError(f"Excel processing requires pandas with openpyxl or xlrd: {e}")
        except Exception as e:
            logger.error(f"Excel handling failed: {type(e).__name__}: {e}", exc_info=True)
            raise RuntimeError(f"Excel handling failed: {e}")
    
    @staticmethod
    def _handle_pdf(content: Union[str, bytes]) -> str:
        """
        Handle PDF files - extract clean text using pdfplumber if available.
        Falls back to PyPDF2, then to text extraction from bytes.
        """
        # Ensure we have bytes
        if isinstance(content, str):
            content = content.encode('utf-8')
        
        # Try pdfplumber first (best quality)
        try:
            import pdfplumber
            from io import BytesIO
            
            pdf_file = BytesIO(content)
            extracted_text = ""
            
            with pdfplumber.open(pdf_file) as pdf:
                logger.info(f"PDF has {len(pdf.pages)} pages")
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            extracted_text += f"\n--- Page {page_num} ---\n{page_text}"
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num}: {e}")
            
            if extracted_text.strip():
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)
                writer.writerow(["content"])
                writer.writerow([extracted_text.strip()])
                return csv_buffer.getvalue()
            
        except ImportError:
            logger.info("pdfplumber not available, trying PyPDF2")
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
        
        # Try PyPDF2 as fallback
        try:
            import PyPDF2
            from io import BytesIO
            
            pdf_file = BytesIO(content)
            extracted_text = ""
            
            with PyPDF2.PdfReader(pdf_file) as reader:
                for page in reader.pages:
                    try:
                        extracted_text += page.extract_text() + "\n"
                    except Exception as e:
                        logger.warning(f"Failed to extract page text: {e}")
            
            if extracted_text.strip():
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)
                writer.writerow(["content"])
                writer.writerow([extracted_text.strip()])
                return csv_buffer.getvalue()
            
        except ImportError:
            logger.info("PyPDF2 not available")
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")
        
        # Fallback: decode bytes as text (PDFs often have some readable text in binary)
        logger.warning("PDF extraction failed, treating as raw text")
        return FormatConverter._handle_text(content)
    
    @staticmethod
    def _handle_docx(content: Union[str, bytes]) -> str:
        """
        Handle DOCX files - extract paragraphs.
        """
        try:
            from docx import Document
            from io import BytesIO
            
            # Convert to BytesIO if needed
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            docx_file = BytesIO(content)
            doc = Document(docx_file)
            
            # Extract all paragraphs
            extracted_text = ""
            for para in doc.paragraphs:
                if para.text.strip():
                    extracted_text += para.text + "\n"
            
            if not extracted_text.strip():
                logger.warning("DOCX extraction returned empty, falling back to text handling")
                return FormatConverter._handle_text(content)
            
            # Convert to CSV with single "content" column
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(["content"])  # Header
            writer.writerow([extracted_text.strip()])  # Data
            return csv_buffer.getvalue()
            
        except Exception as e:
            logger.warning(f"DOCX extraction failed ({e}), falling back to text handling")
            return FormatConverter._handle_text(content)
    
    @staticmethod
    def _handle_text(content: Union[str, bytes]) -> str:
        """
        Handle plain text files.
        Create single-column CSV with 'content' header.
        Also cleans PDF-like binary garbage if this is a PDF fallback.
        
        IMPORTANT: This is also used as a FALLBACK for failed Excel/PDF processing.
        If we detect Excel/PDF signatures here, it means the primary handler failed.
        We should log this clearly but still attempt to extract something useful.
        """
        # Decode if bytes
        if isinstance(content, bytes):
            # Check for binary file signatures
            if content.startswith(b'PK\x03\x04'):  # ZIP/Excel signature
                logger.error("Detected Excel/ZIP file signature - this means Excel handler failed earlier")
                logger.error("Attempting fallback: will try to extract as ZIP archive")
                
                # Try to extract text from Excel as ZIP archive
                try:
                    import zipfile
                    from io import BytesIO
                    
                    try:
                        with zipfile.ZipFile(BytesIO(content), 'r') as zf:
                            logger.info(f"ZIP archive has {len(zf.namelist())} files")
                            
                            # Excel stores data in xl/worksheets/sheet1.xml, etc
                            extracted_text = ""
                            for filename in zf.namelist():
                                if filename.startswith('xl/worksheets/'):
                                    try:
                                        sheet_content = zf.read(filename).decode('utf-8', errors='ignore')
                                        logger.info(f"Extracted from {filename}: {len(sheet_content)} chars")
                                        extracted_text += f"\n--- From {filename} ---\n{sheet_content}\n"
                                    except Exception as e:
                                        logger.warning(f"Failed to extract {filename}: {e}")
                            
                            if extracted_text.strip():
                                logger.info(f"Successfully extracted {len(extracted_text)} chars from Excel ZIP")
                                # Convert to CSV
                                csv_buffer = io.StringIO()
                                writer = csv.writer(csv_buffer)
                                writer.writerow(["content"])
                                writer.writerow([extracted_text.strip()])
                                return csv_buffer.getvalue()
                            else:
                                logger.warning("No worksheet content found in ZIP")
                    except zipfile.BadZipFile:
                        logger.error("File claims to be ZIP but is not a valid ZIP archive")
                except Exception as e:
                    logger.error(f"ZIP fallback extraction failed: {e}")
                
                logger.error("All Excel/ZIP extraction methods failed, returning error message")
                return "error\nFile is a ZIP/Excel file but could not be processed as Excel\n"
            
            if content.startswith(b'%PDF'):  # PDF signature
                logger.warning("Detected PDF signature but extraction failed earlier")
            
            content = content.decode('utf-8', errors='ignore')
        
        # Check for suspicious content (too many non-ASCII or binary-like chars)
        non_text_count = sum(1 for c in content if ord(c) < 32 and c not in '\n\r\t')
        if non_text_count > len(content) * 0.3:  # More than 30% control chars
            logger.warning(f"Content has {non_text_count} ({100*non_text_count/len(content):.1f}%) non-text characters")
            logger.warning("This looks like binary content that wasn't properly decoded")
            return "error\nFile appears to contain binary data that cannot be read as text\n"
        
        # Clean PDF binary garbage (if this is a PDF that failed extraction)
        # Remove: %PDF markers, obj/endobj, stream markers, xref, trailer, etc
        import re
        if '%PDF' in content or 'endstream' in content or 'stream' in content:
            logger.warning("Detected PDF content in text fallback, removing PDF structure markers")
            # Remove PDF structure markers
            content = re.sub(r'%[^\n]*', '', content)  # Remove % comments
            content = re.sub(r'\d+ \d+ obj\n', '', content)  # Remove object markers
            content = re.sub(r'endobj\n', '', content)  # Remove endobj
            content = re.sub(r'stream\n.*?endstream', '', content, flags=re.DOTALL)  # Remove stream blocks
            content = re.sub(r'xref\n.*?trailer', '', content, flags=re.DOTALL)  # Remove xref/trailer
            content = re.sub(r'<<[^>]*>>', '', content)  # Remove PDF dictionaries
            content = re.sub(r'startxref.*', '', content, flags=re.DOTALL)  # Remove xref offset
        
        # Escape any CSV special characters
        lines = content.strip().split('\n')
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['content'])
        
        # Write each line as a row
        for line in lines:
            line = line.strip()
            if line:  # Only write non-empty lines
                writer.writerow([line])
        
        return output.getvalue()
