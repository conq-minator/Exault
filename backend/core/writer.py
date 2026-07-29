"""
ExcelPlorer — Excel Writer

Responsible for injecting validated JSON data back into the original 
Excel template to produce the final output file.
"""

import logging
from pathlib import Path
from typing import Any

import openpyxl

from backend.core.schema import WorkbookSchema

logger = logging.getLogger(__name__)


class WriterError(Exception):
    """Raised when writing to the Excel file fails."""
    pass


class MissingSkuError(Exception):
    """Raised when SKUs from data are not found in the Excel template."""
    def __init__(self, missing_skus: list[str]):
        self.missing_skus = missing_skus
        super().__init__(f"SKUs not found in document: {', '.join(missing_skus)}")


class ExcelWriter:
    """
    Writes validated data into an Excel template.
    """

    def _normalize_sku(self, sku: Any) -> str:
        if sku is None:
            return ""
        s = str(sku).strip().lower()
        if s.endswith(".0"):
            try:
                float_val = float(s)
                if float_val.is_integer():
                    return str(int(float_val))
            except ValueError:
                pass
        return s

    def write(self, template_path: Path, output_path: Path, data: list[dict[str, Any]], schema: WorkbookSchema, skip_missing_skus: bool = False) -> None:
        """
        Inject data into the template and save the output.
        
        Args:
            template_path: Path to the original Excel template (.xlsx).
            output_path: Path where the filled .xlsx should be saved.
            data: List of validated data dictionaries.
            schema: The WorkbookSchema used to map columns.
            skip_missing_skus: If True, skips writing missing SKUs instead of raising MissingSkuError.
            
        Raises:
            WriterError: If the template cannot be loaded or written to.
        """
        if not template_path.exists():
            raise WriterError(f"Template not found at {template_path}")
            
        is_xls = template_path.suffix.lower() == ".xls"
        
        target_template_path = template_path
        temp_output_path = output_path
        
        # If it's an .xls file, use COM automation to convert to .xlsx first
        if is_xls:
            target_template_path = template_path.with_name(f"{template_path.stem}_temp.xlsx")
            temp_output_path = output_path.with_name(f"{output_path.stem}_temp.xlsx")
            try:
                self._convert_excel_format(template_path, target_template_path, ".xlsx")
            except Exception as e:
                logger.error(f"Format conversion failed to convert {template_path.name} to .xlsx: {e}")
                # Fallback to flat data if COM fails
                try:
                    import pandas as pd
                    df = pd.DataFrame(data)
                    df.to_excel(output_path.with_suffix(".xlsx"), index=False)
                    logger.info("Fallback: Wrote flat .xlsx data file.")
                    return
                except Exception as fallback_e:
                    raise WriterError(f"Failed to write Excel file via COM and fallback failed: {fallback_e}")
                    
        try:
            # Load the workbook preserving VBA/data validation where possible.
            # openpyxl drops some advanced features, but keeps basic formatting and validation.
            wb = openpyxl.load_workbook(target_template_path)
            
            data_sheets = schema.get_data_sheets()
            if not data_sheets:
                raise WriterError("No data entry sheets found in the template.")
                
            # Find the data sheet that contains a SKU column
            possible_sku_keys = ["Seller SKU ID", "SKU", "item_sku", "seller sku"]
            target_sheet_schema = None
            sku_key = None
            col_map: dict[str, int] = {}
            
            for sheet_candidate in data_sheets:
                candidate_map = {col.name: col.index for col in sheet_candidate.columns}
                for possible_key in possible_sku_keys:
                    for actual_col_name in candidate_map.keys():
                        if possible_key.lower() == actual_col_name.lower():
                            target_sheet_schema = sheet_candidate
                            sku_key = actual_col_name
                            col_map = candidate_map
                            break
                    if sku_key:
                        break
                if sku_key:
                    break
                    
            if not target_sheet_schema or not sku_key:
                raise WriterError("Could not identify SKU column in template. Required for matching.")
            
            if target_sheet_schema.name not in wb.sheetnames:
                raise WriterError(f"Expected sheet '{target_sheet_schema.name}' not found in workbook.")
                
            ws = wb[target_sheet_schema.name]
                
            sku_col_idx = col_map[sku_key]
            
            # Start scanning from after the header (header is 1-indexed)
            start_scan = target_sheet_schema.header_row + 1
            
            # Pre-scan the sheet to build a map of SKUs to row numbers
            existing_skus = {}
            for row_num in range(start_scan, ws.max_row + 1):
                cell_val = ws.cell(row=row_num, column=sku_col_idx).value
                if cell_val is not None and str(cell_val).strip() != "":
                    norm_val = self._normalize_sku(cell_val)
                    if norm_val:
                        existing_skus[norm_val] = row_num
                    
            missing_skus = []
            valid_items = []
            
            for item in data:
                item_sku = item.get(sku_key)
                if not item_sku:
                    # Ignore items with entirely missing SKU fields
                    continue
                    
                sku_norm = self._normalize_sku(item_sku)
                if not sku_norm:
                    continue

                if sku_norm not in existing_skus:
                    missing_skus.append(str(item_sku).strip())
                else:
                    valid_items.append((item, existing_skus[sku_norm]))
            
            if missing_skus and not skip_missing_skus:
                raise MissingSkuError(missing_skus)
            
            # Write data for matched rows
            for item, matched_row in valid_items:
                # Inject the value into the matched row
                for field_name, value in item.items():
                    if field_name in col_map:
                        col_idx = col_map[field_name]
                        cell = ws.cell(row=matched_row, column=col_idx)
                        
                        # Check if cell is already filled
                        if cell.value is not None and str(cell.value).strip() != "":
                            # Already filled, skip modifying it
                            continue
                            
                        # Convert string numbers to actual int/float for Excel
                        if isinstance(value, str):
                            value_str = value.strip()
                            if value_str.isdigit() or (value_str.startswith('-') and value_str[1:].isdigit()):
                                value = int(value_str)
                            else:
                                try:
                                    # Try float conversion if it has exactly one decimal point
                                    if '.' in value_str and value_str.count('.') == 1:
                                        value = float(value_str)
                                except ValueError:
                                    pass

                        cell.value = value
                        
            # Save the new workbook
            wb.save(temp_output_path)
            
            # If original was .xls, convert back to .xls
            if is_xls:
                try:
                    self._convert_excel_format(temp_output_path, output_path, ".xls")
                except Exception as e:
                    logger.error(f"Format conversion failed to convert back to .xls: {e}")
                    raise WriterError("Could not convert output back to .xls format.")
                finally:
                    # Cleanup temporary files
                    target_template_path.unlink(missing_ok=True)
                    temp_output_path.unlink(missing_ok=True)
            
            logger.info(f"Successfully wrote {len(valid_items)} rows to {output_path.name}")
            
        except (WriterError, MissingSkuError):
            raise
        except Exception as e:
            logger.error(f"Failed to write to Excel template: {e}", exc_info=True)
            raise WriterError(f"An error occurred while writing the Excel file: {e}")

    def _find_start_row(self, ws, header_row_index: int) -> int:
        """
        Dynamically finds the first blank row after the header row.
        This modularly skips sample data and tooltips found in Flipkart, Amazon, etc.
        """
        # header_row_index is 0-indexed relative to pandas (where row 1 is columns if header=0)
        # But our schema uses header=None so header_row_index 0 = Excel row 1.
        # So we start scanning from Excel row = header_row_index + 2
        start_scan = header_row_index + 2
        
        # Scan up to 20 rows down
        for row_num in range(start_scan, start_scan + 20):
            # Check how many cells in this row actually have content
            row_data = [cell.value for cell in ws[row_num]]
            non_empty_count = sum(1 for val in row_data if val is not None and str(val).strip() != "")
            
            # If the row is completely or mostly empty (<= 1 cell filled), it's the start row
            if non_empty_count <= 1:
                return row_num
                
        # Fallback if no empty row found
        return start_scan + 1

    def _convert_excel_format(self, input_path: Path, output_path: Path, target_ext: str) -> None:
        """
        Converts an Excel file format using a cascading fallback strategy:
        1. Microsoft Excel COM Automation (highest fidelity).
        2. LibreOffice Headless (free alternative).
        Raises WriterError if both fail.
        """
        format_code = 51 if target_ext.lower() == ".xlsx" else 56
        
        # Ensure paths are absolute
        abs_input = input_path.resolve()
        abs_output = output_path.resolve()
        
        if abs_output.exists():
            abs_output.unlink()
            
        # 1. Attempt Microsoft Excel COM Automation
        try:
            import win32com.client
            excel = win32com.client.DispatchEx("Excel.Application")
            excel.Visible = False
            excel.DisplayAlerts = False
            try:
                wb = excel.Workbooks.Open(str(abs_input))
                wb.SaveAs(str(abs_output), FileFormat=format_code)
                wb.Close(SaveChanges=False)
            finally:
                excel.Quit()
                del excel
            logger.debug(f"Converted via COM Automation: {input_path.name} -> {target_ext}")
            return
        except ImportError:
            logger.debug("pywin32 not installed, skipping COM automation.")
        except Exception as e:
            logger.warning(f"COM Automation failed: {e}. Falling back to LibreOffice.")
            
        # 2. Attempt LibreOffice Headless
        try:
            self._convert_with_libreoffice(abs_input, abs_output, target_ext)
            logger.debug(f"Converted via LibreOffice: {input_path.name} -> {target_ext}")
            return
        except Exception as e:
            logger.warning(f"LibreOffice conversion failed: {e}")
            
        raise WriterError("All external format conversion tools (Excel COM, LibreOffice) failed or are missing.")

    def _convert_with_libreoffice(self, input_path: Path, output_path: Path, target_ext: str) -> None:
        """
        Uses LibreOffice headless mode to convert the file format.
        """
        import subprocess
        import os
        import shutil
        
        # Standard LibreOffice installation paths on Windows
        lo_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        
        soffice_exe = None
        for p in lo_paths:
            if os.path.exists(p):
                soffice_exe = p
                break
                
        # If not found in standard paths, check system PATH
        if not soffice_exe:
            soffice_exe = shutil.which("soffice")
            
        if not soffice_exe:
            raise Exception("LibreOffice 'soffice.exe' not found in standard paths or system PATH.")
            
        outdir = output_path.parent
        target_fmt = "xlsx" if target_ext.lower() == ".xlsx" else "xls"
        
        cmd = [
            soffice_exe,
            "--headless",
            "--convert-to",
            target_fmt,
            str(input_path),
            "--outdir",
            str(outdir)
        ]
        
        # Run conversion
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"LibreOffice command failed: {result.stderr}")
            
        # LibreOffice outputs a file with the same base name as input but new extension
        expected_lo_output = outdir / f"{input_path.stem}{target_ext}"
        
        if not expected_lo_output.exists():
            raise Exception(f"LibreOffice completed but output file not found at {expected_lo_output}")
            
        # Rename to the requested output_path if it differs
        if expected_lo_output != output_path:
            shutil.move(str(expected_lo_output), str(output_path))
