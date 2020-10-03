import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Tuple

LOG = logging.getLogger('nestor')


@dataclass
class Board(object):
    name: str
    id: str
    lists: Dict[str, str]
    labels: Dict[str, str]


class Trello(object):

    def __init__(self, api_key: str, api_token: str):
        """ Initializer
        :param api_key: The trello api-key to use; see: https://trello.com/app-key
        :param api_token: The trello api-token to use; see: https://trello.com/app-key
        """
        self._api_key = api_key
        self._api_token = api_token
        self._boards: Dict[str, Board] = dict()

    def add_card(self, board_name: str, list_name: str, card_name: str, description: Optional[str] = None,
                 labels_names: Optional[List[str]] = None, due: Optional[datetime] = None,
                 checklist: Optional[Tuple[str, List[str]]] = None, place_at_top: bool = False) -> None:
        """ Create a trello card
        :param board_name: board name, must exist
        :param list_name: name of list in board, will be created if it doesn't exist
        :param card_name: name of the card
        :param description: Optional description
        :param labels_names: Optional label names, labels must exists - otherwise they will be skipped
        :param due: Optional due date, must be in the future
        :param checklist: Optional checklist, a new checklist is created always
        :param place_at_top: Optional flag to place the card on top of the list instead of the bottom
        """
        # TODO
        # ensure the board is cached
        self._cache_board(board_name)
        LOG.info('Board cached')
        # ensure the list exists in the board
        self._ensure_list_exists(board_name, list_name)
        LOG.info('List exists')
        # create the card with due-date, description & position
        card_id = self._create_card(board_name, list_name, card_name, description, due, place_at_top)
        LOG.info('Bare card created')
        if labels_names:
            # get the valid labels
            labels_to_add = self._get_valid_labels(board_name, labels_names)
            # add the valid labels
            self._add_labels(card_id, labels_to_add)
            LOG.info('Labels added to card')
        if checklist:
            # create the checklist
            checklist_name, checklist_items = checklist[0], checklist[1]
            self._create_checklist(card_id, checklist_name, checklist_items)
            LOG.info('Checklist created & added to card')
        LOG.info('Complete card created')

    def _create_card(self, board_name: str, list_name: str, card_name: str,
                     description: Optional[str] = None, due: Optional[datetime] = None,
                     place_at_top: Optional[bool] = None) -> str:
        pass

    def _cache_board(self, board_name: str) -> None:
        pass

    def _ensure_list_exists(self, board_name: str, list_name: str) -> None:
        pass

    def _get_valid_labels(self, board_name: str, label_names: List[str]) -> List[str]:
        pass

    def _add_labels(self, card_id: str, label_ids: List[str]) -> None:
        pass

    def _create_checklist(self, card_id: str, checklist_name: str, items: List[str]) -> None:
        pass

    def __auth_params(self) -> Dict[str, str]:
        return {
            'key': self._api_key,
            'token': self._api_token
        }
