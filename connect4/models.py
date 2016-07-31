"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from protorpc import message_types
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()


class Disc(ndb.Model):
    """Game Disc"""
    user = ndb.KeyProperty(required=True, kind='User')
    column = ndb.IntegerProperty(required=True)
    row = ndb.IntegerProperty(required=True)


class Game(ndb.Model):
    """Game object"""
    rows = ndb.IntegerProperty(required=True)
    columns = ndb.IntegerProperty(required=True)
    moves = ndb.IntegerProperty(required=True, default=0)
    game_over = ndb.BooleanProperty(required=True, default=False)
    game_canceled = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        game = Game(user=user,
                    rows=6,
                    columns=7,
                    moves=0,
                    game_canceled=False,
                    game_over=False)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.moves = self.moves
        form.game_over = self.game_over
        form.game_canceled = self.game_canceled
        form.message = message
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), won=won,
                      moves=self.moves)
        score.put()

    def store_history_entry(self, move, result):
        history_entry = GameHistoryEntry(game=self.key, move=move, result=result)
        history_entry.put()

    def get_free_column(self):

        rows_filled = self.rows
        column = -1
        while rows_filled >= self.rows:
            column = random.randrange(0, self.columns)
            game_discs = Disc.query(ancestor=self.key)
            game_discs = game_discs.filter(Disc.column == column)
            rows_filled = game_discs.count()

        return column

    def check_full(self):
        return Disc.query(ancestor=self.key).count() >= (self.columns * self.rows)

    def check_win(self, user):

        tile = user

        # create game board
        board = [[0 for i in range(self.rows)] for j in range(self.columns)]

        # fill game board
        game_discs = Disc.query(ancestor=self.key).fetch()
        for disc in game_discs:
            board[disc.column][disc.row] = disc.user

        boardHeight = len(board[0])
        boardWidth = len(board)

        # check horizontal spaces
        for y in range(boardHeight):
            for x in range(boardWidth - 3):
                if board[x][y] == tile and board[x + 1][y] == tile and board[x + 2][y] == tile and board[x + 3][
                    y] == tile:
                    return True

        # check vertical spaces
        for x in range(boardWidth):
            for y in range(boardHeight - 3):
                if board[x][y] == tile and board[x][y + 1] == tile and board[x][y + 2] == tile and board[x][
                            y + 3] == tile:
                    return True

        # check / diagonal spaces
        for x in range(boardWidth - 3):
            for y in range(3, boardHeight):
                if board[x][y] == tile and board[x + 1][y - 1] == tile and board[x + 2][y - 2] == tile and \
                                board[x + 3][y - 3] == tile:
                    return True

        # check \ diagonal spaces
        for x in range(boardWidth - 3):
            for y in range(boardHeight - 3):
                if board[x][y] == tile and board[x + 1][y + 1] == tile and board[x + 2][y + 2] == tile and \
                                board[x + 3][y + 3] == tile:
                    return True

        return False


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    moves = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), moves=self.moves)


class GameHistoryEntry(ndb.Model):
    """Game history object"""
    game = ndb.KeyProperty(required=True, kind='Game')
    move = ndb.IntegerProperty(required=True)
    result = ndb.StringProperty(required=True)
    created_at = ndb.DateTimeProperty(auto_now_add=True)

    def to_form(self):
        return GameHistoryForm(urlsafe_key=self.key.urlsafe(), move=self.move,
                               result=self.result, created_at=self.created_at)


class GameHistoryForm(messages.Message):
    """GameHistoryForm for outbound game history information"""
    urlsafe_key = messages.StringField(1, required=True)
    move = messages.IntegerField(2, required=True)
    result = messages.StringField(3, required=True)
    created_at = message_types.DateTimeField(4)


class GameHistoryForms(messages.Message):
    """Return multiple GameHistoryForms"""
    items = messages.MessageField(GameHistoryForm, 1, repeated=True)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    moves = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    game_canceled = messages.BooleanField(4, required=True)
    message = messages.StringField(5, required=True)
    user_name = messages.StringField(6, required=True)


class GameForms(messages.Message):
    """Return multiple GameForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    move_column = messages.IntegerField(1, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    moves = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class RankingForm(messages.Message):
    """RankingForm for outbound ranking information"""
    user_name = messages.StringField(1, required=True)
    win_ration = messages.FloatField(2, required=True)


class RankingForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(RankingForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
