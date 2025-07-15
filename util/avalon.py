import os
import sqlite3
import json
import uuid

from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
import datetime
from pathlib import Path

import util.avalon_game_state as ags


class AvalonDBConfig:
    def __init__(self, env: str = "prod"):
        self.env = env
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

        if self.env == "test":
            self.db_path = self.data_dir / "avalon_test.db"
        else:
            self.db_path = self.data_dir / "avalon.db"


class AvalonDB:
    def __init__(self, config: AvalonDBConfig = None):
        if config is None:
            config = AvalonDBConfig()
        self.db_path = str(config.db_path)
        self.initialize_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        # Enable returning dictionary-like objects
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def initialize_database(self):
        """Create tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    player_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    gameId TEXT PRIMARY KEY,
                    state TEXT NOT NULL,  -- JSON stored as TEXT
                    start_time TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 0
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    noteId TEXT PRIMARY KEY,
                    gameId TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    content TEXT NOT NULL,
                    FOREIGN KEY (gameId) REFERENCES games(gameId) ON DELETE CASCADE
                )
            """)
            
            conn.commit()

    # Player operations
    def add_player(self, name: str) -> Tuple[bool, Optional[int]]:
        """Add a new player to the database"""
        player_id = self.get_next_player_id()
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO players (player_id, name, active) VALUES (?, ?, 1)",
                    (player_id, name)
                )
                conn.commit()
                return True, player_id
        except sqlite3.IntegrityError:
            return False, None

    def set_player_active(self, player_id: int, active: bool) -> bool:
        """Set the active status of a player"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE players SET active = ? WHERE player_id = ?",
                (1 if active else 0, player_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_active_players(self) -> List[Dict]:
        """Get all active players"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM players WHERE active = 1")
            return [dict(row) for row in cursor.fetchall()]

    def get_player(self, player_id: int) -> Optional[Dict]:
        """Get player by player_id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM players WHERE player_id = ?", (player_id,))
            result = cursor.fetchone()
            return dict(result) if result else None

    def get_all_players(self) -> List[Dict]:
        """Get all players"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM players")
            return [dict(row) for row in cursor.fetchall()]

    def get_next_player_id(self) -> int:
        """Get the next available player ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(player_id) FROM players")
            result = cursor.fetchone()[0]
            return (result + 1) if result is not None else 1

    def update_player_name(self, player_id: int, name: str) -> bool:
        """Update a player's name by player_id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE players SET name = ? WHERE player_id = ?",
                (name, player_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    # Game operations
    def create_game(self) -> str:
        """Create a new game with initial state and return its ID"""
        game_id = str(uuid.uuid4())
        initial_state = ags.create_initial_game_state()
        start_time = datetime.datetime.now(datetime.UTC).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO games (gameId, state, start_time, active) VALUES (?, ?, ?, 0)",
                (game_id, json.dumps(initial_state), start_time)
            )
            conn.commit()
        return game_id

    def set_game_active_status(self, game_id: str, active_status: int) -> bool:
        """Set the active status of a game"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE games SET active = ? WHERE gameId = ?",
                (active_status, game_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_games(self) -> list[dict[str, str]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM games ORDER BY start_time DESC")
            games = [dict(row) for row in cursor.fetchall()]
            return games

    def get_game(self, game_id) -> dict[str, str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM games WHERE gameId = ?", (game_id,))
            game = dict(cursor.fetchone())
            return game

    def get_game_state(self, game_id: str) -> Optional[ags.GameState]:
        """Get game by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM games WHERE gameId = ?", (game_id,))
            result = cursor.fetchone()
            if result:
                row = dict(result)
                row['state'] = json.loads(row['state'])
                return row['state']
            return None

    def update_game_state(self, game_id: str, new_state: ags.GameState) -> tuple[bool, Optional[str]]:
        """
        Update game state after validating it
        
        Args:
            game_id: ID of the game to update
            new_state: New game state to save
        
        Returns:
            tuple[bool, Optional[str]]: (True, None) if update was successful, (False, error_message) if failed
        """
        # Get list of valid player_ids from database
        valid_player_ids = [player['player_id'] for player in self.get_all_players()]
        
        # Validate the new state before saving
        is_valid, error_msg = ags.validate_game_state(new_state, valid_player_ids)
        if not is_valid:
            return False, error_msg
            
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE games SET state = ? WHERE gameId = ?",
                    (json.dumps(new_state), game_id)
                )
                conn.commit()
                return (cursor.rowcount > 0, None)
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"

    def get_round(self, game_id: str, quest_number: int, round_number: int) -> ags.Round:
        game_state = self.get_game_state(game_id)
        quest = ags.get_quest(game_state, quest_number)
        round = ags.get_round(quest, round_number)
        return round

    def remove_round(self, game_id: str, quest_number: int, round_number: int) -> tuple[bool, str | None]:
        """Remove a round from a quest"""
        game_state = self.get_game_state(game_id)

        new_state = ags.remove_round(game_state, quest_number - 1, round_number - 1)
        return db.update_game_state(game_id, new_state)

    def get_quest_count(self, game_id: str) -> int:
        """Get the number of quests in a game"""
        game_state = self.get_game_state(game_id)
        return len(game_state['quests']) if game_state else 0

    def get_round_count(self, game_id: str, quest_number: int) -> int:
        """Get the number of rounds in a quest"""
        game_state = self.get_game_state(game_id)
        quest = ags.get_quest(game_state, quest_number)
        return len(quest['rounds']) if quest else 0

    def round_approved(self, game_id: str, quest_number: int, round_number: int) -> bool:
        """Check if a round is approved"""
        game_state = self.get_game_state(game_id)
        quest = ags.get_quest(game_state, quest_number)
        round = ags.get_round(quest, round_number)
        return ags.round_approved(game_state, round)

    def get_reabable_player_list_from_ids(self, player_ids: List[int]) -> str:
        """Convert a list of player IDs to a readable string"""
        return ", ".join([self.get_player(player_id)['name'] for player_id in player_ids])

    # Note operations
    def add_note(self, game_id: str, content: str) -> Optional[str]:
        """Add a new note and return its ID"""
        try:
            note_id = str(uuid.uuid4())
            timestamp = datetime.datetime.now(datetime.UTC).isoformat()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO notes (noteId, gameId, timestamp, content) VALUES (?, ?, ?, ?)",
                    (note_id, game_id, timestamp, content)
                )
                conn.commit()
                return note_id
        except sqlite3.Error:
            return None

    def get_game_notes(self, game_id: str) -> List[Dict]:
        """Get all notes for a specific game"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM notes WHERE gameId = ? ORDER BY timestamp DESC",
                (game_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_note(self, note_id: str) -> Optional[Dict]:
        """Get note by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notes WHERE noteId = ?", (note_id,))
            result = cursor.fetchone()
            return dict(result) if result else None

    def delete_note(self, note_id: str) -> bool:
        """Delete a note by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM notes WHERE noteId = ?", (note_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False

if __name__ == "__main__":
    # Set up test environment
    test_config = AvalonDBConfig(env="test")
    
    # Delete existing test database if it exists
    if test_config.db_path.exists():
        test_config.db_path.unlink()
    
    # Create fresh database
    db = AvalonDB(test_config)
    
    # Add 5 test players
    test_players = [
        (1, "Alice Anderson"),
        (2, "Bob Baker"),
        (3, "Carol Chen"),
        (4, "Dave Davis"),
        (5, "Eve Edwards")
    ]
    
    print("Adding players...")
    for player_id, name in test_players:
        success = db.add_player(player_id, name)
        print(f"Added {name} ({player_id}): {'✓' if success else '✗'}")
    
    # Create a new game
    game_id = db.create_game()
    print(f"\nCreated game: {game_id}")
    
    # Get initial state
    game = db.get_game_state(game_id)
    state = game['state']
    
    # First quest - 2 rounds
    print("\nQuest 1:")
    state = ags.add_quest(state)
    
    # Round 1
    state = ags.add_round(state, 0, ["alice", "bob"])
    state = ags.update_approvals(state, 0, 0, ["alice", "bob", "carol"])
    state = ags.update_fails(state, 0, 0, 1)
    print("Round 1: Failed")
    
    # Add note about suspicious behavior
    db.add_note(game_id, "Quest 1, Round 1: Bob seemed nervous when team was proposed")
    
    # Round 2
    state = ags.add_round(state, 0, ["carol", "dave"])
    state = ags.update_approvals(state, 0, 1, ["alice", "bob", "carol", "dave", "eve"])
    state = ags.update_fails(state, 0, 1, 0)
    print("Round 2: Succeeded")
    
    db.add_note(game_id, "Quest 1, Round 2: Eve's confidence in approving this team was notable")
    
    # Second quest - 3 rounds
    print("\nQuest 2:")
    state = ags.add_quest(state)
    
    # Round 1
    state = ags.add_round(state, 1, ["eve", "alice", "bob"])
    state = ags.update_approvals(state, 1, 0, ["bob", "carol", "dave"])
    state = ags.update_fails(state, 1, 0, 2)
    print("Round 1: Failed")
    
    # Round 2
    state = ags.add_round(state, 1, ["carol", "dave", "eve"])
    state = ags.update_approvals(state, 1, 1, ["alice", "dave", "eve"])
    state = ags.update_fails(state, 1, 1, 1)
    print("Round 2: Failed")
    
    db.add_note(game_id, "Quest 2: Dave keeps pushing for teams with Eve")
    
    # Round 3
    state = ags.add_round(state, 1, ["alice", "carol", "eve"])
    state = ags.update_approvals(state, 1, 2, ["alice", "bob", "carol", "dave", "eve"])
    state = ags.update_fails(state, 1, 2, 0)
    print("Round 3: Succeeded")
    
    # After game ends, add roles
    roles = ["Merlin", "Assassin", "Loyal Servant", "Morgana", "Percival"]
    for (alias, _), role in zip(test_players, roles):
        state = ags.add_player(state, alias, role)
    
    # Save final state
    db.update_game_state(game_id, state)
    
    # Add final notes about the game
    db.add_note(game_id, "Final thoughts: Dave (Morgana) played well but got too obvious with Eve")
    db.add_note(game_id, "Bob correctly identified Alice as Merlin - good read on the Quest 2 approval pattern")
    
    # Print game summary
    print("\nGame Summary:")
    print(f"Number of quests: {len(state['quests'])}")
    print(f"Number of players: {len(state['players'])}")
    
    # Print quest results
    for quest_idx in range(len(state['quests'])):
        result = ags.get_quest_result(state, quest_idx)
        print(f"Quest {quest_idx + 1} result: {'Success' if result else 'Failure'}")
    
    # Print all notes
    print("\nGame Notes:")
    notes = db.get_game_notes(game_id)
    notes.sort(key=lambda n: n['timestamp'])
    for note in notes:
        print(f"\n[{note['timestamp']}]")
        print(note['content'])