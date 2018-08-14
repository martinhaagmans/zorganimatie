import os

from flask import Flask
from flask import render_template, flash, request

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'tmp'
app.config['SECRET_KEY'] = 'amygdala'
MYDIR = os.path.dirname(os.path.abspath(__file__))
save_location = os.path.join(MYDIR,  app.config['UPLOAD_FOLDER'])

def parse_filmscript(filmscript):
    i = 0
    time = str()
    tekst = str()
    out = dict()
    out['filename'] = os.path.basename(str(filmscript))
    with open(filmscript, 'r', encoding="utf-8") as f:
        for line in f:
            i += 1

            if i == 1:
                continue

            elif i == 2:
                time = line.split(' --> ')[0]
                time = time.split(',')[0]
                h, m, s = time.split(':')
                time = int(h) * (60*60) + int(m) * 60 + int(s)

            elif i >= 3 and line not in ['\n', '\r\n']:
                tekst = tekst + ' ' + line.rstrip()

            elif line in ['\n', '\r\n']:
                i = 0
                out[time] = tekst.lstrip()
                time = str()
                tekst = str()
    return out

def parse_jong_specifiek(parsed_filmscript, out):
    zwanger = False
    if 'vrouw' in parsed_filmscript['filename'].lower():
        zwanger = True
    else:
        out['t6'] = ''
    for k, v in parsed_filmscript.items():
        if 'Hoe weet ik of ik dit medicijn mag gebruiken?' in v:
            out['t2'] = k
        elif 'Moet ik zelf nog ergens op letten als ik dit medicijn gebruik?' in v:
            out['t3'] = k
        elif 'Mag ik gewoon auto rijden als ik dit medicijn gebruik?' in v:
            out['t7'] = k
        elif 'Okay, en hoe moet ik het gebruiken?' in v:
            out['t8'] = k
        elif 'Wat moet ik doen als ik teveel heb gebruikt?' in v:
            out['t9'] = k            
        elif 'Heeft dit middel ook bijwerkingen?' in v:
            out['t11'] = k         
        elif zwanger and 'zwanger' in v:
            out['t6'] = k
            zwanger = False
    return out

def parse_oud_specifiek(parsed_filmscript, out):
    out['t6'] = ''
    for k, v in parsed_filmscript.items():
        if 'Hoe weet ik zeker of ik dit medicijn mag gebruiken?' in v:
            out['t2'] = k
        elif 'Moet ik ergens specifiek op letten als ik dit medicijn gebruik?' in v:
            out['t3'] = k
        elif 'Mag ik wel zelf rijden als ik dit medicijn gebruik?' in v:
            out['t7'] = k
        elif 'Okay, en hoe moet ik dit medicijn precies gebruiken?' in v:
            out['t8'] = k
        elif 'Wat moet ik doen als ik per ongeluk te veel heb gebruikt?' in v:
            out['t9'] = k            
        elif 'Wat voor bijwerkingen kan ik verwachten?' in v:
            out['t11'] = k                        
    return out

def parse_algemeen(parsed_filmscript, out):
    for k, v in parsed_filmscript.items():
        if 'Uw medicijn heet' in v:
            out['t1'] = k
        elif 'Het is ook belangrijk dat u de dokter en de apotheek vertelt welke andere medicijnen u' in v:
            out['t4'] = k
        elif 'Moet ik nog ergens op letten met eten en drinken?' in v:
            out['t5'] = k        
        elif 'En als ik het een keer vergeet?' in v:
            out['t10'] = k
        elif 'Ik hoop dat deze informatie u heeft geholpen.'in v and 'En een hele fijne dag nog!' in v:
            out['aOuit'] = k            

    return out

def parse_alles(filmscript):
    timing_json = dict()
    dscript = parse_filmscript(filmscript)

    timing_json = parse_algemeen(dscript, timing_json)

    if 'jong' in dscript['filename'].lower():
        timing_json = parse_jong_specifiek(dscript, timing_json)
    elif 'oud' in dscript['filename'].lower():
        timing_json = parse_oud_specifiek(dscript, timing_json)

    timing_json['t12'] = ''
    errors = list()
    for _ in range(1, 13):
            to_check = 't{_}'.format(_)
            if not to_check in timing_json:
                errors.append(to_check)
                timing_json['errors'][to_check] = '?'

    if len(errors) == 0:
        timing_json['niet_gevonden'] = '# Alles ok'
    else:
        timing_json['niet_gevonden'] = '# {} niet gevonden.'.format(' '.join(errors))
    
    
    output = str("""{niet_gevonden}
                {{
                "Tijden" : {{
                    "achtergrondOverlayAan":"32",
                    "achtergrondOverlayUit":"{aOuit}" 
                            }},        
                "Hoofdstukken" : 
                    [
                    {{"nr":"1",
                            "naam":"waarvoor",
                            "tijd":"{t1}"}},
                    {{"nr":"2",
                            "naam":"wanneer niet",
                            "tijd":"{t2}"}},
                    {{"nr":"3",
                            "naam":"extra voorzichtig",
                            "tijd":"{t3}"}},
                    {{"nr":"4",
                            "naam":"andere medicijnen",
                            "tijd":"{t4}"}},
                    {{"nr":"5",
                            "naam":"eten en drinken",
                            "tijd":"{t5}"}},
                    {{"nr":"6",
                            "naam":"zwanger borstvoeden",
                            "tijd":"{t6}"}},
                    {{"nr":"7",
                            "naam":"autorijden",
                            "tijd":"{t7}"}},
                    {{"nr":"8",
                            "naam":"hoe gebruiken",
                            "tijd":"{t8}"}},
                    {{"nr":"9",
                            "naam":"teveel gebruikt",
                            "tijd":"{t9}"}},
                    {{"nr":"10",
                            "naam":"vergeten of stoppen",
                            "tijd":"{t10}"}},
                    {{"nr":"11",
                            "naam":"bijwerkingen",
                            "tijd":"{t11}"}},
                    {{"nr":"12",
                            "naam":"hoe bewaren",
                            "tijd":"{t12}"}}        
                    ]
                }}
                """).format(**timing_json)

    return output                

@app.route('/', methods=['GET', 'POST'])
def upload_filmscript():
    if request.method == 'POST':
        
        upload = request.files['targetfile']
        if not upload:
            flash('Geen file opgegeven', 'error')
            return render_template('upload_filmscript.html')

        input_file = os.path.join(save_location,
                                  upload.filename)

        upload.save(input_file)

        output_file = os.path.join('{}.json.txt'.format(os.path.basename(upload.filename)))

        out = parse_alles(input_file)

        r = app.response_class(out, mimetype='text/csv')
        r.headers.set('Content-Disposition', 'attachment', filename=output_file)
        return r


    return render_template('upload_filmscript.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)    
