# CyRSAssistant logo

The turquoise CY headset logo is the application logo. `cyrsassistant-logo-turquoise.png` is the master artwork with a transparent background.

- `cyrsassistant-logo.ico`: Windows icon containing 16, 24, 32, 48, 64, 128 and 256 pixel images.
- `cyrsassistant-logo.rgba`: 256 x 256 straight-alpha RGBA8 texture embedded in the ReShade add-on.

Regenerate these two exports on Windows without changing the master artwork:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/generate_branding.ps1
```

The logo is embedded in the add-on and companion executable; no loose image file is required at runtime.
