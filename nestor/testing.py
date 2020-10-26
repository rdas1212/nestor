from datetime import datetime, timedelta

from nestor.trello import Trello

t = Trello('key', 'token')

t.add_card('Testing', 'TestList1', 'card', labels_names=['hola'], checklist=('todo', ['logging']),
           due=datetime.now() + timedelta(days=1), description='hi', place_at_top=True)
