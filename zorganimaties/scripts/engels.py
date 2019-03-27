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


def parse_algemeen_engels(parsed_filmscript, out):
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
        if 'Your medication is called' in v:
            out['waarvoor'] = start
        elif 'How do I know if this medicine is right for me?' in v:
            out['wanneer_niet'] = start    
        elif 'Is there anything I should watch out for while taking this medicine?' in v:
            out['extra_voorzichtig'] = start
        elif 'It is also important that you tell your' in v:
            out['andere_medicijnen'] = start
        elif 'Is there any food or drink I need to avoid?' in v:
            out['eten_drinken'] = start
        elif 'Can I drive while taking this medicine?' in v:
            out['autorijden'] = start
        elif 'Great, and how exactly should I take it?' in v:
            out['hoe_gebruiken'] = start    
        elif 'What should I do if I accidentally take too much?' in v:
            out['teveel_gebruikt'] = start    
        elif 'And what if I forget to take it?' in v:
            out['vergeten_stoppen'] = start    
        elif 'Does this medicine have any side effect?' in v:
            out['bijwerkingen'] = start            
        elif 'This video explains the most important information in the package leaflet.' in v:
            out['aOstart'] = start
        elif 'This concludes the video about your medicine.' in v:
            out['extra_vragen'] = seconden_naar_uren_minuten_seconden(start)
        elif 'Of course you can also contact your doctor or pharmacist.' in v:
            out['bijwerkingen_end'] = end + Decimal(0.5)
    return out


def parse_jong_specifiek_engels(parsed_filmscript, out):
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
        if zwanger and 'pregnant' in v:
            out['zwanger_borstvoeden'] = start
            zwanger = False
        elif 'Thanks for all the info. Bye!' in v:
            out['aOeind'] = end + Decimal(0.5)
    return out    

    
def parse_oud_specifiek_engels(parsed_filmscript, out):
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
        if 'Thank you very much for all this information. Have a nice day too!' in v:
             out['aOeind'] = end + Decimal(0.5)
    return out    
    
   
def get_output_engels(timing_json):
    output = str("""# {extra_vragen}
{niet_gevonden}
{{    
{{
"chapter" : {{
    "start_time":{aOstart},
    "end_time":{aOeind},
    "chapters" :
        [
        {{      "title": "What is this medicine for?",
                "title_short":"What is it for?",
                "start_time":{waarvoor},
                "end_time":{waarvoor_end},
                "disabled" : {waarvoor_disabled}
        }},
        {{      "title": "When should I not use it?",
                "title_short":"When not to use?",
                "start_time":{wanneer_niet},
                "end_time":{wanneer_niet_end},
                "disabled" : {wanneer_niet_disabled}
        }},
        {{      "title": "When should I be careful?",
                "title_short":"When should I be careful?",
                "start_time":{extra_voorzichtig},
                "end_time":{extra_voorzichtig_end},
                "disabled" : {extra_voorzichtig_disabled}
        }},
        {{      "title": "Other medicines",
                "title_short":"Other medicines",
                "start_time":{andere_medicijnen},
                "end_time":{andere_medicijnen_end},
                "disabled" : {andere_medicijnen_disabled}
        }},
        {{      "title": "Food and drinks",
                "title_short":"Food and drinks",
                "start_time":{eten_drinken},
                "end_time":{eten_drinken_end},
                "disabled" : {eten_drinken_disabled}
        }},
        {{      "title": "Pregnancy and breastfeeding",
                "title_short":"Pregnancy and breastfeeding",
                "start_time":{zwanger_borstvoeden},
                "end_time":{zwanger_borstvoeden_end},
                "disabled" : {zwanger_borstvoeden_disabled}
        }},
        {{      "title": "Driving",
                "title_short":"Driving",
                "start_time":{autorijden},
                "end_time":{autorijden_end},
                "disabled" : {autorijden_disabled}
        }},
        {{      "title": "How to use it?",
                "title_short":"How to use it?",
                "start_time":{hoe_gebruiken},
                "end_time":{hoe_gebruiken_end},
                "disabled" : {hoe_gebruiken_disabled}
        }},
        {{      "title": "Used too much?",
                "title_short":"Used too much?",
                "start_time":{teveel_gebruikt},
                "end_time":{teveel_gebruikt_end},
                "disabled" : {teveel_gebruikt_disabled}
        }},
        {{      "title": "Forgotten to use it or stopping?",
                "title_short":"Forgotten or stopping",
                "start_time":{vergeten_stoppen},
                "end_time":{vergeten_stoppen_end},
                "disabled" : {vergeten_stoppen_disabled}
        }},
        {{      "title": "Side effects",
                "title_short":"Side effects",
                "start_time":{bijwerkingen},
                "end_time":{bijwerkingen_end},
                "disabled" : {bijwerkingen_disabled}
        }},
        {{      "title": "How to store it?",
                "title_short":"How to store it?",
                "start_time":{hoe_bewaren},
                "end_time":null,
                "disabled": {hoe_bewaren_disabled}
        }}
        ]
    }}
}}    
""").format(**timing_json)

    return output