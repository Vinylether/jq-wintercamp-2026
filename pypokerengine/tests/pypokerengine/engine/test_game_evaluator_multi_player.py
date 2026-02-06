from tests.base_unittest import BaseUnitTest
from mock import patch
from pypokerengine.engine.player import Player
from pypokerengine.engine.pay_info import PayInfo
from pypokerengine.engine.table import Table
from pypokerengine.engine.game_evaluator import GameEvaluator
from pypokerengine.engine.card import Card

class GameEvaluatorMultiPlayerTest(BaseUnitTest):

    def setUp(self):
        self.community_cards = [
            Card.from_str('ST'), Card.from_str('CT'),
            Card.from_str('DQ'), Card.from_str('SJ'),
            Card.from_str('SA')
        ]
         
        self.players = [
            self.__create_player_with_pay_info("A", 265, PayInfo.PAY_TILL_END, ['HK', 'H3']),
            self.__create_player_with_pay_info("B", 265, PayInfo.PAY_TILL_END, ['D9', 'HQ']),
            self.__create_player_with_pay_info("C", 265, PayInfo.PAY_TILL_END, ['H9', 'DK'])
        ]
         
        folded_players = [
            self.__create_player_with_pay_info("D", 0, PayInfo.FOLDED, ['C5', 'S6']),
            self.__create_player_with_pay_info("E", 15, PayInfo.FOLDED, ['S2', 'HA']),
            self.__create_player_with_pay_info("F", 0, PayInfo.FOLDED, ['SQ', 'D5']),
            self.__create_player_with_pay_info("G", 0, PayInfo.FOLDED, ['CK', 'S4'])
        ]
        
        self.players.extend(folded_players)

    def test_round_13_gameplay(self):
        """Test the complete gameplay of round 13 from the log"""
        table = self.__setup_table(self.players)
        for card in self.community_cards:
            table.add_community_card(card)
 
        winner, hand_info, prize_map = GameEvaluator.judge(table)
       
       
        self.eq(1, len(winner))
        winner_player = next(p for p in winner if p.name == "C")
        self.true(winner_player in winner)
 
 
        total_pot = sum(p.pay_info.amount for p in self.players)
        self.eq(total_pot, prize_map[self.players.index(winner_player)])
 
        active_players_count = len([p for p in self.players if p.pay_info.status != PayInfo.FOLDED])
        self.eq(3, active_players_count)

    def __setup_table(self, players):
        table = Table()
        for player in players:
            table.seats.sitdown(player)
        return table

    def __create_player_with_pay_info(self, name, amount, status, hole_cards=None):
        player = Player("uuid_" + name, 1000, name)
        player.pay_info.amount = amount
        player.pay_info.status = status
        if hole_cards:
            player.hole_card = [Card.from_str(c) for c in hole_cards]
        return player
