import os

import requests

api_key = os.environ['TRELLO_API_KEY']
api_token = os.environ['TRELLO_API_TOKEN']
auth_params = dict(key=api_key, token=api_token)

resp = requests.get('https://api.trello.com/1/members/me/boards', params=auth_params)

boards = resp.json()
print(f'Got boards: {resp.json()}')

test_board_id = [b['id'] for b in boards if b['name'] == 'Testing'][0]

resp = requests.get(f'https://api.trello.com/1/boards/{test_board_id}/lists', params=auth_params)

lists = resp.json()

test_list_id = [l['id'] for l in lists if l['name'] == 'TestList'][0]

card_params = dict(
    name='This is a test card',
    desc='Testing shall commence',
    pos='bottom',
    idList=test_list_id
)

resp = requests.post('https://api.trello.com/1/cards', params={**auth_params, **card_params})
print(resp)
