import re
import glob
import gzip
import sys
import subprocess
from collections import Counter
from funcy import cut_prefix

def get_keycode_map():
    output = subprocess.run(['xmodmap', '-pke'],
            check = True,
            stdout=subprocess.PIPE).stdout.decode('utf-8')
    mappings = output.splitlines()
    map_dic = {}
    for mapping in mappings:
        code, maps = re.split(' = ?', mapping)
        code = cut_prefix(code, 'keycode ')
        code = int(code)
        maps = tuple(maps.split(' '))
        map_dic[code] = maps
    return map_dic

def parse_events(filename):
    REGEX = re.compile(r'EVENT.*?(?=^EVENT)', re.DOTALL | re.M)
    if filename.endswith('.gz'):
        with gzip.open(filename, 'rt') as f:
            text = f.read()
    else:
        with open(filename) as f:
            text = f.read()
    for mtch in re.finditer(REGEX, text):
        yield mtch.group(0)

def parse_single_event(event):
    REGEX = re.compile(r'EVENT type [0-9]+ [(]([^)]+)[)]')
    event_name = re.match(REGEX, event).group(1)
    key_code = -1
    for line in event.splitlines():
        if 'detail:' in line:
            key_code = cut_prefix(line.strip(), 'detail: ')
            key_code = int(key_code)
    return event_name, key_code

def get_events(filename, keycode_mappings):
    for event in parse_events(filename):
        event_name, key_code = parse_single_event(event)
        if event_name in ('KeyPress', 'KeyRelease'):
            mapping = keycode_mappings.get(key_code,
                    ['UNKNOWN'])[0]
            yield event_name, key_code, mapping

def batch_events(events):
    batch = []
    unmatched = set()
    for event_name, key_code, mapping in events:

        if event_name == 'KeyPress':
            unmatched.add(key_code)
            batch.append(mapping)
        elif event_name == 'KeyRelease' and len(batch) > 0:
            if key_code not in unmatched:
                print('***')
                print(unmatched, batch)
            unmatched.remove(key_code)

        if len(unmatched) == 0 and len(batch) > 0:
            yield tuple(batch)
            batch = []

def count_events(directory_name, keycode_mappings):
    counter = Counter()
    filenames = glob.glob(f'{directory_name}/*events.gz')
    # print(filenames)
    for filename in filenames:
        events = get_events(filename, keycode_mappings_)
        try:
            counter += Counter(batch_events(events))
        except:
            print(f'Error in {filename}')
    return counter

if __name__ == "__main__":
    directory_name_ = sys.argv[1]
    keycode_mappings_ = get_keycode_map()

    counter_ = count_events(directory_name_, keycode_mappings_)

    for ev in counter_.most_common(50):
        print(*ev)
