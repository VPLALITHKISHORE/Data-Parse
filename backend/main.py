from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import time
import xml.etree.ElementTree as ET
import statistics
import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
import traceback
from datetime import datetime

app = FastAPI(title="Multi-File Processor API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

def get_timestamp():
    """Get current timestamp as string"""
    return time.strftime('%Y-%m-%d %H:%M:%S')

def get_file_id():
    """Generate unique file ID"""
    return f"file_{int(time.time())}_{hash(time.time()) % 10000}"

def clean_for_json(obj):
    """Recursively clean any object to make it JSON serializable"""
    if obj is None:
        return None
    elif isinstance(obj, (datetime,)):
        return obj.isoformat()
    elif isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64)):
        if np.isnan(obj) or np.isinf(obj):
            return None  # Convert NaN/inf to null
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (int, float, str, bool)):
        if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
            return None
        return obj
    elif isinstance(obj, dict):
        return {str(k): clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [clean_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return clean_for_json(obj.__dict__)
    else:
        return str(obj)

async def save_uploaded_file(file: UploadFile, prefix: str = "") -> dict:
    """Save uploaded file to data directory"""
    try:
        # Generate unique filename to avoid conflicts
        timestamp = int(time.time())
        original_name = file.filename
        file_extension = original_name.split('.')[-1].lower()
        unique_filename = f"{prefix}_{timestamp}_{original_name}" if prefix else f"{timestamp}_{original_name}"
        file_path = data_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "success": True,
            "original_name": original_name,
            "saved_path": str(file_path),
            "saved_filename": unique_filename,
            "file_size": len(content),
            "file_extension": file_extension
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "original_name": file.filename if file else "unknown"
        }

def process_csv_with_master_data(csv_file_path: str, json_file_path: str) -> dict:
    """Enhanced CSV processing with smart NaN handling and master data integration"""
    start_time = time.time()
    current_timestamp = get_timestamp()
    
    try:
        print(f"[{current_timestamp}] Processing CSV with enhanced NaN handling: {csv_file_path}")
        print(f"[{current_timestamp}] Processing JSON: {json_file_path}")
        
        # Enhanced constraints for retail transaction data
        CONSTRAINTS_BY_NAME = {
            "transaction_id": {"type": "non_empty", "nullable": False},
            "customer_id": {"type": "non_empty", "nullable": False},
            "date": {"type": "date", "nullable": True},  # Allow nullable for NaN handling
            "amount": {"type": "float", "min": 0, "nullable": True},  # Allow nullable for NaN handling
            "total_amount": {"type": "float", "min": 0, "nullable": False},
            "age": {"type": "int", "min": 0, "max": 120, "nullable": True},
            "email": {"type": "pattern", "pattern": r"^[^@]+@[^@]+\.[^@]+$", "nullable": True, "lower": True},
            "phone": {"type": "pattern", "pattern": r"^\+?\d{7,15}$", "nullable": True},
            "ratings": {"type": "int", "min": 1, "max": 5, "nullable": True},
            "total_purchases": {"type": "int", "min": 1, "nullable": True},
            "year": {"type": "int", "min": 2000, "max": 2030, "nullable": True},
        }
        
        MISSING_VALUES = set(["", "na", "n/a", "null", "none", None, "nan", "NaN"])

        def is_missing_or_nan(v):
            """Enhanced missing value detection including NaN"""
            if v is None:
                return True
            if pd.isna(v):  # Handle pandas NaN
                return True
            try:
                s = str(v).strip().lower()
            except Exception:
                return True
            if s == "" or s in MISSING_VALUES:
                return True
            return False

        def smart_nan_handling(row_dict):
            """Smart NaN handling with fallbacks"""
            cleaned = {}
            fixes_applied = []
            
            for col, val in row_dict.items():
                if is_missing_or_nan(val):
                    # Smart fallbacks for critical fields
                    if col == "amount" and "total_amount" in row_dict and not is_missing_or_nan(row_dict["total_amount"]):
                        # If amount is NaN but total_amount exists, try to derive
                        try:
                            total_purchases = int(row_dict.get("total_purchases", 1))
                            total_amount = float(row_dict["total_amount"])
                            cleaned[col] = round(total_amount / total_purchases, 2)
                            fixes_applied.append(f"Derived {col} from total_amount")
                        except:
                            cleaned[col] = None
                    elif col == "date" and "year" in row_dict and "month" in row_dict:
                        # If date is NaN but year/month exist, create approximate date
                        try:
                            year = str(row_dict.get("year", "2023"))
                            month = str(row_dict.get("month", "January"))
                            month_map = {
                                "january": "01", "february": "02", "march": "03", "april": "04",
                                "may": "05", "june": "06", "july": "07", "august": "08",
                                "september": "09", "october": "10", "november": "11", "december": "12"
                            }
                            month_num = month_map.get(month.lower(), "01")
                            cleaned[col] = f"{year}-{month_num}-01"  # First day of month
                            fixes_applied.append(f"Derived {col} from year/month")
                        except:
                            cleaned[col] = None
                    else:
                        cleaned[col] = None
                else:
                    cleaned[col] = val
            
            return cleaned, fixes_applied

        def validate_and_normalize_row_enhanced(row_dict, constraints_map):
            """Enhanced validation with smart NaN handling"""
            # First apply smart NaN handling
            row_dict, smart_fixes = smart_nan_handling(row_dict)
            
            errors = []
            normalized = {}
            
            for col, raw in row_dict.items():
                conf = constraints_map.get(col, {"type":"any","nullable":True})
                ctype = conf.get("type", "any")
                nullable = conf.get("nullable", True)

                if is_missing_or_nan(raw):
                    if not nullable:
                        errors.append(f"{col}: missing but not nullable")
                    else:
                        normalized[col] = None
                    continue

                s = str(raw).strip()
                try:
                    if ctype == "int":
                        val = int(float(s))  # Handle string numbers
                        if "min" in conf and val < conf["min"]:
                            raise ValueError(f"{val} < min({conf['min']})")
                        if "max" in conf and val > conf["max"]:
                            raise ValueError(f"{val} > max({conf['max']})")
                        normalized[col] = val

                    elif ctype == "float":
                        val = float(s)
                        if "min" in conf and val < conf["min"]:
                            raise ValueError(f"{val} < min({conf['min']})")
                        if "max" in conf and val > conf["max"]:
                            raise ValueError(f"{val} > max({conf['max']})")
                        normalized[col] = val

                    elif ctype == "pattern":
                        pattern = conf.get("pattern")
                        value_for_check = s.lower() if conf.get("lower", False) else s
                        if not pattern:
                            raise ValueError("no pattern provided")
                        if not re.fullmatch(pattern, value_for_check):
                            raise ValueError("pattern mismatch")
                        normalized[col] = value_for_check

                    elif ctype == "date":
                        # Enhanced date parsing
                        allowed_formats = ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d"]
                        parsed = None
                        for fmt in allowed_formats:
                            try:
                                parsed = datetime.strptime(s, fmt)
                                break
                            except:
                                continue
                        
                        if parsed:
                            normalized[col] = parsed.strftime("%Y-%m-%d")
                        else:
                            raise ValueError(f"invalid date format: {s}")

                    elif ctype == "non_empty":
                        if s == "":
                            raise ValueError("empty string")
                        normalized[col] = s

                    else:
                        normalized[col] = s

                except Exception as e:
                    errors.append(f"{col}: {str(e)}")
                    # For non-critical errors, still include the original value
                    normalized[col] = raw

            valid = len(errors) == 0
            return valid, normalized, errors, smart_fixes

        # Check if files exist
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"JSON master file not found: {json_file_path}")

        # Load master data
        print(f"[{current_timestamp}] Loading master data...")
        with open(json_file_path, "r", encoding="utf-8") as mf:
            master_data = json.load(mf)
        
        print(f"[{current_timestamp}] Master data loaded: {len(master_data)} records")
        
        # Initialize processing variables
        merged_data = list(master_data)  # Start with master data
        error_entries = []
        stats = {
            "total_rows_seen": 0,
            "rows_kept": 0,
            "rows_removed": 0,
            "rows_with_smart_fixes": 0,
            "rows_with_minor_errors": 0,
            "removed_reasons": {},
            "master_records": len(master_data)
        }

        # Process CSV with enhanced handling
        print(f"[{current_timestamp}] Processing CSV file...")
        try:
            df = pd.read_csv(csv_file_path, dtype=str, keep_default_na=True)  # Keep NaN as NaN
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
            print(f"[{current_timestamp}] CSV loaded: {len(df)} rows, {len(df.columns)} columns")
            
            for idx, row in df.iterrows():
                stats["total_rows_seen"] += 1
                row_dict = row.to_dict()
                
                # Check if smart fixes were applied
                original_nulls = sum(1 for v in row_dict.values() if is_missing_or_nan(v))
                
                valid, normalized_row, errors, smart_fixes = validate_and_normalize_row_enhanced(row_dict, CONSTRAINTS_BY_NAME)
                
                # Check if smart fixes reduced nulls
                processed_nulls = sum(1 for v in normalized_row.values() if v is None)
                has_smart_fixes = len(smart_fixes) > 0
                
                if has_smart_fixes:
                    stats["rows_with_smart_fixes"] += 1

                # Add metadata
                normalized_row.update({
                    "_processed_at": current_timestamp,
                    "_source": "csv_enhanced_processing",
                    "_row_number": idx + 1,
                    "_smart_fixes_applied": has_smart_fixes
                })
                
                if smart_fixes:
                    normalized_row["_smart_fixes"] = smart_fixes

                # Allow records with minor errors (<=2 errors) to pass
                if valid or (len(errors) <= 2 and len(errors) > 0):
                    stats["rows_kept"] += 1
                    if errors:
                        normalized_row["_minor_errors"] = errors
                        normalized_row["_error_count"] = len(errors)
                        stats["rows_with_minor_errors"] += 1
                    merged_data.append(normalized_row)
                else:
                    stats["rows_removed"] += 1
                    for e in errors:
                        stats["removed_reasons"][e] = stats["removed_reasons"].get(e, 0) + 1
                    
                    normalized_row.update({
                        "_errors": errors,
                        "_error_count": len(errors)
                    })
                    error_entries.append({
                        "row_number": idx + 1,
                        "errors": errors,
                        "original_row": normalized_row
                    })

        except Exception as csv_error:
            raise Exception(f"CSV processing failed: {csv_error}")

        processing_time = time.time() - start_time
        success_rate = (stats["rows_kept"] / stats["total_rows_seen"] * 100) if stats["total_rows_seen"] > 0 else 0
        
        print(f"[{current_timestamp}] Enhanced CSV processing completed:")
        print(f"[{current_timestamp}] - Total CSV rows: {stats['total_rows_seen']}")
        print(f"[{current_timestamp}] - Kept rows: {stats['rows_kept']}")
        print(f"[{current_timestamp}] - Error rows: {stats['rows_removed']}")
        print(f"[{current_timestamp}] - Smart fixes applied: {stats['rows_with_smart_fixes']}")
        print(f"[{current_timestamp}] - Minor errors fixed: {stats['rows_with_minor_errors']}")
        print(f"[{current_timestamp}] - Master records: {stats['master_records']}")
        print(f"[{current_timestamp}] - Total merged records: {len(merged_data)}")
        print(f"[{current_timestamp}] - Success rate: {success_rate:.2f}%")

        return {
            "success": True,
            "merged_data": merged_data,
            "clean_data": [r for r in merged_data if not r.get('_errors')],
            "error_data": [entry["original_row"] for entry in error_entries],
            "processing_time": f"{processing_time:.2f}s",
            "total_csv_rows": stats["total_rows_seen"],
            "total_rows": stats["total_rows_seen"],
            "clean_count": stats["rows_kept"],
            "error_count": stats["rows_removed"],
            "smart_fixes_applied": stats["rows_with_smart_fixes"],
            "minor_errors_fixed": stats["rows_with_minor_errors"],
            "master_records_count": stats["master_records"],
            "total_merged_count": len(merged_data),
            "success_rate": round(success_rate, 2),
            "validation_stats": stats,
            "constraints_used": CONSTRAINTS_BY_NAME,
            "file_info": {
                "csv_file": os.path.basename(csv_file_path),
                "master_file": os.path.basename(json_file_path),
                "processing_mode": "enhanced_with_master_data"
            }
        }
        
    except Exception as e:
        print(f"[{current_timestamp}] Error in enhanced CSV processing: {e}")
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "merged_data": [],
            "error_data": [{
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": current_timestamp
            }],
            "processing_time": f"{time.time() - start_time:.2f}s",
            "success_rate": 0,
            "total_csv_rows": 0,
            "clean_count": 0,
            "error_count": 1
        }

def process_csv_standalone(csv_file_path: str) -> dict:
    """Process CSV file standalone without master data"""
    start_time = time.time()
    current_timestamp = get_timestamp()
    
    try:
        print(f"[{current_timestamp}] Processing CSV standalone: {csv_file_path}")
        
        # Basic constraints for standalone processing
        BASIC_CONSTRAINTS = {
            "age": {"type": "int", "min": 0, "max": 120, "nullable": True},
            "amount": {"type": "float", "min": 0, "nullable": True},
            "price": {"type": "float", "min": 0, "nullable": True},
            "total": {"type": "float", "min": 0, "nullable": True},
            "total_amount": {"type": "float", "min": 0, "nullable": True},
            "ratings": {"type": "int", "min": 1, "max": 5, "nullable": True},
        }
        
        MISSING_VALUES = set(["", "na", "n/a", "null", "none", None, "nan", "NaN"])

        def is_missing(v):
            if v is None:
                return True
            if pd.isna(v):
                return True
            try:
                s = str(v).strip()
            except Exception:
                return False
            if s == "":
                return True
            return s.lower() in MISSING_VALUES

        def try_parse_numeric(s, target_type="float"):
            if target_type == "int":
                s2 = re.sub(r"[^\d\-]", "", str(s))
                if s2 == "" or s2 in ["-", "+"]:
                    raise ValueError("not an integer")
                return int(float(s2))
            else:
                s2 = re.sub(r"[^\d\.\-]", "", str(s))
                if s2 == "" or s2 in ["-", "+", "."]:
                    raise ValueError("not a number")
                return float(s2)

        # Read CSV
        try:
            df = pd.read_csv(csv_file_path, dtype=str, keep_default_na=False, na_values=[""])
        except Exception as read_error:
            raise Exception(f"Could not read CSV file: {read_error}")
        
        # Clean column names
        df.columns = [c.strip().lower().replace(" ", "_") for c in list(df.columns)]
        
        print(f"[{current_timestamp}] CSV loaded: {len(df)} rows, {len(df.columns)} columns")
        print(f"[{current_timestamp}] Columns: {df.columns.tolist()}")
        
        clean_data = []
        error_data = []
        stats = {"total_rows": len(df), "clean_count": 0, "error_count": 0}
        
        for idx, row in df.iterrows():
            try:
                record = {}
                errors = []
                
                for col, val in row.items():
                    if is_missing(val):
                        record[col] = None
                        continue
                    
                    # Try to apply basic constraints
                    if col in BASIC_CONSTRAINTS:
                        conf = BASIC_CONSTRAINTS[col]
                        try:
                            if conf["type"] == "int":
                                parsed_val = try_parse_numeric(val, "int")
                                if "min" in conf and parsed_val < conf["min"]:
                                    raise ValueError(f"Value {parsed_val} below minimum {conf['min']}")
                                if "max" in conf and parsed_val > conf["max"]:
                                    raise ValueError(f"Value {parsed_val} above maximum {conf['max']}")
                                record[col] = parsed_val
                            elif conf["type"] == "float":
                                parsed_val = try_parse_numeric(val, "float")
                                if "min" in conf and parsed_val < conf["min"]:
                                    raise ValueError(f"Value {parsed_val} below minimum {conf['min']}")
                                record[col] = parsed_val
                            else:
                                record[col] = str(val).strip()
                        except Exception as parse_error:
                            errors.append(f"{col}: {str(parse_error)}")
                            record[col] = str(val).strip()
                    else:
                        # For other columns, just clean the string
                        record[col] = str(val).strip() if not is_missing(val) else None
                
                # Add metadata
                record["_processed_at"] = current_timestamp
                record["_source"] = "csv_standalone"
                record["_row_number"] = int(idx) + 1
                
                if errors:
                    record["_errors"] = errors
                    record["_error_count"] = len(errors)
                    error_data.append(record)
                    stats["error_count"] += 1
                else:
                    clean_data.append(record)
                    stats["clean_count"] += 1
                    
            except Exception as row_error:
                error_data.append({
                    "_row_number": int(idx) + 1,
                    "_error": str(row_error),
                    "_error_type": type(row_error).__name__,
                    "_processed_at": current_timestamp,
                    "_source": "csv_standalone"
                })
                stats["error_count"] += 1
        
        processing_time = time.time() - start_time
        success_rate = (stats["clean_count"] / stats["total_rows"] * 100) if stats["total_rows"] > 0 else 0
        
        print(f"[{current_timestamp}] CSV standalone processing completed:")
        print(f"[{current_timestamp}] - Total rows: {stats['total_rows']}")
        print(f"[{current_timestamp}] - Clean rows: {stats['clean_count']}")
        print(f"[{current_timestamp}] - Error rows: {stats['error_count']}")
        print(f"[{current_timestamp}] - Success rate: {success_rate:.2f}%")
        
        return {
            "success": True,
            "clean_data": clean_data,
            "error_data": error_data,
            "processing_time": f"{processing_time:.2f}s",
            "total_rows": stats["total_rows"],
            "clean_count": stats["clean_count"],
            "error_count": stats["error_count"],
            "success_rate": round(success_rate, 2),
            "columns_processed": df.columns.tolist(),
            "file_info": {
                "csv_file": os.path.basename(csv_file_path),
                "processing_mode": "standalone"
            }
        }
        
    except Exception as e:
        print(f"[{current_timestamp}] Error in CSV standalone processing: {e}")
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "clean_data": [],
            "error_data": [{
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": current_timestamp
            }],
            "processing_time": f"{time.time() - start_time:.2f}s",
            "success_rate": 0,
            "total_rows": 0,
            "clean_count": 0,
            "error_count": 1
        }

def process_pdf_with_validation(pdf_file_path: str) -> dict:
    """Process PDF using multiple extraction methods with OCR fallback for image-based PDFs"""
    start_time = time.time()
    current_timestamp = get_timestamp()
    
    try:
        print(f"[{current_timestamp}] Processing PDF: {pdf_file_path}")
        
        # Step 1: Try multiple PDF extraction methods
        combined_df = None
        extraction_method = "none"
        raw_tables = []
        
        # Method 1: Try tabula-py first with multiple configurations
        try:
            print(f"[{current_timestamp}] Trying tabula extraction...")
            import tabula
            
            # Try multiple tabula configurations
            tabula_configs = [
                {"pages": "all", "multiple_tables": True},
                {"pages": "all", "multiple_tables": True, "lattice": True},
                {"pages": "all", "multiple_tables": True, "stream": True},
                {"pages": "all", "multiple_tables": True, "guess": False, "area": [0, 0, 792, 612]},
                {"pages": "all", "multiple_tables": True, "pandas_options": {"header": None}}
            ]
            
            for i, config in enumerate(tabula_configs):
                try:
                    print(f"[{current_timestamp}] Trying tabula config {i+1}...")
                    tables = tabula.read_pdf(pdf_file_path, **config)
                    
                    if tables and len(tables) > 0:
                        print(f"[{current_timestamp}] Tabula config {i+1} found {len(tables)} tables")
                        
                        # Process tables
                        valid_tables = []
                        for j, table in enumerate(tables):
                            if len(table) > 0:
                                # Remove completely empty rows and columns
                                table = table.dropna(how='all').dropna(axis=1, how='all')
                                
                                if len(table) > 0 and len(table.columns) > 0:
                                    # Clean column names
                                    table.columns = [f"col_{k}" if pd.isna(col) or str(col).strip() == "" else str(col).strip() 
                                                   for k, col in enumerate(table.columns)]
                                    valid_tables.append(table)
                                    print(f"[{current_timestamp}] Valid table {j+1}: {len(table)} rows, {len(table.columns)} columns")
                        
                        if valid_tables:
                            raw_tables = valid_tables
                            extraction_method = f"tabula_config_{i+1}"
                            break
                            
                except Exception as config_error:
                    print(f"[{current_timestamp}] Tabula config {i+1} failed: {config_error}")
                    continue
            
        except Exception as tabula_error:
            print(f"[{current_timestamp}] Tabula extraction completely failed: {tabula_error}")
        
        # Method 2: Try camelot if tabula didn't work well
        if not raw_tables:
            try:
                print(f"[{current_timestamp}] Trying camelot extraction...")
                import camelot
                
                # Try different camelot flavors
                camelot_configs = [
                    {"flavor": "lattice", "pages": "all"},
                    {"flavor": "stream", "pages": "all"},
                    {"flavor": "lattice", "pages": "all", "split_text": True},
                    {"flavor": "stream", "pages": "all", "edge_tol": 50}
                ]
                
                for i, config in enumerate(camelot_configs):
                    try:
                        print(f"[{current_timestamp}] Trying camelot config {i+1}...")
                        tables = camelot.read_pdf(pdf_file_path, **config)
                        
                        if len(tables) > 0:
                            print(f"[{current_timestamp}] Camelot config {i+1} found {len(tables)} tables")
                            
                            valid_tables = []
                            for j, table in enumerate(tables):
                                df = table.df
                                if len(df) > 0:
                                    # Remove empty rows and columns - fix pandas warning
                                    df = df.replace('', np.nan)
                                    df = df.dropna(how='all').dropna(axis=1, how='all')
                                    
                                    if len(df) > 0 and len(df.columns) > 0:
                                        # Clean column names
                                        df.columns = [f"col_{k}" if pd.isna(col) or str(col).strip() == "" else str(col).strip() 
                                                     for k, col in enumerate(df.columns)]
                                        valid_tables.append(df)
                                        print(f"[{current_timestamp}] Valid camelot table {j+1}: {len(df)} rows, {len(df.columns)} columns")
                            
                            if valid_tables:
                                raw_tables = valid_tables
                                extraction_method = f"camelot_{config['flavor']}"
                                break
                                
                    except Exception as config_error:
                        print(f"[{current_timestamp}] Camelot config {i+1} failed: {config_error}")
                        continue
                        
            except Exception as camelot_error:
                print(f"[{current_timestamp}] Camelot extraction failed: {camelot_error}")
        
        # Method 3: Try PyPDF2 for text extraction
        if not raw_tables:
            try:
                print(f"[{current_timestamp}] Trying PyPDF2 text extraction...")
                import PyPDF2
                
                with open(pdf_file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    all_text = ""
                    
                    for page_num, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        all_text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                
                print(f"[{current_timestamp}] Extracted {len(all_text)} characters of text")
                
                if all_text.strip() and len(all_text.strip()) > 20:  # Need meaningful text
                    # Try to parse text into structured data
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    
                    if len(lines) > 2:
                        # Look for patterns that might indicate tabular data
                        potential_rows = []
                        
                        for line in lines:
                            # Split line by multiple spaces, tabs, or other delimiters
                            parts = re.split(r'\s{2,}|\t+', line)
                            if len(parts) >= 2:  # At least 2 columns
                                potential_rows.append(parts)
                        
                        if len(potential_rows) > 1:
                            # Find the maximum number of columns
                            max_cols = max(len(row) for row in potential_rows)
                            
                            # Normalize rows to have the same number of columns
                            normalized_rows = []
                            for row in potential_rows:
                                if len(row) < max_cols:
                                    row.extend([''] * (max_cols - len(row)))
                                else:
                                    row = row[:max_cols]
                                normalized_rows.append(row)
                            
                            # Create DataFrame
                            if len(normalized_rows) > 1:
                                # Use first row as headers or create generic headers
                                headers = [f"col_{i}" for i in range(max_cols)]
                                df_data = normalized_rows
                                
                                df = pd.DataFrame(df_data, columns=headers)
                                raw_tables = [df]
                                extraction_method = "pypdf2_text_parsing"
                                print(f"[{current_timestamp}] PyPDF2 created table: {len(df)} rows, {len(df.columns)} columns")
                
            except Exception as pypdf_error:
                print(f"[{current_timestamp}] PyPDF2 extraction failed: {pypdf_error}")
        
        # Method 4: Try OCR for image-based PDFs
        if not raw_tables:
            try:
                print(f"[{current_timestamp}] Trying OCR extraction (image-based PDF detected)...")
                
                # Try to import required libraries
                try:
                    import pytesseract
                    from pdf2image import convert_from_path
                    from PIL import Image
                    
                    # Convert PDF to images
                    print(f"[{current_timestamp}] Converting PDF to images...")
                    images = convert_from_path(pdf_file_path)
                    
                    if images:
                        print(f"[{current_timestamp}] Converted {len(images)} pages to images")
                        
                        all_ocr_text = ""
                        for i, image in enumerate(images):
                            try:
                                # Extract text using OCR
                                page_text = pytesseract.image_to_string(image)
                                all_ocr_text += f"\n--- Page {i+1} (OCR) ---\n{page_text}\n"
                                print(f"[{current_timestamp}] OCR page {i+1}: {len(page_text)} characters")
                            except Exception as ocr_page_error:
                                print(f"[{current_timestamp}] OCR failed for page {i+1}: {ocr_page_error}")
                                continue
                        
                        if all_ocr_text.strip() and len(all_ocr_text.strip()) > 50:
                            # Process OCR text similar to PyPDF2
                            lines = [line.strip() for line in all_ocr_text.split('\n') if line.strip() and len(line.strip()) > 3]
                            
                            if len(lines) > 2:
                                # Create a simple DataFrame with OCR text
                                text_data = []
                                for line_num, line in enumerate(lines):
                                    # Try to split into columns based on spaces
                                    parts = re.split(r'\s{3,}|\t+', line)  # Split on 3+ spaces or tabs
                                    if len(parts) >= 2:
                                        text_data.append(parts)
                                
                                if text_data and len(text_data) > 1:
                                    # Create DataFrame
                                    max_cols = max(len(row) for row in text_data)
                                    
                                    # Normalize rows
                                    normalized_data = []
                                    for row in text_data:
                                        if len(row) < max_cols:
                                            row.extend([''] * (max_cols - len(row)))
                                        else:
                                            row = row[:max_cols]
                                        normalized_data.append(row)
                                    
                                    headers = [f"ocr_col_{i}" for i in range(max_cols)]
                                    df = pd.DataFrame(normalized_data, columns=headers)
                                    raw_tables = [df]
                                    extraction_method = "ocr_tesseract"
                                    print(f"[{current_timestamp}] OCR created table: {len(df)} rows, {len(df.columns)} columns")
                                else:
                                    # Create simple single-column table with all text
                                    df = pd.DataFrame({
                                        'ocr_text': lines,
                                        'line_number': range(1, len(lines) + 1)
                                    })
                                    raw_tables = [df]
                                    extraction_method = "ocr_text_lines"
                                    print(f"[{current_timestamp}] OCR created text table: {len(df)} lines")
                        
                except ImportError as import_error:
                    print(f"[{current_timestamp}] OCR libraries not available: {import_error}")
                    print(f"[{current_timestamp}] Install with: pip install pytesseract pdf2image pillow")
                    
            except Exception as ocr_error:
                print(f"[{current_timestamp}] OCR extraction failed: {ocr_error}")
        
        # Method 5: Create simple metadata table as last resort
        if not raw_tables:
            try:
                print(f"[{current_timestamp}] Creating metadata representation...")
                
                # Get basic PDF information
                import PyPDF2
                with open(pdf_file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    metadata = {
                        'total_pages': len(pdf_reader.pages),
                        'pdf_filename': os.path.basename(pdf_file_path),
                        'processing_timestamp': current_timestamp,
                        'extraction_attempted': 'tabula,camelot,pypdf2,ocr',
                        'file_size_mb': round(os.path.getsize(pdf_file_path) / (1024*1024), 2),
                        'status': 'image_based_pdf_detected'
                    }
                    
                    # Try to get any text at all
                    sample_text = ""
                    for i, page in enumerate(pdf_reader.pages[:3]):  # First 3 pages
                        try:
                            page_text = page.extract_text()
                            if page_text.strip():
                                sample_text += page_text[:200] + "..."
                                break
                        except:
                            continue
                    
                    if not sample_text.strip():
                        sample_text = "No extractable text found - likely image-based PDF"
                    
                    metadata['sample_text'] = sample_text
                    
                    # Create DataFrame from metadata
                    df = pd.DataFrame([metadata])
                    raw_tables = [df]
                    extraction_method = "pdf_metadata"
                    print(f"[{current_timestamp}] Created metadata table: {len(df)} records")
                    
            except Exception as metadata_error:
                print(f"[{current_timestamp}] Metadata extraction failed: {metadata_error}")
        
        # Final check - if still no data, return structured error
        if not raw_tables:
            print(f"[{current_timestamp}] All extraction methods failed, returning structured error response")
            
            return {
                "success": False,
                "error": (
                    "Could not extract any data from PDF. This appears to be an image-based (scanned) PDF. "
                    "Recommendations:\n"
                    "1. Install OCR libraries: pip install pytesseract pdf2image pillow\n"
                    "2. Install Tesseract OCR engine\n"
                    "3. Convert PDF to text-based format\n"
                    "4. Use online OCR tools first\n"
                    "5. Check if PDF is password protected"
                ),
                "processed_data": [],
                "error_data": [{
                    "error_type": "image_based_pdf",
                    "filename": os.path.basename(pdf_file_path),
                    "timestamp": current_timestamp,
                    "extraction_methods_tried": ["tabula", "camelot", "pypdf2", "ocr", "metadata"],
                    "recommendation": "Use OCR tools or convert to text-based PDF"
                }],
                "processing_time": f"{time.time() - start_time:.2f}s",
                "success_rate": 0,
                "total_pdf_rows": 0,
                "extraction_method": "failed",
                "processed_count": 0,
                "error_count": 1,
                "tables_found": 0,
                "columns_extracted": []
            }
        
        # Step 2: Combine tables if multiple
        if len(raw_tables) == 1:
            combined_df = raw_tables[0]
        else:
            # Try to combine tables with similar structure
            try:
                # Find the table with the most columns as reference
                reference_table = max(raw_tables, key=lambda x: len(x.columns))
                reference_cols = len(reference_table.columns)
                
                compatible_tables = []
                for table in raw_tables:
                    if len(table.columns) == reference_cols:
                        # Align column names
                        table.columns = reference_table.columns
                        compatible_tables.append(table)
                    else:
                        # Resize table to match reference
                        if len(table.columns) < reference_cols:
                            # Add empty columns
                            for i in range(len(table.columns), reference_cols):
                                table[f'col_{i}'] = ''
                        else:
                            # Truncate extra columns
                            table = table.iloc[:, :reference_cols]
                        
                        table.columns = reference_table.columns
                        compatible_tables.append(table)
                
                combined_df = pd.concat(compatible_tables, ignore_index=True)
                
            except Exception as combine_error:
                print(f"[{current_timestamp}] Could not combine tables: {combine_error}")
                # Use the largest table
                combined_df = max(raw_tables, key=len)
        
        print(f"[{current_timestamp}] Final combined data: {len(combined_df)} rows, {len(combined_df.columns)} columns")
        print(f"[{current_timestamp}] Columns: {combined_df.columns.tolist()}")
        
        # Show sample data for debugging
        if len(combined_df) > 0:
            print(f"[{current_timestamp}] Sample data preview:")
            print(combined_df.head(3).to_string())
        
        # Step 3: Process and validate the extracted data
        processed_data = []
        error_data = []
        
        for idx, row in combined_df.iterrows():
            try:
                record = {}
                errors = []
                non_empty_values = 0
                
                # Convert row to dictionary and clean data types
                for col, val in row.items():
                    if pd.isna(val) or val == '' or str(val).lower() in ['nan', 'null', 'none']:
                        record[col] = None
                    elif isinstance(val, (np.integer, np.int64)):
                        record[col] = int(val)
                        non_empty_values += 1
                    elif isinstance(val, (np.floating, np.float64)):
                        if np.isnan(val) or np.isinf(val):
                            record[col] = None
                        else:
                            record[col] = float(val)
                            non_empty_values += 1
                    else:
                        clean_val = str(val).strip()
                        if clean_val and clean_val not in ['', 'nan', 'null', 'none']:
                            record[col] = clean_val
                            non_empty_values += 1
                        else:
                            record[col] = None
                
                # Data quality validation
                total_columns = len(record)
                empty_ratio = (total_columns - non_empty_values) / total_columns if total_columns > 0 else 1
                
                if empty_ratio > 0.8:  # More than 80% empty
                    errors.append(f"Row mostly empty: {non_empty_values}/{total_columns} fields have data")
                
                if non_empty_values == 0:
                    errors.append("Completely empty row")
                
                # Add processing metadata
                record["_processed_at"] = current_timestamp
                record["_source"] = f"pdf_extraction_{extraction_method}"
                record["_row_number"] = idx + 1
                record["_extraction_method"] = extraction_method
                record["_data_quality_score"] = round((non_empty_values / total_columns) * 100, 2) if total_columns > 0 else 0
                
                # Categorize record
                if errors:
                    record["_errors"] = errors
                    error_data.append(record)
                else:
                    processed_data.append(record)
                    
            except Exception as row_error:
                error_data.append({
                    "_row_number": idx + 1,
                    "_error": str(row_error),
                    "_processed_at": current_timestamp,
                    "_source": f"pdf_extraction_{extraction_method}",
                    "_extraction_method": extraction_method
                })
        
        processing_time = time.time() - start_time
        total_records = len(processed_data) + len(error_data)
        success_rate = (len(processed_data) / len(combined_df) * 100) if len(combined_df) > 0 else 0
        
        print(f"[{current_timestamp}] PDF processing completed: {len(processed_data)} processed, {len(error_data)} errors")
        print(f"[{current_timestamp}] Success rate: {success_rate:.2f}%")
        
        return {
            "success": True,
            "processed_data": processed_data,
            "error_data": error_data,
            "processing_time": f"{processing_time:.2f}s",
            "total_pdf_rows": len(combined_df),
            "processed_count": len(processed_data),
            "error_count": len(error_data),
            "success_rate": round(success_rate, 2),
            "columns_extracted": combined_df.columns.tolist(),
            "extraction_method": extraction_method,
            "tables_found": len(raw_tables)
        }
        
    except Exception as e:
        print(f"[{current_timestamp}] Error in PDF processing: {e}")
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "processed_data": [],
            "error_data": [{
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": current_timestamp,
                "_extraction_method": "failed"
            }],
            "processing_time": f"{time.time() - start_time:.2f}s",
            "success_rate": 0,
            "total_pdf_rows": 0,
            "extraction_method": "failed",
            "processed_count": 0,
            "error_count": 1,
            "tables_found": 0,
            "columns_extracted": []
        }

def process_excel_with_validation(excel_file_path: str) -> dict:
    """Process Excel file using your exact validation logic"""
    start_time = time.time()
    current_timestamp = get_timestamp()
    
    try:
        print(f"[{current_timestamp}] Processing Excel: {excel_file_path}")
        
        # Read Excel file
        df = pd.read_excel(excel_file_path, sheet_name=0)
        df.columns = df.columns.str.strip()
        
        print(f"[{current_timestamp}] Excel loaded, columns: {df.columns.tolist()}")
        
        # Initialize error tracking
        error_rows = pd.DataFrame()
        error_info = {col: 0 for col in df.columns}
        
        # Validation functions
        def validate_txn_id(x):
            return bool(re.fullmatch(r'TXN\d{10}', str(x)))

        def validate_customer_id(x):
            return bool(re.fullmatch(r'\d{6}', str(x)))

        def validate_timestamp_strict(x):
            try:
                dt = pd.to_datetime(x, errors="raise", dayfirst=True)
                return 0 <= dt.hour <= 23 and 0 <= dt.minute <= 59
            except:
                return False

        def validate_transaction_type(x):
            return str(x).lower() in ["p2p", "p2m", "bill payment", "billpayment"]

        def validate_string(x):
            return isinstance(x, str) and len(str(x).strip()) > 0

        def validate_numeric(x):
            try:
                float(x)
                return True
            except:
                return False

        def validate_status(x):
            return str(x).lower() in ["success", "failed"]

        def validate_device_type(x):
            return str(x).lower() in ["android", "ios", "web"]

        def validate_network_type(x):
            return str(x) in ["4G", "5G", "WiFi", "3G"]

        def validate_boolean(x):
            try:
                return int(x) in [0, 1]
            except:
                return False

        def validate_hour(x):
            try:
                return 0 <= int(x) < 24
            except:
                return False

        # Column-wise validation
        for col in df.columns:
            col_lower = col.lower()
            
            if col_lower in ["transaction id", "transaction_id"]:
                mask = df[col].apply(lambda x: not validate_txn_id(x))
            elif col_lower in ["customer id", "customer_id"]:
                mask = df[col].apply(lambda x: not validate_customer_id(x))
            elif col_lower == "timestamp":
                mask = ~df[col].apply(validate_timestamp_strict)
            elif col_lower in ["transaction type", "transaction_type"]:
                mask = df[col].apply(lambda x: not validate_transaction_type(x))
            elif col_lower in ["merchant_category", "metchant_catogory", "sender_age_group", "receiver_age_group",
                               "sender_state","receiver_state","receiver_bank","sender_bank","day_of_tranaction", "day_of_week"]:
                mask = df[col].apply(lambda x: not validate_string(x))
            elif col_lower in ["amount", "amount (inr)"]:
                mask = df[col].apply(lambda x: not validate_numeric(x))
            elif col_lower in ["transaction_status", "transaction status"]:
                mask = df[col].apply(lambda x: not validate_status(x))
            elif col_lower in ["device_type", "device type"]:
                mask = df[col].apply(lambda x: not validate_device_type(x))
            elif col_lower in ["network_type", "network type"]:
                mask = df[col].apply(lambda x: not validate_network_type(x))
            elif col_lower in ["fraud_flag", "fraud_falg", "fraud flag"]:
                mask = df[col].apply(lambda x: not validate_boolean(x))
            elif col_lower in ["hour_of_day", "hour of day"]:
                mask = df[col].apply(lambda x: not validate_hour(x))
            elif col_lower in ["is_weekend", "is weekend"]:
                mask = df[col].apply(lambda x: not validate_boolean(x))
            else:
                mask = pd.Series([False]*len(df))
            
            # Track errors
            error_info[col] += mask.sum()
            if mask.any():
                error_rows = pd.concat([error_rows, df[mask]])

        # Remove duplicates in error_rows
        error_rows = error_rows.drop_duplicates()
        
        # Clean data
        # For numeric columns, fill missing/invalid with 0
        numeric_cols = ["amount", "amount (inr)", "fraud_flag", "fraud_falg", "hour_of_day", "is_weekend"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # For string columns, fill missing with "Unknown"
        string_cols = ["merchant_category", "metchant_catogory", "sender_age_group", "receiver_age_group",
                       "sender_state","receiver_state","receiver_bank","sender_bank",
                       "transaction type", "transaction_type","transaction_status", "transaction status",
                       "device_type", "device type", "network_type", "network type", "day_of_tranaction", "day_of_week"]
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].fillna("Unknown").astype(str)

        # For timestamp column, convert to datetime and then to string
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", dayfirst=True)
            # Convert datetime to string for JSON serialization, handle NaT
            df["timestamp"] = df["timestamp"].dt.strftime('%Y-%m-%d %H:%M:%S')
            df["timestamp"] = df["timestamp"].fillna("Unknown")

        # Handle any remaining NaN values
        df = df.fillna("Unknown")

        # Remove error rows from clean data
        clean_data = df.drop(error_rows.index, errors='ignore')

        # Convert to records for JSON serialization with proper type handling
        clean_records = []
        for _, row in clean_data.iterrows():
            record = {}
            for col, val in row.items():
                if pd.isna(val):
                    record[col] = None
                elif isinstance(val, (np.integer, np.int64)):
                    record[col] = int(val)
                elif isinstance(val, (np.floating, np.float64)):
                    if np.isnan(val) or np.isinf(val):
                        record[col] = None
                    else:
                        record[col] = float(val)
                else:
                    record[col] = str(val)
            # Add processing metadata
            record["_processed_at"] = current_timestamp
            record["_source"] = "excel_cleaning"
            clean_records.append(record)

        error_records = []
        for _, row in error_rows.iterrows():
            record = {}
            for col, val in row.items():
                if pd.isna(val):
                    record[col] = None
                elif isinstance(val, (np.integer, np.int64)):
                    record[col] = int(val)
                elif isinstance(val, (np.floating, np.float64)):
                    if np.isnan(val) or np.isinf(val):
                        record[col] = None
                    else:
                        record[col] = float(val)
                else:
                    record[col] = str(val)
            # Add processing metadata
            record["_processed_at"] = current_timestamp
            record["_source"] = "excel_cleaning"
            record["_error_reason"] = "validation_failed"
            error_records.append(record)
        
        processing_time = time.time() - start_time
        total_rows = len(df)
        clean_count = len(clean_records)
        error_count = len(error_records)
        success_rate = (clean_count / total_rows * 100) if total_rows > 0 else 0
        
        print(f"[{current_timestamp}] Excel processing completed: {clean_count} clean, {error_count} errors")
        
        return {
            "success": True,
            "clean_data": clean_records,
            "error_data": error_records,
            "processing_time": f"{processing_time:.2f}s",
            "total_rows": int(total_rows),
            "clean_count": int(clean_count),
            "error_count": int(error_count),
            "success_rate": round(float(success_rate), 2),
            "error_info": {k: int(v) for k, v in error_info.items()},
            "columns_processed": [str(col) for col in df.columns.tolist()]
        }
        
    except Exception as e:
        print(f"[{current_timestamp}] Error in Excel processing: {e}")
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "clean_data": [],
            "error_data": [{
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": current_timestamp
            }],
            "processing_time": f"{time.time() - start_time:.2f}s",
            "success_rate": 0,
            "total_rows": 0,
            "clean_count": 0,
            "error_count": 0,
            "error_info": {},
            "columns_processed": []
        }

def process_xml_with_master_data(xml_file_path: str, json_file_path: str) -> dict:
    """Process XML using your exact logic with master data validation"""
    start_time = time.time()
    current_timestamp = get_timestamp()
    
    try:
        print(f"[{current_timestamp}] Processing XML: {xml_file_path}")
        print(f"[{current_timestamp}] Processing JSON: {json_file_path}")
        
        # Step 1: Load XML
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        print(f"[{current_timestamp}] XML loaded successfully")
        
        # Step 2: Load Master Customer Data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            master_data = json.load(f)
        print(f"[{current_timestamp}] Master data loaded: {len(master_data)} records")
        
        # Create a set of valid Customer_IDs for fast lookup
        valid_customer_ids = set([str(cust["Customer_ID"]) for cust in master_data])
        
        # Step 3: Prepare for Cleaning
        numeric_fields = [
            "BALANCE", "BALANCE_FREQUENCY", "PURCHASES", "ONEOFF_PURCHASES",
            "INSTALLMENTS_PURCHASES", "CASH_ADVANCE", "PURCHASES_FREQUENCY",
            "ONEOFF_PURCHASES_FREQUENCY", "PURCHASES_INSTALLMENTS_FREQUENCY",
            "CASH_ADVANCE_FREQUENCY", "CASH_ADVANCE_TRX", "PURCHASES_TRX",
            "CREDIT_LIMIT", "PAYMENTS", "MINIMUM_PAYMENTS", "PRC_FULL_PAYMENT",
            "TENURE"
        ]
        
        all_values = {field: [] for field in numeric_fields}
        customers = []
        xml_customer_ids = set()  # Track all CUST_IDs in XML
        
        # Step 4: First pass to collect numeric values
        for cust in root.findall("Customer"):
            record = {}
            for field in cust:
                value = field.text.strip() if field.text and field.text.strip() else None
                record[field.tag] = value
                if field.tag in numeric_fields and value not in (None, "", "NaN", "null"):
                    try:
                        all_values[field.tag].append(float(value))
                    except ValueError:
                        pass
            customers.append(record)
            # Track valid XML customer IDs
            cust_id = record.get("CUST_ID")
            if cust_id and str(cust_id).strip():
                xml_customer_ids.add(str(cust_id).strip())
        
        print(f"[{current_timestamp}] Found {len(customers)} customers in XML")
        
        # Calculate medians for imputation
        medians = {f: statistics.median(v) if v else 0 for f, v in all_values.items()}
        
        # Step 5: Clean + Validate
        cleaned_data = []
        error_log = []
        
        for record in customers:
            errors = []
            cleaned_record = {}
            
            # RecordId
            try:
                cleaned_record["RecordId"] = int(record.get("RecordId", -1))
            except (ValueError, TypeError):
                cleaned_record["RecordId"] = -1
            
            # Handle CUST_ID safely
            raw_cust_id = record.get("CUST_ID")
            original_cust_id = str(raw_cust_id).strip() if raw_cust_id else None
            
            if not original_cust_id or original_cust_id == "None":
                cust_id = f"TEMP_{cleaned_record['RecordId']}"
                errors.append("Missing CUST_ID")
            else:
                cust_id = original_cust_id
            
            cleaned_record["CUST_ID"] = str(cust_id)
            
            # Validate against master data
            if str(cust_id) not in valid_customer_ids:
                errors.append("CUST_ID not found in customer_master_data.json")
            
            # Handle numeric fields
            for field in numeric_fields:
                value = record.get(field)
                try:
                    if value in (None, "", "NaN", "null") or not value:
                        cleaned_record[field] = float(medians[field])
                        errors.append(f"Missing {field} (imputed with median)")
                    else:
                        cleaned_record[field] = float(value)
                except (ValueError, TypeError):
                    cleaned_record[field] = float(medians[field])
                    errors.append(f"Invalid {field} (imputed with median)")
            
            # Validate purchases sum
            try:
                purchases = cleaned_record["PURCHASES"]
                sum_parts = cleaned_record["ONEOFF_PURCHASES"] + cleaned_record["INSTALLMENTS_PURCHASES"]
                if abs(purchases - sum_parts) > 1e-6:
                    errors.append("Mismatch: PURCHASES != ONEOFF_PURCHASES + INSTALLMENTS_PURCHASES")
            except (KeyError, TypeError):
                errors.append("Error in purchases validation")
            
            # Validate percentage fields
            percentage_fields = ["PRC_FULL_PAYMENT", "BALANCE_FREQUENCY",
                               "PURCHASES_FREQUENCY", "ONEOFF_PURCHASES_FREQUENCY",
                               "PURCHASES_INSTALLMENTS_FREQUENCY", "CASH_ADVANCE_FREQUENCY"]
            
            for f in percentage_fields:
                try:
                    if f in cleaned_record and not (0 <= cleaned_record[f] <= 1):
                        errors.append(f"{f} out of range [0,1]")
                except (KeyError, TypeError):
                    errors.append(f"Error validating {f}")
            
            # Credit limit & tenure checks
            try:
                if "CREDIT_LIMIT" in cleaned_record and cleaned_record["CREDIT_LIMIT"] <= 0:
                    errors.append("Invalid CREDIT_LIMIT <= 0")
                if "TENURE" in cleaned_record and cleaned_record["TENURE"] < 0:
                    errors.append("Invalid TENURE < 0")
            except (KeyError, TypeError):
                errors.append("Error validating CREDIT_LIMIT or TENURE")
            
            # Add processing metadata
            cleaned_record["_processed_at"] = current_timestamp
            
            # Save results
            if errors:
                error_log.append({
                    "CUST_ID": str(cust_id),
                    "Original_CUST_ID": str(original_cust_id) if original_cust_id else None,
                    "RecordId": cleaned_record["RecordId"],
                    "Errors": errors,
                    "timestamp": current_timestamp
                })
            else:
                cleaned_data.append(cleaned_record)
        
        # Step 6: Check master customers not in XML
        for cust in master_data:
            master_id = str(cust["Customer_ID"])
            if master_id not in xml_customer_ids:
                error_log.append({
                    "CUST_ID": master_id,
                    "Original_CUST_ID": master_id,
                    "RecordId": None,
                    "Errors": ["No credit card usage found in XML"],
                    "timestamp": current_timestamp
                })
        
        processing_time = time.time() - start_time
        total_records = len(cleaned_data) + len(error_log)
        success_rate = (len(cleaned_data) / total_records * 100) if total_records > 0 else 0
        
        print(f"[{current_timestamp}] XML processing completed: {len(cleaned_data)} cleaned, {len(error_log)} errors")
        
        return {
            "success": True,
            "cleaned_data": cleaned_data,
            "error_log": error_log,
            "processing_time": f"{processing_time:.2f}s",
            "total_customers_processed": len(customers),
            "total_master_records": len(master_data),
            "success_rate": round(success_rate, 2),
            "xml_customers": len(customers),
            "master_customers": len(master_data)
        }
        
    except Exception as e:
        print(f"[{current_timestamp}] Error in XML processing: {e}")
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "cleaned_data": [],
            "error_log": [{
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": current_timestamp
            }],
            "processing_time": f"{time.time() - start_time:.2f}s",
            "success_rate": 0,
            "xml_customers": 0,
            "master_customers": 0
        }

def save_processing_results(file_id: str, results: Dict[str, Any], file_types: Dict[str, str]):
    """Save processing results to output folder"""
    try:
        current_timestamp = get_timestamp()
        
        # Save XML results if available
        if 'xml_results' in results and results['xml_results']['success']:
            xml_results = results['xml_results']
            
            # Save cleaned customers final
            cleaned_file = output_dir / "cleaned_customers_final.json"
            with open(cleaned_file, 'w', encoding='utf-8') as f:
                json.dump(xml_results["cleaned_data"], f, indent=2, ensure_ascii=False, default=str)
            
            # Save error log final
            error_file = output_dir / "error_log_final.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(xml_results["error_log"], f, indent=2, ensure_ascii=False, default=str)
        
        # Save Excel results if available
        if 'excel_results' in results and results['excel_results']['success']:
            excel_results = results['excel_results']
            
            # Save clean Excel data
            clean_excel_file = output_dir / "clean_excel_data.json"
            with open(clean_excel_file, 'w', encoding='utf-8') as f:
                json.dump(excel_results["clean_data"], f, indent=2, ensure_ascii=False, default=str)
            
            # Save Excel errors
            error_excel_file = output_dir / "excel_errors.json"
            with open(error_excel_file, 'w', encoding='utf-8') as f:
                json.dump(excel_results["error_data"], f, indent=2, ensure_ascii=False, default=str)
        
        # Save PDF results if available
        if 'pdf_results' in results and results['pdf_results']['success']:
            pdf_results = results['pdf_results']
            
            # Save processed PDF data
            processed_pdf_file = output_dir / "processed_pdf_data.json"
            with open(processed_pdf_file, 'w', encoding='utf-8') as f:
                json.dump(pdf_results["processed_data"], f, indent=2, ensure_ascii=False, default=str)
            
            # Save PDF errors
            error_pdf_file = output_dir / "pdf_errors.json"
            with open(error_pdf_file, 'w', encoding='utf-8') as f:
                json.dump(pdf_results["error_data"], f, indent=2, ensure_ascii=False, default=str)
        
        # Save CSV results if available
        if 'csv_results' in results and results['csv_results']['success']:
            csv_results = results['csv_results']
            
            # For CSV with master data (merged data)
            if 'merged_data' in csv_results:
                # Save merged data (master + clean CSV)
                merged_csv_file = output_dir / "merged_csv_master_data.json"
                with open(merged_csv_file, 'w', encoding='utf-8') as f:
                    json.dump(csv_results["merged_data"], f, indent=2, ensure_ascii=False, default=str)
                
                # Save CSV errors
                error_csv_file = output_dir / "csv_errors.json"
                with open(error_csv_file, 'w', encoding='utf-8') as f:
                    json.dump(csv_results["error_data"], f, indent=2, ensure_ascii=False, default=str)
            else:
                # For standalone CSV processing
                clean_csv_file = output_dir / "clean_csv_data.json"
                with open(clean_csv_file, 'w', encoding='utf-8') as f:
                    json.dump(csv_results["clean_data"], f, indent=2, ensure_ascii=False, default=str)
                
                # Save CSV errors
                error_csv_file = output_dir / "csv_errors.json"
                with open(error_csv_file, 'w', encoding='utf-8') as f:
                    json.dump(csv_results["error_data"], f, indent=2, ensure_ascii=False, default=str)
        
        # Save combined summary
        summary_file = output_dir / f"{file_id}_processing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "file_id": file_id,
                "processed_at": current_timestamp,
                "file_types": file_types,
                "results": results
            }, f, indent=2, ensure_ascii=False, default=str)
        
        return {
            "summary_file": str(summary_file),
            "xml_files": {
                "cleaned_customers_final": str(output_dir / "cleaned_customers_final.json"),
                "error_log_final": str(output_dir / "error_log_final.json")
            } if 'xml_results' in results else None,
            "excel_files": {
                "clean_excel_data": str(output_dir / "clean_excel_data.json"),
                "excel_errors": str(output_dir / "excel_errors.json")
            } if 'excel_results' in results else None,
            "pdf_files": {
                "processed_pdf_data": str(output_dir / "processed_pdf_data.json"),
                "pdf_errors": str(output_dir / "pdf_errors.json")
            } if 'pdf_results' in results else None,
            "csv_files": {
                "merged_csv_master_data": str(output_dir / "merged_csv_master_data.json") if 'csv_results' in results and 'merged_data' in results['csv_results'] else str(output_dir / "clean_csv_data.json"),
                "csv_errors": str(output_dir / "csv_errors.json")
            } if 'csv_results' in results else None
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.post("/upload/multi-files")
async def upload_multi_files(
    files: List[UploadFile] = File(...)
):
    """Upload and process XML, JSON (Master Data), Excel, PDF, and CSV files"""
    start_time = time.time()
    file_id = get_file_id()
    current_timestamp = get_timestamp()
    
    try:
        print(f"[{current_timestamp}] === Starting multi-file processing ===")
        print(f"[{current_timestamp}] Received {len(files)} files")
        
        # Organize files by type
        xml_file = None
        json_file = None
        excel_file = None
        pdf_file = None
        csv_file = None
        
        saved_files = {}
        file_types = {}
        
        for file in files:
            filename_lower = file.filename.lower()
            
            if filename_lower.endswith('.xml'):
                xml_file = file
                file_types['xml'] = file.filename
            elif filename_lower.endswith('.json'):
                json_file = file
                file_types['json'] = file.filename
            elif filename_lower.endswith(('.xlsx', '.xls')):
                excel_file = file
                file_types['excel'] = file.filename
            elif filename_lower.endswith('.pdf'):
                pdf_file = file
                file_types['pdf'] = file.filename
            elif filename_lower.endswith('.csv'):
                csv_file = file
                file_types['csv'] = file.filename
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")
        
        print(f"[{current_timestamp}] File types detected: {file_types}")
        
        # Save all files
        for file_type, file_obj in [('xml', xml_file), ('json', json_file), ('excel', excel_file), ('pdf', pdf_file), ('csv', csv_file)]:
            if file_obj:
                save_result = await save_uploaded_file(file_obj, file_type)
                if not save_result["success"]:
                    raise HTTPException(status_code=500, detail=f"Failed to save {file_type} file: {save_result['error']}")
                saved_files[file_type] = save_result
                print(f"[{current_timestamp}] {file_type.upper()} saved: {save_result['saved_path']}")
        
        # Process files based on what's available
        results = {}
        
        # Process XML + JSON if both are available
        if xml_file and json_file:
            print(f"[{current_timestamp}] Processing XML with Master Data validation...")
            xml_results = process_xml_with_master_data(
                saved_files['xml']['saved_path'],
                saved_files['json']['saved_path']
            )
            results['xml_results'] = xml_results
            print(f"[{current_timestamp}] XML processing completed")
        
        # Process PDF if available (standalone, no master data needed)
        if pdf_file:
            print(f"[{current_timestamp}] Processing PDF with validation...")
            pdf_results = process_pdf_with_validation(saved_files['pdf']['saved_path'])
            results['pdf_results'] = pdf_results
            print(f"[{current_timestamp}] PDF processing completed")
        
        # Process Excel if available
        if excel_file:
            print(f"[{current_timestamp}] Processing Excel with validation...")
            excel_results = process_excel_with_validation(saved_files['excel']['saved_path'])
            results['excel_results'] = excel_results
            print(f"[{current_timestamp}] Excel processing completed")
        
        # Process CSV - with or without master data
        if csv_file:
            if json_file:
                print(f"[{current_timestamp}] Processing CSV with Master Data integration...")
                csv_results = process_csv_with_master_data(
                    saved_files['csv']['saved_path'],
                    saved_files['json']['saved_path']
                )
            else:
                print(f"[{current_timestamp}] Processing CSV standalone...")
                csv_results = process_csv_standalone(saved_files['csv']['saved_path'])
            
            results['csv_results'] = csv_results
            print(f"[{current_timestamp}] CSV processing completed")
        
        if not results:
            raise HTTPException(status_code=400, detail="No valid file combinations found for processing")
        
        # Save results to output folder
        output_files = save_processing_results(file_id, results, file_types)
        
        if "error" in output_files:
            print(f"[{current_timestamp}] Warning: Could not save all output files: {output_files['error']}")
        else:
            print(f"[{current_timestamp}] Output files saved successfully")
        
        total_processing_time = time.time() - start_time
        
        # Prepare response - Clean all data before JSON serialization
        response_data = clean_for_json({
            "success": True,
            "message": "Multi-file processing completed successfully",
            "file_id": file_id,
            "processing_time": f"{total_processing_time:.2f}s",
            "files_processed": file_types,
            "saved_files": saved_files,
            "results": results,
            "output_files": output_files
        })
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[{current_timestamp}] ERROR in multi-file upload: {e}")
        traceback.print_exc()
        
        error_response = clean_for_json({
            "success": False,
            "message": "Multi-file processing failed",
            "error": str(e),
            "file_id": file_id,
            "timestamp": current_timestamp
        })
        return JSONResponse(content=error_response, status_code=500)

@app.post("/upload/xml-json")
async def upload_xml_json_files(
    xml_file: UploadFile = File(...),
    json_file: UploadFile = File(...)
):
    """Upload XML and JSON files, process them using your exact logic"""
    start_time = time.time()
    file_id = get_file_id()
    current_timestamp = get_timestamp()
    
    try:
        print(f"[{current_timestamp}] === Starting XML+JSON processing ===")
        
        # Validate file types
        if not xml_file.filename.lower().endswith('.xml'):
            raise HTTPException(status_code=400, detail="First file must be XML format (.xml)")
        
        if not json_file.filename.lower().endswith('.json'):
            raise HTTPException(status_code=400, detail="Second file must be JSON format (.json)")
        
        print(f"[{current_timestamp}] File validation passed")
        print(f"[{current_timestamp}] XML file: {xml_file.filename}")
        print(f"[{current_timestamp}] JSON file: {json_file.filename}")
        
        # Save both files
        xml_save_result = await save_uploaded_file(xml_file, "xml")
        json_save_result = await save_uploaded_file(json_file, "json")
        
        if not xml_save_result["success"]:
            raise HTTPException(status_code=500, detail=f"Failed to save XML file: {xml_save_result['error']}")
        
        if not json_save_result["success"]:
            raise HTTPException(status_code=500, detail=f"Failed to save JSON file: {json_save_result['error']}")
        
        print(f"[{current_timestamp}] Files saved successfully")
        print(f"[{current_timestamp}] XML: {xml_save_result['saved_path']}")
        print(f"[{current_timestamp}] JSON: {json_save_result['saved_path']}")
        
        # Process the files using your exact XML logic
        processing_result = process_xml_with_master_data(
            xml_save_result["saved_path"], 
            json_save_result["saved_path"]
        )
        
        if not processing_result["success"]:
            raise HTTPException(status_code=500, detail=f"Processing failed: {processing_result.get('error', 'Unknown error')}")
        
        print(f"[{current_timestamp}] XML processing completed")
        
        # Save results to output folder
        try:
            # Save cleaned customers final
            cleaned_file = output_dir / "cleaned_customers_final.json"
            with open(cleaned_file, 'w', encoding='utf-8') as f:
                json.dump(processing_result["cleaned_data"], f, indent=2, ensure_ascii=False, default=str)
            
            # Save error log final
            error_file = output_dir / "error_log_final.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(processing_result["error_log"], f, indent=2, ensure_ascii=False, default=str)
            
            output_files = {
                "cleaned_customers_final": str(cleaned_file),
                "error_log_final": str(error_file)
            }
            print(f"[{current_timestamp}] Output files saved successfully")
        except Exception as save_error:
            print(f"[{current_timestamp}] Warning: Could not save all output files: {save_error}")
            output_files = {"error": str(save_error)}
        
        total_processing_time = time.time() - start_time
        
        # Prepare response
        response_data = clean_for_json({
            "success": True,
            "message": "XML and JSON files processed successfully using your exact logic",
            "file_id": file_id,
            "xml_saved_path": xml_save_result["saved_path"],
            "json_saved_path": json_save_result["saved_path"],
            "processing_time": f"{total_processing_time:.2f}s",
            "summary": {
                "xml_filename": xml_file.filename,
                "json_filename": json_file.filename,
                "xml_customers": processing_result.get("total_customers_processed", 0),
                "master_customers": processing_result.get("total_master_records", 0),
                "total_cleaned_records": len(processing_result["cleaned_data"]),
                "total_error_records": len(processing_result["error_log"]),
                "success_rate": processing_result.get("success_rate", 0),
                "processing_time": processing_result.get("processing_time", "0s")
            },
            "output_files": output_files,
            "data_preview": {
                "first_5_cleaned": processing_result["cleaned_data"][:5] if processing_result["cleaned_data"] else [],
                "first_5_errors": processing_result["error_log"][:5] if processing_result["error_log"] else []
            }
        })
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[{current_timestamp}] ERROR in upload endpoint: {e}")
        traceback.print_exc()
        
        error_response = clean_for_json({
            "success": False,
            "message": "Processing failed",
            "error": str(e),
            "file_id": file_id,
            "timestamp": current_timestamp
        })
        return JSONResponse(content=error_response, status_code=500)

@app.get("/")
async def root():
    return JSONResponse(content={
        "message": "Multi-File Processor API is running",
        "timestamp": get_timestamp(),
        "endpoints": {
            "/upload/multi-files": "Upload XML, JSON (Master Data), Excel, PDF, and/or CSV files for processing",
            "/upload/xml-json": "Upload XML transactions + JSON master data for processing",
            "/health": "Health check",
            "/": "This endpoint"
        }
    })

@app.get("/health")
async def health_check():
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": get_timestamp(),
        "directories": {
            "data": str(data_dir),
            "output": str(output_dir)
        }
    })

if __name__ == "__main__":
    import uvicorn
    print("Starting Multi-File Processor API...")
    print(f"Data directory: {data_dir.absolute()}")
    print(f"Output directory: {output_dir.absolute()}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
