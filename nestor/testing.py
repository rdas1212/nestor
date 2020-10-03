from nestor.trello import Trello

t = Trello('key', 'token')

t.add_card('board', 'list', 'card', labels_names=['hola'], checklist=('todo', ['loging']))
