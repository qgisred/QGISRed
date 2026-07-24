# -*- coding: utf-8 -*-
"""Lightweight text overlay drawn over the QGIS map canvas.

Used to show a transient progress message
centered on the map while a synchronous, main-thread operation runs. Because
the plugin does all its heavy work on the main thread, callers must trigger a
repaint after updating the overlay; ``setProgress`` calls
``QApplication.processEvents()`` so the text is actually painted between chunks.

To avoid a distracting flicker on fast operations, the overlay is *armed* by
``start()`` but only becomes visible once ``delayMs`` has elapsed. The delay
timer is dispatched by the ``processEvents()`` calls happening in the read loop,
so if ``finish()`` is reached before ``delayMs`` the overlay never appears.
"""
from qgis.PyQt.QtWidgets import QLabel, QApplication
from qgis.PyQt.QtCore import Qt, QTimer


class QGISRedMapOverlay(QLabel):
    """A semi-transparent, non-interactive label centered over a map canvas."""

    def __init__(self, canvas, delayMs=500):
        super().__init__(canvas)
        self._canvas = canvas
        self._baseText = ""
        self._delayMs = delayMs
        self._pending = False
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            "QLabel {"
            "  background-color: rgba(0, 0, 0, 160);"
            "  color: white;"
            "  padding: 12px 20px;"
            "  border-radius: 8px;"
            "  font-size: 14px;"
            "  font-weight: bold;"
            "}"
        )
        self._delayTimer = QTimer(self)
        self._delayTimer.setSingleShot(True)
        self._delayTimer.timeout.connect(self._reveal)
        self.hide()

    def start(self, baseText):
        """Arm the overlay with the given base text (already translated).

        It only becomes visible if ``delayMs`` elapses before ``finish()``.
        """
        self._baseText = baseText
        self.setText(baseText)
        self._pending = True
        self._delayTimer.start(self._delayMs)

    def setProgress(self, percent):
        """Update the overlay to '<baseText> <percent>%' and repaint.

        Always pumps the event loop so the pending delay timer can fire.
        """
        self.setText("{0} {1}%".format(self._baseText, percent))
        if self.isVisible():
            self._recenter()
        QApplication.processEvents()

    def finish(self):
        """Cancel the pending show (if any), hide and schedule deletion."""
        self._delayTimer.stop()
        self._pending = False
        self.hide()
        self.deleteLater()

    def _reveal(self):
        """Show the overlay once the arming delay has elapsed."""
        if not self._pending:
            return
        self._recenter()
        self.show()
        self.raise_()

    def _recenter(self):
        """Center the overlay over the canvas based on its current size hint."""
        self.adjustSize()
        size = self.sizeHint()
        x = (self._canvas.width() - size.width()) // 2
        y = (self._canvas.height() - size.height()) // 2
        self.move(max(x, 0), max(y, 0))
