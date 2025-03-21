from typing import Optional

from PIL.Image import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtGui import QColor, QPaintEvent, QPainter, QPixmap
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QSizePolicy, QWidget

from fancyfolders.constants import FolderStyle
from fancyfolders.external.waitingspinnerwidget import QWaitingSpinner


class CentreFolderIconContainer(QWidget):
    """Container to hold a folder icon and loading spinner."""

    MINIMUM_SIZE = (400, 240)
    SPINNER_PADDING = 15
    SPINNER_COLOUR = (200, 200, 200)

    def __init__(self) -> None:
        super().__init__()

        # Ensure minimum size of the center folder icon
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(*self.MINIMUM_SIZE)
        self.setAcceptDrops(True)

        # Z-stack container to hold the folder icon and the spinner on different planes
        self.container = QGridLayout()
        self.container.setContentsMargins(0, 0, 0, 0)

        # Spinner
        spinner_container = QHBoxLayout()
        spinner_container.setContentsMargins(
            self.SPINNER_PADDING, self.SPINNER_PADDING,
            self.SPINNER_PADDING, self.SPINNER_PADDING)
        self.spinner = QWaitingSpinner(
            self, QColor.fromRgb(*self.SPINNER_COLOUR), 80.0,
            0.0, 50.0, 1.5,
            10, 6.0, 6.0, 10.0,
            False)
        spinner_container.addWidget(self.spinner)
        self.container.addLayout(spinner_container, 0, 0, Qt.AlignBottom | Qt.AlignRight)
        # TODO: fix spinner behind folder icon

        # Folder icon
        self.folder_icon = CentreFolderIcon()
        self.container.addWidget(self.folder_icon, 0, 0)

        self.setLayout(self.container)

    def set_loading(self):
        """Starts the spinner to indicate waiting for folder generation"""
        self.spinner.start()

    def set_image(self, image: Image, folder_style: FolderStyle):
        """Sets the folder icon after validating that it is the latest one"""
        self.spinner.stop()
        self.folder_icon.set_folder_image(image, folder_style)


class CentreFolderIcon(QLabel):
    """Displays the scaled preview folder image"""

    folder_pixmap: Optional[QPixmap] = None

    # TODO: override drag enter to render a dotted box around to accept drops

    def __init__(self):
        super().__init__()

    def set_folder_image(self, image: Image,
                         folder_style=FolderStyle.sequoia_light) -> None:
        """Sets the image on the display

        :param image: PIL Image to display
        :param folder_style: The folder style of the image to set in order to
            crop away any extra space
        """
        crop_rect_percentages = folder_style.preview_crop_percentages()
        crop_rect = QRect()
        crop_rect.setCoords(
            *tuple(int(image.size[0] * percent) for percent in crop_rect_percentages))

        # Remove any unnecessary blank space on the image to avoid weird UI layout
        cropped_image: ImageQt = ImageQt(image).copy(crop_rect)

        self.folder_pixmap = QPixmap(cropped_image)
        self.update()

    def paintEvent(self, _: QPaintEvent) -> None:
        """Custom paint event to scale the image when the size of the
        widget changes.
        """
        if self.folder_pixmap is None:
            return

        dpi_ratio = self.devicePixelRatio()
        self.folder_pixmap.setDevicePixelRatio(dpi_ratio)

        size = QSize(int(self.size().width() * dpi_ratio),
                     int(self.size().height() * dpi_ratio))
        painter = QPainter(self)
        point = QPoint(0, 0)

        scaled_pix = self.folder_pixmap.scaled(
            size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        point.setX(int((size.width() - scaled_pix.width()) / (2 * dpi_ratio)))
        point.setY(int((size.height() - scaled_pix.height()) / (2 * dpi_ratio)))

        painter.drawPixmap(point, scaled_pix)
        painter.end()
