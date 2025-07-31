# src/gui/windows/components/summary_update_methods.py
"""
Update methods for the Summary Widget - separated for better organization
This file contains all the specific update methods for each tab content
"""

from PyQt5.QtWidgets import QLabel, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
import pandas as pd
from typing import Dict, Any, List


class SummaryUpdate