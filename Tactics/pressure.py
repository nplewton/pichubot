import melee
import globals
import Chains
import random
from melee.enums import Action, Button, Character
from Chains.smashattack import SMASH_DIRECTION
from Chains.shffl import Shffl
from Chains.smashattack import SmashAttack

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
        inrange = globals.gamestate.distance < 30

        return not sheilding and inrange

    def step(self):
        self.pickchain(SmashAttack, [0, SMASH_DIRECTION.UP])
        return

