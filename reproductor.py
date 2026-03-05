import os
import random
import io
import json
import customtkinter as ctk  # type: ignore
import pygame  # type: ignore
from tkinter import filedialog, Canvas
from mutagen.mp3 import MP3  # type: ignore
from mutagen.easyid3 import EasyID3  # type: ignore
from mutagen.id3 import ID3, APIC  # type: ignore
from PIL import Image, ImageDraw, ImageFilter  # type: ignore

# ─────────────────────────────────────────────
# Configuración Visual Global
# ─────────────────────────────────────────────
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Paleta de colores premium
C_BG_DARK    = "#0a0a0f"
C_BG_MID     = "#12121a"
C_BG_LIGHT   = "#1e1e2e"
C_BG_CARD    = "#16213e"
C_ACCENT     = "#7c3aed"
C_ACCENT2    = "#9f67ff"
C_ACCENT3    = "#f59e0b"
C_TEXT_PRI   = "#f0f0ff"
C_TEXT_SEC   = "#a0a0c0"
C_TEXT_DIM   = "#484860"
C_ACTIVE     = "#7c3aed"
C_HOVER      = "#252535"
C_GREEN      = "#10b981"

# Ruta donde se guarda la playlist persistente
PLAYLIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playlist.json")

# Constantes de animacion del titulo (Canvas pixel-scroll)
_TITLE_W       = 400    
_TITLE_H       = 50     
_TITLE_SPEED   = 1.0    
_TITLE_FRAME   = 33    
_HOLD_START    = 70     
_HOLD_END      = 45     


def make_placeholder_art(size: int = 200) -> ctk.CTkImage:  # type: ignore
    """Genera un arte placeholder con gradiente violeta/ambar premium."""
    img = Image.new("RGB", (size, size), color="#0a0a1a")
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    for layer_r, color in [
        (cx, "#7c3aed"), (int(cx * 0.78), "#6d28d9"),
        (int(cx * 0.55), "#4c1d95"), (int(cx * 0.35), "#f59e0b"),
        (int(cx * 0.18), "#fbbf24"),
    ]:
        if layer_r > 0:
            draw.ellipse([cx - layer_r, cy - layer_r, cx + layer_r, cy + layer_r], fill=color)
    # Circulo interior negro
    draw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill="#0a0a1a")
    draw.text((cx - 10, cy - 14), "\u266a", fill="#f0f0ff", font=None)
    img = img.filter(ImageFilter.GaussianBlur(1.5))
    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))  # type: ignore


def load_album_art(ruta: str, size: int = 200):  
    """Extrae el artwork incrustado en el MP3 si existe."""
    try:
        tags = ID3(ruta)
        for key in tags.keys():
            if key.startswith("APIC"):
                apic: APIC = tags[key]
                img = Image.open(io.BytesIO(apic.data)).resize((size, size), Image.LANCZOS)
                return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))  # type: ignore
    except Exception:
        pass
    return None


def format_time(seconds: float) -> str:
    """Convierte segundos a MM:SS."""
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


# ─────────────────────────────────────────────
# Clase Principal
# ─────────────────────────────────────────────
class ReproductorMusica(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── Ventana ────────────────────────────
        self.title("Beats — Reproductor Pro")
        self.geometry("900x580")
        self.minsize(780, 520)
        self.configure(fg_color=C_BG_DARK)

        # ── Motor de audio ─────────────────────
        pygame.mixer.pre_init(44100, -16, 2, 512)  # type: ignore
        pygame.mixer.init()  # type: ignore

        # ── Estado ─────────────────────────────
        self.lista_canciones: list[str] = []   
        self.indice_actual: int = 0
        self.reproduciendo: bool = False
        self.duracion_total: float = 0.0       
        self.arrastrando_slider: bool = False  
        self._seek_offset: float = 0.0          

        self.shuffle: bool = False
        self.repeat: str = "off"              
        self.historial_shuffle: list = []       

        # Botones de la playlist 
        self.btns_playlist: list = []             

        # Animacion del titulo 
        self._title_anim_job  = None
        self._title_x: float  = 0.0
        self._title_end_x: float = 0.0
        self._title_state: str = 'idle'
        self._title_hold: int  = 0

        # Arte de álbum 
        self._art_placeholder = None  
        self._art_current = None

        # ── UI ─────────────────────────────────
        self._crear_interfaz()

        # ── Loop de eventos ────────────────────
        self._poll_eventos()

        # ── Cargar playlist guardada ────────────
        self.after(200, self._cargar_playlist_guardada)

    # ═══════════════════════════════════════════════════════════════
    # CONSTRUCCIÓN DE LA INTERFAZ
    # ═══════════════════════════════════════════════════════════════
    def _crear_interfaz(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._crear_panel_playlist()
        self._crear_panel_principal()

    # ── Panel Izquierdo: Playlist ───────────────────────────────────
    def _crear_panel_playlist(self):
        self.frame_izq = ctk.CTkFrame(
            self, width=260, corner_radius=0, fg_color=C_BG_MID
        )
        self.frame_izq.grid(row=0, column=0, sticky="nsew")
        self.frame_izq.grid_propagate(False)

        # Cabecera
        header = ctk.CTkFrame(self.frame_izq, fg_color="#111111", corner_radius=0, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="MI BIBLIOTECA",
            font=("Segoe UI", 13, "bold"),
            text_color=C_ACCENT
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkButton(
            self.frame_izq,
            text="＋  Cargar Carpeta",
            font=("Segoe UI", 13, "bold"),
            fg_color=C_ACCENT,
            hover_color=C_ACCENT2,
            text_color="#000000",
            corner_radius=8,
            height=38,
            command=self.cargar_carpeta
        ).pack(pady=(12, 4), padx=16, fill="x")

        ctk.CTkButton(
            self.frame_izq,
            text="🎵  Cargar Archivos",
            font=("Segoe UI", 12),
            fg_color=C_BG_LIGHT,
            hover_color=C_HOVER,
            text_color=C_TEXT_SEC,
            corner_radius=8,
            height=34,
            command=self.cargar_archivos
        ).pack(pady=(0, 4), padx=16, fill="x")

        ctk.CTkButton(
            self.frame_izq,
            text="Limpiar Lista",
            font=("Segoe UI", 11),
            fg_color="transparent",
            hover_color="#3a0000",
            text_color="#ff5555",
            corner_radius=8,
            height=28,
            command=self.limpiar_lista
        ).pack(pady=(0, 8), padx=16, fill="x")

        # Separador
        ctk.CTkLabel(self.frame_izq, text="", height=1, fg_color=C_BG_LIGHT).pack(fill="x", padx=10)

        # Lista scrollable
        self.lista_visual = ctk.CTkScrollableFrame(
            self.frame_izq, fg_color="transparent", scrollbar_button_color=C_BG_LIGHT
        )
        self.lista_visual.pack(fill="both", expand=True, padx=6, pady=6)

    # ── Panel Derecho: Display + Controles ──────────────────────────
    def _crear_panel_principal(self):
        self.frame_der = ctk.CTkFrame(self, corner_radius=0, fg_color=C_BG_DARK)
        self.frame_der.grid(row=0, column=1, sticky="nsew")
        self.frame_der.grid_rowconfigure(0, weight=1)
        self.frame_der.grid_columnconfigure(0, weight=1)

        # --- Display central (arte + título + artista) ---
        self.frame_display = ctk.CTkFrame(self.frame_der, fg_color="transparent")
        self.frame_display.grid(row=0, column=0, sticky="nsew")
        self.frame_display.grid_rowconfigure(0, weight=1)
        self.frame_display.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(self.frame_display, fg_color="transparent")
        inner.place(relx=0.5, rely=0.45, anchor="center")

        # Arte de album con borde de acento
        self.frame_art = ctk.CTkFrame(
            inner, width=200, height=200,
            corner_radius=20,
            fg_color=C_BG_CARD,
            border_width=2, border_color=C_ACCENT
        )
        self.frame_art.pack(pady=(0, 20))
        self.frame_art.pack_propagate(False)

        self._art_placeholder = make_placeholder_art(200)
        self.lbl_art = ctk.CTkLabel(
            self.frame_art, text="", image=self._art_placeholder
        )
        self.lbl_art.place(relx=0.5, rely=0.5, anchor="center")

        # Titulo -- Canvas para scroll
        self.canvas_titulo = Canvas(
            inner,
            width=_TITLE_W,
            height=_TITLE_H,
            bg=C_BG_DARK,
            highlightthickness=0
        )
        self.canvas_titulo.pack(pady=(0, 2))
        self.canvas_titulo_text = self.canvas_titulo.create_text(
            _TITLE_W // 2, _TITLE_H // 2,
            text="Ninguna pista seleccionada",
            font=("Segoe UI", 22, "bold"),
            fill=C_TEXT_PRI,
            anchor="center"
        )

        # Artista
        self.lbl_artista = ctk.CTkLabel(
            inner,
            text="—",
            font=("Segoe UI", 14),
            text_color=C_TEXT_SEC
        )
        self.lbl_artista.pack(pady=(4, 0))

        # --- Barra de progreso + tiempos ---
        self.frame_progreso = ctk.CTkFrame(self.frame_der, fg_color="transparent", height=40)
        self.frame_progreso.grid(row=1, column=0, sticky="ew", padx=40)

        self.lbl_tiempo_actual = ctk.CTkLabel(
            self.frame_progreso, text="00:00",
            font=("Segoe UI", 11), text_color=C_TEXT_SEC, width=42
        )
        self.lbl_tiempo_actual.pack(side="left")

        self.slider_progreso = ctk.CTkSlider(
            self.frame_progreso,
            from_=0, to=100,
            progress_color=C_ACCENT,
            button_color=C_TEXT_PRI,
            button_hover_color=C_ACCENT2,
            fg_color=C_BG_LIGHT,
            command=self._on_slider_move
        )
        self.slider_progreso.set(0)
        self.slider_progreso.pack(side="left", fill="x", expand=True, padx=10)
        self.slider_progreso.bind("<ButtonPress-1>",   lambda e: self._iniciar_arrastre())
        self.slider_progreso.bind("<ButtonRelease-1>", lambda e: self._soltar_arrastre())

        self.lbl_tiempo_total = ctk.CTkLabel(
            self.frame_progreso, text="00:00",
            font=("Segoe UI", 11), text_color=C_TEXT_SEC, width=42
        )
        self.lbl_tiempo_total.pack(side="left")

        # --- Panel de controles inferior ---
        self.frame_controles = ctk.CTkFrame(
            self.frame_der,
            height=96,
            corner_radius=24,
            fg_color=C_BG_MID,
            border_width=1,
            border_color=C_BG_LIGHT
        )
        self.frame_controles.grid(row=2, column=0, sticky="ew", padx=28, pady=18)
        self.frame_controles.grid_propagate(False)
        self.frame_controles.grid_columnconfigure(
            (0, 1, 2, 3, 4, 5, 6, 7, 8), weight=1
        )

        _sm: dict = {"fg_color": "transparent", "hover_color": C_HOVER,
                     "corner_radius": 10, "height": 36}
        _md: dict = {"fg_color": "transparent", "hover_color": C_HOVER,
                     "corner_radius": 10, "height": 36}

        # Shuffle
        self.btn_shuffle = ctk.CTkButton(
            self.frame_controles, text="\U0001f500", width=36,
            font=("Segoe UI", 17), text_color=C_TEXT_DIM,
            command=self._toggle_shuffle, **_sm
        )
        self.btn_shuffle.grid(row=0, column=0, padx=4, pady=30)

        # Anterior
        ctk.CTkButton(
            self.frame_controles, text="\u23ee", width=40,
            font=("Segoe UI", 19), text_color=C_TEXT_SEC,
            command=self.cancion_anterior, **_md
        ).grid(row=0, column=1, padx=2, pady=30)

        # Retroceder 10 s  
        ctk.CTkButton(
            self.frame_controles, text="-10", width=40,
            font=("Segoe UI", 11, "bold"), text_color=C_TEXT_SEC,
            command=lambda: self._saltar_segundos(-10), **_md
        ).grid(row=0, column=2, padx=2, pady=30)

        # Play / Pause  
        self.btn_play = ctk.CTkButton(
            self.frame_controles,
            text="\u25b6", width=62, height=62,
            font=("Segoe UI", 26, "bold"),
            fg_color=C_ACCENT,
            hover_color=C_ACCENT2,
            text_color="#ffffff",
            corner_radius=32,
            command=self.toggle_play_pause
        )
        self.btn_play.grid(row=0, column=3, padx=8, pady=17)

        # Avanzar 10 s
        ctk.CTkButton(
            self.frame_controles, text="+10", width=40,
            font=("Segoe UI", 11, "bold"), text_color=C_TEXT_SEC,
            command=lambda: self._saltar_segundos(10), **_md
        ).grid(row=0, column=4, padx=2, pady=30)

        # Siguiente
        ctk.CTkButton(
            self.frame_controles, text="\u23ed", width=40,
            font=("Segoe UI", 19), text_color=C_TEXT_SEC,
            command=self.cancion_siguiente, **_md
        ).grid(row=0, column=5, padx=2, pady=30)

        # Repeat
        self.btn_repeat = ctk.CTkButton(
            self.frame_controles, text="\U0001f501", width=36,
            font=("Segoe UI", 17), text_color=C_TEXT_DIM,
            command=self._toggle_repeat, **_sm
        )
        self.btn_repeat.grid(row=0, column=6, padx=4, pady=30)

        # Icono volumen
        ctk.CTkLabel(
            self.frame_controles,
            text="\U0001f50a", font=("Segoe UI", 14), text_color=C_TEXT_SEC
        ).grid(row=0, column=7, padx=(8, 0), pady=30)

        # Slider volumen
        self.slider_volumen = ctk.CTkSlider(
            self.frame_controles,
            width=95,
            from_=0, to=1,
            progress_color=C_ACCENT,
            button_color=C_ACCENT2,
            button_hover_color="#ffffff",
            fg_color=C_BG_LIGHT,
            command=self._cambiar_volumen
        )
        self.slider_volumen.set(0.65)
        self.slider_volumen.grid(row=0, column=8, padx=(2, 12), pady=30)
        pygame.mixer.music.set_volume(0.65)  # type: ignore

    # ═══════════════════════════════════════════════════════════════
    # CARGA DE CANCIONES
    # ═══════════════════════════════════════════════════════════════
    def cargar_carpeta(self):
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de música")
        if not carpeta:
            return

        extensiones = (".mp3", ".wav", ".ogg", ".flac")
        rutas: list[str] = []
        # Buscar recursivamente en todas las subcarpetas
        for raiz, _, archivos in os.walk(carpeta):
            for archivo in sorted(archivos):
                if archivo.lower().endswith(extensiones):
                    rutas.append(os.path.join(raiz, archivo))

        self._poblar_playlist(rutas)

    def cargar_archivos(self):
        """Permite seleccionar archivos de música individuales."""
        rutas_raw = filedialog.askopenfilenames(
            title="Seleccionar archivos de música",
            filetypes=[
                ("Archivos de audio", "*.mp3 *.wav *.ogg *.flac"),
                ("MP3", "*.mp3"),
                ("WAV", "*.wav"),
                ("OGG", "*.ogg"),
                ("FLAC", "*.flac"),
                ("Todos los archivos", "*.*"),
            ]
        )
        if not rutas_raw:
            return
        self._poblar_playlist(list(rutas_raw))

    def _poblar_playlist(self, rutas: list[str]):
        """Acumula rutas nuevas en la playlist (sin borrar las existentes). Evita duplicados."""
        anteriores = len(self.lista_canciones)
        for ruta in rutas:
            if ruta not in self.lista_canciones:
                self.lista_canciones.append(ruta)
                self._agregar_fila_playlist(len(self.lista_canciones) - 1, ruta)

        if not self.lista_canciones:
            self._set_titulo("No se encontraron archivos de audio")
            return

        self._guardar_playlist()
        # Si antes estaba vacia, reproducir la primera nueva
        if anteriores == 0:
            self.reproducir_cancion(0)

    def _agregar_fila_playlist(self, idx: int, ruta: str):
        """Crea una fila (boton cancion + boton eliminar) en el panel."""
        nombre = os.path.splitext(os.path.basename(ruta))[0]
        if len(nombre) > 26:
            nombre = nombre[:23] + "..."

        fila = ctk.CTkFrame(self.lista_visual, fg_color="transparent", corner_radius=6)
        fila.pack(fill="x", pady=2, padx=4)
        fila.grid_columnconfigure(0, weight=1)

        btn_song = ctk.CTkButton(
            fila,
            text=f"  {nombre}",
            font=("Segoe UI", 12),
            fg_color="transparent",
            text_color=C_TEXT_SEC,
            anchor="w",
            hover_color=C_BG_LIGHT,
            height=34,
            corner_radius=6,
            command=lambda i=idx: self.reproducir_cancion(i)
        )
        btn_song.grid(row=0, column=0, sticky="ew")

        btn_x = ctk.CTkButton(
            fila,
            text="x",
            width=28,
            height=28,
            font=("Segoe UI", 13, "bold"),
            fg_color="transparent",
            hover_color="#3a0000",
            text_color="#666666",
            corner_radius=6,
            command=lambda i=idx: self._eliminar_cancion(i)
        )
        btn_x.grid(row=0, column=1, padx=(2, 0))
        self.btns_playlist.append(btn_song)

    def _eliminar_cancion(self, idx: int):
        """Elimina una cancion de la lista y reconstruye el panel."""
        if idx < 0 or idx >= len(self.lista_canciones):
            return
        era_actual = (idx == self.indice_actual and self.reproduciendo)
        self.lista_canciones.pop(idx)
        if era_actual:
            pygame.mixer.music.stop()  # type: ignore
            self.reproduciendo = False
            self.btn_play.configure(text="\u25b6")
            self._set_titulo("Ninguna pista seleccionada")
            self.lbl_artista.configure(text="\u2014")
        if idx < self.indice_actual:
            self.indice_actual -= 1
        elif idx == self.indice_actual and self.indice_actual >= len(self.lista_canciones):
            self.indice_actual = max(0, len(self.lista_canciones) - 1)
        self._reconstruir_filas()
        self._guardar_playlist()

    def limpiar_lista(self):
        """Borra toda la playlist."""
        pygame.mixer.music.stop()  # type: ignore
        self.reproduciendo = False
        self.btn_play.configure(text="\u25b6")
        self.lista_canciones.clear()
        self.btns_playlist.clear()
        for widget in self.lista_visual.winfo_children():
            widget.destroy()
        self._set_titulo("Ninguna pista seleccionada")
        self.lbl_artista.configure(text="\u2014")
        self.slider_progreso.set(0)
        self.lbl_tiempo_actual.configure(text="00:00")
        self.lbl_tiempo_total.configure(text="00:00")
        self._guardar_playlist()

    def _reconstruir_filas(self):
        """Limpia y redibuja todas las filas de la playlist."""
        self.btns_playlist.clear()
        for widget in self.lista_visual.winfo_children():
            widget.destroy()
        for i, ruta in enumerate(self.lista_canciones):
            self._agregar_fila_playlist(i, ruta)
        if self.lista_canciones:
            self._resaltar_activo(self.indice_actual)

    def _guardar_playlist(self):
        """Guarda lista_canciones en playlist.json."""
        try:
            with open(PLAYLIST_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.lista_canciones, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _cargar_playlist_guardada(self):
        """Carga playlist.json al iniciar si existe."""
        try:
            with open(PLAYLIST_PATH, 'r', encoding='utf-8') as f:
                rutas = json.load(f)
            rutas_validas = [r for r in rutas if os.path.isfile(r)]
            for ruta in rutas_validas:
                self.lista_canciones.append(ruta)
                self._agregar_fila_playlist(len(self.lista_canciones) - 1, ruta)
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════
    # METADATOS
    # ═══════════════════════════════════════════════════════════════
    def _extraer_metadata(self, ruta: str) -> tuple[str, str, float]:
        """Devuelve (título, artista, duración_en_segundos)."""
        nombre_base = os.path.splitext(os.path.basename(ruta))[0]
        titulo, artista, duracion = nombre_base, "Artista desconocido", 0.0

        try:
            if ruta.lower().endswith(".mp3"):
                audio = MP3(ruta)
                duracion = audio.info.length
                try:
                    tags = EasyID3(ruta)
                    titulo  = tags.get("title",  [nombre_base])[0]
                    artista = tags.get("artist", ["Artista desconocido"])[0]
                except Exception:
                    pass
        except Exception:
            pass

        return titulo, artista, duracion

    # ═══════════════════════════════════════════════════════════════
    # REPRODUCCIÓN
    # ═══════════════════════════════════════════════════════════════
    def reproducir_cancion(self, indice: int):
        if not self.lista_canciones:
            return

        self.indice_actual = indice
        ruta = self.lista_canciones[indice]

        # Metadatos
        titulo, artista, duracion = self._extraer_metadata(ruta)
        self.duracion_total = duracion
        self.lbl_tiempo_total.configure(text=format_time(duracion))

        # Titulo con animacion pixel-level
        self._iniciar_animacion_titulo(titulo)
        self.lbl_artista.configure(text=artista)

        # Arte de álbum
        art = load_album_art(ruta, 180)
        self._art_current = art if art else self._art_placeholder
        self.lbl_art.configure(image=self._art_current)

        # Reproducir desde el inicio — resetear offset de seek
        self._seek_offset = 0.0
        try:
            pygame.mixer.music.load(ruta)  # type: ignore
            pygame.mixer.music.play()  # type: ignore
        except Exception as e:
            self._set_titulo(f"Error al cargar")
            return

        self.reproduciendo = True
        self.btn_play.configure(text="⏸")
        self.slider_progreso.set(0)
        self.lbl_tiempo_actual.configure(text="00:00")

        # Resaltar en playlist
        self._resaltar_activo(indice)

    def toggle_play_pause(self):
        if not self.lista_canciones:
            return

        if self.reproduciendo:
            pygame.mixer.music.pause()
            self.reproduciendo = False
            self.btn_play.configure(text="▶")
        else:
            if pygame.mixer.music.get_pos() == -1:
                self.reproducir_cancion(self.indice_actual)
            else:
                pygame.mixer.music.unpause()
                self.reproduciendo = True
                self.btn_play.configure(text="⏸")

    def cancion_siguiente(self):
        if not self.lista_canciones:
            return
        if self.shuffle:
            siguiente = self._siguiente_shuffle()
        else:
            siguiente = (self.indice_actual + 1) % len(self.lista_canciones)
        self.reproducir_cancion(siguiente)

    def cancion_anterior(self):
        if not self.lista_canciones:
            return
        if self.shuffle and self.historial_shuffle:
            self.historial_shuffle.pop()  
            anterior = self.historial_shuffle[-1] if self.historial_shuffle else self.indice_actual
        else:
            anterior = (self.indice_actual - 1) % len(self.lista_canciones)
        self.reproducir_cancion(anterior)

    def _siguiente_shuffle(self) -> int:
        if len(self.lista_canciones) == 1:
            return 0
        opciones = [i for i in range(len(self.lista_canciones)) if i != self.indice_actual]
        sig = random.choice(opciones)
        self.historial_shuffle.append(sig)
        if len(self.historial_shuffle) > 50:
            keep = len(self.historial_shuffle) - 50
            self.historial_shuffle = [self.historial_shuffle[i] for i in range(keep, len(self.historial_shuffle))]
        return sig

    # ═══════════════════════════════════════════════════════════════
    # MODOS: SHUFFLE Y REPEAT
    # ═══════════════════════════════════════════════════════════════
    def _toggle_shuffle(self):
        self.shuffle = not self.shuffle
        color = C_ACCENT if self.shuffle else C_TEXT_DIM
        self.btn_shuffle.configure(text_color=color)

    def _toggle_repeat(self):
        ciclo = {"off": "all", "all": "one", "one": "off"}
        iconos = {"off": "🔁", "all": "🔁", "one": "🔂"}
        colores = {"off": C_TEXT_DIM, "all": C_ACCENT, "one": C_ACCENT}
        self.repeat = ciclo[self.repeat]
        self.btn_repeat.configure(
            text=iconos[self.repeat],
            text_color=colores[self.repeat]
        )

    # ═══════════════════════════════════════════════════════════════
    # VOLUMEN Y PROGRESO
    # ═══════════════════════════════════════════════════════════════
    def _cambiar_volumen(self, valor):
        pygame.mixer.music.set_volume(float(valor))

    def _iniciar_arrastre(self):
        self.arrastrando_slider = True

    def _soltar_arrastre(self):
        self.arrastrando_slider = False
        if self.duracion_total > 0:
            pos_pct = self.slider_progreso.get() / 100
            nueva_pos = pos_pct * self.duracion_total
            self._seek_offset = nueva_pos
            try:
                pygame.mixer.music.play(0, nueva_pos)  # type: ignore
                if not self.reproduciendo:
                    pygame.mixer.music.pause()  # type: ignore
            except Exception:
                pass

    def _on_slider_move(self, valor):
        if self.arrastrando_slider and self.duracion_total > 0:
            secs = (float(valor) / 100) * self.duracion_total
            self.lbl_tiempo_actual.configure(text=format_time(secs))

    def _saltar_segundos(self, delta: int):
        """Salta delta segundos en la cancion actual (positivo=adelantar, negativo=retroceder)."""
        if not self.reproduciendo or self.duracion_total <= 0:
            return
        # Posicion actual real
        pos_ms = pygame.mixer.music.get_pos()  # type: ignore
        pos_actual = self._seek_offset + (pos_ms / 1000 if pos_ms >= 0 else 0)
        nueva_pos = max(0.0, min(pos_actual + delta, self.duracion_total - 0.5))
        self._seek_offset = nueva_pos
        try:
            pygame.mixer.music.play(0, nueva_pos)  # type: ignore
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════════════
    # RESALTAR CANCIÓN ACTIVA
    # ═══════════════════════════════════════════════════════════════
    def _resaltar_activo(self, indice: int):
        for i, btn in enumerate(self.btns_playlist):
            if i == indice:
                btn.configure(text_color=C_ACCENT, fg_color=C_BG_LIGHT)
            else:
                btn.configure(text_color=C_TEXT_SEC, fg_color="transparent")

    # ═══════════════════════════════════════════════════════════════
    # ANIMACION DE TITULO 
    # ═══════════════════════════════════════════════════════════════
    def _set_titulo(self, texto: str):
        """Muestra texto estatico en el canvas titulo."""
        if self._title_anim_job:
            self.after_cancel(self._title_anim_job)
            self._title_anim_job = None
        self._title_state = 'idle'
        self.canvas_titulo.itemconfigure(
            self.canvas_titulo_text, text=texto, anchor="center"
        )
        self.canvas_titulo.coords(
            self.canvas_titulo_text, _TITLE_W // 2, _TITLE_H // 2
        )

    def _iniciar_animacion_titulo(self, titulo: str):
        """Inicia scroll pixel-level del titulo."""
        if self._title_anim_job:
            self.after_cancel(self._title_anim_job)
            self._title_anim_job = None

        # Medir ancho del texto
        self.canvas_titulo.itemconfigure(
            self.canvas_titulo_text, text=titulo, anchor="w"
        )
        self.canvas_titulo.coords(
            self.canvas_titulo_text, _TITLE_W + 5, _TITLE_H // 2
        )
        self.canvas_titulo.update_idletasks()

        bbox = self.canvas_titulo.bbox(self.canvas_titulo_text)
        if not bbox:
            self._set_titulo(titulo)
            return

        text_w = bbox[2] - bbox[0]
        start_x = 10.0
        end_x   = float(_TITLE_W - text_w - 10)

        if end_x >= start_x:
            # El texto cabe: centrarlo
            self.canvas_titulo.itemconfigure(
                self.canvas_titulo_text, anchor="center"
            )
            self.canvas_titulo.coords(
                self.canvas_titulo_text, _TITLE_W // 2, _TITLE_H // 2
            )
            self._title_state = 'idle'
            return

        # Scroll necesario
        self._title_x     = start_x
        self._title_end_x = end_x
        self.canvas_titulo.coords(
            self.canvas_titulo_text, self._title_x, _TITLE_H // 2
        )
        self._title_state = 'hold_start'
        self._title_hold  = _HOLD_START
        self._title_anim_job = self.after(_TITLE_FRAME, self._animar_titulo_px)

    def _animar_titulo_px(self):
        """Loop 30fps: hold -> scroll -> hold -> reset."""
        if self._title_state == 'hold_start':
            self._title_hold -= 1
            if self._title_hold <= 0:
                self._title_state = 'scroll'

        elif self._title_state == 'scroll':
            self._title_x -= _TITLE_SPEED
            self.canvas_titulo.coords(
                self.canvas_titulo_text, self._title_x, _TITLE_H // 2
            )
            if self._title_x <= self._title_end_x:
                self._title_state = 'hold_end'
                self._title_hold  = _HOLD_END

        elif self._title_state == 'hold_end':
            self._title_hold -= 1
            if self._title_hold <= 0:
                self._title_x    = 10.0
                self.canvas_titulo.coords(
                    self.canvas_titulo_text, self._title_x, _TITLE_H // 2
                )
                self._title_state = 'hold_start'
                self._title_hold  = _HOLD_START

        self._title_anim_job = self.after(_TITLE_FRAME, self._animar_titulo_px)

    # ═══════════════════════════════════════════════════════════════
    # LOOP DE EVENTOS (polling cada 400 ms)
    # ═══════════════════════════════════════════════════════════════
    def _poll_eventos(self):
        # Detectar fin de canción con get_busy()
        if self.reproduciendo and not pygame.mixer.music.get_busy():  # type: ignore
            self._cancion_terminada()

        # Actualizar barra de progreso con posición REAL 
        if self.reproduciendo and not self.arrastrando_slider and self.duracion_total > 0:
            pos_ms = pygame.mixer.music.get_pos()  # type: ignore
            if pos_ms >= 0:
                # pos_real = punto donde se hizo el último seek + ms transcurridos desde entonces
                pos_s = self._seek_offset + pos_ms / 1000
                pos_s = min(pos_s, self.duracion_total)  
                pct = (pos_s / self.duracion_total) * 100
                self.slider_progreso.set(pct)
                self.lbl_tiempo_actual.configure(text=format_time(pos_s))

        self.after(400, self._poll_eventos)

    def _cancion_terminada(self):
        """Lógica al terminar una canción según el modo repeat."""
        if self.repeat == "one":
            self.reproducir_cancion(self.indice_actual)
        elif self.repeat == "all" or len(self.lista_canciones) > 1:
            self.cancion_siguiente()
        else:
            # Sin repeat, última canción → detener
            self.reproduciendo = False
            self.btn_play.configure(text="▶")
            self.slider_progreso.set(0)
            self.lbl_tiempo_actual.configure(text="00:00")


# ─────────────────────────────────────────────
# Arranque
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = ReproductorMusica()
    app.mainloop()
