import httpx
from config.settings import FOOTBALL_DATA_API_KEY

EQUIPOS_IDS = {
    # --- PREMIER LEAGUE 2026/27 (20 Equipos Confirmados) ---
    "arsenal": 57,
    "aston villa": 58,
    "bournemouth": 1044,
    "brentford": 402,
    "brighton": 397,
    "chelsea": 61,
    "coventry": 1076,
    "coventry city": 1076,
    "crystal palace": 354,
    "everton": 62,
    "fulham": 63,
    "hull city": 322,
    "hull": 322,
    "ipswich": 349,
    "leeds": 341,
    "leeds united": 341,
    "liverpool": 64,
    "manchester city": 65,
    "man city": 65,
    "manchester united": 66,
    "man utd": 66,
    "newcastle": 67,
    "nottingham forest": 351,
    "sunderland": 71,
    "tottenham": 73,
    "spurs": 73,

    # --- LALIGA (España) ---
    "real madrid": 86,
    "madrid": 86,
    "barcelona": 81,
    "barca": 81,

    # --- BUNDESLIGA (Alemania) ---
    "bayer leverkusen": 3,
    "leverkusen": 3,
    "bayern munich": 5,
    "bayern": 5,
}

def consult_last_matches(equipo: str, tipo: str = "PASADOS", cantidad: int = 3) -> str:
    nombre_normalizado = equipo.strip().lower()
    
    if nombre_normalizado in EQUIPOS_IDS:
        equipo_id = EQUIPOS_IDS[nombre_normalizado]
    elif equipo.isdigit():
        equipo_id = int(equipo)
    else:
        return f"El equipo '{equipo}' no está registrado en tu lista."

    url = f"https://api.football-data.org/v4/teams/{equipo_id}/matches"
    headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
    status_filter = "FINISHED" if tipo.upper() == "PASADOS" else "SCHEDULED"
    params = {"status": status_filter, "limit": str(cantidad)}

    try:
        # Client con timeout de 2.5 segundos para no congelar la ejecución
        with httpx.Client(timeout=2.5) as client:
            response = client.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                return f"Error HTTP {response.status_code}: {response.text}"
                
            data = response.json()
            partidos = data.get("matches", [])

            if not partidos:
                params.pop("status", None)
                response = client.get(url, headers=headers, params=params)
                partidos = response.json().get("matches", [])
                if not partidos:
                    return f"No se encontraron partidos ({tipo}) para {equipo}."

            resumen = []
            for item in partidos[:cantidad]:
                local = item["homeTeam"]["name"]
                visita = item["awayTeam"]["name"]
                goles_local = item["score"]["fullTime"]["home"]
                goles_visita = item["score"]["fullTime"]["away"]
                fecha = item["utcDate"][:10]
                competicion = item["competition"]["name"]

                if status_filter == "FINISHED" and goles_local is not None:
                    resumen.append(f"[{competicion}] {fecha} | {local} {goles_local} - {goles_visita} {visita}")
                else:
                    resumen.append(f"[{competicion}] {fecha} | {local} vs {visita} (Próximo)")

            encabezado = "Últimos resultados" if tipo.upper() == "PASADOS" else "Próximos partidos"
            return f"--- {encabezado} de {equipo.title()} ---\n" + "\n".join(resumen)

    except httpx.TimeoutException:
        return "Error: La API de fútbol tardó demasiado en responder."
    except Exception as e:
        return f"Error al consultar la API: {str(e)}"