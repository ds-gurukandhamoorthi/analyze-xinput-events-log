import re
import subprocess
from funcy import cut_prefix

def get_keycode_map():
    output = subprocess.run(['xmodmap', '-pke'],
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
