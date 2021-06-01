import requests

__title__ = "FaunaDB"
__version__ = "4.1.0"
__api_version__ = "4"
__author__ = "Fauna, Inc"
__license__ = "MPL 2.0"
__copyright__ = "2020 Fauna, Inc"


response = requests.get('https://pypi.org/pypi/faunadb/json')
latest_version = response.json().get('info').get('version')
latest_version_arr = latest_version.split(".")
current_version = __version__.split(".")
is_new_version_available = False

for i in range(len(current_version)):
  if latest_version_arr[i] > current_version[i]:
    is_new_version_available = True

def print_msg_box(msg, indent=2, width=None, title=None):
    """Print message-box with optional title."""
    lines = msg.split('\n')
    space = " " * indent
    if not width:
        width = max(map(len, lines))
    box = f'╔{"═" * (width + indent * 2)}╗\n'  # upper_border
    if title:
        box += f'║{space}{title:<{width}}{space}║\n'  # title
        box += f'║{space}{"-" * len(title):<{width}}{space}║\n'  # underscore
    box += ''.join([f'║{space}{line:<{width}}{space}║\n' for line in lines])
    box += f'╚{"═" * (width + indent * 2)}╝'  # lower_border
    print(box)

if is_new_version_available:
  print_msg_box("New fauna version available {} → {}\nChangelog: https://github.com/fauna/faunadb-python/blob/master/CHANGELOG.md".format(__version__, latest_version))

