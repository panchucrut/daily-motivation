#!/usr/bin/env python3
"""
daily_motivation_email_ai.py — v3.2
- Lee config.json desde GitHub para ajustar el prompt dinamicamente
- Lee ultimas respuestas de Matias via Gmail API
- Incluye link al Wordle en el email
- Guarda historial de vuelta a GitHub (persistente entre runs)
- Genera y envia email diario de lunes a viernes
"""

import urllib.request
import urllib.error
import urllib.parse
import os
import json
import sys
import base64
import random
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Constantes
CELTAVIA_CONNECTION_ID = 'de11f065-b424-4174-8116-fbb2c5bc5510'
WORDLE_URL             = 'https://panchucrut.github.io/daily-motivation/'
REPO                   = 'panchucrut/daily-motivation'
BRANCH                 = 'main'

# He-Man Shorts (rotan por dia del año)
ASCII_PENES = [
    # --- CLÁSICOS ---
    "8====D~~~",
    "8==========D~~~~~~~~~~",
    "(__)8====D~~~",
    "( oo )8==========D~~~~~~~~~",
    "~~~~~8<====",
    "~~~~D====8~  (al reves, como le gusta a ti)",

    # --- EL OBELISCO ---
    """
   OBELISCO DE CARNE
        /\\
       /  \\
      / 8= \\
     / === \\
    / ==D~~ \\
   /~~~~~~~~~\\
  /___________\\""",

    # --- EL COHETE ---
    """
        *  *  *
       * * * * *
      *    8    *
     *    ===    *
    *    ===D     *
   *   ~~~~~~~~~   *
  *  ~~~~~~~~~~~~~~~  *
 (  )             (  )
  --               --""",

    # --- EL CLÁSICO VERTICAL GRANDE ---
    """
      ___
     /   \\
    | o o |
     \\___/
      |||
     |   |
     |   |
     |   |
     |   |
    /     \\
   /       \\
  |         |
  |  8===D  |
   \\_________/
   ~~~~~~~~~~~~""",

    # --- LA TORRE EIFFEL ---
    """
       *
      /|\\
     / | \\
    /  8  \\
   /  ===  \\
  /  ===D~  \\
 /~~~~~~~~~~~\\
/|___________|\\""",

    # --- EL MICROFONO DE CUERO ---
    """
    _____
   /     \\
  | () () |
  |       |
   \\ ___ /
     | |
     | |
     | |
    /   \\
   /     \\
  |  8=D  |
  |~~~~~~~|
   \\_____/
  "MICROFONO DE CUERO" """,

    # --- EL CUCHUFLÍ ---
    """
  +---------+
  |:::::::::| <--- cuchuflí de carne
  |:::::::::|
  |:::::::::| ~~~
  |:::::::::| ~~~~
  |:::::::::| ~~~~~
  +---------+""",

    # --- LA PISTOLA DE QUAKER ---
    """
  ___________
 |           |===D~~~
 |  PISTOLA  |
 |  QUAKER   |
 |___________|
      |
     ===
    =====
     | |""",

    # --- EL CICLOPE LLORÓN ---
    """
      ___
     /   \\
    | ( ) |   <-- ojo
    |  |  |
     \\_|_/
      | |
      | |
   8==| |==D
      | |
    ~~| |~~
   ~~~| |~~~  (llorando)""",

    # --- LA ANACONDA ---
    """
  ~  ~  ~  ~  ~  ~  8====D
 ~                          ~
~    ANACONDA IMPERIAL        ~
 ~                          ~
  ~  ~  ~  ~  ~  ~  ~  ~  ~""",

    # --- EL ESCUPE SÉMOLA (surtidor) ---
    """
               * * *
              *     *
             *   *   *
            *  *   *  *
           *             *
          *               *
         *   ESCUPE SEMOLA *
          *               *
           *             *
            \\           /
             \\         /
              \\  8=D  /
               \\_____/""",

    # --- EL GANSO ---
    """
     ___
    /   \\      <-- cabeza del ganso
   ( o   )
    \\ _ /
      | |
      | |     "el ganso"
      | |
  8===| |===D~~~""",

    # --- EL SUBMARINO ---
    """
             __|__
            |     |
  ~~~~~~~~~~|8===D|~~~~~~~~~~
            |_____|
           /|     |\\
          / |     | \\
  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  "SUBMARINO DE CUERO"  """,

    # --- LA PALANCA ---
    """
    _____
   |     |
   |     |
   |     |        LA PALANCA
   |     |    ==================>
   |     |
   |_____|
   /|   |\\
  / |   | \\
     | |
     |_|""",

    # --- LA HERRAMIENTA (llave inglesa) ---
    """
    ___
   /   \\___________
  | o   8=========D~~~
   \\___/___________

   "LA HERRAMIENTA" """,

    # --- EL MATASAPO PELADO ---
    """
  .-------.
 /  PELAO  \\
|  MATASAPO |
 \\_________/
      |
      |  8====D~~~
      |
  (  ) (  )
  "PELAO MATASAPO"  """,

    # --- BANDERA ---
    """
  8====D~~~|  REPUBLICA
           |  INDEPENDIENTE
           |  DE LA
           |  PICHULA""",

    # --- EL CAMPEÓN (con copa) ---
    """
      ___
     /   \\
    | 1er |
     \\___/
      |||
    ___|___
   /       \\
  | CAMPEON |
  |  PICHULA|
   \\_______/
   8========D~~~~""",

    # --- EL COHETE ESPACIAL V2 ---
    """
         /\\
        /  \\
       /    \\
      / 8==  \\
     / ====   \\
    / ====D~~  \\
   /~~~~~~~~~~~~\\
  | () () () () |
  |_____________|
       ||||
      ||  ||
    _||    ||_""",

    # --- LA MANGUERA DE CUERO ---
    """
  [===]
   | |
   | |    MANGUERA DE CUERO
   | |    ==================8====D~~~~~~~~
   | |
  [===]""",

    # --- MINIMALISTA ARTÍSTICO ---
    """
  ─────────────────────────8═══╗
                                ║
  ─────────────────────────────╝

  "el puñal de carne" """,

    # --- EL CHAMPIGNON (hongo) ---
    """
     _______
    /       \\
   /  8===D  \\    <-- sombrero
  /___________\\
       |||
       |||
      /   \\
     /     \\
    |       |
     \\_____/
   "EL CHAMPIGNON" """,

    # --- DIAGRAMA TÉCNICO ---
    """
  DIAGRAMA TÉCNICO - VISTA LATERAL

  ┌──────┐
  │  ()  │  <-- unidad productiva bilateral
  │  ()  │
  └──┬───┘
     │
  ┌──┴──────────────────┐
  │  8==================D│~~~
  └─────────────────────┘

  Escala: 1:1 (tamaño real)""",

    # --- EL ARROLLADO DE VENA ---
    """
  +---------------------------+
  |   ARROLLADO DE VENA       |
  |                           |
  |  ~~~~~~8========D~~~~~~   |
  |                           |
  +---------------------------+""",

    # --- CLÁSICO CON TEMBLOR ---
    """
  (  )
 (    )
( 8==D )~~
 (    )
  (  )

  "el temblor" """,

    # --- CERTIFICADO OFICIAL ---
    """
  ╔══════════════════════════════════╗
  ║   CERTIFICADO DE AUTENTICIDAD    ║
  ║                                  ║
  ║   8 = = = = = = = D ~ ~ ~ ~      ║
  ║                                  ║
  ║  Se certifica que el portador    ║
  ║  de este email es 100% pichula   ║
  ╚══════════════════════════════════╝""",

    # --- EL SEMÁFORO ---
    """
   ┌─────┐
   │  🔴 │  <- bola 1
   │     │
   │  🔴 │  <- bola 2
   │     │
   │ 8=D │~~
   └─────┘
   "el semaforo"  """,

    # --- MAPA DEL TESORO ---
    """
  ~  ~  ~  ~  ~  ~  ~  ~  ~
  ~   X marca el lugar       ~
  ~                           ~
  ~    (oo)                   ~
  ~     ||  8======D~~~~      ~
  ~     ||                    ~
  ~  ~  ~  ~  ~  ~  ~  ~  ~  """,

    # --- RECETA DE COCINA ---
    """
  ╔══════════════════════════╗
  ║   RECETA: LONGANIZA      ║
  ║   al natural             ║
  ╠══════════════════════════╣
  ║                          ║
  ║   ( o )                  ║
  ║   ( o )                  ║
  ║    \_/                   ║
  ║     |                    ║
  ║  8======D~~~~            ║
  ║                          ║
  ║  Porciones: 1            ║
  ║  Tiempo: toda la noche   ║
  ╚══════════════════════════╝""",

    # --- INFOGRAFÍA ---
    """
  ANATOMÍA DEL SALCHICHON
  ─────────────────────────────
  ←  cabeza →   ← cuerpo →
      ___         ═══════
     /   \  8 ═══════════ D ~~~
    | ( ) |
     \___/
  ←  testiculario →
  ( oo )""",

    # --- ESTADÍSTICAS ---
    """
  ESTADÍSTICAS DEL DÍA
  ─────────────────────
  Pichulas enviadas hoy:  1
  Tamaño promedio:        8====D
  Nivel de entusiasmo:    ████████░░ 80%
  Humedad relativa:       ~~~~~~~~~~~
  """,

    # --- NOTA MUSICAL ---
    """
  ♩  ♪  ♫  ♬  ♩  ♪  ♫  ♬

  8 ═══════ D ~~~

  ♩  ♪  ♫  ♬  ♩  ♪  ♫  ♬
  "el coyoma canta" """,

    # --- TAROT ---
    """
  ┌─────────────────┐
  │   LA PIRULA     │
  │                 │
  │  ( o )  ( o )  │
  │      \\ /       │
  │    8══╪══D~~~  │
  │       |        │
  │  CARTA XVII    │
  └─────────────────┘
  Significado: suerte y abundancia""",

    # --- EL SUSHI ---
    """
  ╭─────────────────────────╮
  │  ·· MENÚ DEL DÍA ··    │
  │                         │
  │  Roll de Pepino:        │
  │                         │
  │   ====8====D====        │
  │   ~~~~~~~~~~~~~~~~~~~~  │
  │                         │
  │  Chef recomendado       │
  ╰─────────────────────────╯""",

    # --- MINECRAFT ---
    """
  [ ][ ][ ][ ][ ][ ][ ]
  [ ][ ][ ][ ][ ][ ][ ]
  [8][=][=][=][=][D][~]
  [ ][ ][ ][ ][ ][ ][ ]
  [ ][ ][ ][ ][ ][ ][ ]
  "pichula pixelada (minecraft edition)" """,

    # --- PRESENTACIÓN POWERPOINT ---
    """
  ┌──────────────────────────────┐
  │  SLIDE 1 / 1                 │
  │                              │
  │   Estrategia Q3 2026         │
  │                              │
  │      8 ══════ D ~~~          │
  │                              │
  │   "crecer en todos los       │
  │    sentidos del negocio"     │
  └──────────────────────────────┘""",

    # --- PRONÓSTICO DEL TIEMPO ---
    """
  ╔══════════════════════════╗
  ║  PRONÓSTICO: CALUROSO    ║
  ║                          ║
  ║   ☀️  🌡️  ~~~  ~~~  ~~~  ║
  ║                          ║
  ║   ( o )                  ║
  ║    \\ /  8====D~~~~       ║
  ║     V                    ║
  ║  Probabilidad de lluvia: ║
  ║  espesa. 100%.           ║
  ╚══════════════════════════╝""",

    # --- CÓDIGO QR FALSO ---
    """
  ██████████████████████
  ██ ▄▄▄▄▄ █ 8====D ██
  ██ █   █ █ ~~~~~~ ██
  ██ █▄▄▄█ █▄▄▄▄▄▄ ██
  ██▄▄▄▄▄▄▄█▄▄▄▄▄▄▄██
  ██████████████████████
  Escanea para ver más""",

    # --- LA CONSTELACIÓN ---
    """
  .  *    .       *    .
     *  .    *       .
  .    *   o           *
         o   .    *
    *      o     .
        .    8====D~~~~   *
  .  *    .       *    .
  "CONSTELACIÓN: EL CACHALOTE" """,

    # --- EL CONTRATO ---
    """
  POR MEDIO DEL PRESENTE INSTRUMENTO
  ─────────────────────────────────

  El suscrito declara haber recibido:

         8 ═══════════ D ~~~

  En perfectas condiciones de uso.

  Firma receptor: _____________

  Fecha: hoy. Lugar: tu cara.""",

    # --- HISTOGRAMA ---
    """
  DISTRIBUCIÓN DE TAMAÑOS
  ─────────────────────────
  XS  │█
  S   │███
  M   │███████
  L   │█████████████
  XL  │███████████████████
  TU  │8======D~~~~
      └──────────────────""",

    # --- TICKET DE ESTACIONAMIENTO ---
    """
  ┌────────────────────────┐
  │  TICKET N° 00069       │
  │  ESTACIONAMIENTO FULL  │
  │                        │
  │  Vehículo: ANACONDA    │
  │  Largo: 8=======D~~~~  │
  │  Hora entrada: 00:00   │
  │  Hora salida: nunca    │
  │                        │
  │  TARIFA: tu dignidad   │
  └────────────────────────┘""",

    # --- EL DIAGRAMA DE FLUJO ---
    """
  ¿Tiene ganas?
       │
       ▼
  ┌─────────┐    NO    ┌──────────────┐
  │  8====D │ ──────► │ igual 8====D │
  └─────────┘         └──────────────┘
       │ SI
       ▼
   ~~~~~~~~~~
  "el flujograma" """,

    # --- LA ECUACIÓN ---
    """
  ┌────────────────────────────┐
  │                            │
  │   8 + ====== + D = ~~~~    │
  │                            │
  │   TEOREMA DE PITUCHAGORAS  │
  │   comprobado               │
  └────────────────────────────┘""",

    # --- EL TRENDING TOPIC ---
    """
  TWITTER / X  —  TRENDING NOW
  ─────────────────────────────
  1. #Pichula          8====D
  2. #Longaniza         8=====D~
  3. #CallampaFina     8==D~~
  4. #ObeliscoDeCarne  8=========D~~~~
  5. #Matias           ...
  ─────────────────────────────""",

    # --- LOADING BAR ---
    """
  Cargando motivación...

  [████████████████████] 100%

  8 ══════════════════ D ~~~~

  ¡Listo! Que tengas un buen día.""",

    # --- WHATSAPP FAKE ---
    """
  ┌─────────────────────────────┐
  │ 📱 WhatsApp                 │
  │ ─────────────────────────── │
  │ Matias: hola como estai     │
  │                             │
  │              8====D~~~  ✓✓ │
  │                             │
  │ Matias: ...                 │
  │ Matias está escribiendo...  │
  └─────────────────────────────┘""",

    # --- EL FÓSIL ---
    """
  HALLAZGO PALEONTOLÓGICO
  MUSEO DE HISTORIA NATURAL
  ──────────────────────────

   fossilus pichulensis
   Era: Pleistoceno

   ( o )──8═══════D~~~~
   ( o )

  "espécimen en excelente estado" """,
]

HEMAN_SHORTS = [
    "https://www.youtube.com/shorts/Dg8tHpjqxfQ",   # hombre sabio
    "https://www.youtube.com/shorts/tpNn0-s97Xo",   # combatir el estres
    "https://www.youtube.com/shorts/qrJL4DmWU8k",   # no ser arrestado
    "https://www.youtube.com/shorts/WymmEl93TYg",   # Fisto le echa una mano
    "https://www.youtube.com/shorts/aEmSsJaAT-o",   # las cariñosas
    "https://www.youtube.com/shorts/eY6fi3WoKPg",   # tener hambre
    "https://www.youtube.com/shorts/hsLI2QuXeFE",   # consejo laboral
    "https://www.youtube.com/shorts/xjfZCUMYN8A",   # consejo motivacional
    "https://www.youtube.com/shorts/NF6P_WDMlJA",   # pedir perdon
    "https://www.youtube.com/shorts/vd3Y9NyuDWA",   # dormir bien
    "https://www.youtube.com/shorts/U36tu07Swvo",   # generar dinero
    "https://www.youtube.com/shorts/LN6DSHb0CEA",   # consejo general
    "https://www.youtube.com/shorts/ZYJuVpdMMEU",   # fidelidad
    "https://www.youtube.com/shorts/FQxUzLpD_bI",   # el mejor consejo
    "https://www.youtube.com/shorts/wHqw1JFPgS8",   # intro spawned memes
    "https://www.youtube.com/shorts/x_ynXXEitP0",   # he-man coreano
    "https://www.youtube.com/shorts/xnE2AnJrtuU",   # PSA hugging
    "https://www.youtube.com/shorts/el9ejqhcJ-g",   # 4 Non Blondes vs He-Man
    "https://www.youtube.com/shorts/YRRLYEVUQpQ",   # He-Man PSA
    "https://www.youtube.com/shorts/txsy72SJXys",   # He-Man PSA 2
    "https://www.youtube.com/shorts/V3X5v6BXZHI",   # He-Man meme
    "https://www.youtube.com/shorts/QlKBtfl0pf0",   # He-Man PSA 3
]

# Credenciales
MATON_API_KEY      = os.environ.get('MATON_API_KEY')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', os.environ.get('MATON_API_KEY'))
GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN')

# Historial en GitHub
def gh_api(method, path, body=None):
    url = f"https://api.github.com/{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method,
        headers={"Authorization": f"token {GITHUB_TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            return (json.loads(raw) if raw else {}), r.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        return (json.loads(raw) if raw else {}), e.code

def load_history():
    try:
        data, s = gh_api("GET", f"repos/{REPO}/contents/motivation_history.json")
        if s == 200:
            return json.loads(base64.b64decode(data["content"]).decode("utf-8")), data["sha"]
    except Exception as e:
        print(f"No se pudo leer historial: {e}")
    return [], None

def save_history_to_github(history, sha):
    try:
        content = base64.b64encode(json.dumps(history, ensure_ascii=False, indent=2).encode()).decode()
        body = {"message": "update motivation_history.json", "content": content}
        if sha:
            body["sha"] = sha
        _, s = gh_api("PUT", f"repos/{REPO}/contents/motivation_history.json", body)
        print(f"Historial guardado en GitHub: {s}")
    except Exception as e:
        print(f"No se pudo guardar historial: {e}")

def get_history_subjects(history, n=7):
    if not history:
        return "(ninguno aun)"
    return "\n".join([f"- {h['date']}: {h['body'][:60]}" for h in history[-n:]])

# Leer config.json desde GitHub
def load_remote_config():
    try:
        data, status = gh_api("GET", f"repos/{REPO}/contents/config.json")
        if status == 200:
            return json.loads(base64.b64decode(data["content"].replace("\n", "")).decode("utf-8"))
        print(f"Config remota no disponible (HTTP {status}), usando defaults")
        return {}
    except Exception as e:
        print(f"Config remota no disponible ({e}), usando defaults")
        return {}

# Leer respuestas de Matias desde Gmail
def get_matias_replies():
    try:
        query = 'from:matias.levy@alyplas.cl newer_than:7d'
        search_url = f'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages?q={urllib.parse.quote(query)}&maxResults=5'
        req = urllib.request.Request(search_url)
        req.add_header('Authorization', f'Bearer {MATON_API_KEY}')
        req.add_header('Maton-Connection', CELTAVIA_CONNECTION_ID)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.load(r)
        messages = data.get('messages', [])
        if not messages:
            return None
        msg_id = messages[0]['id']
        msg_url = f'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/{msg_id}?format=metadata'
        req2 = urllib.request.Request(msg_url)
        req2.add_header('Authorization', f'Bearer {MATON_API_KEY}')
        req2.add_header('Maton-Connection', CELTAVIA_CONNECTION_ID)
        with urllib.request.urlopen(req2, timeout=10) as r:
            msg = json.load(r)
        snippet = msg.get('snippet', '').strip()
        if snippet:
            print(f"Respuesta de Matias: {snippet[:80]}...")
            return snippet
        return None
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f"Maton Gmail error {e.code}: {body[:300]}")
        return None
    except Exception as e:
        print(f"No se pudo leer respuestas de Matias: {e}")
        return None

# Construir prompt
def build_prompt(config, day_info, history_subjects, matias_reply):
    estilos_map = {
        'chiste':   'CHISTE CORTO al estilo Alvaro Salas o Charly Badulaque: humor chileno, liviano, con remate.',
        'sabio':    'FRASE ABSURDA DE SABIO ANTIGUO: inventada, que suene profunda pero sea una estupidez. Cita a Confucio, Aristoteles, Sun Tzu, Seneca, etc.',
        'graffiti': 'FRASE DE GRAFFITI: absurda, poetica de forma ridicula, remate inesperado.',
        'action':   'ESTILO ANTI-CHUCK NORRIS: Matias NO es un duro. Usa a Stallone, Van Damme, Seagal, Bruce Lee, Schwarzenegger, La Roca, Statham.',
        'paya':     'PAYA CHILENA: cuarteta de 4 versos en rima ABAB o ABCB, estilo payador campesino chileno. Maximo 2 versos de setup, remate picante en los ultimos 2.',
        'cuento':   'CUENTO ULTRA-BREVE: historia de maximo 4 lineas. Personaje, situacion, giro, remate. Estilo absurdo o de humor negro chileno.',
    }

    estilo_sel = config.get('estilo', 'auto')
    if estilo_sel != 'auto' and estilo_sel in estilos_map:
        instruccion_estilo = f"HOY usa este estilo:\n- {estilos_map[estilo_sel]}"
    else:
        instruccion_estilo = "Rota entre estos estilos:\n" + "\n".join([f"- {v}" for v in estilos_map.values()])

    intensidad = config.get('intensidad', 3)
    intensidad_texto = {
        1: "Humor sutil, casi inocente.",
        2: "Humor ligero. El remate es claro pero no tan directo.",
        3: "Humor normal. El remate es claro.",
        4: "Humor directo. Sin rodeos.",
        5: "Humor brutal. El mas explicito posible dentro del limite de 200 caracteres.",
    }.get(intensidad, "Humor normal.")

    priorizar = config.get('temas_priorizar', [])
    evitar    = config.get('temas_evitar', [])
    notas     = config.get('notas_libres', '')

    priorizar_texto = f"\nPRIORIZAR esta semana: {', '.join(priorizar)}" if priorizar else ""
    evitar_texto    = f"\nEVITAR: {', '.join(evitar)}" if evitar else ""
    notas_texto     = f"\nNOTAS ADICIONALES DEL OPERADOR: {notas}" if notas else ""
    reply_texto     = f"\nULTIMA RESPUESTA DE MATIAS: \"{matias_reply}\"" if matias_reply else ""

    if estilo_sel == 'paya':
        formato_chars = "- Exactamente 4 versos separados por salto de linea (\\n), sin limite de caracteres total"
    elif estilo_sel == 'cuento':
        formato_chars = "- Hasta 4 lineas separadas por salto de linea (\\n), sin limite de caracteres total"
    elif estilo_sel == 'auto':
        formato_chars = "- Si eliges paya o cuento: hasta 4 lineas separadas por \\n, sin limite de chars. Si eliges otro estilo: maximo 200 caracteres"
    else:
        formato_chars = "- Maximo 200 caracteres en el body"

    return f"""Eres Francisco Cruz. Le mandas un email diario a tu amigo Matias Levy.

FECHA: {day_info['day']} {day_info['date']}

{instruccion_estilo}

INTENSIDAD DEL HUMOR: {intensidad_texto}

REGLA FIJA: el remate siempre hace referencia a que a Matias le gusta el pene. Usa una palabra al azar de esta lista:
pichula, callampa, chulapi, nepe, tula, corneta, cuchuflí de carne, manguera de cuero, pepino, salchichon, longaniza, obelisco de carne, ciclópe llorón pelado, chino tuerto, anaconda, jeringa de carne, pelao matasapo, escupe semola, el que llora espeso, dedo sin una, cogote de pavo, pistola de quaker, punal de carne, microfono de cuero, pico, diuca, arrollado de vena, el sin oreja, manguaco, coyoma, pirula, la pija, mani, la tranca, la penca, la verga, la palanca, pitulín, la herramienta, el champinon, el ganso, la nutria, el gusanito.

OPCIONAL: también puedes (o no) hacer referencia a que Matias es gay. Si lo haces, usa una de estas palabras o eufemismos al azar:
gay, maricón, maraco, weco, cola, fleto, wekreke, cotito, loca, loquita, colipato, amariconado, afeminado, amujerado, floripondio, del otro equipo, de la vereda del frente, del otro lado, lo tiene puesto, se le quema el arroz, le gustan los tacos altos, le brillan los ojos con los hombres, tiene el radar activo, camina bonito, camina a lo cowboy, secreto en la montaña, no le silba el culo, no le suenan los peos, dobla bien la ropa, hace la cama con esquinas, pliega las servilletas, afina diferente, canta en otro tono, patea con la izquierda, patea para el otro arco, juega de enganche por atrás, usa la puerta de servicio, entra por la cocina, toca el tambor por detrás, duerme boca abajo, masca la almohada, toca la corneta, le gusta la flauta, le gusta el palo en la mano ajena, pone la rodilla en tierra, tiene el asiento reclinado, le gusta el chocolate por detrás.
{priorizar_texto}{evitar_texto}{notas_texto}{reply_texto}

FORMATO:
{formato_chars}
- Sin emojis
- Sin preguntar por planes
- Firma: "Sensei"
- Asunto: siempre "Motivacion diaria"
- NO uses el nombre Matias en el body, usa "tu"

ULTIMOS 7 MENSAJES ENVIADOS (no repetir estilo ni remate):
{history_subjects}

Responde SOLO con JSON:
{{"subject": "Motivacion diaria", "body": "mensaje aqui"}}"""

def get_day_info():
    days_es = {'Monday':'Lunes','Tuesday':'Martes','Wednesday':'Miercoles',
               'Thursday':'Jueves','Friday':'Viernes','Saturday':'Sabado','Sunday':'Domingo'}
    now = datetime.now()
    return {'date': now.strftime('%d/%m/%Y'), 'day': days_es.get(now.strftime('%A'), now.strftime('%A'))}

def generate_ai_content(config, day_info, history):
    print("Generando contenido con IA...")
    history_subjects = get_history_subjects(history, 7)
    matias_reply = get_matias_replies()
    prompt = build_prompt(config, day_info, history_subjects, matias_reply)

    data = json.dumps({
        "model": "anthropic/claude-sonnet-4-5",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 1.0,
        "max_tokens": 400
    }).encode('utf-8')

    req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=data, method='POST')
    req.add_header('Authorization', f'Bearer {OPENROUTER_API_KEY}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('HTTP-Referer', 'https://github.com/panchucrut/daily-motivation')
    req.add_header('X-Title', 'DailyMotivation')

    try:
        response = urllib.request.urlopen(req, timeout=30)
        result = json.load(response)
        content = result['choices'][0]['message']['content']
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0:
            return json.loads(content[json_start:json_end])
        raise ValueError("No JSON en respuesta")
    except Exception as e:
        print(f"Error IA: {e}")
        return {"subject": "Motivacion diaria", "body": f"Hoy es {day_info['day']}. Por si no te habias dado cuenta.\n\nSensei"}

def get_heman_link():
    idx = datetime.now().timetuple().tm_yday % len(HEMAN_SHORTS)
    return HEMAN_SHORTS[idx]

def build_parts(ai_body):
    """Retorna (plain_body, ascii_art, heman, wordle) como componentes separados."""
    heman     = get_heman_link()
    ascii_art = random.choice(ASCII_PENES)
    return ai_body, ascii_art, heman

def build_plain(ai_body, ascii_art, heman):
    return f"{ai_body}\n\n{ascii_art}\n\n---\nWordle de hoy: {WORDLE_URL}\nHe-Man del dia: {heman}"

def build_html(ai_body, ascii_art, heman):
    import html as html_lib
    text_html  = html_lib.escape(ai_body).replace('\n', '<br>')
    ascii_html = html_lib.escape(ascii_art).strip('\n')
    wordle_url = html_lib.escape(WORDLE_URL)
    heman_url  = html_lib.escape(heman)
    return f"""<html><head><meta charset="utf-8"></head>
<body style="font-family: Arial, sans-serif; font-size: 14px; color: #222;">
<p>{text_html}</p>
<pre style="font-family: 'Courier New', Courier, monospace; font-size: 13px; line-height: 1.4; background: #f4f4f4; padding: 12px; border-radius: 4px; display: inline-block; white-space: pre;">{ascii_html}</pre>
<p style="color: #666; font-size: 12px;">---<br>
<a href="{wordle_url}">Wordle de hoy</a> &nbsp;|&nbsp;
<a href="{heman_url}">He-Man del dia</a>
</p>
</body></html>"""

def send_email(subject, ai_body, ascii_art, heman):
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    from_email = 'fcruz@celtavia.cl'
    to_email   = 'matias.levy@alyplas.cl'
    bcc_email  = 'fcruz@celtavia.cl'

    plain = build_plain(ai_body, ascii_art, heman)
    html  = build_html(ai_body, ascii_art, heman)

    print(f"Enviando a {to_email}...")
    message = MIMEMultipart('alternative')
    message['From']    = from_email
    message['To']      = to_email
    message['Bcc']     = bcc_email
    message['Subject'] = subject
    message.attach(MIMEText(plain, 'plain', 'utf-8'))
    message.attach(MIMEText(html,  'html',  'utf-8'))

    raw  = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    data = json.dumps({'raw': raw}).encode('utf-8')

    req = urllib.request.Request(
        'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/send',
        data=data, method='POST')
    req.add_header('Authorization',    f'Bearer {MATON_API_KEY}')
    req.add_header('Maton-Connection', CELTAVIA_CONNECTION_ID)
    req.add_header('Content-Type',     'application/json')

    try:
        response = urllib.request.urlopen(req)
        result = json.load(response)
        print(f"Enviado. ID: {result.get('id','N/A')}")
        return True
    except urllib.error.HTTPError as e:
        print(f"Error HTTP {e.code}: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=" * 60)
    print(f"DAILY MOTIVATION v3.2 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if not MATON_API_KEY:
        print("Error: MATON_API_KEY no configurada")
        sys.exit(1)

    if datetime.now().weekday() >= 5:
        print("Fin de semana, no se envia.")
        sys.exit(0)

    day_info = get_day_info()
    config   = load_remote_config()
    print(f"Config: estilo={config.get('estilo','auto')}, intensidad={config.get('intensidad',3)}, notas={repr(config.get('notas_libres',''))}")

    history, history_sha = load_history()
    ai_content = generate_ai_content(config, day_info, history)

    subject            = ai_content['subject']
    ai_body, ascii_art, heman = build_parts(ai_content['body'])

    print(f"\nAsunto: {subject}")
    print(f"Mensaje:\n{build_plain(ai_body, ascii_art, heman)}\n")

    success = send_email(subject, ai_body, ascii_art, heman)

    if success:
        history.append({'date': datetime.now().strftime('%Y-%m-%d'), 'subject': subject, 'body': ai_content['body']})
        history = history[-30:]
        save_history_to_github(history, history_sha)
        print("\nCOMPLETADO")
    else:
        print("\nFALLO EL ENVIO")
        sys.exit(1)

if __name__ == '__main__':
    main()
