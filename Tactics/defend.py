import melee
import globals
import Chains
from Chains.spotdodge import SpotDodge
from Chains.dashdance import DashDance
from Chains.powershield import Powershield
from melee.enums import Character, Action, Button

# Dash dance a just a little outside our opponont's range
class Defend():
    chain = None

    def pickchain(self, chain, args=[]):
        if type(self.chain) != chain:
            self.chain = chain(*args)
        self.chain.step()

    def needsdefense():
        # Is opponent attacking?
        opponent_state = globals.opponent_state
        smashbot_state = globals.smashbot_state
        framedata = globals.framedata

        if smashbot_state.invulnerability_left > 2:
            return False

        # FireFox is different
        firefox = opponent_state.action in [Action.SWORD_DANCE_4_HIGH, Action.SWORD_DANCE_4_MID] and opponent_state.character in [Character.FOX, Character.FALCO]
        if firefox:
            # Assume they're heading at us, shield in time
            speed = 2.2
            if opponent_state.character == Character.FOX:
                speed = 3.8
            if (globals.gamestate.distance - 12) / speed < 3:
                return True

        # What state of the attack is the opponent in?
        # Windup / Attacking / Cooldown / Not Attacking
        attackstate = framedata.attackstate_simple(opponent_state)
        if attackstate == melee.enums.AttackState.COOLDOWN:
            return False
        if attackstate == melee.enums.AttackState.NOT_ATTACKING:
            return False

        # We can't be grabbed while on the edge
        if globals.framedata.isgrab(opponent_state.character, opponent_state.action) and \
                smashbot_state.action in [Action.EDGE_HANGING, Action.EDGE_CATCHING]:
            return False

        # Will we be hit by this attack if we stand still?
        hitframe = framedata.inrange(opponent_state, smashbot_state, globals.gamestate.stage)
        # Only defend on the edge if the hit is about to get us
        if smashbot_state.action in [Action.EDGE_HANGING, Action.EDGE_CATCHING] and hitframe > 2:
            return False
        if hitframe:
            return True

        return False

    def step(self):
        opponent_state = globals.opponent_state
        smashbot_state = globals.smashbot_state
        framedata = globals.framedata

        hitframe = framedata.inrange(opponent_state, smashbot_state, globals.gamestate.stage)
        framesuntilhit = hitframe - opponent_state.action_frame

        firefox = opponent_state.action in [Action.SWORD_DANCE_4_HIGH, Action.SWORD_DANCE_4_MID] and opponent_state.character in [Character.FOX, Character.FALCO]

        if firefox:
            # Assume they're heading at us, shield in time
            speed = 2.2
            if opponent_state.character == Character.FOX:
                speed = 3.8
            if (globals.gamestate.distance - 12) / speed < 3:
                framesuntilhit = 0

        # Is the attack a grab? If so, spot dodge right away
        if globals.framedata.isgrab(opponent_state.character, opponent_state.action):
            if framesuntilhit <= 2:
                self.pickchain(SpotDodge)
                return

        if framesuntilhit <= 2:
            if smashbot_state.action == Action.EDGE_HANGING:
                self.chain = None
                self.pickchain(Chains.DI, [0.5, 0.65])
                return
            hold = framedata.hitboxcount(opponent_state.character, opponent_state.action) > 1
            self.pickchain(Chains.Powershield, [hold])
        else:
            # 12 starting buffer for Fox's character model size
            bufferzone = 12
            if onfront:
                bufferzone += framedata.getrange_forward(opponent_state.character, opponent_state.action, opponent_state.action_frame)
            else:
                bufferzone += framedata.getrange_backward(opponent_state.character, opponent_state.action, opponent_state.action_frame)

            pivotpoint = opponent_state.x
            # Dash to a point away from the opponent, out of range
            if opponent_state.x < smashbot_state.x:
                # Dash right
                pivotpoint += bufferzone
                # But don't run off the edge
                pivotpoint = min(melee.stages.edgegroundposition(globals.gamestate.stage)-5, pivotpoint)
            else:
                # Dash Left
                pivotpoint -= bufferzone
                # But don't run off the edge
                pivotpoint = max(-melee.stages.edgegroundposition(globals.gamestate.stage) + 5, pivotpoint)
            self.pickchain(Chains.DashDance, [pivotpoint])
