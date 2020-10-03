import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Tuple

LOG = logging.getLogger('nestor')

CACHE_VALIDITY = 86400.0  # cache for a day


@dataclass
class TrelloList(object):
    name: str
    id: str


@dataclass
class TrelloLabel(object):
    name: str
    id: str
    color: str


@dataclass
class TrelloBoard(object):
    name: str
    id: str
    lists: List[TrelloList]
    labels: List[TrelloLabel]


class RequiredResourceMissingException(Exception):
    pass


class Trello(object):

    def __init__(self, api_key: str, api_token: str):
        """ Initializer
        :param api_key: The trello api-key to use; see: https://trello.com/app-key
        :param api_token: The trello api-token to use; see: https://trello.com/app-key
        """
        self._api_key = api_key
        self._api_token = api_token
        self._boards: List[TrelloBoard] = list()
        self._cache_time: float = 0.0

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
        # get the board
        target_board = self._get_board(board_name)
        if not target_board:
            raise RequiredResourceMissingException(f'Board by name {board_name} does not exist')
        LOG.info('Board cached')
        # ensure the list exists in the board
        target_list = self._get_list(target_board, list_name)
        LOG.info('List exists')
        # create the card with due-date, description & position
        card_id = self._create_card(target_board, target_list, card_name, description, due, place_at_top)
        LOG.info('Base card created')
        if labels_names:
            # get the valid labels
            labels_to_add = self._get_valid_labels(target_board, labels_names)
            # add the valid labels
            self._add_labels(card_id, labels_to_add)
            LOG.info('Labels added to card')
        if checklist:
            # create the checklist
            checklist_name, checklist_items = checklist[0], checklist[1]
            self._create_checklist(card_id, checklist_name, checklist_items)
            LOG.info('Checklist created & added to card')
        LOG.info('Complete card created')

    def _get_board(self, board_name: str) -> Optional[TrelloBoard]:
        cache_refreshed_already = False
        # if the cache expired, refresh it
        if not self.__cache_is_valid():
            self._cache_all_boards()
            cache_refreshed_already = True
        # find in cache
        cached_board = self.__get_cached_board(board_name)
        if cached_board:
            LOG.debug('Cached board was found')
            return cached_board
        # if not found in cache
        if cache_refreshed_already:
            # if cache was refreshed but board was still not found, then it's missing
            LOG.error('Board was not found even after cache refresh')
            return None
        # if we hadn't refreshed the cached earlier, try refreshing again
        self._cache_all_boards()
        return self.__get_cached_board(board_name)

    def _get_list(self, board: TrelloBoard, list_name: str) -> TrelloList:
        # board is assumed to be fresh (i.e. from a valid cache)
        cached_list = self.__get_cached_list(board, list_name)
        if cached_list:
            return cached_list
        LOG.debug('List %s does not exist, will be created', list_name)
        created_list = self._create_list(board, list_name)
        LOG.info('List was created: %s', created_list)
        return created_list

    def _create_card(self, target_board: TrelloBoard, target_list: TrelloList, card_name: str,
                     description: Optional[str], due: Optional[datetime], place_at_top: Optional[bool]) -> str:
        pass

    def _create_list(self, target_board: TrelloBoard, list_name: str) -> TrelloList:
        pass

    def _cache_all_boards(self) -> None:
        pass

    def _get_valid_labels(self, target_board: TrelloBoard, label_names: List[str]) -> List[str]:
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

    def __get_cached_board(self, board_name) -> Optional[TrelloBoard]:
        searched_boards = [b for b in self._boards if b.name == board_name]
        if not searched_boards:
            return None
        LOG.debug('Found %s boards by name %s', len(searched_boards), board_name)
        return searched_boards[0]

    def __get_cached_list(self, board: TrelloBoard, list_name) -> Optional[TrelloList]:  # noqa
        searched_lists = [l for l in board.lists if l.name == list_name]
        if not searched_lists:
            return None
        LOG.debug('Found %s lists by name %s in board %s', len(searched_lists), list_name, board.name)
        return searched_lists[0]

    def __cache_is_valid(self):
        return self._boards and time.time() - self._cache_time <= CACHE_VALIDITY
