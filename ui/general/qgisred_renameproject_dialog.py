# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt import uic
from ...tools.utils.qgisred_ui_utils import QGISRedBanner
from ...tools.utils.qgisred_filesystem_utils import DIR_BACKUPS
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_renameproject_dialog.ui"))


class QGISRedRenameProjectDialog(QDialog, FORM_CLASS):
    # Common variables
    NewNetworkName = ""
    NewQGISName = ""
    NewFolderName = ""
    OldNetworkName = ""
    ProjectDirectory = ""
    QgisProjectBase = None
    ProcessDone = False
    RenameProject = False
    RenameQGISProject = False
    RenameBackups = False
    RenameFolder = False

    def __init__(self, parent=None, oldName="", project="", qgisProjectBase=None, canRenameFolder=True):
        """Constructor."""
        super(QGISRedRenameProjectDialog, self).__init__(parent)
        self.OldNetworkName = oldName
        self.ProjectDirectory = project
        self.QgisProjectBase = qgisProjectBase
        self._canRenameFolder = canRenameFolder
        self.setupUi(self)
        self.btAccept.clicked.connect(self.accept)

        self.tbNetworkName.setText(oldName)

        qgisRowVisible = qgisProjectBase is not None
        self.containerQgis.setVisible(qgisRowVisible)
        if qgisRowVisible:
            self.tbQGISName.setText(os.path.basename(qgisProjectBase))

        # Backups detection
        backupsFolder = os.path.join(self.ProjectDirectory, DIR_BACKUPS)
        hasBackups = False
        if os.path.isdir(backupsFolder):
            for f in os.listdir(backupsFolder):
                if f.startswith(self.OldNetworkName + "_") and f.endswith(".zip"):
                    hasBackups = True
                    break
        self.containerBackups.setVisible(hasBackups)

        currentFolderName = os.path.basename(os.path.normpath(self.ProjectDirectory))
        self.tbFolderName.setText(currentFolderName)
        self.tbFolderName.setEnabled(self.cbRenameFolder.isChecked())
        # While the folder is named after the project, typing a new project name keeps
        # suggesting the same folder name — until the user edits the folder field by hand.
        self._folderFollowsProjectName = currentFolderName == oldName

        self.cbRenameFolder.setEnabled(canRenameFolder)
        if not canRenameFolder:
            self.cbRenameFolder.setToolTip(self.tr("Another project in this folder is currently open in QGIS."))

        self.cbRenameProject.toggled.connect(self.tbNetworkName.setEnabled)
        self.cbRenameQGISProject.toggled.connect(self.tbQGISName.setEnabled)
        self.cbRenameFolder.toggled.connect(self.tbFolderName.setEnabled)
        self.tbNetworkName.textChanged.connect(self._onProjectNameChanged)
        self.tbFolderName.textEdited.connect(self._onFolderNameEdited)

        self.messageBar = QGISRedBanner.inject(self, self.gridLayout)
        self.adjustSize()

    def _onProjectNameChanged(self, text):
        if self._folderFollowsProjectName:
            self.tbFolderName.setText(text)

    def _onFolderNameEdited(self, _text):
        self._folderFollowsProjectName = False

    def pushMessage(self, title, text, level=0, duration=5):
        self.messageBar.pushMessage(title, text, level, duration)

    def accept(self):
        doProject = self.cbRenameProject.isChecked()
        doQgis = self.cbRenameQGISProject.isChecked() and self.QgisProjectBase is not None
        doRenameFolder = self.cbRenameFolder.isChecked() and self._canRenameFolder

        if not doProject and not doQgis and not doRenameFolder:
            self.pushMessage(self.tr("Validations"), self.tr("At least one option must be selected"), level=1)
            return

        if doProject:
            name = self.tbNetworkName.text().strip()
            if not name:
                self.pushMessage(self.tr("Validations"), self.tr("Not valid New Project Name"), level=1)
                return
            if name == self.OldNetworkName:
                doProject = False  # checkbox checked but name unchanged → treat as no rename
            elif os.path.exists(os.path.join(self.ProjectDirectory, name + "_Pipes.shp")):
                self.pushMessage(self.tr("Validations"), self.tr("There is already a project with this name in the project folder."), level=1)
                return
            else:
                self.NewNetworkName = name

        if doQgis:
            qname = self.tbQGISName.text().strip()
            if not qname:
                self.pushMessage(self.tr("Validations"), self.tr("Not valid QGIS file name"), level=1)
                return
            oldQgisBasename = os.path.basename(self.QgisProjectBase)
            if qname == oldQgisBasename:
                doQgis = False  # checkbox checked but name unchanged → treat as no rename
            else:
                self.NewQGISName = qname

        if doRenameFolder:
            folderName = self.tbFolderName.text().strip()
            if not folderName:
                self.pushMessage(self.tr("Validations"), self.tr("Not valid folder name"), level=1)
                return
            currentFolderName = os.path.basename(os.path.normpath(self.ProjectDirectory))
            if folderName == currentFolderName:
                doRenameFolder = False  # checkbox checked but name unchanged → treat as no rename
            else:
                targetFolder = os.path.join(os.path.dirname(self.ProjectDirectory), folderName)
                if os.path.exists(targetFolder):
                    self.pushMessage(self.tr("Validations"), self.tr("There is already a folder with this name."), level=1)
                    return
                self.NewFolderName = folderName

        if not doProject and not doQgis and not doRenameFolder:
            self.pushMessage(self.tr("Validations"), self.tr("At least one name must be different from the original"), level=1)
            return

        self.RenameProject = doProject
        self.RenameQGISProject = doQgis
        self.RenameBackups = self.cbRenameBackups.isChecked() and self.cbRenameBackups.isVisible()
        self.RenameFolder = doRenameFolder
        self.ProcessDone = True
        self.close()
