# Facturado Sticker Studio

Aplicacion local para Windows orientada a la impresion de stickers corporativos internos en impresoras termicas como Honeywell PC42t Plus, sin depender de BarTender.

## Descarga directa (Windows)

- Releases: [https://github.com/trececlub/facturado/releases](https://github.com/trececlub/facturado/releases)
- Ultimo ZIP ejecutable: [Descargar FacturadoStickerStudio-windows.zip](https://github.com/trececlub/facturado/releases/latest/download/FacturadoStickerStudio-windows.zip)

## Enfoque de seguridad y cumplimiento

- Esta solucion esta diseniada para uso corporativo interno (activos, acceso interno, inventario, identificacion interna).
- No incluye ni promueve plantillas que imiten documentos oficiales, gubernamentales o estatales.
- La plantilla por defecto mantiene estilo corporativo neutro y no institucional.

## Arquitectura propuesta

- `Python + PySide6` para interfaz de escritorio estable en Windows.
- `templates/*.json` para plantillas parametrizadas (posiciones, tamanios, fuentes).
- `printer/print_engine.py` para transformar datos + plantilla a ZPL.
- `printer/printer_service.py` para envio RAW por USB (Windows spooler) o red (futuro).
- `data/` para registros, historial e inspeccion de jobs.
- `utils/importer.py` para carga CSV/Excel.

## Estructura

- `main.py`
- `ui/`
- `templates/`
- `printer/`
- `data/`
- `utils/`
- `assets/`
- `config/app_config.json`
- `samples/sample_data.csv`

## Fases implementadas en este MVP

1. Fase 1:
- Estructura del proyecto
- Interfaz base con formulario + preview en tiempo real
- Mock visual corporativo

2. Fase 2:
- Plantilla parametrizada por JSON
- Generacion y vista previa de barcode y QR
- Carga de imagen opcional
- Editor de plantilla (X/Y, tamanios, fuentes basicas)

3. Fase 3:
- Exportacion a ZPL
- Modulo de impresion RAW (`printer_service`)
- Flujo USB Windows (spooler RAW)
- Preparado para red (socket 9100)

4. Fase 4:
- Importacion CSV/Excel
- Impresion por lote
- Historial de impresiones

5. Fase 5 (parcial en MVP):
- Pulido visual base
- Validaciones requeridas
- Base para empaquetado con PyInstaller

## Requisitos

- Windows 10/11 recomendado
- Python 3.11+
- Honeywell PC42t Plus configurada y visible en Windows
- Para envio directo RAW: driver instalado y nombre de impresora correcto

## Instalacion

```bash
python -m venv .venv
# PowerShell:
.venv\Scripts\Activate.ps1
# CMD:
# .venv\Scripts\activate.bat
pip install -r requirements.txt
```

## Ejecucion

```bash
python main.py
```

## Configuracion de impresora

Editar `config/app_config.json`:

```json
{
  "printer": {
    "interface": "usb",
    "default_name": "Honeywell PC42t Plus",
    "network_host": "",
    "network_port": 9100
  }
}
```

Notas:
- Para red futura: usar `interface = "network"` y completar `network_host`.
- Si tu PC42t Plus usa emulacion ZPL, mantenla habilitada en el equipo (modo ZSim/ZPL compatible segun firmware).

## Uso rapido

1. Completa formulario (panel izquierdo).
2. Revisa vista previa en tiempo real (panel derecho).
3. `Generar codigo` para autocompletar barcode/QR.
4. `Imprimir` para 1 etiqueta.
5. `Importar CSV/Excel` y luego `Impresion por lote` para multiples.
6. `Editar plantilla` para mover elementos y guardar JSON nuevo.

## Archivos de salida y auditoria

- Copias ZPL: `data/zpl_exports/*.zpl`
- Registros manuales: `data/records.json`
- Historial de impresion: `data/print_history.json`

## Empaquetado Windows (PyInstaller)

Instalar PyInstaller:

```bash
pip install pyinstaller
```

Generar ejecutable:

```bash
pyinstaller --noconfirm --windowed --name FacturadoStickerStudio main.py
```

El ejecutable quedara en `dist/FacturadoStickerStudio/`.

## Distribucion desde GitHub (recomendado)

El repositorio incluye workflow de GitHub Actions en:

- `.github/workflows/windows-release.yml`

Que hace lo siguiente:

- Compila la app en `windows-latest`
- Empaqueta en `FacturadoStickerStudio-windows.zip`
- Publica artefacto descargable
- Si el push es un tag `v*`, crea release con el ZIP adjunto

### Como publicar una nueva version para descarga

1. Sube cambios a `main`.
2. Crea y sube un tag de version:

```bash
git tag v1.0.0
git push origin v1.0.0
```

3. Ve a **GitHub > Releases** y descarga `FacturadoStickerStudio-windows.zip`.

### Como instalar en cualquier PC Windows

1. Descargar el ZIP desde Releases.
2. Descomprimir en una carpeta local (por ejemplo `C:\\FacturadoStickerStudio`).
3. Ejecutar `FacturadoStickerStudio.exe`.
4. Editar `config/app_config.json` (junto al ejecutable) con el nombre de la impresora Honeywell.

## Limites actuales del MVP

- La impresion de imagen (foto) en ZPL se maneja como placeholder en el motor actual.
- Para foto real en ZPL, se puede agregar conversion a `^GFA` en una siguiente iteracion.
- El preview usa render grafico fiel de layout; la salida exacta puede variar segun firmware/configuracion de impresora.

## Siguientes mejoras recomendadas

- Soporte imagen real en ZPL (`^GFA` + dithering mono).
- Selector visual drag-and-drop de elementos.
- Multi-plantilla por perfil de area (activos, visitantes, inventario).
- Firma digital interna de plantillas para control de cambios.
