import sys
from pathlib import Path

# Add project root to Python path so 'src' can be imported
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

import sys
from PyQt5.QtWidgets import QApplication
from src.gui.views.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
