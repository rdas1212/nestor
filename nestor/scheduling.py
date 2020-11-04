import logging
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Tuple, Optional

from croniter import croniter

from nestor.rule_parser import Rule, TriggerType

LOG = logging.getLogger('nestor')


def parse_schedules(rules) -> Dict[croniter, Rule]:
    return {
        croniter(r.trigger.cron_expr, datetime.now()): r for r in rules if r.trigger.type == TriggerType.SCHEDULED
    }


class CronManager(object):

    def __init__(self, rules: List[Rule]):
        self._rules = rules

    def get_next_execution(self) -> Optional[Tuple[datetime, List[Rule]]]:
        cron_to_rule = parse_schedules(self._rules)
        if not cron_to_rule:
            return None
        next_executions = defaultdict(list)
        for cron, rule in cron_to_rule.items():
            next_executions[cron.get_next(ret_type=datetime)].append(rule)
        next_execution_time, rules_to_execute = min(next_executions.items())
        LOG.info("Found next execution: Rules %s at %s", rules_to_execute, next_execution_time)
        return next_execution_time, rules_to_execute
