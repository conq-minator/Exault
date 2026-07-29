"""
ExcelPlorer — Report Generator

Formats the validation JSON payload into human-readable TXT or HTML reports.
"""

from typing import Any


class ReportGenerator:
    """Formats validation report data into different output types."""
    
    @staticmethod
    def generate_txt(payload: dict[str, Any]) -> str:
        """
        Generate a plain-text report.
        
        Args:
            payload: The dictionary saved in report.json (from /api/validate).
            
        Returns:
            A formatted string.
        """
        is_valid = payload.get("is_valid", False)
        item_count = payload.get("item_count", 0)
        report_data = payload.get("report", {})
        issues = report_data.get("issues", [])
        
        errors = [i for i in issues if i["severity"] == "ERROR"]
        warnings = [i for i in issues if i["severity"] == "WARNING"]
        infos = [i for i in issues if i["severity"] == "INFO"]
        
        lines = []
        lines.append("========================================")
        lines.append("        EXCELPLORER VALIDATION REPORT   ")
        lines.append("========================================")
        lines.append("")
        
        lines.append("--- SUMMARY ---")
        lines.append(f"Status:      {'PASSED' if is_valid else 'FAILED'}")
        lines.append(f"Total Rows:  {item_count}")
        lines.append(f"Errors:      {len(errors)}")
        lines.append(f"Warnings:    {len(warnings)}")
        lines.append(f"Corrections: {len(infos)}")
        lines.append("")
        
        if errors:
            lines.append("--- ERRORS ---")
            for e in errors:
                lines.append(f"[Row {e['item_index'] + 1}] {e['field']}: {e['message']}")
            lines.append("")
            
        if warnings:
            lines.append("--- WARNINGS ---")
            for w in warnings:
                lines.append(f"[Row {w['item_index'] + 1}] {w['field']}: {w['message']}")
            lines.append("")
            
        if infos:
            lines.append("--- AUTO-CORRECTIONS ---")
            for i in infos:
                lines.append(f"[Row {i['item_index'] + 1}] {i['field']}: {i['message']}")
            lines.append("")
            
        return "\n".join(lines)

    @staticmethod
    def generate_html(payload: dict[str, Any]) -> str:
        """
        Generate a styled HTML report.
        """
        is_valid = payload.get("is_valid", False)
        item_count = payload.get("item_count", 0)
        report_data = payload.get("report", {})
        issues = report_data.get("issues", [])
        
        errors = [i for i in issues if i["severity"] == "ERROR"]
        warnings = [i for i in issues if i["severity"] == "WARNING"]
        infos = [i for i in issues if i["severity"] == "INFO"]
        
        status_color = "green" if is_valid else "red"
        status_text = "PASSED" if is_valid else "FAILED"
        
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>ExcelPlorer Validation Report</title>",
            "<style>",
            "body { font-family: sans-serif; margin: 40px; color: #333; }",
            "h1 { border-bottom: 2px solid #ccc; padding-bottom: 10px; }",
            ".summary { background: #f9f9f9; padding: 20px; border-radius: 5px; margin-bottom: 30px; }",
            f".status {{ color: {status_color}; font-weight: bold; font-size: 1.2em; }}",
            "table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }",
            "th, td { padding: 10px; text-align: left; border-bottom: 1px solid #eee; }",
            "th { background: #f2f2f2; }",
            ".error { color: #d32f2f; }",
            ".warning { color: #f57c00; }",
            ".info { color: #1976d2; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>ExcelPlorer Validation Report</h1>",
            "<div class='summary'>",
            "<h2>Summary</h2>",
            f"<p>Status: <span class='status'>{status_text}</span></p>",
            f"<p>Total Rows: <strong>{item_count}</strong></p>",
            f"<p>Errors: <strong>{len(errors)}</strong></p>",
            f"<p>Warnings: <strong>{len(warnings)}</strong></p>",
            f"<p>Auto-Corrections: <strong>{len(infos)}</strong></p>",
            "</div>"
        ]
        
        def render_table(title, items, css_class):
            if not items:
                return
            html.append(f"<h2 class='{css_class}'>{title}</h2>")
            html.append("<table>")
            html.append("<tr><th>Row</th><th>Field</th><th>Message</th></tr>")
            for item in items:
                row = item['item_index'] + 1
                field = item.get('field', 'N/A')
                msg = item.get('message', '')
                html.append(f"<tr><td>{row}</td><td>{field}</td><td>{msg}</td></tr>")
            html.append("</table>")
            
        render_table("Errors", errors, "error")
        render_table("Warnings", warnings, "warning")
        render_table("Auto-Corrections", infos, "info")
        
        html.append("</body></html>")
        return "\n".join(html)
