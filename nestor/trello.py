import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Tuple, NoReturn

import requests

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
    lists: Optional[List[TrelloList]]
    labels: Optional[List[TrelloLabel]]


class RequiredResourceMissingException(Exception):
    pass


class Trello(object):
    API_URL = 'https://api.trello.com'

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
        # get the board
        target_board = self._get_board(board_name)
        if not target_board:
            raise RequiredResourceMissingException(f'Board by name {board_name} does not exist')
        LOG.info('Board cached')
        # ensure the list exists in the board
        target_list = self._get_list(target_board, list_name)
        LOG.info('List exists')
        # create the card with due-date, description & position
        card_id = self._create_card(target_list, card_name, description, due, place_at_top)
        LOG.info('Base card created')
        if labels_names:
            # get the valid labels
            labels_to_add = self._get_valid_label_ids(target_board, labels_names)
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

    def _create_card(self, target_list: TrelloList, card_name: str,
                     description: Optional[str], due: Optional[datetime], place_at_top: Optional[bool]) -> str:
        card_params = {
            'name': card_name,
            'idList': target_list.id
        }
        if description:
            card_params['desc'] = description
        if due:
            card_params['due'] = due.isoformat()[:-3] + 'Z'
        if place_at_top:
            card_params['pos'] = 'top'

        api_params = {**self.__auth_params(), **card_params}
        api_url = Trello.API_URL + '/1/cards'
        LOG.debug('Making API call')
        response = requests.post(api_url, params=api_params)
        response.raise_for_status()
        return response.json()['id']

    def _create_list(self, target_board: TrelloBoard, list_name: str) -> TrelloList:
        LOG.debug('Creating list by name %s', list_name)
        api_params = {
            'name': list_name,
            'idBoard': target_board.id,
            **self.__auth_params()
        }
        api_url = Trello.API_URL + '/1/lists'
        response = requests.post(api_url, params=api_params)
        response.raise_for_status()
        created_list = TrelloList(
            response.json()['name'],
            response.json()['id']
        )
        target_board.lists.append(created_list)
        return created_list

    def _cache_all_boards(self) -> None:
        LOG.debug('Refreshing cache')
        boards = self._discover_all_boards()
        for board in boards:
            lists = self._discover_lists_in_board(board.id)
            labels = self._discover_labels_in_board(board.id)
            board.lists = lists
            board.labels = labels
        self._boards = boards

    def _get_valid_label_ids(self, target_board: TrelloBoard, label_names: List[str]) -> List[str]:  # noqa
        return [
            label.id for label in target_board.labels if label.name in label_names
        ]

    def _add_labels(self, card_id: str, label_ids: List[str]) -> NoReturn:
        LOG.debug('Adding %d labels to card', len(label_ids))
        for label_id in label_ids:
            api_params = {
                'value': label_id,
                **self.__auth_params()
            }
            api_url = Trello.API_URL + f'/1/cards/{card_id}/idLabels'
            response = requests.post(api_url, params=api_params)
            response.raise_for_status()

    def _create_checklist(self, card_id: str, checklist_name: str, items: List[str]) -> NoReturn:
        LOG.debug('Adding checklist %s with %d items to card', checklist_name, len(items))
        create_api_params = {
            'idCard': card_id,
            'name': checklist_name,
            **self.__auth_params()
        }
        create_api_url = Trello.API_URL + '/1/checklists'
        response = requests.post(create_api_url, params=create_api_params)
        response.raise_for_status()
        checklist_id = response.json()['id']
        for item in items:
            add_api_params = {
                'name': item,
                **self.__auth_params()
            }
            add_api_url = Trello.API_URL + f'/1/checklists/{checklist_id}/checkItems'
            response = requests.post(add_api_url, params=add_api_params)
            response.raise_for_status()

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

    def _discover_all_boards(self) -> List[TrelloBoard]:
        api_params = {
            'fields': 'name',
            **self.__auth_params()
        }
        api_url = Trello.API_URL + '/1/members/me/boards'
        response = requests.get(api_url, params=api_params)
        response.raise_for_status()
        return [
            TrelloBoard(e['name'], e['id'], None, None) for e in response.json()
        ]

    def _discover_lists_in_board(self, board_id) -> List[TrelloList]:
        api_params = {
            'fields': 'name',
            **self.__auth_params()
        }
        api_url = Trello.API_URL + f'/1/boards/{board_id}/lists'
        response = requests.get(api_url, params=api_params)
        response.raise_for_status()
        return [
            TrelloList(e['name'], e['id']) for e in response.json()
        ]

    def _discover_labels_in_board(self, board_id) -> List[TrelloLabel]:
        api_params = {
            **self.__auth_params()
        }
        api_url = Trello.API_URL + f'/1/boards/{board_id}/labels'
        response = requests.get(api_url, params=api_params)
        response.raise_for_status()
        return [
            TrelloLabel(e['name'], e['id'], e['color']) for e in response.json()
        ]
