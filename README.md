# 🎵 Reproductor de Música Personalizado

Un reproductor de música de escritorio moderno y elegante, construido con Python. Cuenta con una interfaz oscura premium, reproducción de audio completa y gestión de playlist persistente.

---

## ✨ Características

### Interfaz
- Diseño oscuro premium con paleta **violeta / ámbar**
- Arte de álbum extraído automáticamente del archivo MP3 (o placeholder animado)
- Título con **scroll suave pixel a pixel** (30 fps) cuando es demasiado largo
- Barra de progreso interactiva con tiempos en tiempo real

### Reproducción
- Formatos soportados: **MP3, WAV, OGG, FLAC**
- Play / Pausa, Siguiente, Anterior
- **Retroceder / Avanzar 10 segundos** con los botones `-10` y `+10`
- Seek (click en cualquier punto de la barra) con sincronización precisa
- Control de volumen deslizable

### Modos de reproducción
| Modo | Descripción |
|------|-------------|
| 🔀 Shuffle | Reproducción aleatoria con historial |
| 🔁 Repeat All | Repite la lista completa |
| 🔂 Repeat One | Repite la canción actual |

### Playlist
- **Carga por carpeta**: busca recursivamente en subcarpetas
- **Carga por archivo**: selección múltiple de archivos individuales
- Las canciones se **acumulan** (no se reemplazan al cargar más)
- **Eliminación individual** con el botón `×` por canción
- **Limpiar lista** completa con un clic
- **Persistencia automática**: la lista se guarda en `playlist.json` y se restaura al abrir

---

## 🖼️ Vista previa

```
┌─────────────────┬──────────────────────────────────┐
│  MY LIBRARY     │                                  │
│ ┌─────────────┐ │        [Arte del álbum]          │
│ │ Canción 1 × │ │                                  │
│ │ Canción 2 × │ │     Nombre de la Canción         │
│ │ Canción 3 × │ │        Artista                   │
│ │    ...      │ │                                  │
│ └─────────────┘ │  0:00 ══════●══════════ 3:45     │
│                 │                                  │
│ ＋ Cargar Carp. │  🔀 ⏮ -10 ▶ +10 ⏭ 🔁 🔊━━━  │
│ 🎵 Cargar Arch. │                                  │
└─────────────────┴──────────────────────────────────┘
```

---

## 🚀 Instalación

### Requisitos
- Python **3.10+**

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/reproductor-musica.git
cd reproductor-musica
```

### 2. Instalar dependencias
```bash
pip install customtkinter pygame mutagen pillow
```

### 3. Ejecutar
```bash
python reproductor.py
```

---

## 📦 Dependencias

| Librería | Uso |
|----------|-----|
| `customtkinter` | Interfaz gráfica moderna |
| `pygame` | Motor de reproducción de audio |
| `mutagen` | Lectura de metadatos (título, artista, arte) |
| `Pillow` | Procesamiento de imágenes del álbum |
| `tkinter` | Canvas para scroll del título y diálogos |

---

## 📁 Estructura

```
Reproductor de Música Personalizado/
├── reproductor.py   # Aplicación principal
├── playlist.json    # Playlist guardada automáticamente (se genera al usar)
└── README.md
```

---

## ⚙️ Uso

1. **Agregar música**: usa **Cargar Carpeta** para cargar una carpeta completa (busca recursivamente) o **Cargar Archivos** para elegir archivos individuales.
2. **Reproducir**: haz clic en cualquier canción de la lista o usa los controles.
3. **Seek**: arrastra la barra de progreso o usa `-10`/`+10` para saltar 10 segundos.
4. **Tu lista se guarda sola** al cerrar y se restaura al volver a abrir.

---

## 📄 Licencia

Libre para uso personal y educativo.
