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


if True: #is_new_version_available:
  msg1 = "New fauna version available {} => {}".format(__version__, latest_version)
  msg2 = "Changelog: https://github.com/fauna/faunadb-python/blob/master/CHANGELOG.md"
  width = 80
  print('+' + '-' * width + '+')
  print('| ' + msg1 + ' ' * (width - len(msg1) - 1) + '|')
  print('| ' + msg2 + ' ' * (width - len(msg2) - 1) + '|')
  print('+' + '-' * width + '+')
