import melee
import globals
import Tactics
import random
from melee.enums import Action, Button
from Strategies.strategy import Strategy
from Tactics.punish import Punish
from Tactics.pressure import Pressure
from Tactics.defend import Defend
from Tactics.recover import Recover
from Tactics.mitigate import Mitigate
from Tactics.edgeguard import Edgeguard
from Tactics.infinite import Infinite
from Tactics.celebrate import Celebrate
from Tactics.wait import Wait
from Tactics.retreat import Retreat

class Bait(Strategy):
    def __init__(self):
        self.approach = False

    def __str__(self):
        string = "Bait"

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

        # If we have stopped approaching, reset the state
        if type(self.tactic) != Tactics.Approach:
            self.approach = False

        if Mitigate.needsmitigation():
            self.picktactic(Tactics.Mitigate)
            return

        if self.tactic and not self.tactic.isinteruptible():
            self.tactic.step()
            return

        # If we're stuck in a lag state, just do nothing. Trying an action might just
        #   buffer an input we don't want
        if Wait.shouldwait():
            self.picktactic(Tactics.Wait)
            return

        if Recover.needsrecovery():
            self.picktactic(Tactics.Recover)
            return

        if Celebrate.deservescelebration():
            self.picktactic(Tactics.Celebrate)
            return

        # Difficulty 5 is a debug / training mode
        #   Don't do any attacks, and don't do any shielding
        #   Take attacks, DI, and recover
        if globals.difficulty == 5:
            self.picktactic(Tactics.KeepDistance)
            return

        if Defend.needsprojectiledefense():
            self.picktactic(Tactics.Defend)
            return

        # If we can infinite our opponent, do that!
        if Infinite.caninfinite():
            self.picktactic(Tactics.Infinite)
            return

        # If we can punish our opponent for a laggy move, let's do that
        if Punish.canpunish():
            self.picktactic(Tactics.Punish)
            return

        # Do we need to defend an attack?
        if Defend.needsdefense():
            self.picktactic(Tactics.Defend)
            return

        # Can we edge guard them?
        if Edgeguard.canedgeguard():
            self.picktactic(Tactics.Edgeguard)
            return

        # Can we shield pressure them?
        if Pressure.canpressure():
            self.picktactic(Tactics.Pressure)
            return

        if Retreat.shouldretreat():
            self.picktactic(Tactics.Retreat)
            return

        # Is opponent starting a jump?
        jumping = opponent_state.action == Action.KNEE_BEND
        if opponent_state.action in [Action.JUMPING_FORWARD, Action.JUMPING_BACKWARD] and \
                opponent_state.speed_y_self > 0:
            jumping = True

        # Randomly approach some times rather than keeping distance
        if smashbot_state.action == Action.TURNING and random.randint(0, 40) == 0:
            self.approach = True

        if (jumping and opponent_state.invulnerability_left <= 0) or self.approach:
            self.picktactic(Tactics.Approach)
            return

        self.picktactic(Tactics.KeepDistance)
