import melee
import globals
import Chains
import math
from melee.enums import Action, Button, Character
from Tactics.tactic import Tactic

class Defend(Tactic):
    def needsprojectiledefense():
        opponent_state = globals.opponent_state
        smashbot_state = globals.smashbot_state
        projectiles = globals.gamestate.projectiles

        if smashbot_state.invulnerability_left > 2:
            return False

        # Ignore Fox lasers. They 'just' do damage. Nothing we actually care about
        #   It's worse to put ourselves in stun just to prevent a few percent
        if opponent_state.character == Character.FOX:
            return False

        # Loop through each projectile
        for projectile in projectiles:
            if projectile.subtype == melee.enums.ProjectileSubtype.SAMUS_GRAPPLE_BEAM and opponent_state.on_ground:
                continue
            if projectile.subtype in [melee.enums.ProjectileSubtype.SHEIK_SMOKE, melee.enums.ProjectileSubtype.SHEIK_CHAIN ]:
                continue
            # Missles and needles that aren't moving are actually already exploded. Ignore them
            if projectile.subtype in [melee.enums.ProjectileSubtype.SAMUS_MISSLE, melee.enums.ProjectileSubtype.NEEDLE_THROWN, \
                    melee.enums.ProjectileSubtype.TURNIP] and (-0.01 < projectile.x_speed < 0.01):
                continue

            if projectile.subtype == melee.enums.ProjectileSubtype.SAMUS_BOMB and (-0.01 < projectile.y_speed < 0.01):
                continue

            size = 10
            if projectile.subtype == melee.enums.ProjectileSubtype.PIKACHU_THUNDERJOLT_1:
                size = 18
            if projectile.subtype == melee.enums.ProjectileSubtype.NEEDLE_THROWN:
                size = 12
            if projectile.subtype == melee.enums.ProjectileSubtype.PIKACHU_THUNDER:
                size = 20
            if projectile.subtype == melee.enums.ProjectileSubtype.TURNIP:
                size = 12
            # Your hitbox is super distorted when edge hanging. Give ourselves more leeway here
            if smashbot_state.action == Action.EDGE_HANGING:
                size *= 2

            # Is this about to hit us in the next frame?
            proj_x, proj_y = projectile.x, projectile.y
            for i in range(0, 1):
                proj_x += projectile.x_speed
                proj_y += projectile.y_speed
                smashbot_y = smashbot_state.y
                smashbot_x = smashbot_state.x + smashbot_state.speed_ground_x_self
                # This is a bit hacky, but it's easiest to move our "center" up a little for the math
                if smashbot_state.on_ground:
                    smashbot_y += 8
                distance = math.sqrt((proj_x - smashbot_x)**2 + (proj_y - smashbot_y)**2)
                if distance < size:
                    return True
        return False

    def needsdefense():
        # Is opponent attacking?
        opponent_state = globals.opponent_state
        smashbot_state = globals.smashbot_state
        framedata = globals.framedata

        if smashbot_state.invulnerability_left > 2:
            return False

        # Ignore the chain
        if opponent_state.character == Character.SHEIK and opponent_state.action == Action.SWORD_DANCE_2_HIGH:
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
        #If we can't interrupt the chain, just continue it
        if self.chain != None and not self.chain.interruptible:
            self.chain.step()
            return

        opponent_state = globals.opponent_state
        smashbot_state = globals.smashbot_state
        projectiles = globals.gamestate.projectiles
        framedata = globals.framedata

        # Do we need to defend against a projectile?
        #   If there is a projectile, just assume that's why we're here.
        #   TODO: maybe we should re-calculate if this is what we're defending
        if Defend.needsprojectiledefense():
            for projectile in projectiles:
                # Don't consider a grapple beam a projectile. It doesn't have a hitbox
                if projectile.subtype == melee.enums.ProjectileSubtype.SAMUS_GRAPPLE_BEAM:
                    continue
                if smashbot_state.action == Action.EDGE_HANGING:
                    if opponent_state.character == Character.PEACH and \
                            opponent_state.action in [Action.MARTH_COUNTER, Action.PARASOL_FALLING]:
                        #TODO: Make this a chain
                        self.chain = None
                        globals.controller.press_button(Button.BUTTON_L)
                        return
                    else:
                        self.chain = None
                        self.pickchain(Chains.DI, [0.5, 0.65])
                        return
                self.pickchain(Chains.Powershield)
                return

        hitframe = framedata.inrange(opponent_state, smashbot_state, globals.gamestate.stage)
        framesuntilhit = hitframe - opponent_state.action_frame

        # FireFox is different
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
            if opponent_state.character != Character.SAMUS or framesuntilhit <= 2:
                self.pickchain(Chains.SpotDodge)
                return

        if globals.logger:
            globals.logger.log("Notes", "framesuntilhit: " + str(framesuntilhit) + " ", concat=True)

        # Don't shine clank on the most optimal difficulty
        if globals.difficulty >= 2:
            # If the attack has exactly one hitbox, then try shine clanking to defend
            if framedata.hitboxcount(opponent_state.character, opponent_state.action) == 1:
                # It must be the first frame of the attack
                if hitframe == framedata.firsthitboxframe(opponent_state.character, opponent_state.action):
                    # Grounded attacks only
                    if opponent_state.on_ground:
                        if (framesuntilhit == 2 and smashbot_state.action == Action.DASHING) or \
                                (framesuntilhit == 1 and smashbot_state.action == Action.TURNING):
                            self.pickchain(Chains.Waveshine)
                            return

        onfront = (opponent_state.x < smashbot_state.x) == opponent_state.facing
        # Are we in the powershield window?
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
