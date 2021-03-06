import melee
import globals
import Tactics
from Tactics.keepdistance import KeepDistance
from Tactics.punish import Punish
from Tactics.defend import Defend
from Tactics.retreat import Retreat
from Tactics.recover import Recover
from Tactics.pressure import Pressure
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

        if Recover.needsrecovery():
            self.picktactic(Recover)
            return

        if Defend.needsdefense():
            self.picktactic(Defend)
            return


        if Punish.canpunish():
            self.picktactic(Punish)
            return
        
        if Pressure.canpressure():
            self.picktactic(Pressure)
            return

        if Retreat.shouldretreat():
            self.picktactic(Retreat)
            return

        self.picktactic(KeepDistance)
