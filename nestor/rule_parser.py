from enum import Enum, unique
from typing import Dict, Any, List

import yaml

from nestor.trello import Trello


@unique
class TriggerType(Enum):
    SCHEDULED = 1


@unique
class ActionType(Enum):
    ADD_CARD = 1


class AddCardExecution(object):
    def __init__(self, trello: Trello, arguments: Dict[str, Any]):
        if any(required_arg not in arguments for required_arg in ('board', 'list', 'name')):
            raise ValueError('Required argument missing')
        self._arguments = arguments
        self._trello = trello

    def execute(self):
        # TODO
        pass


class Trigger(object):
    def __init__(self, definition: Dict[str, Any]):
        if 'schedule' in definition:
            self._type = TriggerType.SCHEDULED
            self._cron_expr = definition['schedule']
        else:
            raise ValueError('Unknown schedule definition')

    def __repr__(self):
        return f"Trigger by {self._type}"

    @property
    def type(self):
        return self._type


class Action(object):
    def __init__(self, definition: Dict[str, Any], trello: Trello):
        self._type = ActionType[definition['do'].upper()]
        self._arguments: Dict[str, Any] = definition['with']
        self._execution = ACTION_MAP[self._type](trello, self._arguments)

    def __repr__(self):
        return f"Do {self._type} with arguments: {self._arguments}"

    def execute(self):
        self._execution.execute()

    @property
    def type(self):
        return self._type

    @property
    def arguments(self):
        return self._arguments


class Rule(object):
    def __init__(self, trigger_def: Dict[str, Any], actions_def: List[Dict[str, Any]], trello: Trello):
        self._trigger = Trigger(trigger_def)
        self._actions = [Action(action_def, trello) for action_def in actions_def]

    @property
    def trigger(self):
        return self._trigger

    @property
    def actions(self):
        return self._actions

    def __repr__(self):
        return f"Trigger: {self._trigger}, Actions: {self._actions}"


class ConfiguredRules(object):
    def __init__(self, rule_file_path: str, trello: Trello):
        with open(rule_file_path) as rule_file:
            rule_defs = yaml.safe_load(rule_file)
        self._rules = [Rule(rule_def['trigger'], rule_def['actions'], trello) for rule_def in rule_defs['rules']]

    @property
    def rules(self):
        return self._rules


ACTION_MAP = {
    ActionType.ADD_CARD: AddCardExecution
}
