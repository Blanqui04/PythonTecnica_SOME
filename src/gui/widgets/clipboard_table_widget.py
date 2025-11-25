# src/gui/widgets/clipboard_table_widget.py
"""
Enhanced Clipboard Table Widget
===============================

Provides global Ctrl+C/Ctrl+V support for all table widgets in the application.
Supports:
- Copy selected cells to clipboard (Ctrl+C)
- Paste from clipboard to cells (Ctrl+V)
- Copy/paste entire rows
- Copy/paste multiple selections
- Integration with Excel and other spreadsheets

Author: Enhanced Features Module
Date: November 2025
"""

from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QApplication, QMessageBox,
    QComboBox, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QColor, QFont
import logging

logger = logging.getLogger(__name__)


class ClipboardTableWidget(QTableWidget):
    """
    Enhanced QTableWidget with full clipboard support (Ctrl+C, Ctrl+V).
    
    Features:
    - Copy selected cells/rows to clipboard in tab-separated format
    - Paste from clipboard (supports Excel, CSV, and plain text)
    - Maintains cell formatting after paste
    - Handles dropdown/combo cells
    - Multi-cell selection support
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_clipboard_support()
    
    def _setup_clipboard_support(self):
        """Setup enhanced clipboard support"""
        # Enable extended selection for multi-cell operations
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
    
    def keyPressEvent(self, event):
        """Handle key press events for clipboard operations"""
        # Ctrl+C - Copy
        if event.matches(QKeySequence.Copy):
            self._copy_to_clipboard()
            return
        
        # Ctrl+V - Paste
        if event.matches(QKeySequence.Paste):
            self._paste_from_clipboard()
            return
        
        # Ctrl+X - Cut (Copy then clear)
        if event.matches(QKeySequence.Cut):
            self._cut_to_clipboard()
            return
        
        # Ctrl+A - Select All
        if event.matches(QKeySequence.SelectAll):
            self.selectAll()
            return
        
        # Delete/Backspace - Clear selected cells
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self._clear_selected_cells()
            return
        
        # Default key handling
        super().keyPressEvent(event)
    
    def _copy_to_clipboard(self):
        """Copy selected cells to clipboard in tab-separated format"""
        selected = self.selectedIndexes()
        if not selected:
            return
        
        # Get selection bounds
        rows = sorted(set(index.row() for index in selected))
        cols = sorted(set(index.column() for index in selected))
        
        # Build text matrix
        clipboard_text = []
        for row in rows:
            row_data = []
            for col in cols:
                # Check if cell is selected
                if self.item(row, col) and any(
                    idx.row() == row and idx.column() == col for idx in selected
                ):
                    # Handle combo box cells
                    cell_widget = self.cellWidget(row, col)
                    if isinstance(cell_widget, QComboBox):
                        row_data.append(cell_widget.currentText())
                    else:
                        item = self.item(row, col)
                        row_data.append(item.text() if item else "")
                else:
                    # Include empty for non-selected cells in range
                    item = self.item(row, col)
                    if item and any(idx.row() == row and idx.column() == col for idx in selected):
                        row_data.append(item.text())
                    else:
                        row_data.append("")
            clipboard_text.append("\t".join(row_data))
        
        # Set clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(clipboard_text))
        
        logger.info(f"Copied {len(rows)} row(s), {len(cols)} column(s) to clipboard")
    
    def _paste_from_clipboard(self):
        """Paste data from clipboard to table"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        
        if not text:
            return
        
        # Get starting position
        selected = self.selectedIndexes()
        if selected:
            start_row = min(idx.row() for idx in selected)
            start_col = min(idx.column() for idx in selected)
        else:
            start_row = 0
            start_col = 0
        
        # Parse clipboard text
        lines = text.strip().split('\n')
        pasted_count = 0
        
        for row_offset, line in enumerate(lines):
            # Handle tab-separated or comma-separated values
            if '\t' in line:
                values = line.split('\t')
            else:
                values = line.split(',')
            
            target_row = start_row + row_offset
            
            # Expand table if needed
            if target_row >= self.rowCount():
                self.setRowCount(target_row + 1)
            
            for col_offset, value in enumerate(values):
                target_col = start_col + col_offset
                
                if target_col >= self.columnCount():
                    continue
                
                value = value.strip()
                
                # Check if target cell has a combo box
                cell_widget = self.cellWidget(target_row, target_col)
                if isinstance(cell_widget, QComboBox):
                    # Try to set combo value
                    items = [cell_widget.itemText(i) for i in range(cell_widget.count())]
                    if value in items:
                        cell_widget.setCurrentText(value)
                        pasted_count += 1
                    elif cell_widget.isEditable():
                        cell_widget.setCurrentText(value)
                        pasted_count += 1
                else:
                    # Regular cell
                    item = self.item(target_row, target_col)
                    if not item:
                        item = QTableWidgetItem()
                        self.setItem(target_row, target_col, item)
                    
                    # Check if cell is editable
                    if item.flags() & Qt.ItemIsEditable:
                        item.setText(value)
                        pasted_count += 1
        
        if pasted_count > 0:
            logger.info(f"Pasted {pasted_count} cell(s) from clipboard")
    
    def _cut_to_clipboard(self):
        """Cut selected cells (copy then clear)"""
        self._copy_to_clipboard()
        self._clear_selected_cells()
    
    def _clear_selected_cells(self):
        """Clear content of selected cells"""
        selected = self.selectedIndexes()
        cleared_count = 0
        
        for index in selected:
            row, col = index.row(), index.column()
            
            # Check if cell has a combo box
            cell_widget = self.cellWidget(row, col)
            if isinstance(cell_widget, QComboBox):
                # Reset to first item or empty
                if cell_widget.count() > 0:
                    cell_widget.setCurrentIndex(0)
                    cleared_count += 1
            else:
                item = self.item(row, col)
                if item and (item.flags() & Qt.ItemIsEditable):
                    item.setText("")
                    cleared_count += 1
        
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} cell(s)")


class DimensionalClipboardTable(ClipboardTableWidget):
    """
    Specialized clipboard table for dimensional data.
    
    Additional features:
    - Smart numeric value handling
    - Format preservation for measurements
    - Calculated column protection
    - Status column awareness
    """
    
    # Columns that are calculated and should not be directly edited
    CALCULATED_COLUMNS = [17, 18, 19, 20, 21, 22, 23]  # min, max, mean, std, pp, ppk, status
    
    # Columns that should be formatted as numbers
    NUMERIC_COLUMNS = [9, 10, 11, 12, 13, 14, 15, 16]  # nominal, tolerances, measurements
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_ui = None
    
    def set_parent_ui(self, parent_ui):
        """Set reference to parent UI for styling callbacks"""
        self.parent_ui = parent_ui
    
    def _paste_from_clipboard(self):
        """Enhanced paste with dimensional-specific handling"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        
        if not text:
            return
        
        selected = self.selectedIndexes()
        if selected:
            start_row = min(idx.row() for idx in selected)
            start_col = min(idx.column() for idx in selected)
        else:
            start_row = 0
            start_col = 0
        
        lines = text.strip().split('\n')
        pasted_count = 0
        
        for row_offset, line in enumerate(lines):
            if '\t' in line:
                values = line.split('\t')
            else:
                values = line.split(',')
            
            target_row = start_row + row_offset
            
            if target_row >= self.rowCount():
                continue  # Don't auto-expand for dimensional tables
            
            for col_offset, value in enumerate(values):
                target_col = start_col + col_offset
                
                if target_col >= self.columnCount():
                    continue
                
                # Skip calculated columns
                if target_col in self.CALCULATED_COLUMNS:
                    continue
                
                value = value.strip()
                
                # Handle combo box cells
                cell_widget = self.cellWidget(target_row, target_col)
                if isinstance(cell_widget, QComboBox):
                    items = [cell_widget.itemText(i) for i in range(cell_widget.count())]
                    if value in items:
                        cell_widget.setCurrentText(value)
                        pasted_count += 1
                    elif cell_widget.isEditable():
                        cell_widget.setCurrentText(value)
                        pasted_count += 1
                    continue
                
                item = self.item(target_row, target_col)
                if not item:
                    item = QTableWidgetItem()
                    self.setItem(target_row, target_col, item)
                
                if not (item.flags() & Qt.ItemIsEditable):
                    continue
                
                # Format numeric values
                if target_col in self.NUMERIC_COLUMNS and value:
                    try:
                        numeric_val = float(value.replace(',', '.'))
                        value = f"{numeric_val:.3f}"
                    except ValueError:
                        pass  # Keep original value if not numeric
                
                item.setText(value)
                pasted_count += 1
        
        if pasted_count > 0:
            logger.info(f"Pasted {pasted_count} cell(s) to dimensional table")
            # Trigger parent to mark unsaved changes
            if self.parent_ui and hasattr(self.parent_ui, '_mark_unsaved_changes'):
                self.parent_ui._mark_unsaved_changes()


class NumericPasteTableWidget(ClipboardTableWidget):
    """
    Table widget optimized for pasting numeric data (for element input).
    
    Features:
    - Validates numeric values on paste
    - Auto-formats decimal places
    - Handles single-column paste for measurement values
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.numeric_only = True
        self.decimal_places = 3
    
    def _paste_from_clipboard(self):
        """Paste with numeric validation"""
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        
        if not text:
            return
        
        selected = self.selectedIndexes()
        if selected:
            start_row = min(idx.row() for idx in selected)
            start_col = min(idx.column() for idx in selected)
        else:
            start_row = 0
            start_col = 0
        
        lines = text.strip().split('\n')
        pasted_count = 0
        skipped_count = 0
        
        for row_offset, line in enumerate(lines):
            # Split by tab, comma, or semicolon
            values = line.replace(';', '\t').replace(',', '\t').split('\t')
            
            target_row = start_row + row_offset
            
            # Auto-expand table if needed
            if target_row >= self.rowCount():
                self.setRowCount(target_row + 1)
                # Initialize new row
                for col in range(self.columnCount()):
                    new_item = QTableWidgetItem("")
                    new_item.setTextAlignment(Qt.AlignCenter)
                    self.setItem(target_row, col, new_item)
            
            for col_offset, value in enumerate(values):
                target_col = start_col + col_offset
                
                if target_col >= self.columnCount():
                    continue
                
                value = value.strip()
                
                if not value:
                    continue
                
                # Validate numeric if required
                if self.numeric_only:
                    try:
                        # Handle different decimal separators
                        numeric_val = float(value.replace(',', '.'))
                        value = f"{numeric_val:.{self.decimal_places}f}"
                    except ValueError:
                        skipped_count += 1
                        continue
                
                item = self.item(target_row, target_col)
                if not item:
                    item = QTableWidgetItem()
                    item.setTextAlignment(Qt.AlignCenter)
                    self.setItem(target_row, target_col, item)
                
                item.setText(value)
                pasted_count += 1
        
        if pasted_count > 0 or skipped_count > 0:
            message = f"Enganxats {pasted_count} valor(s) numèric(s)"
            if skipped_count > 0:
                message += f" ({skipped_count} valor(s) no numèric(s) omès(os))"
            logger.info(message)
            
            # Show notification if significant paste
            if pasted_count > 5:
                QMessageBox.information(
                    self,
                    "Valors Enganxats",
                    message
                )


# Export all classes
__all__ = [
    'ClipboardTableWidget',
    'DimensionalClipboardTable',
    'NumericPasteTableWidget'
]
