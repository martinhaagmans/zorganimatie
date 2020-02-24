import math
from decimal import Decimal

def seconden_naar_uren_minuten_seconden(sec):
    """Convert seconds to hours:minutes:seconds:hundreds and return a string."""
    sec, rest = str(sec).split('.')
    sec = int(sec)
    if sec < 60:
        uren = 0
        minuten = 0
        seconden = sec
    elif sec >= 60:
        uren = 0
        minuten = math.floor(sec / 60)
        seconden = sec - 60 * minuten
    elif sec >= 3600:
        uren = math.floor(sec / 3600)
        sec = sec - 3600 * uren
        minuten = math.floor(sec / 60)
        seconden = sec - 60 * minuten
    uren = str(uren).zfill(2)
    minuten = str(minuten).zfill(2)
    seconden = str(seconden).zfill(2)
    return '{}:{}:{}:{}'.format(uren, minuten, seconden, rest)


def parse_algemeen_nl(parsed_filmscript, out):
    """Find specific phrases and return dict.

    Iterate dict of parsed file with timestamp-phrase
    as key-value pairs. Add timestamp for found phrase
    a value to output dict with the corresponding 
    timestamp number as key. Return the output dict
    after iterating the entire dict.
    """
    for k, v in parsed_filmscript.items():
        try:
            start, end = k
        except ValueError:
            continue
        if 'Uw medicijn heet' in v:
            out['waarvoor'] = start
        elif 'Vertel de dokter en de apotheek ook welke andere medicijnen u gebruikt' in v:
            out['andere_medicijnen'] = start
        elif 'Moet ik nog ergens op letten met eten en drinken?' in v:
            out['eten_drinken'] = start
        elif 'Kijksluiter bevat alleen de meest belangrijke informatie uit de bijsluiter.' in v:
            out['aOstart'] = start
        elif 'Dit was Kijksluiter!' in v or 'Dit was Kijksluiter.' in v:
            out['extra_vragen'] = seconden_naar_uren_minuten_seconden(start)
        elif 'Maar u kunt natuurlijk ook met de dokter of met de apotheek contact opnemen.' in v:
            out['bijwerkingen_end'] = end + Decimal(0.5)
    return out


def parse_jong_specifiek_nl(parsed_filmscript, out):
    """Find specific phrases and return dict.

    Iterate dict of parsed file with timestamp-phrase
    as key-value pairs. Add timestamp for found phrase
    a value to output dict with the corresponding 
    timestamp number as key. Return the output dict
    after iterating the entire dict.
    """

    zwanger = False
    if 'vrouw' in parsed_filmscript['filename'].lower():
        zwanger = True
    else:
        out['zwanger_borstvoeden'] = ''
    for k, v in parsed_filmscript.items():
        try:
            start, end = k
        except ValueError:
            continue
        if 'Hoe weet ik of ik dit medicijn mag gebruiken?' in v:
            out['wanneer_niet'] = start
        elif 'Moet ik zelf nog ergens op letten als ik dit medicijn gebruik?' in v:
            out['extra_voorzichtig'] = start
        elif ('Mag ik gewoon auto rijden als ik dit medicijn gebruik?' in v or 
              'Mag ik gewoon autorijden als ik dit medicijn gebruik?' in v):
            out['autorijden'] = start
        elif 'Okay, en hoe moet ik het gebruiken?' in v:
            out['hoe_gebruiken'] = start
        elif ('Wat moet ik doen als ik teveel heb gebruikt?' in v or
              'Wat moet ik doen als ik te veel heb gebruikt?' in v):
            out['teveel_gebruikt'] = start
        elif 'En als ik het een keer vergeet?' in v:
            out['vergeten_stoppen'] = start
        elif 'Heeft dit middel ook bijwerkingen?' in v:
            out['bijwerkingen'] = start
        elif zwanger and 'zwanger' in v:
            out['zwanger_borstvoeden'] = start
            zwanger = False
        elif 'Dank voor alle informatie. Tot ziens!' in v:
            out['aOeind'] = end + Decimal(0.5)
    return out


def parse_oud_specifiek_nl(parsed_filmscript, out):
    """Find specific phrases and return dict.

    Iterate dict of parsed file with timestamp-phrase
    as key-value pairs. Add timestamp for found phrase
    a value to output dict with the corresponding 
    timestamp number as key. Return the output dict
    after iterating the entire dict.
    """
    out['zwanger_borstvoeden'] = ''
    for k, v in parsed_filmscript.items():
        try:
            start, end = k
        except ValueError:
            continue
        if 'Hoe weet ik zeker of ik dit medicijn mag gebruiken?' in v:
            out['wanneer_niet'] = start
        elif 'Moet ik ergens speciaal op letten als ik dit medicijn gebruik?' in v:
            out['extra_voorzichtig'] = start
        elif 'zelf rijden als ik dit medicijn gebruik' in v:
            out['autorijden'] = start
        elif 'Okay, en hoe moet ik dit medicijn precies gebruiken?' in v:
            out['hoe_gebruiken'] = start
        elif ('Het is me duidelijk. Wat moet ik doen als ik per ongeluk te veel heb gebruikt?' in v or 
              'Het is me duidelijk. Wat moet ik doen als ik per ongeluk teveel heb gebruikt?' in v):
            out['teveel_gebruikt'] = start
        elif 'En mocht ik een keer vergeten dit medicijn te gebruiken?' in v:
            out['vergeten_stoppen'] = start
        elif 'Wat voor bijwerkingen kan ik verwachten?' in v:
            out['bijwerkingen'] = start
        elif 'Hartelijk dank voor alle informatie. U ook een fijne dag!' in v:
             out['aOeind'] = end + Decimal(0.5)
    return out

def get_output_nl(timing_json):
    output = str("""# {extra_vragen}
{niet_gevonden}
{{
"chapter" : {{
    "start_time":{aOstart},
    "end_time":{aOeind},
    "chapters" :
        [
        {{      "title": "Waarvoor is dit medicijn?",
                "title_short":"Waarvoor is het?",
                "start_time":{waarvoor},
                "end_time":{waarvoor_end},
                "disabled" : {waarvoor_disabled}
        }},
        {{      "title": "Wanneer niet gebruiken?",
                "title_short":"Wanneer niet gebruiken?",
                "start_time":{wanneer_niet},
                "end_time":{wanneer_niet_end},
                "disabled" : {wanneer_niet_disabled}
        }},
        {{      "title": "Waar moet ik op letten?",
                "title_short":"Waar op letten?",
                "start_time":{extra_voorzichtig},
                "end_time":{extra_voorzichtig_end},
                "disabled" : {extra_voorzichtig_disabled}
        }},
        {{      "title": "Andere medicijnen",
                "title_short":"Andere medicijnen",
                "start_time":{andere_medicijnen},
                "end_time":{andere_medicijnen_end},
                "disabled" : {andere_medicijnen_disabled}
        }},
        {{      "title": "Eten en drinken",
                "title_short":"Eten en drinken",
                "start_time":{eten_drinken},
                "end_time":{eten_drinken_end},
                "disabled" : {eten_drinken_disabled}
        }},
        {{      "title": "Zwangerschap of borstvoeding",
                "title_short":"Zwanger of borstvoeding",
                "start_time":{zwanger_borstvoeden},
                "end_time":{zwanger_borstvoeden_end},
                "disabled" : {zwanger_borstvoeden_disabled}
        }},
        {{      "title": "Autorijden",
                "title_short":"Autorijden",
                "start_time":{autorijden},
                "end_time":{autorijden_end},
                "disabled" : {autorijden_disabled}
        }},
        {{      "title": "Hoe gebruiken?",
                "title_short":"Hoe gebruiken?",
                "start_time":{hoe_gebruiken},
                "end_time":{hoe_gebruiken_end},
                "disabled" : {hoe_gebruiken_disabled}
        }},
        {{      "title": "Teveel gebruikt?",
                "title_short":"Teveel gebruikt?",
                "start_time":{teveel_gebruikt},
                "end_time":{teveel_gebruikt_end},
                "disabled" : {teveel_gebruikt_disabled}
        }},
        {{      "title": "Vergeten of stoppen",
                "title_short":"Vergeten of stoppen",
                "start_time":{vergeten_stoppen},
                "end_time":{vergeten_stoppen_end},
                "disabled" : {vergeten_stoppen_disabled}
        }},
        {{      "title": "Bijwerkingen",
                "title_short":"Bijwerkingen",
                "start_time":{bijwerkingen},
                "end_time":{bijwerkingen_end},
                "disabled" : {bijwerkingen_disabled}
        }},
        {{      "title": "Hoe bewaren?",
                "title_short":"Hoe bewaren?",
                "start_time":{hoe_bewaren},
                "end_time":null,
                "disabled": {hoe_bewaren_disabled}
        }}
        ]
    }}
}}
""").format(**timing_json)

    return output