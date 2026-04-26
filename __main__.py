"""
System Monitor - Main Entry Point
"""
import sys
import os

# Ensure proper path setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main application entry point"""
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt

    app = QApplication(sys.argv)
    
    # Import and create main window
    from core.window import MainWindow
    from core.theme import ThemeManager
    
    # Apply theme
    theme_manager = ThemeManager()
    app.setStyleSheet(theme_manager.get_stylesheet())
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start data collection
    from data.collector import DataCollector
    collector = DataCollector()
    collector.start()

    # Connect data updates to window
    collector.data_ready.connect(window.update_data)

    # Connect heavy operation signals to views
    from views.overview_page import OverviewPage
    from views.cpu import CPUView
    if isinstance(window._views["overview"], OverviewPage):
        window._views["overview"].set_data_collector(collector)
    if isinstance(window._views["cpu"], CPUView):
        window._views["cpu"].set_data_collector(collector)
    
    # Run application
    try:
        result = app.exec_()
    finally:
        # Cleanup
        collector.stop()
    
    return result


if __name__ == "__main__":
    sys.exit(main())
