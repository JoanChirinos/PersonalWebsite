from flask import Flask, render_template, request, jsonify

import json
import logging

import util.avalon_game_state as ags
from util.avalon import AvalonDB

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
db = AvalonDB()  # Using default production config

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/avalon')
def avalon():
    return '''
    <html>
        <head>
            <title>Avalon API Test</title>
            <script>
                async function makeRequest(url, method, data) {
                    // Show request details
                    const requestDetails = {
                        url: url,
                        method: method,
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: data
                    };
                    document.getElementById('request').textContent = JSON.stringify(requestDetails, null, 2);

                    try {
                        const response = await fetch(url, {
                            method: method,
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: data ? JSON.stringify(data) : null
                        });
                        const result = await response.json();
                        document.getElementById('response').textContent = JSON.stringify(result, null, 2);
                    } catch (error) {
                        document.getElementById('response').textContent = `Error: ${error.message}`;
                    }
                }

                function addPlayer() {
                    const alias = document.getElementById('playerAlias').value;
                    const name = document.getElementById('playerName').value;
                    makeRequest('/api/players', 'POST', { alias, name });
                }

                function createGame() {
                    makeRequest('/api/games', 'POST');
                }

                function addPlayerToGame() {
                    const gameId = document.getElementById('gameId').value;
                    const alias = document.getElementById('gamePlayerAlias').value;
                    const role = document.getElementById('playerRole').value;
                    makeRequest(`/api/games/${gameId}/players`, 'POST', { alias, role });
                }

                function addQuest() {
                    const gameId = document.getElementById('questGameId').value;
                    makeRequest(`/api/games/${gameId}/quests`, 'POST');
                }

                function addRound() {
                    const gameId = document.getElementById('roundGameId').value;
                    const questNum = document.getElementById('questNumber').value;
                    const king = document.getElementById('king').value;
                    const team = document.getElementById('team').value.split(',').map(s => s.trim()).filter(s => s);
                    // If the input is empty or contains only an empty string, use an empty array
                    const approvals = document.getElementById('approvals').value.trim() 
                        ? document.getElementById('approvals').value.split(',').map(s => s.trim()).filter(s => s)
                        : [];
                    const failures = parseInt(document.getElementById('failures').value) || 0;
                    makeRequest(`/api/games/${gameId}/quests/${questNum}/rounds`, 'POST', 
                        { team, king, approvals, failures });
                }

                function addNote() {
                    const gameId = document.getElementById('noteGameId').value;
                    const content = document.getElementById('noteContent').value;
                    makeRequest(`/api/games/${gameId}/notes`, 'POST', { content });
                }

                function getNotes() {
                    const gameId = document.getElementById('getNotesGameId').value;
                    makeRequest(`/api/games/${gameId}/notes`, 'GET');
                }

                function getAllPlayers() {
                    makeRequest('/api/players', 'GET');
                }

                function getAllGames() {
                    makeRequest('/api/games', 'GET');
                }

                function getGameDetails() {
                    const gameId = document.getElementById('getGameId').value;
                    makeRequest(`/api/games/${gameId}`, 'GET');
                }
            </script>
            <style>
                .section { 
                    margin: 20px; 
                    padding: 10px; 
                    border: 1px solid #ccc; 
                }
                .subsection { 
                    margin: 10px 0; 
                    padding: 5px;
                    border-bottom: 1px solid #eee;
                }
                .code-block { 
                    white-space: pre; 
                    font-family: monospace;
                    background-color: #f5f5f5;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    overflow-x: auto;
                }
            </style>
        </head>
        <body>
            <h1>Avalon API Tester</h1>

            <div class="section">
                <h2>Add Player</h2>
                <label>Alias: <input type="text" id="playerAlias"></label><br>
                <label>Name: <input type="text" id="playerName"></label><br>
                <button onclick="addPlayer()">Add Player</button>
            </div>

            <div class="section">
                <h2>Create Game</h2>
                <button onclick="createGame()">Create Game</button>
            </div>

            <div class="section">
                <h2>Add Player to Game</h2>
                <label>Game ID: <input type="text" id="gameId"></label><br>
                <label>Alias: <input type="text" id="gamePlayerAlias"></label><br>
                <label>Role: <input type="text" id="playerRole"></label><br>
                <button onclick="addPlayerToGame()">Add Player to Game</button>
            </div>

            <div class="section">
                <h2>Add Quest</h2>
                <label>Game ID: <input type="text" id="questGameId"></label><br>
                <button onclick="addQuest()">Add Quest</button>
            </div>

            <div class="section">
                <h2>Add Round to Quest</h2>
                <label>Game ID: <input type="text" id="roundGameId"></label><br>
                <label>Quest Number: <input type="number" id="questNumber"></label><br>
                <label>King (who's picking the team): <input type="text" id="king"></label><br>
                <label>Team (comma-separated): <input type="text" id="team"></label><br>
                <label>Approvals (comma-separated): <input type="text" id="approvals"></label><br>
                <label>Failures: <input type="number" id="failures"></label><br>
                <button onclick="addRound()">Add Round</button>
            </div>

            <div class="section">
                <h2>Add Note</h2>
                <label>Game ID: <input type="text" id="noteGameId"></label><br>
                <label>Content: <textarea id="noteContent"></textarea></label><br>
                <button onclick="addNote()">Add Note</button>
            </div>

            <div class="section">
                <h2>Get Notes</h2>
                <label>Game ID: <input type="text" id="getNotesGameId"></label><br>
                <button onclick="getNotes()">Get Notes</button>
            </div>

            <div class="section">
                <h2>View Database Contents</h2>
                
                <div class="subsection">
                    <h3>Players</h3>
                    <button onclick="getAllPlayers()">Get All Players</button>
                </div>

                <div class="subsection">
                    <h3>Games</h3>
                    <button onclick="getAllGames()">Get All Games</button>
                </div>

                <div class="subsection">
                    <h3>Game Details</h3>
                    <label>Game ID: <input type="text" id="getGameId"></label><br>
                    <button onclick="getGameDetails()">Get Game Details</button>
                </div>
            </div>

            <div class="section">
    <h2>API Communication</h2>
    <div class="subsection">
        <h3>Request:</h3>
        <pre id="request" class="code-block"></pre>
    </div>
    <div class="subsection">
        <h3>Response:</h3>
        <pre id="response" class="code-block"></pre>
    </div>
</div>
        </body>
    </html>
    '''

@app.route('/api/players', methods=['POST'])
def add_player():
    data = request.get_json()
    if not data or 'alias' not in data or 'name' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    success = db.add_player(data['alias'], data['name'])
    if not success:
        return jsonify({'error': 'Player already exists'}), 409
        
    return jsonify({'message': 'Player added successfully'}), 201

@app.route('/api/games', methods=['POST'])
def create_game():
    game_id = db.create_game()
    return jsonify({'gameId': game_id}), 201

@app.route('/api/games/<game_id>/players', methods=['POST'])
def add_game_player(game_id):
    data = request.get_json()
    if not data or 'alias' not in data or 'role' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    game = db.get_game(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404
        
    # Check if player exists
    player = db.get_player(data['alias'])
    if not player:
        return jsonify({'error': 'Player not found'}), 404
        
    state = game['state']
    state = ags.add_player(state, data['alias'], data['role'])
    
    if not db.update_game_state(game_id, state):
        return jsonify({'error': 'Invalid game state'}), 400
        
    return jsonify({'message': 'Player added to game'}), 200

@app.route('/api/games/<game_id>/quests', methods=['POST'])
def add_quest(game_id):
    game = db.get_game(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404
        
    state = game['state']
    state = ags.add_quest(state)
    
    if not db.update_game_state(game_id, state):
        return jsonify({'error': 'Invalid game state'}), 400
        
    return jsonify({'message': 'Quest added', 'questNumber': len(state['quests'])}), 200

@app.route('/api/games/<game_id>/quests/<int:quest_number>/rounds', methods=['POST'])
def add_round(game_id, quest_number):
    data = request.get_json()
    if not data or 'team' not in data or 'king' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    game = db.get_game(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404
        
    quest_index = ags.quest_number_to_index(quest_number)
    state = game['state']
    
    # Add the round with the proposed team
    state = ags.add_round(state, quest_index, data['team'], data['king'])
    if state is None:
        return jsonify({'error': 'Invalid quest number'}), 400
        
    # Update the round with approvals if provided and not empty
    if 'approvals' in data:
        round_index = len(state['quests'][quest_index]['rounds']) - 1
        # Filter out any empty strings from approvals list
        approvals = [a for a in data['approvals'] if a]
        state = ags.update_approvals(state, quest_index, round_index, approvals)
    
    # If failures were provided, update fails
    if 'failures' in data:
        round_index = len(state['quests'][quest_index]['rounds']) - 1
        state = ags.update_fails(state, quest_index, round_index, data['failures'])
    
    if not db.update_game_state(game_id, state):
        return jsonify({'error': 'Invalid game state'}), 400
        
    return jsonify({
        'message': 'Round added',
        'questNumber': quest_number,
        'roundNumber': len(state['quests'][quest_index]['rounds'])
    }), 200

# Note-related endpoints
@app.route('/api/games/<game_id>/notes', methods=['POST'])
def add_note(game_id):
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Missing content field'}), 400
        
    game = db.get_game(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404
        
    note_id = db.add_note(game_id, data['content'])
    if not note_id:
        return jsonify({'error': 'Failed to add note'}), 500
        
    return jsonify({'noteId': note_id}), 201

@app.route('/api/games/<game_id>/notes', methods=['GET'])
def get_game_notes(game_id):
    game = db.get_game(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404
        
    notes = db.get_game_notes(game_id)
    return jsonify({'notes': notes}), 200

@app.route('/api/players', methods=['GET'])
def get_all_players():
    players = db.get_all_players()
    return jsonify({'players': players}), 200

@app.route('/api/games/<game_id>', methods=['GET'])
def get_game_details(game_id):
    game = db.get_game(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    return jsonify(game), 200

@app.route('/api/games', methods=['GET'])
def get_all_games():
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM games")
        games = [dict(row) for row in cursor.fetchall()]
        # Parse the JSON state for each game
        for game in games:
            game['state'] = json.loads(game['state'])
        return jsonify({'games': games}), 200

if __name__ == '__main__':
    app.run(debug=True)
