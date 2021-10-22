from typing import Tuple

UNIT = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

def parse_size(size: int) -> Tuple[float, str]:
    unit_level = 0
    while size > 1024 and unit_level < len(UNIT):
        size /= 1024
        unit_level += 1
    return (round(size, 2), UNIT[unit_level])

if __name__ == '__main__':
    print(parse_size(1024))
    print(parse_size(1024 * 1024))
    print(parse_size(6142425))