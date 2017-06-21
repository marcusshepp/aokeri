import copy

from django.shortcuts import render
from django.http import JsonResponse

from main.models import (
    all_cards,
    generate_cards,
    Game,
    Player,
    players_from_game_id,
    winning_hand
)

def create_new_game(cards_used, cards_on_board):
    # create the game
    game_data = {}
    game_data["cards_used"] = str(cards_used)
    game_data["players_turn"] = 1
    game_data["number_of_players"] = 2
    game_data["ante"] = 10
    game_data["small_blind"] = 5
    game_data["big_blind"] = 10
    game_data["cards_on_board"] = str(cards_on_board)
    game_data["phase_of_hand"] = 1 # preflop
    game_data["current_pot"] = 0
    game_data["bet_active"] = False
    Game.objects.create(**game_data)

def create_new_player(stack, current_game, hole_cards, number):
    player_data = {}
    player_data["stack"] = stack
    player_data["current_game"] = current_game
    player_data["hole_cards"] = hole_cards
    player_data["number"] = number
    Player.objects.create(**player_data)

def latest_game():
    return Game.objects.latest("id")

def build_start_objects():
    """
    Use this function to build out a dictionary for the entire start of the game.
    Including creating the appropriate model objects.
    """
    cards, cards_on_board, player_one_hole_cards, player_two_hole_cards = generate_cards()
    create_new_game(cards, cards_on_board)
    game = latest_game()
    # player one
    create_new_player(
        1000,
        game,
        player_one_hole_cards,
        1
    )
    # player two
    create_new_player(
        1000,
        game,
        player_two_hole_cards,
        2
    )

def update_game(game_id,
                cards_used=None,
                current_pot=None,
                players_turn=None,
                archived=None,
                cards_on_board=None
                ):
    """ update the game with whatever field needed. """
    if game_id:
        game = Game.objects.filter(id=game_id)
        if game:
            game = game[0]
            if cards_used:
                game.cards_used = cards_used
            if current_pot:
                game.current_pot = current_pot
            if players_turn:
                game.players_turn = players_turn
            if archived:
                game.archived = archived
            if cards_on_board:
                game.cards_on_board = cards_on_board
            game.save()


def update_player(player_id,
                  stack=None,
                  wins=None,
                  loses=None,
                  hole_cards=None,
                  current_game=None,
                  number=None,
                  current_bet_size=None,
                  ):
    """ update the player with whatever field needed. """
    if player_id:
        player = Player.objects.filter(id=player_id)
        if player:
            if stack:
                if stack != player[0].stack:
                    player[0].stack = stack
            if wins:
                player[0].wins = wins
            if loses:
                player[0].loses = loses
            if hole_cards:
                player[0].hole_cards = hole_cards
            if current_game:
                player[0].current_game = current_game
            if number:
                player[0].number = number
            if current_bet_size:
                player[0].current_bet_size = current_bet_size
            player[0].save()

def start_hand(game_id):
    """
    To be called at the beginning of each hand.
    deal the cards
    update the objects.
    """
    cards, cards_on_board, player_one_hole_cards, player_two_hole_cards = generate_cards()
    game = Game.objects.filter(id=game_id)
    # update cards on board
    if game:
        game = game[0]
        game.cards_on_board = cards_on_board
        game.save()
        # update players hole cards
        players = Player.objects.filter(current_game__id=game.id)
        if players:
            player_one = [ player for player in players if player.number == 1 ]
            if player_one:
                player_one = player_one[0]
                player_one.hole_cards = player_one_hole_cards
                player_one.save()
            player_two = [ player for player in players if player.number == 2 ]
            if player_two:
                player_two = player_two[0]
                player_two.hole_cards = player_two_hole_cards
                player_two.save()

def take_ante(player_id, game_id):
    """ take the ante out of the players stack at the beginning of a hand. """
    player = Player.objects.filter(id=player_id)
    if player:
        game = Game.objects.filter(id=game_id)
        if game:
            stack = player[0].stack - game.ante
            update_player(player_id=player_id, stack=stack)

def deal_next_hand(game_id):
    """ Action to be called at the end of each hand. """
    pass

def start(r, *a, **kw):
    """
    Starts a game of Aokeri.
    :returns:
    type JSON
    - number_of_players
    - game state
    """
    build_start_objects()
    # build json that describes the context of the game being played.
    # this could list the available end points for playing the game.
    data = {}
    game = latest_game()
    data["game_id"] = game.id
    data["number_of_players"] = game.number_of_players
    data["players_turn"] = game.players_turn
    players = Player.objects.filter(current_game__id=game.id)
    if players:
        data["player_one_id"] = [player
            for player in players
            if player.number == 1][0].id
        data["player_two_id"] = [player
            for player in players
            if player.number == 2][0].id
    return JsonResponse(data)

def players_game_info(r, *a, **kw):
    """
    Endpoint for game info specific to a player.
    Get the player
    Get the game
    respond with
    game:
        - player id
        - game id
        - hole cards
        - community_cards
        - stack
        - ante
        - is ur turn
        - last bet size
        - phase of hand
        - bet active
    """
    player_id = r.GET.get("player_id")
    game_id = r.GET.get("game_id")
    data = {}
    # player id and game id in the get params
    if player_id and game_id:
        # grab player object if exists
        player_obj = Player.objects.filter(id=player_id)
        if player_obj:
            player_obj = player_obj[0]
            data["player_id"] = player_obj.id
            data["player_number"] = player_obj.number
            data["hole_cards"] = player_obj.hole_cards
            data["stack"] = player_obj.stack
        # grab game object if exists
        game = Game.objects.filter(id=game_id)
        if game:
            game = game[0]
            data["game_id"] = game_id
            data["ante"] = game.ante
            data["is_your_turn"] = player_obj.number == game.players_turn
            data["community_cards"] = game.cards_shown_on_board()
            data["last_bet_size"] = game.last_bet_size
            data["pot_size"] = game.current_pot
            data["phase_of_hand"] = game.phase_of_hand_str()
            data["bet_active"] = game.bet_active
            players = Player.objects.filter(current_game__id=game.id)
            opponent = [ player for player in players if player.id != player_obj.id ][0]
            data["opponents_stack"] = opponent.stack
    if not game_id:
        data['no_game_id'] = True
    if not player_id:
        data['no_player_id'] = True
    return JsonResponse(data)

def game_from_game_id(game_id):
    if game_id:
        game = Game.objects.filter(id=game_id)
        if game:
            game = game[0]
            return game

def player_from_player_id(player_id):
    if player_id:
        player = Player.objects.filter(id=player_id)
        if player:
            player = player[0]
            return player

def is_players_turn(game, player):
    """ Returns true or false, accepts player and game objects. """
    if game:
        players_turn = game.players_turn
        if player:
            number = player.number
            is_thier_turn = False
            if number == players_turn:
                is_thier_turn = True
            return is_thier_turn

def not_your_turn():
    return JsonResponse( { "not_your_turn": True } )



"""
The following endpoints take the following parameters.
player_id=1
raise_amount=200
bet_size=50
"""

def call(r, *a, **kw):
    """
    An endpoint for the `call` action.
    Will trigger `end of phase`
    """
    player_id = r.GET.get("player_id")
    player = player_from_player_id(player_id)
    game_id = r.GET.get("game_id")
    game = game_from_game_id(game_id)
    data = {}
    if is_players_turn(game, player):
        if game:
            if game.bet_active:
                if player:
                    last_bet_size = game.last_bet_size
                    player.update_stack(amount=last_bet_size)
                    game.update_pot(last_bet_size)
                    game.update_players_turn()
                    if game.phase_of_hand_str() == "river":
                        player_one, player_two = players_from_game_id(game.id)
                        winner = winning_hand(
                            player_one.hole_cards,
                            player_two.hole_cards,
                            game.cards_on_board
                        )
                        data["winner"] = winner
                        data["player_one_hole_cards"] = player_one.hole_cards
                        data["player_two_hole_cards"] = player_two.hole_cards
                        data["community_cards"] = game.cards_on_board
                        if winner == "player_one":
                            player_one.update_stack(win=True)
                            game.end_hand(winner_id=player_one.id)
                            data["winner_of_hand"] = "player_one"
                        if winner == "player_two":
                            player_two.update_stack(win=True)
                            game.end_hand(winner_id=player_two.id)
                            data["winner_of_hand"] = "player_two"
                        data["end_hand"] = True
                        game.update_phase_of_hand(end=True)
                    else:
                        data["new_stack_size"] = player.stack
                        game.update_phase_of_hand()
                        data["new_pot_size"] = game.current_pot
                else:
                    data['no_player_id'] = True
            else:
                data["no_bet_to_call"] = True
        else:
            data['no_game_id'] = True
    else:
        data["not_your_turn"] = True
    data["call"] = True
    return JsonResponse(data)

def fold(r, *a, **kw):
    """
    An endpoint for the `fold` action.
    Will trigger `end of phase`
    end hand
    change players turn
    update pot to zero
    declare a winner
    update players stack
    """
    player_id = r.GET.get("player_id")
    player_id = int(player_id)
    player = player_from_player_id(player_id)
    game_id = r.GET.get("game_id")
    game = game_from_game_id(game_id)
    data = {}
    if is_players_turn(game, player):
        if player:
            if game:
                if game.bet_active:
                    players = players_from_game_id(game.id)
                    if players:
                        player_one, player_two = players
                        folder = None
                        winner_id = None
                        if player_one.id == player_id:
                            folder = player_one
                            winner_id = player_two.id
                            data["winner_of_hand"] = "player_two"
                        elif player_two.id == player_id:
                            folder = player_two
                            winner_id = player_one.id
                            data["winner_of_hand"] = "player_one"
                        if folder:
                            game.update_players_turn()
                            game.update_phase_of_hand(end=True)
                            game.end_hand(winner_id=winner_id)
                            data["end_hand"] = True
                else:
                    data["no_bet_active"] = True
            else:
                data["no_game_id"] = True
        else:
            data["no_player_id"] = True
    else:
        data["not_your_turn"] = True
    data["fold"] = True
    return JsonResponse(data)

def bet(r, *a, **kw):
    """
    An endpoint for the `bet` action.
    params:
    player_id
    game_id
    bet_size
    """
    player_id = r.GET.get("player_id")
    player = player_from_player_id(player_id)
    game_id = r.GET.get("game_id")
    game = game_from_game_id(game_id)
    data = {}
    if is_players_turn(game, player):
        if player:
            if game:
                bet_size = r.GET.get("bet_size")
                if bet_size:
                    game.update_pot(bet_size)
                    data["bet"] = True
                    data["new_pot_size"] = game.current_pot
                    data["bet_size"] = bet_size
                    player.update_stack(amount=bet_size)
                    data["new_stack_size"] = player.stack
                    game.update_players_turn()
                else:
                    data["no_bet_size"] = True
            else:
                data["no_game_id"] = True
        else:
            data["no_player_id"] = True
    else:
        data["not_your_turn"] = True
    return JsonResponse(data)

def _raise(r, *a, **kw):
    """
    An endpoint for the `raise` action.
    take from player stack
    add to pot_size
    update players turn
    """
    player_id = r.GET.get("player_id")
    player = player_from_player_id(player_id)
    game_id = r.GET.get("game_id")
    game = game_from_game_id(game_id)
    data = {}
    if is_players_turn(game, player):
        if game:
            if player:
                raise_amount = r.GET.get("raise_amount")
                data["raise_amount"] = raise_amount
                # take from player stack
                player.update_stack(amount=raise_amount)
                # add raise amount to pot_size
                game.update_pot(raise_amount)
                data["new_pot_size"] = game.current_pot
                # update who's turn it is
                game.update_players_turn()
            else:
                data["no_player_id"] = True
        else:
            data["no_game_id"] = True
    else:
        data["not_your_turn"] = True
    data["raise"] = True
    return JsonResponse(data)

def check(r, *a, **kw):
    data = {}
    player_id = r.GET.get("player_id")
    player = player_from_player_id(player_id)
    game_id = r.GET.get("game_id")
    game = game_from_game_id(game_id)
    if game:
        if player:
            if is_players_turn(game, player):
                data["check"] = True
                if game.phase_of_hand_str == "river":
                    player_one, player_two = players_from_game_id(game.id)
                    winner = winning_hand(
                        player_one.hole_cards,
                        player_two.hole_cards,
                        game.cards_on_board
                    )
                    data["winner"] = winner
                    data["player_one_hole_cards"] = player_one.hole_cards
                    data["player_two_hole_cards"] = player_two.hole_cards
                    data["community_cards"] = game.cards_on_board
                    if winner == "player_one":
                        player_one.update_stack(win=True)
                    if winner == "player_two":
                        player_two.update_stack(win=True)
                    game.end_hand()
                else:
                    game.update_phase_of_hand()
            else:
                data["not_your_turn"] = True
        else:
            data["no_player_id"] = True
    else:
        data["no_game_id"] = True
    JsonResponse(data)

def bar(r, *a, **kw):
    game = Game.objects.get(id=2)
    game.phase_of_hand = 4
    game.save()
    players = Player.objects.filter(current_game__id=2)
    print players[0].hole_cards
    print players[1].hole_cards
    print game.cards_on_board
    winner = winning_hand(players[0].hole_cards, players[1].hole_cards, game.cards_on_board)
    return JsonResponse({
        "hand_one": players[0].hole_cards,
        "hand_two": players[1].hole_cards,
        "winner": winner,
        "community_cards": game.cards_on_board
    })
