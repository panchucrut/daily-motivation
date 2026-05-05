#!/usr/bin/env python3
"""
daily_motivation_email_ai.py — v3.0
- Lee config.json desde GitHub para ajustar el prompt dinámicamente
- Lee últimas respuestas de Matías vía Gmail API
- Incluye link al Wordle en el email
- Genera y envía email diario de lunes a viernes
"""

import urllib.request
import urllib.error
import os
import json
import sys
import base64
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# ── Constantes ─────────────────────────────────────────────────────────────────
SCRIPT_DIR             = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE           = os.path.join(SCRIPT_DIR, 'motivation_history.json')
CELTAVIA_CONNECTION_ID = 'de11f065-b424-4174-8116-fbb2c5bc5510'
WORDLE_URL             = 'https://panchucrut.github.io/daily-motivation/'
REPO                   = 'panchucrut/daily-motivation'
BRANCH                 = 'main'

# ── Credenciales ───────────────────────────────────────────────────────────────
MATON_API_KEY      = os.environ.get('MATON_API_KEY')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', os.environ.get('MATON_API_KEY'))
GITHUB_TOKEN       = os.environ.get('GITHUB_TOKEN')

# ── Historial local ────────────────────────────────────────────────────────────
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
    history.append({'date': datetime.now().strftime('%Y-%m-%d'), 'subject': subject, 'body': body})
    history = history[-30:]
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def get_history_subjects(n=7):
    history = load_history()
    if not history:
        return "(ninguno aun)"
    return "\n".join([f"- {h['date']}: {h['subject']}" for h in history[-n:]])

# ── Leer config.json desde GitHub ─────────────────────────────────────────────
def load_remote_config():
    try:
        url = f'https://raw.githubusercontent.com/{REPO}/{BRANCH}/config.json'
        req = urllib.request.Request(url)
        if GITHUB_TOKEN:
            req.add_header('Authorization', f'Bearer {GITHUB_TOKEN}')
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.load(r)
    except Exception as e:
        print(f"Config remota no disponible ({e}), usando defaults")
        return {}

# ── Leer respuestas de Matías desde Gmail ─────────────────────────────────────
def get_matias_replies():
    """Lee emails recientes de matias.levy@alyplas.cl en los últimos 7 días."""
    try:
        # Buscar emails de Matías en los últimos 7 días
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

        # Leer el más reciente
        msg_id = messages[0]['id']
        msg_url = f'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/{msg_id}?format=snippet'
        req2 = urllib.request.Request(msg_url)
        req2.add_header('Authorization', f'Bearer {MATON_API_KEY}')
        req2.add_header('Maton-Connection', CELTAVIA_CONNECTION_ID)

        with urllib.request.urlopen(req2, timeout=10) as r:
            msg = json.load(r)

        snippet = msg.get('snippet', '').strip()
        if snippet:
            print(f"Respuesta de Matías encontrada: {snippet[:80]}...")
            return snippet
        return None

    except Exception as e:
        print(f"No se pudo leer respuestas de Matías: {e}")
        return None

# ── Construir prompt desde config ──────────────────────────────────────────────
def build_prompt(config, day_info, history_subjects, matias_reply):
    estilos_map = {
        'chileno': 'CHISTE CORTO al estilo Álvaro Salas o Charly Badulaque: humor chileno, liviano, con remate.',
        'sabio':   'FRASE ABSURDA DE SABIO ANTIGUO: inventada, que suene profunda pero sea una estupidez. Cita a Confucio, Aristóteles, Sun Tzu, Séneca, etc.',
        'graffiti':'FRASE DE GRAFFITI: absurda, poética de forma ridícula, remate inesperado.',
        'accion':  'ESTILO ANTI-CHUCK NORRIS: Matías NO es un duro. Usa a Stallone, Van Damme, Seagal, Bruce Lee, Ivan Drago, Schwarzenegger, Bruce Willis, La Roca, Vin Diesel, Statham.',
    }

    estilos_seleccionados = config.get('estilos', [])
    if estilos_seleccionados:
        estilos_texto = "\n".join([f"- {estilos_map[e]}" for e in estilos_seleccionados if e in estilos_map])
        instruccion_estilo = f"HOY usa uno de estos estilos:\n{estilos_texto}"
    else:
        estilos_texto = "\n".join([f"- {v}" for v in estilos_map.values()])
        instruccion_estilo = f"Rota entre estos estilos:\n{estilos_texto}"

    intensidad = config.get('intensidad', 3)
    intensidad_texto = {
        1: "Humor sutil, casi inocente. El remate es suave.",
        2: "Humor ligero. El remate es claro pero no tan directo.",
        3: "Humor normal. El remate es claro.",
        4: "Humor directo. Sin rodeos.",
        5: "Humor brutal. El más explícito posible dentro del límite de 200 caracteres.",
    }.get(intensidad, "Humor normal.")

    priorizar = config.get('priorizar', [])
    evitar = config.get('evitar', [])
    notas = config.get('notas', '')

    priorizar_texto = f"\nPRIORIZAR esta semana: {', '.join(priorizar)}" if priorizar else ""
    evitar_texto = f"\nEVITAR: {', '.join(evitar)}" if evitar else ""
    notas_texto = f"\nNOTAS ADICIONALES: {notas}" if notas else ""
    reply_texto = f"\nÚLTIMA RESPUESTA DE MATÍAS (considera su tono para ajustar): \"{matias_reply}\"" if matias_reply else ""

    prompt = f"""Eres Francisco Cruz. Le mandas un email diario a tu amigo Matías Levy.

FECHA: {day_info['day']} {day_info['date']}

{instruccion_estilo}

INTENSIDAD DEL HUMOR: {intensidad_texto}

REGLA FIJA: el remate siempre hace referencia a que a Matías le gusta el pene. Construcción: el chiste construye hacia ese remate de forma inesperada. Usa una palabra al azar de esta lista — varía cada día:
pichula, callampa, chulapi, nepe, tula, corneta, cuchuflí de carne, manguera de cuero, pepino, salchichón, longaniza, obelisco de carne, cíclope llorón pelado, chino tuerto, anaconda, jeringa de carne, pelao matasapo, escupe sémola, el que llora espeso, dedo sin uña, cogote de pavo, pistola de quaker, puñal de carne, micrófono de cuero, pico, diuca, arrollado de vena, el sin oreja, manguaco, coyoma, el bufanda de queso, el cabeza'e coyac, pirula, el nariz de calamardo, la que cuelga, el niño, el fierro, la presa, el destornillador, virula, el manguaco, la pija, maní, la tranca, la penca, la verga, la palanca, el pedazo, pitulín, la herramienta, el champiñón, el ganso, la nutria, el gusanito, el cacho paraguas, el ñipiñi.
{priorizar_texto}{evitar_texto}{notas_texto}{reply_texto}

FORMATO:
- Máximo 200 caracteres en el body
- Sin emojis
- Sin preguntar por planes
- Firma: "Sensei"
- Asunto: siempre "Motivación diaria"
- NO uses el nombre Matías en el body, usa "tú"

ÚLTIMOS 7 ASUNTOS (no repetir):
{history_subjects}

Responde SOLO con JSON:
{{"subject": "asunto aqui", "body": "mensaje aqui"}}"""

    return prompt

# ── Info del día ───────────────────────────────────────────────────────────────
def get_day_info():
    days_es = {'Monday':'Lunes','Tuesday':'Martes','Wednesday':'Miércoles',
               'Thursday':'Jueves','Friday':'Viernes','Saturday':'Sábado','Sunday':'Domingo'}
    now = datetime.now()
    return {'date': now.strftime('%d/%m/%Y'), 'day': days_es.get(now.strftime('%A'), now.strftime('%A'))}

# ── Generación con IA ──────────────────────────────────────────────────────────
def generate_ai_content(config, day_info):
    print("Generando contenido con IA...")
    history_subjects = get_history_subjects(7)
    matias_reply = get_matias_replies()
    prompt = build_prompt(config, day_info, history_subjects, matias_reply)

    try:
        data = json.dumps({
            "model":       "anthropic/claude-sonnet-4-5",
            "messages":    [{"role": "user", "content": prompt}],
            "temperature": 1.0,
            "max_tokens":  400
        }).encode('utf-8')

        req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions', data=data, method='POST')
        req.add_header('Authorization', f'Bearer {OPENROUTER_API_KEY}')
        req.add_header('Content-Type', 'application/json')
        req.add_header('HTTP-Referer', 'https://github.com/panchucrut/daily-motivation')
        req.add_header('X-Title', 'DailyMotivation')

        response = urllib.request.urlopen(req, timeout=30)
        result   = json.load(response)
        content  = result['choices'][0]['message']['content']

        json_start = content.find('{')
        json_end   = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            return json.loads(content[json_start:json_end])
        raise ValueError("No JSON en respuesta")

    except Exception as e:
        print(f"Error IA, usando respaldo: {e}")
        day_of_year = datetime.now().timetuple().tm_yday
        fallbacks = [
            {"subject": "Motivación diaria", "body": f"Hoy es {day_info['day']}. Por si no te habías dado cuenta.\n\nSensei"},
            {"subject": "Motivación diaria", "body": "Me desperté pensando en ti.\nDespués me arrepentí.\n\nSensei"},
        ]
        return fallbacks[day_of_year % len(fallbacks)]

# ── Construir body con link al Wordle ─────────────────────────────────────────
def build_body(ai_body):
    return f"{ai_body}\n\n---\nWordle de hoy: {WORDLE_URL}"

# ── Envío ──────────────────────────────────────────────────────────────────────
def send_email(subject, body):
    from_email = 'fcruz@celtavia.cl'
    to_email   = 'matias.levy@alyplas.cl'
    bcc_email  = 'fcruz@celtavia.cl'

    print(f"Enviando a {to_email}...")

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
        print(f"Enviado. ID: {result.get('id', 'N/A')}")
        return True
    except urllib.error.HTTPError as e:
        print(f"Error HTTP {e.code}: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"DAILY MOTIVATION v3.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if not MATON_API_KEY:
        print("Error: MATON_API_KEY no configurada")
        sys.exit(1)

    if datetime.now().weekday() >= 5:
        print("Fin de semana — no se envía.")
        sys.exit(0)

    day_info = get_day_info()
    config   = load_remote_config()
    print(f"Config cargada: estilos={config.get('estilos','auto')}, intensidad={config.get('intensidad',3)}")

    ai_content = generate_ai_content(config, day_info)
    subject    = ai_content['subject']
    body       = build_body(ai_content['body'])

    print(f"\nAsunto: {subject}")
    print(f"Mensaje:\n{body}\n")

    success = send_email(subject, body)

    if success:
        save_to_history(subject, ai_content['body'])
        print("\nCOMPLETADO")
    else:
        print("\nFALLÓ EL ENVÍO")
        sys.exit(1)

if __name__ == '__main__':
    import urllib.parse
    main()
