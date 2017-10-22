import melee
import globals
import Tactics
from Tactics.keepdistance import KeepDistance
from melee.enums import Action, Button

class Strategy:
    tactic = None

    def __init__(self):
        self.approach = False

    def picktactic(self, tactic, args=[]):
        if type(self.tactic) != tactic:
            self.tactic = tactic()
        self.tactic.step()

    def __str__(self):
        string = "Strategy"

        if not self.tactic:
            return string
        string += str(type(self.tactic))

        if not self.tactic.chain:
            return string
        string += str(type(self.tactic.chain))
        return string

    def step(self):
        opponent_state = globals.opponent_state
        smashbot_state = globals.smashbot_state

        # This is where we will put all of the if statements to pick tactics

        self.picktactic(KeepDistance)
