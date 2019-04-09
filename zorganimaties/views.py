"""This script is for zorganimaties. It parses a textfile and returns JSON."""

import os
# import math
import time
import zipfile

from decimal import Decimal

from flask import Flask
from flask import flash
from flask import url_for
from flask import request
from flask import redirect
from flask import render_template
from flask import send_from_directory

from .scripts import *

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


def parse_filmscript(filmscript):
    """Parse input text file and return a dictionary."""
    i = 0
    time_start = str()
    time_end = str()
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
                time_start, time_end = line.split(' --> ')
                time_start, fraction_start = time_start.split(',')
                hs, ms, ss = time_start.split(':')
                time_start = int(hs) * (60*60) + int(ms) * 60 + int(ss)
                time_start = '{}.{}'.format(time_start, str(fraction_start)[:2])
                time_start = Decimal(time_start)

                time_end, fraction_end = time_end.split(',')
                he, me, se = time_end.split(':')
                time_end = int(he) * (60*60) + int(me) * 60 + int(se)
                time_end = '{}.{}'.format(time_end, str(fraction_end)[:2])
                time_end = Decimal(time_end)


            elif i >= 3 and line not in ['\n', '\r\n']:
                tekst = tekst.lstrip() + ' ' + line.rstrip()

            elif line in ['\n', '\r\n']:
                i = 0
                out[(time_start, time_end)] = tekst.lstrip()
                time_start = str()
                time_end = str()
                tekst = str()
    return out


def check_and_disable_events(dict_to_check):
    """Check if events are present in dict and return dict.

    Check for all EVENTS if they are present in the dict. 
    Set EVENT_disabled to true if present. 
    Set EVENT_disabled to false if not present.
    Return dict with added keys.
    """
    for to_check in EVENTS:
        if to_check not in dict_to_check:
            dict_to_check[to_check] = ''
            dict_to_check['{}_disabled'.format(to_check)] = 'true'
        else:
            dict_to_check['{}_disabled'.format(to_check)] = 'false'

    return dict_to_check


def get_disabled_events(dict_to_check):
    """Parse dict and return list with all disabled events."""
    errors = list()
    for event in EVENTS:
        if dict_to_check['{}_disabled'.format(event)] == 'true':
            errors.append(event)
        elif dict_to_check['{}_end'.format(event)] == '':
            if event not in errors:
                errors.append('{}_geen_eindtijd'.format(event))
    return errors


def add_end_times_to_dict(timing_dict, zwanger):
    for i in range(0, 11):
        key_start = EVENTS[i]
        key_end = EVENTS[i + 1]

        if not zwanger and key_start == 'eten_drinken':
            key_end = EVENTS[i + 2]

        if '{}_end'.format(key_start) in timing_dict:
            continue

        time_end = timing_dict['{}'.format(key_end)]

        try:
            time_end = Decimal(float(time_end)) - Decimal((1/100))
        except ValueError as e:
            timing_dict['{}_end'.format(key_start)] = ''
        else:
            time_end = round(time_end, 2)

        timing_dict['{}_end'.format(key_start)] = time_end
    return timing_dict


def add_quotes_and_null_to_output_dict(output_dict):
    for k, v in output_dict.items():
        if not 'disabled' in k:
            if v == '':
                output_dict[k] = 'null'
            else:
                output_dict[k] = '"{}"'.format(v)

    return output_dict


def parse_alles(filmscript):
    """Collect all timestamp times, parse them into a string and return the string."""
    timing_json = dict()

    dscript = parse_filmscript(filmscript)
    if filmscript.endswith('ENGELS.srt'):
        timing_json = parse_algemeen_engels(dscript, timing_json)
    else:
        timing_json = parse_algemeen_nl(dscript, timing_json)

    script_name = dscript['filename'].lower()

    zwanger = True

    if 'jong' in script_name:
        if filmscript.endswith('ENGELS.srt'):
            timing_json = parse_jong_specifiek_engels(dscript, timing_json)
        else:
            timing_json = parse_jong_specifiek_nl(dscript, timing_json)

        if not 'vrouw' in script_name:
            zwanger = False

    elif 'oud' in script_name:
        zwanger = False
        if filmscript.endswith('ENGELS.srt'):
            timing_json = parse_oud_specifiek_engels(dscript, timing_json)
        else:
            timing_json = parse_oud_specifiek_nl(dscript, timing_json)

    timing_json = check_and_disable_events(timing_json)
    timing_json = add_end_times_to_dict(timing_json, zwanger)
    errors = get_disabled_events(timing_json)

    if not 'aOeind' in timing_json:
        errors.append('aOeind')
        timing_json['aOeind'] = ''

    if not zwanger:
        timing_json['zwanger_borstvoeden_disabled'] = 'true'
        timing_json['zwanger_borstvoeden_end'] = ''
        timing_json['zwanger_borstvoeden'] = ''

    timing_json = add_quotes_and_null_to_output_dict(timing_json)

    if len(errors) == 0:
        timing_json['niet_gevonden'] = '# Alles ok'
    else:
        timing_json['niet_gevonden'] = '# {} niet gevonden.'.format(' '.join(errors))
    
    if filmscript.endswith('ENGELS.srt'):
        output = get_output_engels(timing_json)
    else: 
        output = get_output_nl(timing_json)        
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
