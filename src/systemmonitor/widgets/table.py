"""
Sortable Table Widget
"""
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from typing import List, Dict, Any, Optional, Callable

from systemmonitor.styles.theme import theme_manager


class SortableTable(QTableWidget):
    """
    Sortable table widget with custom styling
    Supports filtering and custom cell rendering
    """
    
    def __init__(self, columns: List[Dict[str, Any]], parent=None):
        """
        Initialize table
        
        Args:
            columns: List of column definitions
                     [{'key': 'name', 'title': 'Name', 'width': 100}, ...]
        """
        super().__init__(parent)
        self._columns = columns
        self._data: List[Dict[str, Any]] = []
        self._setup_ui()
        self._apply_theme()
    
    def _setup_ui(self):
        """Setup table UI"""
        # Set columns
        self.setColumnCount(len(self._columns))
        headers = [col.get('title', col['key']) for col in self._columns]
        self.setHorizontalHeaderLabels(headers)
        
        # Configure table
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        
        # Header configuration
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Set column widths
        for i, col in enumerate(self._columns):
            if 'width' in col:
                self.setColumnWidth(i, col['width'])
        
        # Vertical header
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(32)
    
    def _apply_theme(self):
        """Apply theme styles"""
        c = theme_manager.colors
        self.setStyleSheet(f"""
            SortableTable {{
                background-color: {c.BG_CARD};
                color: {c.TEXT_PRIMARY};
                border: 1px solid {c.BORDER};
                border-radius: 8px;
                gridline-color: transparent;
            }}
            
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {c.BORDER};
            }}
            
            QTableWidget::item:selected {{
                background-color: {c.BG_HOVER};
                color: {c.TEXT_PRIMARY};
            }}
            
            QHeaderView::section {{
                background-color: {c.BG_SECONDARY};
                color: {c.TEXT_SECONDARY};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {c.BORDER};
                font-weight: bold;
            }}
            
            QHeaderView::section:hover {{
                background-color: {c.BG_HOVER};
            }}
        """)
    
    def set_data(self, data: List[Dict[str, Any]]):
        """Set table data"""
        self._data = data
        self.setRowCount(len(data))
        
        for row_idx, row_data in enumerate(data):
            for col_idx, col in enumerate(self._columns):
                key = col['key']
                value = row_data.get(key, '')
                
                # Format value
                if 'formatter' in col:
                    value = col['formatter'](value)
                
                item = QTableWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, row_data)  # Store full row data
                
                # Alignment
                align = col.get('align', Qt.AlignmentFlag.AlignLeft)
                item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
                
                self.setItem(row_idx, col_idx, item)
    
    def get_selected_row(self) -> Optional[Dict[str, Any]]:
        """Get selected row data"""
        selected = self.selectedItems()
        if selected:
            return selected[0].data(Qt.ItemDataRole.UserRole)
        return None
    
    def filter_data(self, text: str):
        """Filter table rows by text"""
        text = text.lower()
        for row in range(self.rowCount()):
            match = False
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.setRowHidden(row, not match)

