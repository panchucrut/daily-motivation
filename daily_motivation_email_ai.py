#!/usr/bin/env python3
"""
daily_motivation_email_ai.py — v3.1
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
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Constantes
CELTAVIA_CONNECTION_ID = 'de11f065-b424-4174-8116-fbb2c5bc5510'
WORDLE_URL             = 'https://panchucrut.github.io/daily-motivation/'
REPO                   = 'panchucrut/daily-motivation'
BRANCH                 = 'main'

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
        url = f'https://raw.githubusercontent.com/{REPO}/{BRANCH}/config.json'
        req = urllib.request.Request(url)
        if GITHUB_TOKEN:
            req.add_header('Authorization', f'Bearer {GITHUB_TOKEN}')
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.load(r)
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
        msg_url = f'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/{msg_id}?format=snippet'
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

    return f"""Eres Francisco Cruz. Le mandas un email diario a tu amigo Matias Levy.

FECHA: {day_info['day']} {day_info['date']}

{instruccion_estilo}

INTENSIDAD DEL HUMOR: {intensidad_texto}

REGLA FIJA: el remate siempre hace referencia a que a Matias le gusta el pene. Usa una palabra al azar de esta lista:
pichula, callampa, chulapi, nepe, tula, corneta, cuchuflí de carne, manguera de cuero, pepino, salchichon, longaniza, obelisco de carne, ciclópe llorón pelado, chino tuerto, anaconda, jeringa de carne, pelao matasapo, escupe semola, el que llora espeso, dedo sin una, cogote de pavo, pistola de quaker, punal de carne, microfono de cuero, pico, diuca, arrollado de vena, el sin oreja, manguaco, coyoma, pirula, la pija, mani, la tranca, la penca, la verga, la palanca, pitulín, la herramienta, el champinon, el ganso, la nutria, el gusanito.
{priorizar_texto}{evitar_texto}{notas_texto}{reply_texto}

FORMATO:
- Maximo 200 caracteres en el body
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

def build_body(ai_body):
    return f"{ai_body}\n\n---\nWordle de hoy: {WORDLE_URL}"

def send_email(subject, body):
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

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
    print(f"DAILY MOTIVATION v3.1 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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

    subject = ai_content['subject']
    body    = build_body(ai_content['body'])

    print(f"\nAsunto: {subject}")
    print(f"Mensaje:\n{body}\n")

    success = send_email(subject, body)

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
