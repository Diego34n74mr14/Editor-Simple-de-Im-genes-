import os  # Permite interactuar con funciones del sistema operativo (como listar directorios)
import sys  # Proporciona acceso a variables y funciones del intérprete de Python (como cerrar la app)
from pathlib import (
    Path,
)  # Herramienta moderna para manipular rutas de archivos de forma segura en Windows/Linux

from PyQt5.QtCore import (
    Qt,
)  # Importa las constantes principales de Qt (como alineaciones de texto y flags)
from PyQt5.QtGui import (
    QImage,
    QPixmap,
)  # Importa las clases para el manejo y renderizado de imágenes en la interfaz gráfica
from PyQt5.QtWidgets import (  # Importa todos los componentes visuales necesarios para la interfaz:
    QApplication,  # Gestiona el flujo de control y la configuración principal de la aplicación
    QFileDialog,  # Ventana emergente para seleccionar archivos o carpetas del sistema
    QHBoxLayout,  # Contenedor para organizar elementos de forma horizontal
    QLabel,  # Elemento para mostrar texto o imágenes en la pantalla
    QListWidget,  # Lista interactiva para mostrar elementos seleccionables
    QMessageBox,  # Ventana emergente para mostrar avisos, advertencias o errores
    QPushButton,  # Botón clásico interactivo
    QVBoxLayout,  # Contenedor para organizar elementos de forma vertical
    QWidget,  # La clase base para todos los objetos de la interfaz de usuario
)
from PIL import (
    Image,
    ImageFilter,
)  # Importa las herramientas de la librería Pillow para edición y filtros de imágenes


class ImageProcessor:
    """Gestiona la carga, edición y visualización de imágenes."""

    def __init__(self, label, list_widget, parent=None):
        """Inicializa el procesador vinculando los elementos visuales de la interfaz."""
        self.image = None  # Almacenará el objeto de imagen Pillow actual
        self.filename = None  # Guardará el nombre del archivo de la imagen seleccionada
        self.workdir = ""  # Guardará la ruta de la carpeta de trabajo actual
        self.save_dir = "Modified"  # Nombre de la subcarpeta donde se guardarán los cambios
        self.label = label  # Vincula la etiqueta de la interfaz donde se dibuja la imagen
        self.list_widget = list_widget  # Vincula el componente de lista de archivos
        self.parent = parent  # Guarda el componente padre (la ventana) para centrar los mensajes emergentes

    def load_image(self, filename):
        """Carga una imagen desde la carpeta seleccionada."""
        try:  # Bloque de seguridad para capturar errores si el archivo está corrupto o inaccesible
            self.filename = filename  # Guarda el nombre del archivo elegido
            fullname = (
                Path(self.workdir).resolve() / filename
            )  # Genera una ruta absoluta limpia y compatible con Windows

            self.image = Image.open(str(fullname)).convert(
                "RGBA"
            )  # Abre la imagen con Pillow y la convierte a canales de color RGBA
            self.show_image()  # Llama al método para dibujar la imagen recién cargada en la pantalla
        except Exception as e:  # Si algo falla en el proceso anterior...
            QMessageBox.critical(  # Muestra una ventana de error crítico al usuario
                self.parent or self.label,  # Posiciona el mensaje sobre la interfaz
                "Error",  # Título de la ventana flotante
                f"No se pudo cargar la imagen:\n{e}",  # Detalle del error ocurrido
            )

    def ensure_save_dir(self):
        """Crea la carpeta de salida si no existe."""
        path = (
            Path(self.workdir) / self.save_dir
        )  # Define la ruta hacia la subcarpeta "Modified"
        path.mkdir(
            parents=True, exist_ok=True
        )  # Crea físicamente la carpeta en el disco si aún no existe
        return path  # Devuelve el objeto de la ruta lista para usarse

    def save_image(self):
        """Guarda una copia modificada en la carpeta de salida."""
        if (
            self.image is None or self.filename is None
        ):  # Si no hay ninguna imagen cargada en el editor...
            return  # Cancela la ejecución de la función de inmediato

        path = self.ensure_save_dir()  # Obtiene la ruta de la carpeta "Modified" asegurando su existencia
        fullname = (
            path / self.filename
        )  # Define la ruta completa incluyendo el nombre del archivo original
        self.image.convert("RGB").save(
            str(fullname)
        )  # Transforma temporalmente a RGB (para soportar JPEG) y guarda en el disco

    def show_image(self):
        """Muestra la imagen actual en la etiqueta principal."""
        if (
            self.image is None
        ):  # Si no se ha cargada nada, escribe un mensaje de guía en pantalla
            self.label.setText("Seleccione una imagen")  # Establece el texto
            return  # Sale de la función

        self.label.clear()  # Limpia cualquier texto o imagen previa de la etiqueta gráfica

        data = self.image.tobytes(
            "raw", "RGBA"
        )  # Extrae la matriz de bytes puros de la imagen de Pillow
        qimage = QImage(  # Construye una imagen nativa de Qt usando esos bytes crudos
            data,  # Puntero a los bytes de la imagen
            self.image.size[0],  # Ancho de la imagen original
            self.image.size[1],  # Alto de la imagen original
            QImage.Format_RGBA8888,  # Especifica que los bytes vienen en formato de color RGBA estándar
        )

        self._current_qimage_bytes = data  # Truco de memoria: Mantiene vivos los bytes para evitar cierres inesperados de la app

        pixmap = QPixmap.fromImage(
            qimage
        )  # Convierte la QImage en un mapa de píxeles optimizado para pantallas (QPixmap)

        target_w = max(
            1, self.label.width()
        )  # Obtiene el ancho actual de la etiqueta en la interfaz (mínimo 1 píxel)
        target_h = max(
            1, self.label.height()
        )  # Obtiene el alto actual de la etiqueta en la interfaz (mínimo 1 píxel)
        scaled_pixmap = pixmap.scaled(  # Redimensiona la imagen de forma dinámica al tamaño del contenedor
            target_w,  # Ancho destino
            target_h,  # Alto destino
            Qt.KeepAspectRatio,  # Mantiene la proporción original de la imagen para que no se deforme
            Qt.SmoothTransformation,  # Aplica un filtro de suavizado anti-aliasing de alta calidad
        )
        self.label.setPixmap(
            scaled_pixmap
        )  # Introduce finalmente la imagen redimensionada dentro del QLabel visual

    def apply_transform(self, transform):
        """Aplica una transformación Pillow y actualiza la vista."""
        if (
            self.image is None
        ):  # Valida que el usuario tenga algo seleccionado antes de editar
            QMessageBox.information(  # Lanza un aviso informativo en pantalla
                self.parent or self.label,  # Ubicación visual del mensaje
                "Editor simple",  # Título de la ventana
                "Primero selecciona una imagen.",  # Mensaje instructivo
            )
            return  # Detiene la transformación

        self.image = transform(
            self.image
        )  # Aplica la función lambda (filtro/rotación) a la imagen actual
        self.save_image()  # Guarda automáticamente el nuevo resultado en la carpeta "Modified"
        self.show_image()  # Actualiza la interfaz de usuario con los nuevos píxeles en pantalla

    def do_left(self):
        """Rota la imagen 90 grados hacia la izquierda."""
        self.apply_transform(
            lambda img: img.transpose(Image.Transpose.ROTATE_90)
        )  # Aplica rotación geométrica de 90°

    def do_right(self):
        """Rota la imagen 90 grados hacia la derecha (270 en sentido horario)."""
        self.apply_transform(
            lambda img: img.transpose(Image.Transpose.ROTATE_270)
        )  # Aplica rotación geométrica de 270°

    def do_flip(self):
        """Invierte la imagen horizontalmente (efecto espejo)."""
        self.apply_transform(
            lambda img: img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        )  # Voltea de izquierda a derecha

    def do_sharpen(self):
        """Aumenta la nitidez de la imagen aplicando un filtro de realce."""
        self.apply_transform(
            lambda img: img.filter(ImageFilter.SHARPEN)
        )  # Pasa la imagen por el filtro Kernel SHARPEN

    def do_bw(self):
        """Convierte la imagen a escala de grises (Blanco y Negro)."""
        self.apply_transform(
            lambda img: img.convert("L").convert("RGBA")
        )  # Convierte a luminancia ('L') y regresa a 'RGBA' para compatibilidad gráfica

    def show_chosen_image(self):
        """Carga la imagen seleccionada en la lista."""
        if (
            self.list_widget.currentRow() < 0
        ):  # Si el usuario hace clic en el vacío de la lista o no hay selección...
            return  # No hace nada

        filename = (
            self.list_widget.currentItem().text()
        )  # Recupera el nombre en texto del archivo seleccionado en la lista
        if (
            self.workdir
        ):  # Si hay un directorio válido asignado, procede a cargar la imagen
            self.load_image(filename)


# --- Interfaz de usuario ---
app = QApplication(
    sys.argv
)  # Instancia principal de Qt obligatoria para inicializar cualquier aplicación visual
win = QWidget()  # Crea la ventana principal contenedora de la aplicación
win.resize(700, 500)  # Define el tamaño inicial de la ventana (700x500 píxeles)
win.setWindowTitle("Editor simple")  # Asigna el título de la barra superior de la ventana

lb_image = QLabel(
    "Seleccione una imagen"
)  # Crea la etiqueta central destinada a renderizar las imágenes
lb_image.setAlignment(
    Qt.AlignCenter
)  # Centra tanto el texto de guía como la imagen en medio del QLabel
lb_image.setStyleSheet(
    "border: 1px solid #aaa; background: #f5f5f5;"
)  # Añade diseño CSS (borde gris y fondo gris claro)

btn_dir = QPushButton("Carpeta")  # Crea el botón para buscar directorios
lw_files = (
    QListWidget()
)  # Crea la lista interactiva lateral para desplegar los archivos descubiertos
lw_files.setAlternatingRowColors(
    True
)  # Activa colores alternos en los renglones de la lista (cebra) para leer mejor

btn_left = QPushButton("Izquierda")  # Botón de rotación izquierda
btn_right = QPushButton("Derecha")  # Botón de rotación derecha
btn_flip = QPushButton("Reflejo")  # Botón para efecto espejo
btn_sharp = QPushButton("Nitidez")  # Botón para el filtro de enfoque
btn_bw = QPushButton("B/N")  # Botón para convertir a blanco y negro

row = QHBoxLayout()  # Layout horizontal principal encargado de dividir la pantalla en dos columnas
col1 = (
    QVBoxLayout()
)  # Layout vertical (columna 1, izquierda) para el buscador y la lista de archivos
col2 = (
    QVBoxLayout()
)  # Layout vertical (columna 2, derecha) para el visor de fotos y botonera de edición

col1.addWidget(btn_dir)  # Añade el botón de carpeta arriba en la columna izquierda
col1.addWidget(
    lw_files
)  # Añade la lista de archivos debajo del botón de carpeta en la columna izquierda
col2.addWidget(
    lb_image, 1
)  # Añade el visor de imágenes arriba en la columna derecha, asignándole prioridad de expansión (factor 1)

row_tools = (
    QHBoxLayout()
)  # Layout horizontal interno (faja) exclusivo para agrupar los botones de edición
row_tools.addWidget(btn_left)  # Agrega el botón Izquierda a la hilera de herramientas
row_tools.addWidget(btn_right)  # Agrega el botón Derecha a la hilera de herramientas
row_tools.addWidget(btn_flip)  # Agrega el botón Reflejo a la hilera de herramientas
row_tools.addWidget(btn_sharp)  # Agrega el botón Nitidez a la hilera de herramientas
row_tools.addWidget(btn_bw)  # Agrega el botón Blanco y Negro a la hilera de herramientas
col2.addLayout(
    row_tools
)  # Inserta la hilera de herramientas completa debajo del visor de imágenes en la columna derecha

row.addLayout(
    col1, 30
)  # Acopla la columna 1 (izquierda) al layout maestro ocupando el 30% del ancho total de la ventana
row.addLayout(
    col2, 70
)  # Acopla la columna 2 (derecha) al layout maestro ocupando el 70% del ancho total de la ventana
win.setLayout(
    row
)  # Aplica de manera definitiva la configuración del diseño maestro 'row' sobre la ventana


def filter_files(files, extensions):
    """Filtra archivos por extensiones válidas."""
    result = []  # Lista vacía para recolectar los nombres de imágenes válidas encontrados
    valid_extensions = {
        ext.lower() for ext in extensions
    }  # Convierte la lista de extensiones en un Set optimizado de minúsculas
    for filename in files:  # Itera a través de todos los archivos de la lista original
        if (
            os.path.splitext(filename)[1].lower() in valid_extensions
        ):  # Si la extensión del archivo coincide...
            result.append(filename)  # Lo agrega a los resultados
    return sorted(result)  # Devuelve la lista filtrada ordenada alfabéticamente


def choose_workdir():
    """Abre el selector de carpeta y devuelve la ruta elegida."""
    directory = QFileDialog.getExistingDirectory(
        win, "Selecciona una carpeta"
    )  # Despliega el buscador de carpetas del sistema nativo
    if directory:  # Si el usuario eligió una carpeta y no canceló la operación...
        return os.path.normpath(
            directory
        )  # Devuelve la ruta normalizando diagonales de forma correcta para Windows
    return ""  # Si se canceló la operación, devuelve una cadena vacía


def show_filenames_list():
    """Muestra las imágenes encontradas en la carpeta seleccionada."""
    selected_dir = (
        choose_workdir()
    )  # Abre la ventana de selección de carpetas y guarda su ruta
    if not selected_dir:  # Si la ruta está vacía (cancelado)...
        return  # Rompe la ejecución del cargador de archivos de inmediato

    workimage.workdir = (
        selected_dir  # Asigna la ruta de trabajo actual al gestor 'workimage'
    )
    extensions = [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
    ]  # Formatos de imagen válidos permitidos por la app
    filenames = filter_files(
        os.listdir(selected_dir), extensions
    )  # Lee la carpeta en disco y extrae los nombres válidos

    lw_files.clear()  # Borra el listado de archivos antiguo de la interfaz gráfica
    for filename in filenames:  # Recorre la lista de imágenes ya depuradas...
        lw_files.addItem(
            filename
        )  # Agrega visualmente cada nombre de archivo a la lista interactiva


# --- Conexiones ---
workimage = ImageProcessor(
    lb_image, lw_files, win
)  # Instancia la clase lógica vinculando los componentes visuales

btn_dir.clicked.connect(
    show_filenames_list
)  # Conecta el botón "Carpeta" para escanear directorios al hacer clic
lw_files.currentRowChanged.connect(
    workimage.show_chosen_image
)  # Al cambiar de selección en la lista, carga la nueva imagen en pantalla automáticamente
btn_bw.clicked.connect(
    workimage.do_bw
)  # Vincula el botón B/N con la transformación a escala de grises
btn_left.clicked.connect(
    workimage.do_left
)  # Vincula el botón Izquierda con la acción de rotación de 90° antihoraria
btn_right.clicked.connect(
    workimage.do_right
)  # Vincula el botón Derecha con la acción de rotación de 90° horaria
btn_sharp.clicked.connect(
    workimage.do_sharpen
)  # Vincula el botón Nitidez con el filtro de enfoque de Pillow
btn_flip.clicked.connect(
    workimage.do_flip
)  # Vincula el botón Reflejo con el cambio geométrico espejo

win.show()  # Ordena al motor de Qt desplegar y renderizar la ventana principal en la pantalla
sys.exit(
    app.exec_()
)  # Enciende el bucle infinito de eventos de la app y asegura un cierre limpio del proceso al salir