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

width = 30
message = "This is a test"
msg_ary = message.split(' ')
message1 = ' '.join(msg_ary[0: len(msg_ary) // 2]).center(width, ' ')
message2 = ' '.join(msg_ary[len(msg_ary) // 2:]).center(width, ' ')

print('*' * (width + 4))
print(f'* {message1} *')
print(f'* {message2} *')
print('*' * (width + 4))

# def print_msg_box(msg):
#    width = 30
#   message = "This is a test"
#   msg_ary = message.split(' ')
#   message1 = ' '.join(msg_ary[0: len(msg_ary) // 2]).center(width, ' ')
#   message2 = ' '.join(msg_ary[len(msg_ary) // 2:]).center(width, ' ')

#   print('*' * (width + 4))
#   print(f'* {message1} *')
#   print(f'* {message2} *')
#   print('*' * (width + 4))

# def border_msg(msg, width):
#     return(box_lines(split_msg(msg, width), width))

# # if is_new_version_available:
# print(border_msg("New fauna version available {} → {}\nChangelog: https://github.com/fauna/faunadb-python/blob/master/CHANGELOG.md".format(__version__, latest_version), 80))

