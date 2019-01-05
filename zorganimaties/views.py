"""This script is for zorganimaties. It parses a textfile and returns JSON."""

import os
import math
import time
from decimal import Decimal

import zipfile
from flask import Flask
from flask import render_template, flash, request, redirect, send_from_directory, url_for

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'tmp'
app.config['SECRET_KEY'] = 'amygdala'
MYDIR = os.path.dirname(os.path.abspath(__file__))
save_location = os.path.join(MYDIR,  app.config['UPLOAD_FOLDER'])

EVENTS = [  "waarvoor",
            "wanneer_niet",
            "extra_voorzichtig",
            "andere_medicijnen",
            "eten_drinken",
            "zwanger_borstvoeden",
            "autorijden",
            "hoe_gebruiken",
            "teveel_gebruikt",
            "vergeten_stoppen",
            "bijwerkingen",
            "hoe_bewaren"]

def seconden_naar_minuten_seconden(sec):
    """Convert seconds to minutes:seconds and return a string."""
    sec = int(sec) - 1
    if sec < 60:
        minuten = 0
        seconden = sec
    elif sec >= 60:
        minuten = math.floor(sec / 60)
        seconden = sec - 60 * minuten
    minuten = str(minuten).zfill(2)
    seconden = str(seconden).zfill(2)
    return('{}.{}'.format(minuten, seconden))


def parse_filmscript(filmscript):
    """Parse input text file and return a dictionary."""
    i = 0
    time = str()
    tekst = str()
    out = dict()
    out['filename'] = os.path.basename(str(filmscript))
    with open(filmscript, 'r', encoding="utf-8") as f:
        for line in f:
            if not line in ['\n', '\r\n']:
                i += 1

            if i == 1:
                continue

            elif i == 2:
                time = line.split(' --> ')[0]
                time, fraction = time.split(',')
                h, m, s = time.split(':')
                time = int(h) * (60*60) + int(m) * 60 + int(s)
                time = '{}.{}'.format(time, str(fraction)[:2])
                time = Decimal(time)

            elif i >= 3 and line not in ['\n', '\r\n']:
                tekst = tekst + ' ' + line.rstrip()

            elif line in ['\n', '\r\n']:
                i = 0
                out[time] = tekst.lstrip()
                time = str()
                tekst = str()
    return out


def parse_jong_specifiek(parsed_filmscript, out):
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
        if 'Hoe weet ik of ik dit medicijn mag gebruiken?' in v:
            out['wanneer_niet'] = k
        elif 'Moet ik zelf nog ergens op letten als ik dit medicijn gebruik?' in v:
            out['extra_voorzichtig'] = k
        elif 'Mag ik gewoon auto rijden als ik dit medicijn gebruik?' in v:
            out['autorijden'] = k
        elif 'Okay, en hoe moet ik het gebruiken?' in v:
            out['hoe_gebruiken'] = k
        elif 'Wat moet ik doen als ik teveel heb gebruikt?' in v:
            out['teveel_gebruikt'] = k
        elif 'Heeft dit middel ook bijwerkingen?' in v:
            out['bijwerkingen'] = k
        elif 'Zal ik doen!' in v:
            out['bijwerkingen_end'] = k
        elif zwanger and 'zwanger' in v:
            out['zwanger_borstvoeden'] = k
            zwanger = False
    return out


def parse_oud_specifiek(parsed_filmscript, out):
    """Find specific phrases and return dict.

    Iterate dict of parsed file with timestamp-phrase
    as key-value pairs. Add timestamp for found phrase
    a value to output dict with the corresponding 
    timestamp number as key. Return the output dict
    after iterating the entire dict.
    """
    out['zwanger_borstvoeden'] = ''
    for k, v in parsed_filmscript.items():
        if 'Hoe weet ik zeker of ik dit medicijn mag gebruiken?' in v:
            out['wanneer_niet'] = k
        elif 'Moet ik ergens specifiek op letten als ik dit medicijn gebruik?' in v:
            out['extra_voorzichtig'] = k
        elif 'zelf rijden als ik dit medicijn gebruik' in v:
            out['autorijden'] = k
        elif 'Okay, en hoe moet ik dit medicijn precies gebruiken?' in v:
            out['hoe_gebruiken'] = k
        elif 'Wat moet ik doen als ik per ongeluk te veel heb gebruikt?' in v:
            out['teveel_gebruikt'] = k
        elif 'Wat voor bijwerkingen kan ik verwachten?' in v:
            out['bijwerkingen'] = k
        elif 'Ik laat van me horen als er iets is.' in v:
            out['bijwerkingen_end'] = k
    return out


def parse_algemeen(parsed_filmscript, out):
    """Find specific phrases and return dict.

    Iterate dict of parsed file with timestamp-phrase
    as key-value pairs. Add timestamp for found phrase
    a value to output dict with the corresponding 
    timestamp number as key. Return the output dict
    after iterating the entire dict.
    """
    for k, v in parsed_filmscript.items():
        if 'Uw medicijn heet' in v:
            out['waarvoor'] = k
        elif 'Het is ook belangrijk dat u de dokter en de apotheek vertelt welke andere medicijnen u' in v:
            out['andere_medicijnen'] = k
        elif 'Moet ik nog ergens op letten met eten en drinken?' in v:
            out['eten_drinken'] = k
        elif 'En als ik het een keer vergeet?' in v:
            out['vergeten_stoppen'] = k
        elif 'Ik hoop dat deze informatie u heeft geholpen.'in v and 'En een hele fijne dag nog!' in v:
            out['aOuit'] = k

    return out


def parse_alles(filmscript):
    """Collect all timestamp times, parse them into a string and return the string."""
    timing_json = dict()

    dscript = parse_filmscript(filmscript)

    timing_json = parse_algemeen(dscript, timing_json)

    script_name = dscript['filename'].lower()

    zwanger = True

    if 'jong' in script_name:
        timing_json = parse_jong_specifiek(dscript, timing_json)

        if not 'vrouw' in script_name:
            zwanger = False

    elif 'oud' in script_name:
        zwanger = False
        timing_json = parse_oud_specifiek(dscript, timing_json)

    errors = list()

    for to_check in EVENTS:
        if to_check not in timing_json:
            errors.append(to_check)
            timing_json[to_check] = ''
            timing_json['{}_disabled'.format(to_check)] = 'true'
        else:
            timing_json['{}_disabled'.format(to_check)] = 'false'

    for i in range(0, 11):
        key_start = EVENTS[i]
        key_end = EVENTS[i + 1]

        if not zwanger and key_start == 'eten_drinken':
            key_end = EVENTS[i + 2]

        if '{}_end'.format(key_start) in timing_json:
            continue

        time_end = timing_json['{}'.format(key_end)]

        try:
            time_end = Decimal(float(time_end)) - Decimal((1/100))
        except ValueError as e:
            timing_json['{}_end'.format(key_start)] = ''
        else:
            time_end = round(time_end, 2)

        timing_json['{}_end'.format(key_start)] = time_end

    if not 'aOuit' in timing_json:
        errors.append('aOuit')
        timing_json['aOuit'] = ''

    if not zwanger:
        timing_json['zwanger_borstvoeden_disabled'] = 'true'
        timing_json['zwanger_borstvoeden_end'] = ''
        timing_json['zwanger_borstvoeden'] = ''

    if len(errors) == 0:
        timing_json['niet_gevonden'] = '# Alles ok'
    else:
        timing_json['niet_gevonden'] = '# {} niet gevonden.'.format(' '.join(errors))

    output = str("""{niet_gevonden}
{{
"Tijden" : {{
    "start_time":"32.00",
    "end_time":"{aOuit}"
            }},
"chapters" :
    [
    {{      "title": "Waarvoor is dit medicijn",
            "title_short":"Waarvoor",
            "start_time":"{waarvoor}",
            "end_time":"{waarvoor_end}",
            "disabled" : {waarvoor_disabled},
    }},
    {{      "title": "Wanneer niet gebruiken",
            "title_short":"Wanneer niet",
            "start_time":"{wanneer_niet}",
            "end_time":"{wanneer_niet_end}",
            "disabled" : {wanneer_niet_disabled},
    }},
    {{      "title": "Waar moet ik op letten",
            "title_short":"Extra voorzichtig",
            "start_time":"{extra_voorzichtig}",
            "end_time":"{extra_voorzichtig_end}",
            "disabled" : {extra_voorzichtig_disabled},
    }},
    {{      "title": "Andere medicijnen",
            "title_short":"Andere medicijnen",
            "start_time":"{andere_medicijnen}",
            "end_time":"{andere_medicijnen_end}",
            "disabled" : {andere_medicijnen_disabled},
    }},
    {{      "title": "Eten en drinken",
            "title_short":"Eten en drinken",
            "start_time":"{eten_drinken}",
            "end_time":"{eten_drinken_end}",
            "disabled" : {eten_drinken_disabled},
    }},
    {{      "title": "Zwangerschap of borstvoeding",
            "title_short":"Zwanger borstvoeden",
            "start_time":"{zwanger_borstvoeden}",
            "end_time":"{zwanger_borstvoeden_end}",
            "disabled" : {zwanger_borstvoeden_disabled},
    }},
    {{      "title": "Autorijden",
            "title_short":"Autorijden",
            "start_time":"{autorijden}",
            "end_time":"{autorijden_end}",
            "disabled" : {autorijden_disabled},
    }},
    {{      "title": "Hoe gebruiken",
            "title_short":"Hoe gebruiken",
            "start_time":"{hoe_gebruiken}",
            "end_time":"{hoe_gebruiken_end}",
            "disabled" : {hoe_gebruiken_disabled},
    }},
    {{      "title": "Teveel gebruikt",
            "title_short":"Teveel gebruikt",
            "start_time":"{teveel_gebruikt}",
            "end_time":"{teveel_gebruikt_end}",
            "disabled" : {teveel_gebruikt_disabled},
    }},
    {{      "title": "Vergeten of stoppen",
            "title_short":"Vergeten of stoppen",
            "start_time":"{vergeten_stoppen}",
            "end_time":"{vergeten_stoppen_end}",
            "disabled" : {vergeten_stoppen_disabled},
    }},
    {{      "title": "Bijwerkingen",
            "title_short":"Bijwerkingen",
            "start_time":"{bijwerkingen}",
            "end_time":"{bijwerkingen_end}",
            "disabled" : {bijwerkingen_disabled},
    }},
    {{      "title": "Hoe bewaren",
            "title_short":"Hoe bewaren",
            "start_time":"{hoe_bewaren}",
            "end_time":"",
            "disabled": {hoe_bewaren_disabled},
    }}
    ]
}}
""").format(**timing_json)

    return output


def zip_output(file_to_zip, zipname):
    """Zip a list of files to a single file."""
    with zipfile.ZipFile(zipname, 'w' ) as zip:
        for _ in file_to_zip:
            zip.write(_, os.path.basename(_))
    return


def single_file_request(screenout):
    upload = request.files['targetfile']
    input_file = os.path.join(save_location,
                              upload.filename)

    upload.save(input_file)

    output_file = os.path.join('{}.tempo.txt'.format(os.path.basename(upload.filename)))

    out = parse_alles(input_file)

    if screenout:
        return render_template('upload_filmscript.html', json_out=out)

    elif not screenout:
        r = app.response_class(out, mimetype='text/csv')
        r.headers.set('Content-Disposition', 'attachment', filename=output_file)
        return r


def multiple_file_request():
    uploaded_files = request.files.getlist('targetfile')
    parsed_files = list()
    for uploaded_file in uploaded_files:
        input_file = os.path.join(save_location, uploaded_file.filename)
        uploaded_file.save(input_file)
        output_file = os.path.join(save_location, '{}.tempo.txt'.format(os.path.basename(uploaded_file.filename)))
        out = parse_alles(input_file)
        with open(output_file, 'w') as f:
            for line in out:
                f.write(line)
        parsed_files.append(output_file)
    date_time = time.strftime('%Y-%m-%d_%H:%M')
    zipname = os.path.join(save_location, '{}.zip'.format(date_time))
    zip_output(parsed_files, zipname)
    return zipname

@app.route('/<path:filename>')
def send_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
@app.route('/', methods=['GET', 'POST'])
def upload_filmscript():
    """View for zorganimaties app. Return file or rendered html."""
    if request.method == 'POST':
        if len(request.files.getlist('targetfile')) == 0:
            flash('Geen file opgegeven', 'error')
            return redirect('/')
        elif len(request.files.getlist('targetfile')) == 1:
            if 'screenout' in request.form:
                screenout = True
                return single_file_request(screenout)
            else:
                screenout = False
                return single_file_request(screenout)
        elif len(request.files.getlist('targetfile')) > 1:
            zip_out = multiple_file_request()
            return redirect(url_for('send_file', filename=os.path.basename(zip_out)))
    return render_template('upload_filmscript.html')


if __name__ == '__main__':
    app.run(debug=True)
