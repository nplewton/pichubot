import melee
import globals
import Tactics
from melee.enums import Action, Button

class Strategy:
    tactic = None

    def __init__(self):
        self.approach = False

    def picktactic(self, tactic, args=[]):
        print("This stupid function got called")
        if type(self.tactic) != tactic:
            self.tactic = tactic(*args)
        print("About to call the step")
        self.tactic.step()
        print("Called it in theory")

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

        self.picktactic(Tactics.KeepDistance)
