# src/gui/windows/compoenents/dimensional_summary_widget.py
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QHBoxLayout,
    QProgressBar,
    QTextEdit,
    QComboBox,
    QGroupBox,
    QTabWidget,
    QAbstractItemView,
    QMenu,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
import pandas as pd
import logging
import json
import os
import sip  # type: ignore
from datetime import datetime
from typing import List, Optional

from src.models.dimensional.dimensional_result import DimensionalResult

class SummaryWidget:

    def _create_summary_widget(self) -> QWidget:
        """Create summary widget for overall statistics"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Statistics display
        self.stats_label = QLabel("No analysis performed yet")
        self.stats_label.setStyleSheet(
            "QLabel { font-size: 14px; padding: 10px; background-color: #f0f0f0; }"
        )
        layout.addWidget(self.stats_label)

        # Cavity comparison
        self.cavity_group = QGroupBox("Cavity Comparison")
        self.cavity_layout = QVBoxLayout()
        self.cavity_group.setLayout(self.cavity_layout)
        layout.addWidget(self.cavity_group)

        # Feature type breakdown
        self.feature_group = QGroupBox("Feature Type Breakdown")
        self.feature_layout = QVBoxLayout()
        self.feature_group.setLayout(self.feature_layout)
        layout.addWidget(self.feature_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _update_summary_display(self, results: List[DimensionalResult]):
        """Update the summary display with analysis results"""
        if not results:
            return

        # Get enhanced summary
        from src.services.dimensional_service import EnhancedDimensionalService

        service = EnhancedDimensionalService()
        summary = service.get_processing_summary(results)

        # Update main statistics
        stats_text = f"""
        <b>Analysis Results</b><br>
        Total Elements: {summary["total"]}<br>
        ✅ Passed: {summary["good"]} ({summary["success_rate"]:.1f}%)<br>
        ❌ Failed: {summary["bad"]}<br>
        ⚠️ Warnings: {summary["warning"]}<br>
        🔧 GD&T Features: {summary["gdt_count"]} ({summary["gdt_percentage"]:.1f}%)
        """
        self.stats_label.setText(stats_text)

        # Clear previous cavity info
        for i in reversed(range(self.cavity_layout.count())):
            self.cavity_layout.itemAt(i).widget().setParent(None)

        # Update cavity comparison
        cavity_summary = summary["cavity_summary"]
        for cavity, stats in cavity_summary.items():
            success_rate = (
                (stats["good"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            )
            cavity_label = QLabel(
                f"Cavity {cavity}: {stats['good']}/{stats['total']} passed ({success_rate:.1f}%)"
            )

            # Color code based on success rate
            if success_rate >= 95:
                color = "#4CAF50"  # Green
            elif success_rate >= 80:
                color = "#FF9800"  # Orange
            else:
                color = "#F44336"  # Red

            cavity_label.setStyleSheet(
                f"QLabel {{ color: {color}; font-weight: bold; padding: 5px; }}"
            )
            self.cavity_layout.addWidget(cavity_label)

        # Clear previous feature info
        for i in reversed(range(self.feature_layout.count())):
            self.feature_layout.itemAt(i).widget().setParent(None)

        # Update feature type breakdown
        feature_types = summary["feature_types"]
        for feature_type, count in feature_types.items():
            percentage = (count / summary["total"]) * 100
            feature_label = QLabel(
                f"{feature_type.title()}: {count} ({percentage:.1f}%)"
            )
            feature_label.setStyleSheet("QLabel { padding: 2px; }")
            self.feature_layout.addWidget(feature_label)