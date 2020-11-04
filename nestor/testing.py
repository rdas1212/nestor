from nestor.rule_parser import ConfiguredRules
from nestor.scheduling import CronManager
from nestor.trello import Trello

t = Trello('key', 'token')

rules = ConfiguredRules('test_schedule.yml', trello=t)
print(rules.rules)

cron_man = CronManager(rules.rules)

next_exec, next_rules = cron_man.get_next_execution()
print(f"Next exec at: {next_exec}")
print(f"Next rules: {next_rules}")
