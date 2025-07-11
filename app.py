from flask import Flask, render_template, request, jsonify
from flasgger import Swagger

import json
import logging

import util.avalon_game_state as ags
from util.avalon import AvalonDB

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,  # Include all routes
            "model_filter": lambda tag: True,  # Include all models
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Avalon Game Notes API",
        "description": "This is the API for managing Avalon game notes and state.",
        "version": "1.0.0"
    },
    "host": "127.0.0.1:5000",
    "basePath": "/",
    "schemes": ["http"]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)


db = AvalonDB()  # Using default production config

@app.route('/')
@app.route('/index')
def index():
    """
    Home page
    ---
    responses:
      200:
        description: Render apitest.html
    """
    return render_template('index.html')

@app.route('/avalon')
def avalon():
    """
    Avalon page
    ---
    responses:
      200:
        description: Render avalon/apitest.html
    """
    return render_template('avalon/index.html')

@app.route('/avalontester')
def avalon_tester():
    """
    Avalon API test page
    ---
    responses:
      200:
        description: Render avalon/apitest.html
    """
    return render_template('avalon/apitest.html')

@app.route('/avalon/<game_id>')
def avalon_game(game_id):
    """
    Avalon game setup page
    ---
    parameters:
      - in: path
        name: game_id
        type: string
        required: true
    responses:
      200:
        description: Render avalon/game.html
    """
    return render_template('avalon/game.html')

@app.route('/avalon/players')
def avalon_players():
    """
    Avalon Players management page
    ---
    responses:
      200:
        description: Render avalon/players.html
    """
    return render_template('avalon/players.html')

@app.route('/api/players/add', methods=['POST'])
def add_player():
    """
    Add a new player
    ---
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - alias
            - name
          properties:
            alias:
              type: string
            name:
              type: string
    responses:
      201:
        description: Player added successfully
      400:
        description: Missing required fields
      409:
        description: Player already exists
    """
    data = request.get_json()
    if not data or 'alias' not in data or 'name' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    success = db.add_player(data['alias'], data['name'])
    if not success:
        return jsonify({'error': 'Player already exists'}), 409

    return jsonify({'message': 'Player added successfully'}), 201

@app.route('/api/players/get', methods=['GET'])
def get_players():
    """
    Get all players
    ---
    responses:
      200:
        description: List of all players
        schema:
          type: object
          properties:
            players:
              type: array
              items:
                type: object
    """
    players = db.get_all_players()
    return jsonify({'players': players}), 200

@app.route('/api/players/get_active', methods=['GET'])
def get_active_players():
    """
    Get all active players
    ---
    responses:
      200:
        description: List of active players
        schema:
          type: object
          properties:
            players:
              type: array
              items:
                type: object
    """
    players = db.get_active_players()
    return jsonify({'players': players}), 200

@app.route('/api/players/set_active', methods=['POST'])
def set_player_active():
    """
    Set a player's active status
    ---
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - alias
            - active
          properties:
            alias:
              type: string
            active:
              type: boolean
    responses:
      200:
        description: Player status updated
      400:
        description: Missing required fields
      404:
        description: Player not found
    """
    data = request.get_json()
    if not data or 'alias' not in data or 'active' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    success = db.set_player_active(data['alias'], data['active'])
    if not success:
        return jsonify({'error': 'Player not found'}), 404
    return jsonify({'message': 'Player status updated'}), 200

@app.route('/api/games/create', methods=['POST'])
def create_game():
    """
    Create a new game
    ---
    responses:
      201:
        description: Game created
        schema:
          type: object
          properties:
            gameId:
              type: string
    """
    game_id = db.create_game()
    return jsonify({'gameId': game_id}), 201

@app.route('/api/games/get', methods=['GET'])
def get_games():
    """
    Get all games
    ---
    responses:
      200:
        description: List of all games
        schema:
          type: object
          properties:
            games:
              type: array
              items:
                type: object
    """
    games = db.get_games()
    for game in games:
        game['state'] = json.loads(game['state'])
    return jsonify({'games': games}), 200

@app.route('/api/games/<game_id>/get', methods=['GET'])
def get_game_state(game_id):
    """
    Get game state by game ID
    ---
    parameters:
      - in: path
        name: game_id
        type: string
        required: true
    responses:
      200:
        description: Game state
      404:
        description: Game not found
    """
    game = db.get_game_state(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    return jsonify(game), 200

@app.route('/api/games/<game_id>/players/add', methods=['POST'])
def add_game_player(game_id):
    """
    Add player to a game
    ---
    parameters:
      - in: path
        name: game_id
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
          required:
            - alias
          properties:
            alias:
              type: string
    responses:
      200:
        description: Player added to game
      400:
        description: Missing required fields
      404:
        description: Game or player not found
    """
    data = request.get_json()
    if not data or 'alias' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    game = db.get_game_state(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    # Check if player exists
    player = db.get_player(data['alias'])
    if not player:
        return jsonify({'error': 'Player not found'}), 404

    state = game['state']

    # Empty role; to be filled in at the end
    state = ags.add_player(state, data['alias'], '')

    if not db.update_game_state(game_id, state):
        return jsonify({'error': 'Invalid game state'}), 400

    return jsonify({'message': 'Player added to game'}), 200

@app.route('/api/games/<game_id>/players/remove', methods=['POST'])
def remove_game_player(game_id):
    """
    Remove player from a game
    ---
    parameters:
      - in: path
        name: game_id
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
          required:
            - alias
          properties:
            alias:
              type: string
    responses:
      200:
        description: Player removed from game
      400:
        description: Missing required fields or invalid game state
      404:
        description: Game not found
    """
    data = request.get_json()
    if not data or 'alias' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    game = db.get_game_state(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    state = game['state']
    new_state = ags.remove_player(state, data['alias'])
    if new_state is None:
        return jsonify({'error': 'Player not in game'}), 400

    if not db.update_game_state(game_id, new_state):
        return jsonify({'error': 'Invalid game state'}), 400

    return jsonify({'message': 'Player removed from game'}), 200

@app.route('/api/games/<game_id>/quests/add', methods=['POST'])
def add_quest(game_id):
    """
    Add a quest to a game
    ---
    parameters:
      - in: path
        name: game_id
        type: string
        required: true
    responses:
      200:
        description: Quest added
      404:
        description: Game not found
      400:
        description: Invalid game state
    """
    game = db.get_game_state(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    state = game['state']
    state = ags.add_quest(state)

    if not db.update_game_state(game_id, state):
        return jsonify({'error': 'Invalid game state'}), 400

    return jsonify({'message': 'Quest added', 'questNumber': len(state['quests'])}), 200

@app.route('/api/games/<game_id>/quests/<int:quest_number>/rounds/add', methods=['POST'])
def add_round(game_id, quest_number):
    """
    Add a round to a quest
    ---
    parameters:
      - in: path
        name: game_id
        type: string
        required: true
      - in: path
        name: quest_number
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          required:
            - team
            - king
          properties:
            team:
              type: array
              items:
                type: string
            king:
              type: string
            approvals:
              type: array
              items:
                type: string
            failures:
              type: array
              items:
                type: string
    responses:
      200:
        description: Round added
      400:
        description: Missing required fields or invalid quest number/state
      404:
        description: Game not found
    """
    data = request.get_json()
    if not data or 'team' not in data or 'king' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    game = db.get_game_state(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    quest_index = ags.quest_number_to_index(quest_number)
    state = game['state']

    # Add the round with the proposed team
    state = ags.add_round(state, quest_index, data['team'], data['king'])
    if state is None:
        return jsonify({'error': 'Invalid quest number'}), 400

    round_index = len(state['quests'][quest_index]['rounds']) - 1

    # Update the round with approvals if provided and not empty
    if 'approvals' in data:
        # Filter out any empty strings from approvals list
        approvals = [a for a in data['approvals'] if a]
        state = ags.update_approvals(state, quest_index, round_index, approvals)

    # If failures were provided, update fails
    if 'failures' in data:
        state = ags.update_fails(state, quest_index, round_index, data['failures'])

    if not db.update_game_state(game_id, state):
        return jsonify({'error': 'Invalid game state'}), 400

    return jsonify({
        'message': 'Round added',
        'questNumber': quest_number,
        'roundNumber': len(state['quests'][quest_index]['rounds'])
    }), 200

# Note-related endpoints
@app.route('/api/games/<game_id>/notes/add', methods=['POST'])
def add_note(game_id):
    """
    Add a note to a game
    ---
    parameters:
      - in: path
        name: game_id
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
          required:
            - content
          properties:
            content:
              type: string
    responses:
      201:
        description: Note added
      400:
        description: Missing content field
      404:
        description: Game not found
      500:
        description: Failed to add note
    """
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Missing content field'}), 400

    game = db.get_game_state(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    note_id = db.add_note(game_id, data['content'])
    if not note_id:
        return jsonify({'error': 'Failed to add note'}), 500

    return jsonify({'noteId': note_id}), 201

@app.route('/api/games/<game_id>/notes/get', methods=['GET'])
def get_game_notes(game_id):
    """
    Get notes for a game
    ---
    parameters:
      - in: path
        name: game_id
        type: string
        required: true
    responses:
      200:
        description: List of notes
      404:
        description: Game not found
    """
    game = db.get_game_state(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    notes = db.get_game_notes(game_id)
    return jsonify({'notes': notes}), 200

@app.route('/api/games/<game_id>/start', methods=['POST'])
def start_game(game_id):
    """
    Set game as active (started) and start first quest
    ---
    parameters:
      - in: path
        name: game_id
        type: string
        required: true
    responses:
      200:
        description: Game started
      404:
        description: Game not found
    """
    success = db.set_game_active_status(game_id, 1)
    if not success:
        return jsonify({'error': 'Game not found'}), 404
    response, status = add_quest(game_id)
    if response != 200:
        return response, status
    return jsonify({'message': 'Game started'}), 200

@app.route('/api/games/<game_id>/end', methods=['POST'])
def start_game(game_id):
    """
    Set game as active (started) and start first quest
    ---
    parameters:
      - in: path
        name: game_id
        type: string
        required: true
    responses:
      200:
        description: Game started
      404:
        description: Game not found
    """
    success = db.set_game_active_status(game_id, 2)
    if not success:
        return jsonify({'error': 'Game not found'}), 404
    return jsonify({'message': 'Game ended'}), 200

@app.route('/api/players/update_name', methods=['POST'])
def update_player_name():
    """
    Update a player's name
    ---
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - alias
            - name
          properties:
            alias:
              type: string
            name:
              type: string
    responses:
      200:
        description: Player name updated
      400:
        description: Missing required fields
      404:
        description: Player not found
    """
    data = request.get_json()
    if not data or 'alias' not in data or 'name' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    success = db.update_player_name(data['alias'], data['name'])
    if not success:
        return jsonify({'error': 'Player not found'}), 404
    return jsonify({'message': 'Player name updated'}), 200

if __name__ == '__main__':
    app.run(debug=True)
