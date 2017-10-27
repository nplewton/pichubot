import melee
import globals
import Chains
from Chains.spotdodge import SpotDodge
from melee.enums import Character, Action, Button

# Dash dance a just a little outside our opponont's range
class Defend():
    chain = None

    def pickchain(self, chain, args=[]):
        if type(self.chain) != chain:
            self.chain = chain(*args)
        self.chain.step()

 #   def needsdefense():
 #       opponent_state = globals.opponent_state
 #       smashbot_state = globals.smashbot_state
 #       framedata = globals.framedata

    def step(self):
        opponent_state = globals.opponent_state
        smashbot_state = globals.smashbot_state
        framedata = globals.framedata

        hitframe = framedata.inrange(opponent_state, smashbot_state, globals.gamestate.stage)
        framesuntilhit = hitframe - opponent_state.action_frame

        # Is the attack a grab? If so, spot dodge right away
        if globals.framedata.isgrab(opponent_state.character, opponent_state.action):
            if framesuntilhit <= 2:
                self.pickchain(SpotDodge)
                return
