# -*- coding: utf-8 -*-
"""Lightweight text overlay drawn over the QGIS map canvas.

Used to show a transient progress message centered on the map while a
synchronous, main-thread operation runs. ``setProgress`` calls
``repaint()`` on this widget alone -- a synchronous, immediate paint of
just this label -- instead of ``QApplication.processEvents()``, which
used to drain the *entire* Qt event queue (user input, other timers)
from inside the read loop and let unrelated code reenter it while a
QgsFeatureIterator on the results layer was still open.

To avoid a distracting flicker on fast operations, the overlay is *armed* by
``start()`` but only becomes visible once ``delayMs`` has elapsed. The elapsed
time is measured with a plain ``QElapsedTimer`` and checked synchronously on
each ``setProgress()`` call, so if ``finish()`` is reached before ``delayMs``
the overlay never appears -- same behaviour as before, without relying on the
Qt event loop to dispatch a timer.
"""
from qgis.PyQt.QtWidgets import QLabel
from qgis.PyQt.QtCore import Qt, QElapsedTimer


class QGISRedMapOverlay(QLabel):
    """A semi-transparent, non-interactive label centered over a map canvas."""

    def __init__(self, canvas, delayMs=500):
        super().__init__(canvas)
        self._canvas = canvas
        self._baseText = ""
        self._delayMs = delayMs
        self._armed = False
        self._revealed = False
        self._elapsed = QElapsedTimer()
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
        self.hide()

    def start(self, baseText):
        """Arm the overlay with the given base text (already translated).

        It only becomes visible if ``delayMs`` elapses before ``finish()``.
        """
        self._baseText = baseText
        self.setText(baseText)
        self._armed = True
        self._revealed = False
        self._elapsed.start()

    def setProgress(self, percent):
        """Update the overlay to '<baseText> <percent>%' and repaint.

        Reveals the overlay once the arming delay has elapsed, then
        force-repaints just this widget so the text is actually painted
        between chunks -- without touching the rest of the event queue.
        """
        self.setText("{0} {1}%".format(self._baseText, percent))
        if self._armed and not self._revealed and self._elapsed.hasExpired(self._delayMs):
            self._reveal()
        if self._revealed:
            self._recenter()
            self.repaint()

    def finish(self):
        """Cancel the pending show (if any), hide and schedule deletion."""
        self._armed = False
        self._revealed = False
        self.hide()
        self.deleteLater()

    def _reveal(self):
        """Show the overlay once the arming delay has elapsed."""
        self._revealed = True
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
