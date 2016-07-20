# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""

import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score, Disc
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm, \
    ScoreForms, GameForms
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1), )
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1), )
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'


@endpoints.api(name='connect_4', version='v1')
class Connect4Api(remote.Service):
    """Game API"""

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
            request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')

        game = Game.new_game(user.key, request.rows, request.columns)

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        # taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Connect4!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns all of an individual User's games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        games = Game.query(Game.user == user.key)
        return GameForms(items=[game.to_form('') for game in games])

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""

        game = get_by_urlsafe(request.urlsafe_game_key, Game)

        if game.game_over:
            return game.to_form('Game already over!')

        if request.move_column < 0 or request.move_column >= game.columns:
            raise endpoints.BadRequestException('Column must be within game Boundaries')

        game_discs = Disc.query(ancestor=game.key)
        game_discs = game_discs.filter(Disc.column == request.move_column)
        rows_filled = game_discs.count()

        if rows_filled >= game.rows:
            raise endpoints.BadRequestException('Column is filled')

        # do user move
        game.moves += 1

        disc = Disc(parent=game.key, user=game.user, column=request.move_column, row=rows_filled)
        disc.put()

        if game.check_win(user=game.user):
            game.end_game(True)
            return game.to_form('You win!')

        if game.check_full():
            game.end_game(False)
            return game.to_form('Game over! No one wins! Player was last!')

        # do AI move ...
        ai_user = User.query(User.name == 'Computer').get()
        if not ai_user:
            raise endpoints.NotFoundException(
                'No AI User!')

        move_column = game.get_free_column()
        game_discs = Disc.query(ancestor=game.key)
        game_discs = game_discs.filter(Disc.column == move_column)
        rows_filled = game_discs.count()

        disc = Disc(parent=game.key, user=ai_user.key, column=move_column, row=rows_filled)
        disc.put()

        # check_win() --> check AI win
        if game.check_win(user=ai_user.key):
            game.end_game(True)
            return game.to_form('Game Over! You lost!')

        if game.check_full():
            game.end_game(False)
            return game.to_form('Game over! No one wins! Computer was last!')
        else:
            game.put()

        return game.to_form('Nice try! Go on!')


@endpoints.method(response_message=ScoreForms,
                  path='scores',
                  name='get_scores',
                  http_method='GET')
def get_scores(self, request):
    """Return all scores"""
    return ScoreForms(items=[score.to_form() for score in Score.query()])


@endpoints.method(request_message=USER_REQUEST,
                  response_message=ScoreForms,
                  path='scores/user/{user_name}',
                  name='get_user_scores',
                  http_method='GET')
def get_user_scores(self, request):
    """Returns all of an individual User's scores"""
    user = User.query(User.name == request.user_name).get()
    if not user:
        raise endpoints.NotFoundException(
            'A User with that name does not exist!')
    scores = Score.query(Score.user == user.key)
    return ScoreForms(items=[score.to_form() for score in scores])


@endpoints.method(response_message=StringMessage,
                  path='games/average_attempts',
                  name='get_average_attempts_remaining',
                  http_method='GET')
def get_average_attempts(self, request):
    """Get the cached average moves remaining"""
    return StringMessage(message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')


@staticmethod
def _cache_average_attempts():
    """Populates memcache with the average moves remaining of Games"""
    games = Game.query(Game.game_over == False).fetch()
    if games:
        count = len(games)
        total_attempts_remaining = sum([game.attempts_remaining
                                        for game in games])
        average = float(total_attempts_remaining) / count
        memcache.set(MEMCACHE_MOVES_REMAINING,
                     'The average moves remaining is {:.2f}'.format(average))


api = endpoints.api_server([Connect4Api])
