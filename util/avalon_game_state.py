import logging
from typing import List, Optional
from typing_extensions import TypedDict
from copy import deepcopy

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Player(TypedDict):
    player_id: int  # References players.player_id in SQLite
    role: str   # The game role assigned to the player

class Round(TypedDict):
    team: List[int]       # List of player player_ids
    approvals: List[int]  # List of player player_ids who approved
    fails: int            # Number of fail cards played
    king: int             # player_id of the player who is king for this round

class Quest(TypedDict):
    rounds: List[Round]

class GameState(TypedDict):
    players: List[Player]
    quests: List[Quest]

def validate_game_state(state: GameState, valid_player_ids: List[str]) -> tuple[bool, Optional[str]]:
    """
    Validates that a game state matches the schema and references valid players

    Args:
        state: GameState to validate
        valid_player_ids: List of valid player player_ids to check against

    Returns:
        tuple[bool, Optional[str]]: (True, None) if state is valid, (False, error_message) if invalid

    Note:
        Player roles are allowed to be empty strings ('') until the end of the game
        when roles are revealed.
        Rounds may have empty approvals list and no fails recorded until voting/quest is complete.
    """
    logger.debug(f'Validating game state with {len(valid_player_ids)} valid player_ids')
    
    # Basic structure validation
    if not isinstance(state, dict):
        logger.error('State validation failed: not a dictionary')
        return False, 'State must be a dictionary'
    
    # Add logging for each validation step
    logger.debug('Checking basic structure...')
    if 'players' not in state:
        logger.error('State validation failed: missing players field')
        return False, 'State missing "players" field'
    if 'quests' not in state:
        return False, 'State missing "quests" field'
        
    if not isinstance(state['players'], list):
        return False, 'Players must be a list'
    if not isinstance(state['quests'], list):
        return False, 'Quests must be a list'
    
    # Convert list to set for O(1) lookups
    valid_player_ids_set = set(valid_player_ids)
    logger.debug(f'Valid player IDs set: {valid_player_ids_set}')
    
    # Validate players
    for player_idx, player in enumerate(state['players']):
        if not isinstance(player, dict):
            return False, f'Player {player_idx} must be a dictionary'
        if 'player_id' not in player:
            return False, f'Player {player_idx} missing "player_id" field'
        if 'role' not in player:
            return False, f'Player {player_idx} missing "role" field'
        if not isinstance(player['player_id'], int):
            return False, f'Player {player_idx} player_id must be a string'
        if not isinstance(player['role'], str):
            return False, f'Player {player_idx} role must be a string'
        # Note: role can be an empty string
        if player['player_id'] not in valid_player_ids_set:
            return False, f'Invalid player player_id: {player['player_id']}'
    
    # Validate quests
    for quest_idx, quest in enumerate(state['quests']):
        if not isinstance(quest, dict):
            logger.error(f'Quest {quest_idx} validation failed: not a dictionary')
            return False, f'Quest {quest_idx} must be a dictionary'
            
        if 'rounds' not in quest:
            logger.error(f'Quest {quest_idx} validation failed: missing rounds')
            return False, f'Quest {quest_idx} missing "rounds" field'
            
        if not isinstance(quest['rounds'], list):
            logger.error(f'Quest {quest_idx} validation failed: rounds not a list')
            return False, f'Quest {quest_idx} rounds must be a list'
            
        for round_idx, round in enumerate(quest['rounds']):
            if not isinstance(round, dict):
                logger.error(f'Round {round_idx} in Quest {quest_idx} validation failed: not a dictionary')
                return False, f'Round {round_idx} in Quest {quest_idx} must be a dictionary'
                
            # Validate required fields
            if 'team' not in round:
                logger.error(f'Round {round_idx} in Quest {quest_idx} validation failed: missing team')
                return False, f'Round {round_idx} in Quest {quest_idx} missing "team" field'
                
            if 'king' not in round:
                logger.error(f'Round {round_idx} in Quest {quest_idx} validation failed: missing king')
                return False, f'Round {round_idx} in Quest {quest_idx} missing "king" field'
            
            # Validate field types
            if not isinstance(round['team'], list):
                logger.error(f'Round {round_idx} in Quest {quest_idx} validation failed: team not a list')
                return False, f'Team in Quest {quest_idx} Round {round_idx} must be a list'
                
            if not isinstance(round['king'], int):
                logger.error(f'Round {round_idx} in Quest {quest_idx} validation failed: king not a string')
                return False, f'King in Quest {quest_idx} Round {round_idx} must be a string'
                
            if round['king'] not in valid_player_ids_set:
                logger.error(f'Round {round_idx} in Quest {quest_idx} validation failed: invalid king')
                return False, f'Invalid king player_id in Quest {quest_idx} Round {round_idx}: {round['king']}'
            
            # Validate team members exist
            for player_id in round['team']:
                if not isinstance(player_id, int):
                    logger.error(f'Round {round_idx} in Quest {quest_idx} validation failed: team member not an int')
                    return False, f'Team member player_id in Quest {quest_idx} Round {round_idx} must be an int'
                if player_id not in valid_player_ids_set:
                    logger.error(f'Round {round_idx} in Quest {quest_idx} validation failed: invalid team member')
                    return False, f'Invalid team member player_id in Quest {quest_idx} Round {round_idx}: {player_id}'
            
            # Optional fields validation
            if 'approvals' in round:
                if not isinstance(round['approvals'], list):
                    logger.error(f'Round {round_idx} in Quest {quest_idx} validation failed: approvals not a list')
                    return False, f'Approvals in Quest {quest_idx} Round {round_idx} must be a list'
                    
                # Validate approvals exist if present
                for player_id in round['approvals']:
                    if not isinstance(player_id, int):
                        logger.error(f'Round {round_idx} in Quest {quest_idx} validation failed: approval not a string')
                        return False, f'Approval player_id in Quest {quest_idx} Round {round_idx} must be a string'
                    if player_id not in valid_player_ids_set:
                        logger.error(f'Round {round_idx} in Quest {quest_idx} validation failed: invalid approval')
                        return False, f'Invalid approval player_id in Quest {quest_idx} Round {round_idx}: {player_id}'
            
            if 'fails' in round:
                if not isinstance(round['fails'], int):
                    logger.error(f'Round {round_idx} in Quest {quest_idx} validation failed: fails not an integer')
                    return False, f'Fails in Quest {quest_idx} Round {round_idx} must be an integer'
    
    logger.debug('Game state validation successful')
    return True, None

def create_initial_game_state() -> GameState:
    logger.debug('Creating initial game state')
    state: GameState = {
        'players': [],
        'quests': []
    }
    logger.debug(f'Created initial state: {state}')
    return state

def add_quest(state: GameState) -> GameState:
    logger.debug('Adding new quest')
    logger.debug(f'Current state before adding quest: {state}')
    new_state = deepcopy(state)
    new_state['quests'].append({'rounds': []})
    logger.debug(f'New state after adding quest: {new_state}')
    return new_state

def remove_quest(state: GameState, quest_index: int) -> Optional[GameState]:
    logger.debug(f'Removing quest {quest_index}')
    logger.debug(f'Current state before removing quest: {state}')

    if quest_index < 0 or quest_index >= len(state['quests']):
        logger.error(f'Invalid quest index: {quest_index}')
        return None

    new_state = deepcopy(state)
    new_state['quests'].pop(quest_index)
    logger.debug(f'State after removing quest: {new_state}')
    return new_state

def add_round(state: GameState, quest_index: int, team: List[int], king: int) -> Optional[GameState]:
    """
    Adds a new round to a specific quest

    Args:
        state: Current game state
        quest_index: 0-based index of the quest
        team: List of player player_ids for the round team
        king: player_id of the player who is king for this round

    Returns:
        Optional[GameState]: New game state with added round, or None if quest_index is invalid
    """
    logger.debug(f'Adding round to quest {quest_index} with team {team} and king {king}')
    logger.debug(f'Current state before adding round: {state}')
    
    if quest_index < 0 or quest_index >= len(state['quests']):
        logger.error(f'Invalid quest index: {quest_index}')
        return None
        
    new_state = deepcopy(state)
    new_round: Round = {
        'team': team,
        'approvals': [],
        'fails': 0,
        'king': king
    }
    new_state['quests'][quest_index]['rounds'].append(new_round)
    logger.debug(f'New state after adding round: {new_state}')
    return new_state

def remove_round(state: GameState, quest_index: int, round_index: int) -> Optional[GameState]:
    logger.debug(f'Attempting to remove round {round_index} from quest {quest_index}')
    logger.debug(f'Current state before removing round: {state}')

    if quest_index < 0 or quest_index >= len(state['quests']):
        logger.error(f'Invalid quest index: {quest_index}')
        return None

    if round_index < 0 or round_index >= len(state['quests'][quest_index]['rounds']):
        logger.error(f'Invalid round index: {round_index}')
        return None

    new_state = deepcopy(state)
    new_state['quests'][quest_index]['rounds'].pop(round_index)
    logger.debug(f'State after removing round: {new_state}')
    return new_state

def add_player(state: GameState, player_id: int, role: str = '') -> GameState:
    logger.debug(f'Adding player {player_id} with role {role}')
    logger.debug(f'Current state before adding player: {state}')
    new_state = deepcopy(state)
    new_state['players'].append({'player_id': player_id, 'role': role})
    logger.debug(f'New state after adding player: {new_state}')
    return new_state

def remove_player(state: GameState, player_id: int) -> Optional[GameState]:
    logger.debug(f'Removing player {player_id}')
    logger.debug(f'Current state before adding player: {state}')

    if player_id not in (player['player_id'] for player in state['players']):
        logger.error(f'Player {player_id} not in game')
        return None

    new_state = deepcopy(state)
    new_state['players'] = [player for player in state['players'] if player['player_id'] != player_id]
    logger.debug(f'State after removing player: {new_state}')
    return new_state

def update_team(state: GameState, quest_index: int, round_index: int, team: List[int]) -> Optional[GameState]:
    """
    Updates the team for a specific round

    Args:
        state: Current game state
        quest_index: 0-based index of the quest
        round_index: Index of the round within the quest
        team: New team list

    Returns:
        Optional[GameState]: Updated game state, or None if indices are invalid
    """
    if not _validate_indices(state, quest_index, round_index):
        return None
        
    new_state = deepcopy(state)
    new_state['quests'][quest_index]['rounds'][round_index]['team'] = team
    return new_state

def update_approvals(state: GameState, quest_index: int, round_index: int, approvals: List[str]) -> Optional[GameState]:
    logger.debug(f'Updating approvals for quest {quest_index}, round {round_index}')
    logger.debug(f'Approval votes: {approvals}')
    logger.debug(f'Current state before update: {state}')
    
    if not _validate_indices(state, quest_index, round_index):
        logger.error(f'Invalid indices: quest={quest_index}, round={round_index}')
        return None
        
    new_state = deepcopy(state)
    new_state['quests'][quest_index]['rounds'][round_index]['approvals'] = approvals
    logger.debug(f'New state after updating approvals: {new_state}')
    return new_state

def update_fails(state: GameState, quest_index: int, round_index: int, fails: int) -> Optional[GameState]:
    logger.debug(f'Updating fails for quest {quest_index}, round {round_index}')
    logger.debug(f'Number of fails: {fails}')
    logger.debug(f'Current state before update: {state}')
    
    if not _validate_indices(state, quest_index, round_index):
        logger.error(f'Invalid indices: quest={quest_index}, round={round_index}')
        return None
        
    new_state = deepcopy(state)
    new_state['quests'][quest_index]['rounds'][round_index]['fails'] = fails
    logger.debug(f'New state after updating fails: {new_state}')
    return new_state

def get_current_quest(state: GameState) -> Optional[Quest]:
    """
    Gets the most recent quest

    Args:
        state: Current game state

    Returns:
        Optional[Quest]: The most recent quest, or None if no quests exist
    """
    if not state['quests']:
        return None
    return state['quests'][-1]

def get_current_round(state: GameState) -> Optional[Round]:
    """
    Gets the most recent round from the most recent quest

    Args:
        state: Current game state

    Returns:
        Optional[Round]: The most recent round, or None if no rounds exist
    """
    current_quest = get_current_quest(state)
    if not current_quest or not current_quest['rounds']:
        return None
    return current_quest['rounds'][-1]

def get_quest_result(state: GameState, quest_index: int) -> Optional[bool]:
    """
    Determines if a quest was successful

    Args:
        state: Current game state
        quest_index: 0-based index of the quest

    Returns:
        Optional[bool]: True if quest succeeded, False if failed, None if quest doesn't exist
                       or doesn't have a completed round
    """
    if quest_index < 0 or quest_index >= len(state['quests']):
        return None
        
    quest = state['quests'][quest_index]
    if not quest['rounds']:
        return None
        
    # Get the last round that was actually completed (has fails recorded)
    completed_rounds = [r for r in quest['rounds'] if r['fails'] >= 0]
    if not completed_rounds:
        return None
        
    last_round = completed_rounds[-1]
    return last_round['fails'] == 0

def _validate_indices(state: GameState, quest_index: int, round_index: int) -> bool:
    logger.debug(f'Validating indices: quest={quest_index}, round={round_index}')
    
    if quest_index < 0 or quest_index >= len(state['quests']):
        logger.error(f'Invalid quest index: {quest_index}')
        return False
    if round_index < 0 or round_index >= len(state['quests'][quest_index]['rounds']):
        logger.error(f'Invalid round index: {round_index}')
        return False
        
    logger.debug('Index validation successful')
    return True

# Helper functions for getting readable game state
def get_player_ids(state: GameState) -> List[int]:
    return [player['player_id'] for player in state['players']]

def get_quest(state: GameState, n: int) -> Quest:
    return state['quests'][n]

def get_round(quest: Quest, n: int) -> Round:
    return quest['rounds'][n]

def get_king(round: Round) -> str:
    return round['king']

def get_team(round: Round) -> List[str]:
    return round['team']

def get_approvals(round: Round) -> List[str]:
    return round['approvals']

def round_approved(state: GameState, round: Round) -> bool:
    return len(get_approvals(round)) > len(get_player_ids(state)) // 2

def get_failures(round: Round) -> int:
    return round['fails']


# Helper functions for 1-based quest numbers
def quest_index_to_number(index: int) -> int:
    """Converts 0-based index to 1-based quest number"""
    return index + 1

def quest_number_to_index(number: int) -> int:
    """Converts 1-based quest number to 0-based index"""
    return number - 1
