import pandas as pd
from datetime import datetime, timedelta
from csv import reader
import unicodedata

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode()

month_parser = {
    'jan': 1,
    'feb': 2,
    'mrt': 3,
    'apr': 4,
    'mei': 5,
    'jun': 6,
    'jul': 7,
    'aug': 8,
    'sep': 9,
    'okt': 10,
    'nov': 11,
    'dec': 12
}

url_q1 = "https://docs.google.com/spreadsheets/d/1BdDjmZIlnlKC86HdS5OIiTg0zfxy8bogPCmsN--sdYo/gviz/tq?tqx=out:csv"
first_day_in_header = 4
first_day_in_sheet = 3

df = pd.read_csv(url_q1)
csv = df.to_csv()
csvl = csv.split("\n")

surveyors = [
    'Titus van der Zee',
    'Govert Wesseling',
    'Bert van Angeren',
    'Andre Loeve',
    'Robin Stadt',
    'Mark van Vliet',
    'Willem van Opstal'
]
surveyor_index = {}
per_surveyor = {}
vessels = ['Arca', 'Zirfaea']
vessel_index = {}
vessel_per_date = {}
per_vessel = {}

first_date_of_this_sheet = None

for l, line in enumerate(csvl):
    sline = line.split(',')
    if sline[1] == "Support":
        break
    if not first_date_of_this_sheet:
        first_date_of_this_sheet = datetime.strptime(f"{sline[1][:4]}-{month_parser[sline[first_day_in_header].split(' ')[2]]}-{sline[first_day_in_header].split(' ')[1]}", "%Y-%m-%d").date()
    if remove_accents(sline[1]) in surveyors:
        surveyor_index[sline[1]] = l
    if remove_accents(sline[1]) in vessels:
        vessel_index[sline[1]] = l

for vessel, vindex in vessel_index.items():
    print('---------\n', vindex, vessel)
    per_vessel[vessel] = []
    sdp = csvl[vindex].split(',')
    sd = []
    part = ""
    opened = False
    for s, sss in enumerate(sdp):
        if '"' in sss and not opened:
            opened = True
            part += sss
        elif '"' in sss and opened:
            opened = False
            part += sss
            sd.append(part)
            part = ""
        elif opened:
            part += ""
        else:
            sd.append(sss)
    sd = sd[first_day_in_sheet:]
    print(sd)
    current_date = first_date_of_this_sheet
    ci = 0

    event = {'start': current_date, 'end': current_date, 'occupance': None, 'theme': None}

    while ci < len(sd):

        if "Samenvatting" in sd[ci]:
            break

        note = sd[ci + 0]
        occupance = sd[ci + 1].split(' ')[0]
        theme = sd[ci + 2]

        print(f"{ci}: {current_date} - {note} - {occupance} - {theme}")

        if occupance == event.get('occupance') and theme == event.get('theme'):
            event['end'] = current_date
        else:
            if event.get('occupance') or event.get('theme'):
                per_vessel[vessel].append(event)
            event = {'start': current_date, 'end': current_date, 'occupance': occupance, 'theme': theme}

        if theme:
            if current_date not in vessel_per_date.keys():
                vessel_per_date[current_date] = {theme: vessel}
            else:
                vessel_per_date[current_date][theme] = vessel

        ci += 3
        current_date += timedelta(days = 1)

    if event.get('occupance') or event.get('theme'):
        per_vessel[vessel].append(event)

for surveyor, sindex in surveyor_index.items():
    print(f"------------\n{surveyor}")
    per_surveyor[surveyor.split(' ')[0]] = []
    sdp = csvl[sindex].split(',')
    sd = []
    part = ""
    opened = False
    for s, sss in enumerate(sdp):
        if '"' in sss and not opened:
            opened = True
            part += sss
        elif '"' in sss and opened:
            opened = False
            part += sss
            sd.append(part)
            part = ""
        elif opened:
            part += ""
        else:
            sd.append(sss)
    sd = sd[first_day_in_sheet:]
    print(sd)
    current_date = first_date_of_this_sheet
    ci = 0

    event = {'start': current_date, 'end': current_date, 'vessel': None, 'theme': None, 'work': None}

    while ci < len(sd):
        if "Samenvatting" in sd[ci]:
            break

        note = sd[ci + 0]
        work = sd[ci + 1]
        theme = sd[ci + 2]

        try:
            vessel = vessel_per_date.get(current_date).get(theme)
        except:
            vessel = None

        print(f"{ci}: {current_date} - {note} - {work} - {theme} - {vessel}")

        if work == event.get('work') and theme == event.get('theme') and vessel == event.get('vessel'):
            event['end'] = current_date
        else:
            if event.get('work') or event.get('theme') or event.get('vessel') and event.get('work') != 'Afwezig':
                if 'Kantoor' in event.get('work'):
                    event['work'] = "Kantoor"
                per_surveyor[surveyor.split(' ')[0]].append(event)
            event = {'start': current_date, 'end': current_date, 'vessel': vessel, 'theme': theme, 'work': work}


        ci += 3
        current_date += timedelta(days = 1)

    if event.get('work') or event.get('theme') or event.get('vessel') and event.get('work') != 'Afwezig':
        if 'Kantoor' in event.get('work'):
            event['work'] = "Kantoor"
        per_surveyor[surveyor.split(' ')[0]].append(event)


print(per_vessel)
print(per_surveyor)
