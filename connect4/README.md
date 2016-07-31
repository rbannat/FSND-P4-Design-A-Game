# Full Stack Nanodegree Project 4 Refresh

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
1.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.
 
## Game Description:
Connect Four is a two player connection game. Each game begins with a number of rows and columns.
The players take turns and a chosen column is sent to the `make_move` endpoint which will stack a 'Game Disc'
in the given column. If a player has 4 in a row horizontally, vertically or diagonal after his move he wins.

Many different games can be played by many different Users at any
given time. Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

## Score Keeping:
After each game the count of user played discs is saved together with whether the user has won or not. For ranking 
purposes a win/loss ratio in respect to all played games is documented.

## Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

## Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, columns, rows
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game. The `board` property represents the current game state where 'O' 
      is a Users disc and 'X' is the AI's disc.
 
 - **get_game_history**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameHistoryForms with current game history.
    - Description: Returns the history of a game.

- **cancel_game**
    - Path: 'game/{urlsafe_game_key}/cancel'
    - Method: PUT
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Sets game_canceled to True. Returns the current state of a game.

- **get_user_games**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: GameForms.
    - Description: Returns all Games recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, move_column
    - Returns: GameForm with new game state.
    - Description: Accepts a 'column' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **get_user_rankings**
    - Path: 'rankings'
    - Method: GET
    - Returns: RankingForms. 
    - Description: Returns user rankings ordered by highest win ratio.
    
 - **get_active_game_count**
    - Path: 'games/active'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all games
    from a previously cached memcache key.

## Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
     
 - **GameHistoryEntry**
    - Stores unique game history entry. Associated with Game model via KeyProperty.

 - **Disc**
    - Stores a game disc. Associated with Game model and User who made the move.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
## Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, moves, columns, rows
    game_over flag, game_canceled, message, user_name).
 - **GameForms**
    - Multiple GameForm container.
 - **NewGameForm**
    - Used to create a new game (user_name, columns, rows)
 - **MakeMoveForm**
    - Inbound make move form (move_column). Creates a game disc.
 - **GameHistoryForm**
    - Representation of a game history entry (game, move, result).
 - **GameHistoryForms**
    - Multiple GameHistoryForm container.
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    guesses).
 - **ScoreForms**
    - Multiple ScoreForm container.
  - **RankingForm**
    - Representation of a players win/loss ratio (user_name, win_ratio)
 - **RankingForms**
    - Multiple RankingForm container.
 - **StringMessage**
    - General purpose String container.