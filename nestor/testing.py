from nestor.rule_parser import ConfiguredRules
from nestor.trello import Trello

t = Trello('key', 'token')

rules = ConfiguredRules('test_schedule.yml', trello=t)
print(rules.rules)
