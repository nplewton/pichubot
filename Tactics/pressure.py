import melee
import globals
import Chains
import random
from melee.enums import Action, Button, Character
from Chains.smashattack import SMASH_DIRECTION
from Chains.shffl import Shffl
from Chains.smashattack import SmashAttack
from Chains.dashdance import DashDance

class Pressure():
    chain = None

    def pickchain(self, chain, args=[]):
        if type(self.chain) != chain:
            self.chain = chain(*args)
        self.chain.step()

    def canpressure():
        # Opponent must be shielding
        shieldactions = [Action.SHIELD_START, Action.SHIELD, \
            Action.SHIELD_STUN, Action.SHIELD_REFLECT]
        sheilding = globals.opponent_state.action in shieldactions

        if globals.opponent_state.invulnerability_left > 0:
            return False

        # We must be in close range
        inrange = globals.gamestate.distance < 25

        return not sheilding and inrange

    def step(self):
        smashbot_state = globals.smashbot_state
        opponent_state = globals.opponent_state
        smashbot_position = smashbot_state.x
        opponent_position = opponent_state.x
        facing = smashbot_state.facing == (smashbot_position < opponent_position)
        # Remember that if we're turning, the attack will come out the opposite way
        if smashbot_state.action == Action.TURNING:
            facing = not facing
        if facing:
            # Do the upsmash
            self.pickchain(SmashAttack, [0, SMASH_DIRECTION.UP])
            return
        else:
            # Kill the existing chain and start a new one
            self.chain = None
            self.pickchain(DashDance, [opponent_position])
        return

