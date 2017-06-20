"""
routine:
1. collect blinds
2. shuffle deck
3. deal hands
   * while no one has folded
4. collect bets
5. (muck one) deal flop
6. collect bets
7. (muck one) deal turn
8. collect bets
9. (muck one) deal river
"""
import random
import ast

from django.db import models
from django.db.models import Model

from pokereval.card import Card
from pokereval.hand_evaluator import HandEvaluator

card_numbers = [
    "A",
    "K",
    "Q",
    "J",
    "T",
    "9",
    "8",
    "7",
    "6",
    "5",
    "4",
    "3",
    "2"
]

suits = [
    "C",
    "S",
    "H",
    "D"
]

suits_to_num = {
    "C": 4,
    "S": 1,
    "H": 2,
    "D": 3,
}

card_numbers_to_num = {
    "A": 14,
    "K": 13,
    "Q": 12,
    "J": 11,
    "T": 10,
    "9": 9,
    "8": 8,
    "7": 7,
    "6": 6,
    "5": 5,
    "4": 4,
    "3": 3,
    "2": 2,
}


def all_cards():
    deck = []
    for num in card_numbers:
        for suit in suits:
            deck.append(num + suit)
    return deck

def pop_card_off_deck(deck):
    card = deck.pop(random.randint(0, len(deck) - 1))
    return deck, card

def generate_cards():
    cards_in_play = []
    deck = all_cards()
    # generate hole cards
    for player in xrange(2):
        for _ in xrange(2):
            deck, card = pop_card_off_deck(deck)
            cards_in_play.append(card)
    # generate community cards
    for _ in xrange(5):
        deck, card = pop_card_off_deck(deck)
        cards_in_play.append(card)
    # ensure no duplicate cards
    assert sorted(list(set(cards_in_play))) == sorted(cards_in_play)
    return divide_cards(cards_in_play)

def divide_cards(cards_in_play):
    """
    Divide the generated cards to give easier return values.
    Will be used at the start of each hand.
    """
    cards = cards_in_play
    cards_on_board = cards[4:]
    player_one_hole_cards = cards[:2]
    player_two_hole_cards = cards[2:4]
    return cards, cards_on_board, player_one_hole_cards, player_two_hole_cards

def winning_hand(hand_one, hand_two, community_cards):
    """
    winning hand must have only five cards.
    winning hand can use 0 or more of their hole cards.

    """
    hand_one = ast.literal_eval(hand_one)
    hand_one =  [
        Card(card_numbers_to_num[hand_one[0][0]], suits_to_num[hand_one[0][1]]),
        Card(card_numbers_to_num[hand_one[1][0]], suits_to_num[hand_one[1][1]])
    ]
    hand_two = ast.literal_eval(hand_two)
    hand_two = [
        Card(card_numbers_to_num[hand_two[0][0]], suits_to_num[hand_two[0][1]]),
        Card(card_numbers_to_num[hand_two[1][0]], suits_to_num[hand_two[1][1]])
    ]
    community_cards = ast.literal_eval(community_cards)
    community_cards = [
        Card(card_numbers_to_num[community_cards[0][0]], suits_to_num[community_cards[0][1]]),
        Card(card_numbers_to_num[community_cards[1][0]], suits_to_num[community_cards[1][1]]),
        Card(card_numbers_to_num[community_cards[2][0]], suits_to_num[community_cards[2][1]]),
        Card(card_numbers_to_num[community_cards[3][0]], suits_to_num[community_cards[3][1]]),
        Card(card_numbers_to_num[community_cards[4][0]], suits_to_num[community_cards[4][1]])
    ]
    hand_one_score = HandEvaluator.evaluate_hand(hand_one, community_cards)
    hand_two_score = HandEvaluator.evaluate_hand(hand_two, community_cards)
    print hand_one_score
    print hand_two_score
    best_hand = ""
    if hand_one_score > hand_two_score:
        best_hand = "player_one"
    elif hand_one_score == hand_two_score:
        best_hand = "tie"
    else:
        best_hand = "player_two"
    return best_hand

class Player(Model):
    stack = models.PositiveIntegerField(null=True)
    wins = models.IntegerField(null=True)
    loses = models.IntegerField(null=True)
    hole_cards = models.CharField(max_length=1000, null=False)
    current_game = models.ForeignKey("Game")
    # used to determine if it's their turn to move.
    number = models.PositiveIntegerField(null=False)
    current_bet_size = models.PositiveIntegerField(null=True)

    def update_stack(self, amount, bet=True, _raise=True, win=False):
        """
        Updates the players stack if they
        win a hand or bet a certain amount.
        Defaults to bet unless win is True.
        """
        if bet or _raise:
            self.stack = self.stack - int(amount)
        if win:
            self.stack = self.stack + self.current_game.current_pot
        self.save()



class Game(Model):
    # list of all cards being played
    cards_used = models.CharField(max_length=1000, null=True)
    current_pot = models.IntegerField(null=True)
    big_blind = models.IntegerField(null=True)
    small_blind = models.IntegerField(null=True)
    ante = models.IntegerField(null=True)
    number_of_players = models.IntegerField(null=True)
    # player 1 or 2 has descision.
    players_turn = models.IntegerField(null=False)
    # historical game or current game
    archived = models.BooleanField(default=False)
    cards_on_board = models.CharField(max_length=1000, null=False)
    # 1 = preflop, 2 = postflop, 3 = turn, 4 = river
    phase_of_hand = models.PositiveIntegerField(null=True)
    # to keep track of what player 1 bet when it's player 2's turn
    last_bet_size = models.PositiveIntegerField(null=True)
    # is there a bet active?
    bet_active = models.BooleanField()

    def cards_shown_on_board(self):
        cards = ast.literal_eval(self.cards_on_board)
        cards_returned = []
        # preflop
        if self.phase_of_hand == 1:
            cards_returned = []
        # postflop
        elif self.phase_of_hand == 2:
            cards_returned = cards[0:3]
        # turn
        elif self.phase_of_hand == 3:
            cards_returned = cards[0:4]
        # river
        elif self.phase_of_hand == 4:
            cards_returned = cards
        return str(cards_returned)

    def phase_of_hand_str(self):
        phase = ""
        if self.phase_of_hand == 1:
            phase = "preflop"
        # postflop
        elif self.phase_of_hand == 2:
            phase = "postflop"
        # turn
        elif self.phase_of_hand == 3:
            phase = "turn"
        # river
        elif self.phase_of_hand == 4:
            phase = "river"
        return phase

    def update_players_turn(self):
        if self.players_turn == 1:
            self.players_turn = 2
        else:
            self.players_turn = 1
        self.save()

    def update_pot(self, bet_size):
        bet_size = int(bet_size)
        self.current_pot = self.current_pot + bet_size
        self.save()
        self.update_last_bet_size(bet_size)

    def update_last_bet_size(self, bet_size):
        self.last_bet_size = bet_size
        self.bet_active = True
        self.save()

    def update_phase_of_hand(self):
        if self.phase_of_hand == 4:
            self.phase_of_hand = 1
        else:
            self.phase_of_hand = self.phase_of_hand + 1
        self.bet_active = False
        self.save()

    def clear_pot(self):
        self.current_pot = 0
        self.save()

    def end_hand(self, winner_id):
        """
        give winner the pot
        clear pot
        start next hand with the correct player deciding first
        """
        pass
