import re
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
        elif event_name == 'KeyRelease':
            unmatched.remove(key_code)

        if len(unmatched) == 0 and len(batch) > 0:
            yield tuple(batch)
            batch = []

if __name__ == "__main__":
    filename_ = sys.argv[1]

    keycode_mappings_ = get_keycode_map()

    events_ = get_events(filename_, keycode_mappings_)
    counter = Counter(batch_events(events_))

    for ev in counter.most_common(50):
        print(*ev)
