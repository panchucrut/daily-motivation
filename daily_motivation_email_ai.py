#!/usr/bin/env python3
"""
daily_motivation_email_ai.py — v2.3
Genera y envía un email diario de Pancho a Matías Levy.
- Noticias reales del día via RSS (sin API key)
- Prompt corregido: sin lenguaje de pareja, humor con construcción
- TEST_MODE: True = envía solo a fcruz@celtavia.cl
- Al terminar exitosamente regenera Proyecto_DailyMotivationEmail.docx

De:   fcruz@celtavia.cl
Para: matias.levy@alyplas.cl
BCC:  fcruz@celtavia.cl
Hora: 8:00 AM diario (Task Scheduler: OpenClaw_DailyMotivationEmail)
"""

import urllib.request
import xml.etree.ElementTree as ET
import os
import json
import sys
import base64
import subprocess
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# ── Rutas ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE  = os.path.join(SCRIPT_DIR, 'motivation_history.json')
LOG_FILE      = os.path.join(SCRIPT_DIR, '..', 'logs', 'daily_motivation.log')
GENERATE_DOCS = os.path.join(SCRIPT_DIR, 'generate_docs.js')

# ── Credenciales ───────────────────────────────────────────────────────────────
CELTAVIA_CONNECTION_ID = 'de11f065-b424-4174-8116-fbb2c5bc5510'
MATON_API_KEY          = os.environ.get('MATON_API_KEY')
OPENROUTER_API_KEY     = os.environ.get('OPENROUTER_API_KEY', os.environ.get('MATON_API_KEY'))

# ── Historial ──────────────────────────────────────────────────────────────────
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_to_history(subject, body):
    history = load_history()
    history.append({
        'date':    datetime.now().strftime('%Y-%m-%d'),
        'subject': subject,
        'body':    body
    })
    history = history[-30:]
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def get_history_subjects(n=7):
    history = load_history()
    if not history:
        return "(ninguno aun)"
    lines = [f"- {h['date']}: {h['subject']}" for h in history[-n:]]
    return "\n".join(lines)

# ── Info del dia ───────────────────────────────────────────────────────────────
def get_day_info():
    days_es = {
        'Monday':'Lunes','Tuesday':'Martes','Wednesday':'Miercoles',
        'Thursday':'Jueves','Friday':'Viernes','Saturday':'Sabado','Sunday':'Domingo'
    }
    now = datetime.now()
    return {
        'date': now.strftime('%d/%m/%Y'),
        'day':  days_es.get(now.strftime('%A'), now.strftime('%A'))
    }

# ── Noticias reales via RSS ────────────────────────────────────────────────────
def fetch_real_news(max_items=5):
    """Lee titulares reales de medios chilenos via RSS publico. Sin API key."""
    feeds = [
        'https://news.google.com/rss/search?q=farandula+chile&hl=es-419&gl=CL&ceid=CL:es-419',
        'https://news.google.com/rss/search?q=show+business+celebridades+chile&hl=es-419&gl=CL&ceid=CL:es-419',
        'https://news.google.com/rss/search?q=alfombra+roja+premios+famosos&hl=es-419&gl=CL&ceid=CL:es-419',
    ]
    headlines = []
    for url in feeds:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as r:
                tree = ET.parse(r)
            for item in tree.findall('.//item')[:3]:
                title = item.findtext('title', '').strip()
                if title:
                    headlines.append(title)
            if len(headlines) >= max_items:
                break
        except Exception as e:
            print(f"Advertencia RSS {url}: {e}")
            continue

    if not headlines:
        headlines = ["Sin noticias disponibles hoy"]

    print(f"Titulares obtenidos: {len(headlines)}")
    return headlines[:max_items]

# ── Generacion con IA ──────────────────────────────────────────────────────────
def generate_ai_content(day_info):
    print("Generando contenido con IA...")

    history_subjects = get_history_subjects(7)
    prompt = f"""Eres Francisco Cruz. Le mandas un email diario a tu amigo Matias Levy.

FECHA: {day_info['day']} {day_info['date']}

EL CHISTE:
Cada dia mandas UN chiste corto. Puede ser de uno de estos estilos — varia cada dia:
1. CHISTE CORTO al estilo Alvaro Salas o Charly Badulaque: humor chileno, liviano, con remate.
2. FRASE ABSURDA DE SABIO ANTIGUO: inventada, que suene profunda pero sea una estupidez. Como la gente tonta que se las da de inteligente citando a Confucio, Aristoteles, Sun Tzu, Seneca, etc. tambien puedes usar personajes tipicos de peliculas.
3. FRASE DE GRAFFITI: absurda, poetica de forma ridicula, remate inesperado.
4. ESTILO CHUCK NORRIS FACTS pero al reves: Matias NO es un duro. No siempre hagas referencia a Chuck Norris, varia entre Stallone, Van Damme, Seagal, Bruce Lee, Ivan Drago, Schwarzenegger, Bruce Willis, Dwayne "La Roca" Johnson, Vin Diesel, Jason Statham y los personajes clasicos que hicieron estos actores.

REGLA FIJA EN TODOS: el remate o punch line siempre hace referencia a que a Matias le gusta el pene. Tiene que tener CONSTRUCCION: el chiste construye hacia ese remate de forma inesperada y graciosa. Usa una de estas palabras o frases al azar — varia cada dia, no repitas:
pichula, callampa, chulapi, nepe, tula, corneta, cuchuflí de carne, manguera de cuero, pepino, salchichon, longaniza, obelisco de carne, ciclope lloron pelado, chino tuerto, anaconda, jeringa de carne, taladro de carne, pelao matasapo, escupe semola, el que llora espeso, dedo sin uña, cogote de pavo, pistola de quaker, puñal de carne, microfono de cuero, pico, diuca, arrollado de vena, el sin oreja, manguaco, coyoma, el bufanda de queso, el cabeza'e coyac, pirula, el nariz de calamardo, la que cuelga.

FORMATO:
- Maximo 200 caracteres en el body
- Sin emojis
- Sin preguntar por planes
- Firma: "Sensei"
- Asunto: siempre "Motivacion diaria"
- En el body NO uses el nombre Matias, usa "tu" en su lugar

ULTIMOS 7 ASUNTOS (no repetir):
{history_subjects}

Responde SOLO con JSON:
{{"subject": "asunto aqui", "body": "mensaje aqui"}}"""    

    try:
        data = json.dumps({
            "model":       "anthropic/claude-sonnet-4-5",
            "messages":    [{"role": "user", "content": prompt}],
            "temperature": 1.0,
            "max_tokens":  400
        }).encode('utf-8')

        req = urllib.request.Request(
            'https://openrouter.ai/api/v1/chat/completions',
            data=data, method='POST'
        )
        req.add_header('Authorization', f'Bearer {OPENROUTER_API_KEY}')
        req.add_header('Content-Type', 'application/json')
        req.add_header('HTTP-Referer', 'https://openclaw.ai')
        req.add_header('X-Title', 'DailyMotivation')

        response = urllib.request.urlopen(req, timeout=30)
        result   = json.load(response)
        content  = result['choices'][0]['message']['content']

        json_start = content.find('{')
        json_end   = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            return json.loads(content[json_start:json_end])
        raise ValueError("No se encontro JSON en la respuesta")

    except Exception as e:
        print(f"Error con IA, usando respaldo: {e}")
        day_of_year = datetime.now().timetuple().tm_yday
        fallbacks = [
            {
                "subject": "Oye",
                "body": f"Matias.\n\nHoy es {day_info['day']}. Por si no te habias dado cuenta.\nLas oportunidades no avisan. Tu tampoco, pero eso es otro tema.\n\nPancho"
            },
            {
                "subject": "Pense en ti esta manana (y me arrepenti)",
                "body": "Matias.\n\nMe desperte pensando en ti.\nDespues me di cuenta de que habia tomado mucho.\n\nEn fin. A trabajar.\n\nPancho"
            },
            {
                "subject": "Dato del dia",
                "body": f"Matias.\n\n{day_info['day']}. Tu sabes lo que eso significa.\nNada. Para ti todos los dias son iguales.\n\nAprovecha igual.\n\nPancho"
            }
        ]
        return fallbacks[day_of_year % len(fallbacks)]

# ── Envio modo test (solo a celtavia) ─────────────────────────────────────────
def send_email_test(subject, body):
    """Modo test: envia solo a fcruz@celtavia.cl con [TEST] en el asunto"""
    from_email = 'fcruz@celtavia.cl'
    to_email   = 'fcruz@celtavia.cl'

    print(f"[TEST] Enviando solo a {to_email}...")

    message = MIMEMultipart()
    message['From']    = from_email
    message['To']      = to_email
    message['Subject'] = f"[TEST] {subject}"
    message.attach(MIMEText(body, 'plain', 'utf-8'))

    raw  = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    data = json.dumps({'raw': raw}).encode('utf-8')

    req = urllib.request.Request(
        'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/send',
        data=data, method='POST'
    )
    req.add_header('Authorization',    f'Bearer {MATON_API_KEY}')
    req.add_header('Maton-Connection', CELTAVIA_CONNECTION_ID)
    req.add_header('Content-Type',     'application/json')

    try:
        response = urllib.request.urlopen(req)
        result   = json.load(response)
        print(f"[TEST] Enviado! ID: {result.get('id', 'N/A')}")
        return True
    except urllib.error.HTTPError as e:
        print(f"Error HTTP {e.code}: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# ── Envio real ─────────────────────────────────────────────────────────────────
def send_email(subject, body):
    from_email = 'fcruz@celtavia.cl'
    to_email   = 'matias.levy@alyplas.cl'
    bcc_email  = 'fcruz@celtavia.cl'

    print(f"Enviando a {to_email} (BCC: {bcc_email})...")

    message = MIMEMultipart()
    message['From']    = from_email
    message['To']      = to_email
    message['Bcc']     = bcc_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain', 'utf-8'))

    raw  = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    data = json.dumps({'raw': raw}).encode('utf-8')

    req = urllib.request.Request(
        'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/send',
        data=data, method='POST'
    )
    req.add_header('Authorization',    f'Bearer {MATON_API_KEY}')
    req.add_header('Maton-Connection', CELTAVIA_CONNECTION_ID)
    req.add_header('Content-Type',     'application/json')

    try:
        response = urllib.request.urlopen(req)
        result   = json.load(response)
        print(f"Enviado! ID: {result.get('id', 'N/A')}")
        return True
    except urllib.error.HTTPError as e:
        print(f"Error HTTP {e.code}: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# ── Actualizar documentacion ───────────────────────────────────────────────────
def update_docs():
    if not os.path.exists(GENERATE_DOCS):
        print("generate_docs.js no encontrado, omitiendo")
        return
    try:
        print("Actualizando documentacion...")
        result = subprocess.run(
            ['node', GENERATE_DOCS],
            cwd=SCRIPT_DIR, capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            print(result.stdout.strip())
        else:
            print(f"Error docs: {result.stderr.strip()}")
    except Exception as e:
        print(f"No se pudo actualizar docs: {e}")

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"DAILY MOTIVATION v2.3 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if not MATON_API_KEY:
        print("Error: MATON_API_KEY no configurada")
        sys.exit(1)

    day_info   = get_day_info()

    # Solo ejecutar lunes a viernes
    if datetime.now().weekday() >= 5:
        print("Fin de semana — no se envia correo.")
        sys.exit(0)

    ai_content = generate_ai_content(day_info)
    subject    = ai_content['subject']
    body       = ai_content['body']

    print(f"\nAsunto: {subject}")
    print(f"Mensaje:\n{body}\n")

    # TEST_MODE = True  -> envia solo a fcruz@celtavia.cl
    # TEST_MODE = False -> envia a Matias (produccion)
    TEST_MODE = False
    if TEST_MODE:
        success = send_email_test(subject, body)
    else:
        success = send_email(subject, body)

    if success:
        save_to_history(subject, body)
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().isoformat()} | {subject}\n")
        update_docs()
        print("\nCOMPLETADO")
    else:
        print("\nFALLO EL ENVIO")
        sys.exit(1)

if __name__ == '__main__':
    main()
