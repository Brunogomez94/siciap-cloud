# Cómo poner los Secrets en la web (Streamlit Cloud)

## Dónde se configuran

1. Entrá a **https://share.streamlit.io** e iniciá sesión.
2. En la lista de apps, buscá **siciap-cloud** (o el nombre de tu app).
3. Al lado del nombre de la app hay un menú de **tres puntitos (⋮)**. Clic ahí.
4. Elegí **"Settings"** (Configuración).
5. En la ventana de Settings, abrí la pestaña **"Secrets"**.
6. En el cuadro de texto grande pegá **exactamente** esto (con tus valores si los cambiás):

```toml
SUPABASE_URL = "https://hbuencwjgfzypgmwinlp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhidWVuY3dqZ2Z6eXBnbXdpbmxwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg4OTc0MDQsImV4cCI6MjA4NDQ3MzQwNH0.5DReiJ8EKMd0RKzmRhAEqARcRj-5aumo8khOQqWM3TY"
```

7. Clic en **"Save"**.
8. La app se reiniciará sola y ya va a leer los secrets desde la web.

## Si la app todavía no está desplegada

1. En **share.streamlit.io** → **"New app"**.
2. Conectá el repo de GitHub y elegí branch, carpeta y archivo principal (`frontend/app.py`).
3. Antes de Deploy, abrí **"Advanced settings"**.
4. Ahí vas a ver el campo **"Secrets"**. Pegá el mismo bloque TOML de arriba.
5. Clic en **"Deploy"**.

---

Resumen: **Settings → pestaña Secrets → pegar el TOML → Save.**
