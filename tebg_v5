import pygame, sys, math, random, os, json, copy

pygame.init()
pygame.font.init()

# ──────────────────────────────────────────────────────────
#  Screen / FPS / Icon
# ──────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1200, 720
FPS           = 60
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE     = os.path.join(BASE_DIR, "hero_skills.json")   # skill builder auto-save

for _p in (os.path.join('internal', 'icon.ico'), os.path.join(BASE_DIR, 'internal', 'icon.ico')):
    try:
        if os.path.exists(_p):
            pygame.display.set_icon(pygame.image.load(_p))
            break
    except Exception as e:
        print(f"Could not load icon: {e}")

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Epic Battlegrounds (v5)")
clock  = pygame.time.Clock()
world  = pygame.Surface((WIDTH, HEIGHT))      # everything is drawn here first (so the screen can shake)

# ──────────────────────────────────────────────────────────
#  Fonts
# ──────────────────────────────────────────────────────────
F_XS  = pygame.font.SysFont("consolas", 13, bold=True)
F_SM  = pygame.font.SysFont("consolas", 15, bold=True)
F_MD  = pygame.font.SysFont("consolas", 20, bold=True)
F_LG  = pygame.font.SysFont("consolas", 30, bold=True)
F_XL  = pygame.font.SysFont("consolas", 80, bold=True)
F_TTL = pygame.font.SysFont("consolas", 22, bold=True)

# ──────────────────────────────────────────────────────────
#  Arena geometry / constants
# ──────────────────────────────────────────────────────────
AL, AR, AT, AB = 55, WIDTH-55, 55, HEIGHT-115
AW, AH = AR-AL, AB-AT

PLAYER_SIZE  = 40
DUMMY_SIZE   = 44
PLAYER_SPEED = 230
CUSTOM_CD    = 1.5      # cooldown of custom skills (seconds)

# Skill 2 – Consecutive Punches
CONS_HITS      = 20     # how many punches
CONS_TOTAL_DMG = 15     # TOTAL hp taken by all 20 punches together (change to 15*20 if you want 15 PER punch)
CONS_INTERVAL  = 0.06   # seconds between punches
CONS_RANGE     = 190    # enemy must be this close for punches to land
CONS_CD        = 3.0    # cooldown

# Skill 3 – Shove
SHOVE_DMG   = 13.5      # damage of the single shove
SHOVE_RANGE = 110       # enemy must be this close (centre to centre)
SHOVE_FORCE = 900       # how hard he gets pushed back
SHOVE_CD    = 2.0       # cooldown
CLOSE_RANGE  = 120      # closer than this (centre to centre) = "close"  → Normal Punch variant 2
FACE_REACH   = 130      # reach of the "Face Punch" skill-builder block

# Skill 4 - Uppercut
UPPER_DMG    = 15       # damage of the uppercut
UPPER_RANGE  = 120      # enemy must be this close (centre to centre)
UPPER_FORCE  = 900      # launch speed upwards (higher = flies higher / stays in the air longer)
UPPER_CD     = 2.5      # cooldown
GRAVITY      = 1500     # how fast the dummy falls back down after being sent in the air

# R - Serious Mode
SERIOUS_TIME = 10.0     # seconds the buff lasts
SERIOUS_PCT  = 15       # +% damage while serious

DIRT = [(120,105,90), (90,80,70), (160,150,135), (60,52,46)]


def unit(dx, dy):
    d = math.hypot(dx, dy) or 1.0
    return dx/d, dy/d, d


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ══════════════════════════════════════════════════════════
#  PARTICLE
# ══════════════════════════════════════════════════════════
class Particle:
    __slots__ = ("x","y","vx","vy","color","radius","life","max_life","fade","grav","alive","shape")
    def __init__(self, x, y, vx, vy, color, radius, life, fade=True, grav=0, shape="circle"):
        self.x, self.y   = x, y
        self.vx, self.vy = vx, vy
        self.color, self.radius = color, radius
        self.life = self.max_life = life
        self.fade, self.grav, self.shape = fade, grav, shape
        self.alive = True

    def update(self, dt):
        self.x += self.vx*dt
        self.y += self.vy*dt
        self.vy += self.grav*dt
        self.life -= dt
        if self.life <= 0: self.alive = False

    def draw(self, surf):
        if not self.alive: return
        t = max(0.0, self.life/self.max_life)
        a = int(255*t) if self.fade else 255
        r = max(1, int(self.radius*t))
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        if self.shape == "circle": pygame.draw.circle(s, (*self.color[:3], a), (r, r), r)
        else:                      pygame.draw.rect(s, (*self.color[:3], a), (0, 0, r*2, r*2))
        surf.blit(s, (int(self.x)-r, int(self.y)-r))


def burst(cx, cy, count, colors, rmin=3, rmax=9, smin=40, smax=300, lmin=0.3, lmax=1.0, grav=0, shape="circle"):
    out = []
    for _ in range(count):
        a  = random.uniform(0, math.tau)
        sp = random.uniform(smin, smax)
        out.append(Particle(cx, cy, math.cos(a)*sp, math.sin(a)*sp, random.choice(colors),
                            random.randint(rmin, rmax), random.uniform(lmin, lmax), True, grav, shape))
    return out


class _Fist:
    def __init__(self, x, y, dx, dy, col):
        self.x, self.y, self.dx, self.dy, self.col = x, y, dx, dy, col
        self.life = self.max_life = 0.14
        self.alive = True
        self.w, self.h = 20, 13

    def update(self, dt):
        self.x += self.dx*dt*400
        self.y += self.dy*dt*400
        self.life -= dt
        if self.life <= 0: self.alive = False

    def draw(self, surf):
        if not self.alive: return
        a = int(255*(self.life/self.max_life))
        s = pygame.Surface((self.w+10, self.h+10), pygame.SRCALPHA)
        pygame.draw.rect(s, (*self.col[:3], a//2), (0, 0, self.w+10, self.h+10), border_radius=4)
        pygame.draw.rect(s, (*self.col[:3], a),    (5, 5, self.w, self.h),       border_radius=3)
        surf.blit(s, (int(self.x)-self.w//2, int(self.y)-self.h//2))


# ══════════════════════════════════════════════════════════
#  CRATERS, CRATER LINES & GLOBAL EFFECTS
# ══════════════════════════════════════════════════════════
class Crater:
    """A cracked pit in the floor. Pre-rendered once, fades away after a while."""
    def __init__(self, x, y, size):
        self.x, self.y, self.size = x, y, size
        self.life = self.max_life = 12.0
        s = int(size*3.2) + 20
        self.surf = pygame.Surface((s, s), pygame.SRCALPHA)
        c = s//2
        for _ in range(random.randint(6, 10)):                       # cracks
            a = random.uniform(0, math.tau)
            L = size*random.uniform(0.9, 1.5)
            pts = [(c, c)]
            for k in range(1, 4):
                aa = a + random.uniform(-0.25, 0.25)
                pts.append((c + math.cos(aa)*L*k/3, c + math.sin(aa)*L*k/3))
            pygame.draw.lines(self.surf, (15,12,10,235), False, pts, random.randint(2, 4))
        n = 14
        pit = []
        for k in range(n):
            a = k*math.tau/n
            r = size*0.62*random.uniform(0.8, 1.15)
            pit.append((c + math.cos(a)*r, c + math.sin(a)*r))
        rim   = [(c+(x_-c)*1.18, c+(y_-c)*1.18) for x_, y_ in pit]
        inner = [(c+(x_-c)*0.55, c+(y_-c)*0.55) for x_, y_ in pit]
        pygame.draw.polygon(self.surf, (150,140,128,230), rim)
        pygame.draw.polygon(self.surf, (45,38,34,250), pit)
        pygame.draw.polygon(self.surf, (18,14,12,255), inner)

    def update(self, dt):
        self.life -= dt

    def draw(self, surf):
        a = 255 if self.life > 2.0 else int(255*max(0.0, self.life/2.0))
        self.surf.set_alpha(a)
        surf.blit(self.surf, (int(self.x) - self.surf.get_width()//2, int(self.y) - self.surf.get_height()//2))


class CraterLine:
    """Ground crack that races away from the fist. Touching it ONCE = damage + roll back."""
    SPEED = 2000.0
    def __init__(self, x, y, dx, dy, length, damage, roll_force):
        self.ox, self.oy, self.dx, self.dy = x, y, dx, dy
        self.length, self.damage, self.roll_force = length, damage, roll_force
        self.head = 0.0
        self.hit  = False
        self.life = self.max_life = 7.0
        self.pts  = []
        for i in range(int(length/16) + 2):
            d = min(length, i*16)
            j = random.uniform(-5, 5) if i > 0 else 0
            self.pts.append((d, x + dx*d - dy*j, y + dy*d + dx*j))

    def update(self, dt, dummy):
        self.life -= dt
        if self.head < self.length:
            self.head = min(self.length, self.head + self.SPEED*dt)
            hx, hy = self.ox + self.dx*self.head, self.oy + self.dy*self.head
            for _ in range(2):
                fx.particles.append(Particle(hx + random.uniform(-6,6), hy + random.uniform(-6,6),
                    random.uniform(-90,90), random.uniform(-190,-40), random.choice(DIRT),
                    random.randint(2,5), random.uniform(0.3,0.6), True, 520, "rect"))
        if not self.hit and dummy.alive and self.head > 0 and dummy.z < 40:
            t  = clamp((dummy.cx-self.ox)*self.dx + (dummy.cy-self.oy)*self.dy, 0, self.head)
            px, py = self.ox + self.dx*t, self.oy + self.dy*t
            if math.hypot(dummy.cx-px, dummy.cy-py) <= DUMMY_SIZE*0.5 + 8:
                self.hit = True
                dummy.take_damage(self.damage)
                dummy.launch(self.dx, self.dy, self.roll_force, spin=3.0, friction=3.0)   # rolls back
                fx.add_crater(dummy.cx, dummy.cy, 36)
                fx.add_ring(dummy.cx, dummy.cy, 80, 0.3, (255,255,255), 3)
                fx.particles += burst(dummy.cx, dummy.cy, 16, DIRT, 3, 7, 80, 300, 0.3, 0.7, 400, "rect")
                fx.shake(5, 0.15)

    def draw(self, layer):
        a = 255 if self.life > 1.5 else int(255*max(0.0, self.life/1.5))
        vis = [(x, y) for d, x, y in self.pts if d <= self.head]
        if len(vis) >= 2:
            pygame.draw.lines(layer, (150,140,128,a), False, vis, 11)
            pygame.draw.lines(layer, (34,28,25,a),   False, vis, 7)
            pygame.draw.lines(layer, (0,0,0,a),      False, vis, 3)
            for d, x, y in self.pts[::5]:                                 # little pits along the crack
                if d <= self.head and d > 0:
                    pygame.draw.circle(layer, (28,22,20,a), (int(x), int(y)), 9)
                    pygame.draw.circle(layer, (110,100,90,a), (int(x), int(y)), 9, 2)
        if self.head < self.length:
            hx, hy = self.ox + self.dx*self.head, self.oy + self.dy*self.head
            pygame.draw.circle(layer, (255,210,130,210), (int(hx), int(hy)), 12)
            pygame.draw.circle(layer, (255,255,255,230), (int(hx), int(hy)), 6)


class Projectile:
    """Energy blast flying toward the enemy (Skill Builder block 'Energy Blast')."""
    def __init__(self, x, y, dx, dy, speed, damage, col):
        self.x, self.y, self.dx, self.dy = x, y, dx, dy
        self.speed, self.damage, self.col = speed, damage, col
        self.alive = True
        self.life = 3.0

    def update(self, dt, dummy):
        self.x += self.dx*self.speed*dt
        self.y += self.dy*self.speed*dt
        self.life -= dt
        fx.particles.append(Particle(self.x, self.y, random.uniform(-40,40), random.uniform(-40,40),
                                     self.col, random.randint(4,8), 0.25, True))
        if self.life <= 0 or not (AL-40 < self.x < AR+40 and AT-40 < self.y < AB+40):
            self.alive = False
            return
        if dummy.alive and math.hypot(dummy.cx - self.x, dummy.cy - self.y) <= DUMMY_SIZE*0.5 + 12:
            self.alive = False
            dummy.take_damage(self.damage)
            dummy.launch(self.dx, self.dy, 600, spin=1.5, friction=2.5)
            fx.add_ring(self.x, self.y, 90, 0.3, self.col, 5)
            fx.particles += burst(self.x, self.y, 18, [self.col, (255,255,255)], 3, 8, 80, 340, 0.3, 0.7)
            fx.shake(7, 0.2)

    def draw(self, surf):
        s = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.col[:3], 90), (30, 30), 24)
        pygame.draw.circle(s, (*self.col[:3], 220), (30, 30), 14)
        pygame.draw.circle(s, (255,255,255,255), (30, 30), 7)
        surf.blit(s, (int(self.x) - 30, int(self.y) - 30))


class FX:
    def __init__(self):
        self.craters, self.lines, self.rings = [], [], []
        self.particles, self.fists, self.texts = [], [], []
        self.projectiles = []
        self.shake_t = 0.0; self.shake_dur = 0.01; self.shake_p = 0.0
        self.flash_t = 0.0; self.flash_dur = 0.01; self.flash_col = (255,255,255)
        self.layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    def clear(self):
        self.craters.clear(); self.lines.clear(); self.rings.clear()
        self.particles.clear(); self.fists.clear(); self.texts.clear(); self.projectiles.clear()

    def add_crater(self, x, y, size):
        self.craters.append(Crater(x, y, size))
        if len(self.craters) > 60: self.craters.pop(0)

    def add_ring(self, x, y, maxr, dur, col, width=4):
        self.rings.append([x, y, maxr, dur, dur, col, width])

    def add_text(self, x, y, text, col=(255,255,255), big=False):
        self.texts.append([x, y, text, col, 1.1, 1.1, big])

    def shake(self, power, dur):
        cur = self.shake_p*(self.shake_t/self.shake_dur) if self.shake_t > 0 else 0
        if power >= cur:
            self.shake_p, self.shake_t, self.shake_dur = power, dur, dur

    def flash(self, col, dur):
        self.flash_col, self.flash_t, self.flash_dur = col, dur, dur

    def shake_offset(self):
        if self.shake_t <= 0: return (0, 0)
        m = self.shake_p*self.shake_t/self.shake_dur
        return (int(random.uniform(-m, m)), int(random.uniform(-m, m)))

    def update(self, dt, dummy):
        if self.shake_t > 0: self.shake_t -= dt
        if self.flash_t > 0: self.flash_t -= dt
        for c in self.craters[:]:
            c.update(dt)
            if c.life <= 0: self.craters.remove(c)
        for l in self.lines[:]:
            l.update(dt, dummy)
            if l.life <= 0: self.lines.remove(l)
        for r in self.rings[:]:
            r[4] -= dt
            if r[4] <= 0: self.rings.remove(r)
        for pr in self.projectiles[:]:
            pr.update(dt, dummy)
            if not pr.alive: self.projectiles.remove(pr)
        for group in (self.particles, self.fists):
            for p in group[:]:
                p.update(dt)
                if not p.alive: group.remove(p)
        for t in self.texts[:]:
            t[1] -= 38*dt
            t[4] -= dt
            if t[4] <= 0: self.texts.remove(t)

    def draw_under(self, surf):
        for c in self.craters: c.draw(surf)
        if self.lines:
            self.layer.fill((0,0,0,0))
            for l in self.lines: l.draw(self.layer)
            surf.blit(self.layer, (0,0))

    def draw_over(self, surf):
        for f in self.fists: f.draw(surf)
        for pr in self.projectiles: pr.draw(surf)
        for p in self.particles: p.draw(surf)
        if self.rings:
            self.layer.fill((0,0,0,0))
            for x, y, maxr, dur, left, col, w in self.rings:
                t = 1 - left/dur
                r = int(maxr*(1 - (1-t)**2))
                if r > 1:
                    pygame.draw.circle(self.layer, (*col[:3], int(230*(1-t))), (int(x), int(y)), r, max(1, int(w*(1-t)) + 1))
            surf.blit(self.layer, (0,0))
        for x, y, text, col, life, mx, big in self.texts:
            img = (F_LG if big else F_MD).render(text, True, col)
            sh  = (F_LG if big else F_MD).render(text, True, (0,0,0))
            a = int(255*clamp(life/mx*1.6, 0, 1))
            img.set_alpha(a); sh.set_alpha(a)
            surf.blit(sh,  (int(x)-img.get_width()//2+2, int(y)+2))
            surf.blit(img, (int(x)-img.get_width()//2,   int(y)))

    def draw_flash(self, surf):
        if self.flash_t > 0:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((*self.flash_col[:3], int(170*self.flash_t/self.flash_dur)))
            surf.blit(ov, (0,0))


fx = FX()


class Buffs:
    """Damage buff (Serious Mode / Power Up block)."""
    def __init__(self):
        self.t = 0.0
        self.dur = 1.0
        self.pct = 0.0

    @property
    def active(self): return self.t > 0

    def mult(self): return 1.0 + self.pct/100.0 if self.t > 0 else 1.0

    def activate(self, seconds, pct):
        self.t = self.dur = float(seconds)
        self.pct = float(pct)

    def update(self, dt):
        if self.t > 0: self.t = max(0.0, self.t - dt)

    def clear(self): self.t = 0.0


buffs = Buffs()


# ══════════════════════════════════════════════════════════
#  DUMMY
# ══════════════════════════════════════════════════════════
class Dummy:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x, self.y = float(WIDTH//2 - DUMMY_SIZE//2), float((AT+AB)//2 - DUMMY_SIZE//2)
        self.hp = self.max_hp = 100.0
        self.hp_ghost = 100.0
        self.alive = True
        self.vx = self.vy = 0.0
        self.moving = False
        self.friction = 2.0
        self.spin_mult = 1.0
        self.angle = 0.0
        self.flash_timer = 0.0
        self.dead_timer = 0.0
        self.z = 0.0            # height above the floor (uppercut sends him up)
        self.vz = 0.0

    @property
    def cx(self): return self.x + DUMMY_SIZE//2
    @property
    def cy(self): return self.y + DUMMY_SIZE//2
    @property
    def rect(self): return pygame.Rect(int(self.x), int(self.y), DUMMY_SIZE, DUMMY_SIZE)
    @property
    def airborne(self): return self.z > 4

    def take_damage(self, dmg, popup=True):
        if not self.alive: return
        dmg = dmg*buffs.mult()
        self.hp = max(0.0, self.hp - dmg)
        self.flash_timer = 0.09
        if popup: fx.add_text(self.cx, self.y - self.z - 34, f"-{round(dmg, 2):g}",
                              (255,140,60) if buffs.active else (255,220,80), big=dmg >= 15)
        if self.hp <= 0:
            self.alive = False
            self.dead_timer = 1.2
            fx.particles += burst(self.cx, self.cy, 50, [(255,255,255),(255,200,80),(210,90,90)], 4, 11, 80, 380, 0.4, 1.0, 120)

    def launch_up(self, force):
        """Send him into the air (uppercut)."""
        self.vx *= 0.2; self.vy *= 0.2
        self.vz = force
        self.z = max(self.z, 1.0)

    def launch(self, dx, dy, force, spin=1.0, friction=2.0):
        nx, ny, _ = unit(dx, dy)
        self.vx, self.vy = nx*force, ny*force
        self.moving = force > 0
        self.spin_mult, self.friction = spin, friction

    def update(self, dt):
        if self.flash_timer > 0: self.flash_timer -= dt
        if not self.alive and self.dead_timer > 0: self.dead_timer -= dt
        self.hp_ghost += (self.hp - self.hp_ghost)*min(1.0, dt*2.5)

        if self.z > 0 or self.vz != 0:                                    # in the air
            self.vz -= GRAVITY*dt
            self.z += self.vz*dt
            if random.random() < 0.5:
                fx.particles.append(Particle(self.cx, self.cy - self.z, random.uniform(-30,30), 40, (255,255,255), random.randint(3,6), 0.3, True))
            if self.z <= 0:                                               # landed
                impact = -self.vz
                self.z, self.vz = 0.0, 0.0
                if impact > 350:
                    fx.add_crater(self.cx, self.cy, clamp(impact/25, 30, 90))
                    fx.add_ring(self.cx, self.cy, 100, 0.3, (255,235,160), 5)
                    fx.particles += burst(self.cx, self.cy, 16, DIRT, 3, 7, 60, 280, 0.3, 0.7, 380, "rect")
                    fx.shake(clamp(impact/150, 4, 16), 0.25)

        if self.moving:
            speed = math.hypot(self.vx, self.vy)
            self.x += self.vx*dt
            self.y += self.vy*dt
            if speed > 250 and random.random() < 0.7:
                fx.particles.append(Particle(self.cx, self.cy, 0, 0, (255,255,255), random.randint(4,8), 0.25, True))
            wall = False
            if self.x < AL:                  self.x = AL;                 self.vx =  abs(self.vx)*0.55; wall = True
            if self.x + DUMMY_SIZE > AR:     self.x = AR - DUMMY_SIZE;    self.vx = -abs(self.vx)*0.55; wall = True
            if self.y < AT:                  self.y = AT;                 self.vy =  abs(self.vy)*0.55; wall = True
            if self.y + DUMMY_SIZE > AB:     self.y = AB - DUMMY_SIZE;    self.vy = -abs(self.vy)*0.55; wall = True
            if wall and speed > 450:
                fx.shake(9, 0.25)
                fx.add_crater(self.cx, self.cy, 40)
                fx.add_ring(self.cx, self.cy, 90, 0.3, (255,230,150), 4)
                fx.particles += burst(self.cx, self.cy, 14, DIRT, 3, 7, 60, 260, 0.3, 0.7, 380, "rect")
            f = math.exp(-self.friction*dt)
            self.vx *= f; self.vy *= f
            self.angle += speed*self.spin_mult*0.35*dt
            if speed < 40: self.moving = False
        elif self.airborne:
            self.angle += 420*dt                                          # tumbling in the air
        else:
            a = (self.angle + 180) % 360 - 180
            self.angle = a*max(0.0, 1 - 10*dt)

    def _sprite(self):
        S = DUMMY_SIZE + 16
        s = pygame.Surface((S, S), pygame.SRCALPHA)
        flash = self.flash_timer > 0
        col = (255,255,255) if flash else (210,90,90)
        out = (255,255,255) if flash else (160,50,50)
        r = pygame.Rect(0, 0, DUMMY_SIZE, DUMMY_SIZE); r.center = (S//2, S//2)
        pygame.draw.rect(s, out, r.inflate(4,4), border_radius=6)
        pygame.draw.rect(s, col, r, border_radius=5)
        ex1, ex2, ey = r.x + 12, r.right - 12, r.y + 12
        if (self.moving and math.hypot(self.vx, self.vy) > 200) or self.z > 20:           # dizzy X eyes while flying
            for ex in (ex1, ex2):
                pygame.draw.line(s, (0,0,0), (ex-4, ey-4), (ex+4, ey+4), 3)
                pygame.draw.line(s, (0,0,0), (ex+4, ey-4), (ex-4, ey+4), 3)
        else:
            for ex in (ex1, ex2): pygame.draw.circle(s, (0,0,0), (ex, ey), 5)
            pygame.draw.circle(s, (255,255,255), (ex1+2, ey-1), 2)
            pygame.draw.circle(s, (255,255,255), (ex2+2, ey-1), 2)
        return s

    def draw(self, surf):
        if not self.alive:
            sc = max(0.0, self.dead_timer/1.2)
            sz = int(DUMMY_SIZE*sc)
            if sz > 2:
                s = pygame.Surface((sz, sz), pygame.SRCALPHA)
                pygame.draw.rect(s, (255,255,255,int(255*sc)), (0,0,sz,sz), border_radius=4)
                surf.blit(s, (int(self.cx)-sz//2, int(self.cy - self.z)-sz//2))
            return

        if self.airborne:                                                 # shadow on the floor
            k = max(0.3, 1 - self.z/450)
            sw_, sh_ = int(DUMMY_SIZE*1.1*k), int(DUMMY_SIZE*0.45*k)
            sh = pygame.Surface((sw_, sh_), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0,0,0,int(130*k)), (0, 0, sw_, sh_))
            surf.blit(sh, (int(self.cx) - sw_//2, int(self.cy) + DUMMY_SIZE//3 - sh_//2))

        spr = self._sprite()
        if abs(self.angle) > 0.5: spr = pygame.transform.rotate(spr, -self.angle)
        surf.blit(spr, (int(self.cx) - spr.get_width()//2, int(self.cy - self.z) - spr.get_height()//2))

        bw, bh = 82, 10
        bx, by = int(self.cx - bw//2), int(self.y - self.z) - 24
        pygame.draw.rect(surf, (50,15,15), (bx, by, bw, bh), border_radius=3)
        gw = int(bw*self.hp_ghost/self.max_hp)
        if gw > 0: pygame.draw.rect(surf, (240,240,240), (bx, by, gw, bh), border_radius=3)
        fw = int(bw*self.hp/self.max_hp)
        if fw > 0: pygame.draw.rect(surf, (70,210,70), (bx, by, fw, bh), border_radius=3)
        pygame.draw.rect(surf, (200,200,200), (bx, by, bw, bh), 1, border_radius=3)
        lbl = F_SM.render(f"{self.hp:.0f}/{self.max_hp:.0f} HP", True, (255,255,255))
        surf.blit(lbl, (bx + bw//2 - lbl.get_width()//2, by - 17))


# ══════════════════════════════════════════════════════════
#  SHARED HIT FUNCTIONS (used by Normal Punch AND the Skill Builder blocks)
# ══════════════════════════════════════════════════════════
def face_punch_hit(player, dummy, damage=20, force=1500, crater=True):
    """Variant 2 – punch him in the face: crater + damage + send him flying."""
    nx, ny, _ = unit(dummy.cx - player.cx, dummy.cy - player.cy)
    if crater: fx.add_crater(dummy.cx, dummy.cy, 70)
    fx.add_ring(dummy.cx, dummy.cy, 130, 0.35, (255,235,160), 6)
    fx.particles += burst(dummy.cx, dummy.cy, 28, DIRT + [(255,220,120)], 3, 8, 80, 440, 0.3, 0.8, 300, "rect")
    fx.shake(14, 0.3)
    fx.flash((255,255,255), 0.08)
    dummy.take_damage(damage)
    dummy.launch(nx, ny, force, spin=1.0, friction=2.0)


def spawn_crater_line(player, dummy, length=900, damage=10, roll_force=700):
    """Variant 1 – punch from far away: a crater line races toward him."""
    nx, ny, _ = unit(dummy.cx - player.cx, dummy.cy - player.cy)
    ox, oy = player.cx + nx*28, player.cy + ny*28
    fx.lines.append(CraterLine(ox, oy, nx, ny, length, damage, roll_force))
    fx.add_crater(ox, oy, 34)
    fx.add_ring(ox, oy, 80, 0.25, (255,255,255), 3)
    fx.shake(6, 0.2)


def uppercut_hit(player, dummy, damage=15, force=900):
    """Skill 4 – punch from below: damage + sends him up into the air."""
    fx.add_crater(dummy.cx, dummy.cy, 36)
    fx.add_ring(dummy.cx, dummy.cy, 110, 0.3, (190,140,255), 6)
    fx.add_ring(dummy.cx, dummy.cy - 30, 70, 0.25, (255,255,255), 3)
    for _ in range(26):                                                  # upward streaks
        fx.particles.append(Particle(dummy.cx + random.uniform(-18,18), dummy.cy + random.uniform(-10,20),
                                     random.uniform(-60,60), -random.uniform(300,700),
                                     random.choice([(255,255,255), (200,160,255), (255,230,150)]),
                                     random.randint(3,7), random.uniform(0.3,0.7), True, 500))
    fx.particles += burst(dummy.cx, dummy.cy, 12, DIRT, 3, 7, 60, 260, 0.3, 0.7, 380, "rect")
    fx.shake(12, 0.3)
    fx.flash((220,200,255), 0.1)
    dummy.take_damage(damage)
    dummy.launch_up(force)


# ══════════════════════════════════════════════════════════
#  PLAYER  –  THE STRONGEST HERO
# ══════════════════════════════════════════════════════════
class Player:
    PUNCH_CD = 1.2

    def __init__(self):
        self.reset()

    def reset(self):
        self.x = float(AL + 90)
        self.y = float((AT+AB)//2 - PLAYER_SIZE//2)
        self.dir = (1.0, 0.0)
        self.cd1 = 0.0
        self.cd2 = 0.0
        self.cd3 = 0.0
        self.cd4 = 0.0
        self.upper = None            # delayed Uppercut impact
        self.swing_up = False
        self.shoving = None          # delayed Shove impact
        self.swing_both = False
        self.cons = None             # running Consecutive Punches
        self.pending = None          # delayed Normal Punch impact
        self.swing_t = 0.0
        self.swing_dur = 0.18
        self.locked = False

    @property
    def cx(self): return self.x + PLAYER_SIZE//2
    @property
    def cy(self): return self.y + PLAYER_SIZE//2
    @property
    def rect(self): return pygame.Rect(int(self.x), int(self.y), PLAYER_SIZE, PLAYER_SIZE)

    def swing(self, dur=0.18, both=False, up=False):
        self.swing_t = self.swing_dur = dur
        self.swing_both = both
        self.swing_up = up

    @property
    def busy(self):
        return bool(self.pending or self.cons or self.shoving or self.upper)

    # ── Normal Punch ───────────────────────────────────────
    def use_normal_punch(self, dummy):
        if self.cd1 > 0 or self.busy or self.locked or not dummy.alive: return False
        dist = math.hypot(dummy.cx - self.cx, dummy.cy - self.cy)
        variant = 2 if dist <= CLOSE_RANGE else 1
        self.pending = {"t": 0.12 if variant == 2 else 0.15, "variant": variant}
        self.cd1 = self.PUNCH_CD
        self.swing(0.2)
        name = "Face Smash" if variant == 2 else "Crater Line"
        fx.add_text(self.cx, self.y - 30, f"Normal Punch  -  Variant {variant}: {name}", (255,230,90))
        return True

    # ── Skill 2: Consecutive Punches ───────────────────────
    def use_consecutive_punches(self, dummy):
        if self.cd2 > 0 or self.busy or self.locked or not dummy.alive: return False
        self.cons = {"t": 0.0, "n": 0, "dealt": 0.0}
        self.cd2 = CONS_CD
        fx.add_text(self.cx, self.y - 30, "Consecutive Punches", (255,230,90))
        return True

    def _run_consecutive(self, dt, dummy):
        c = self.cons
        c["t"] += dt
        per = CONS_TOTAL_DMG / CONS_HITS
        while c["n"] < CONS_HITS and c["t"] >= c["n"]*CONS_INTERVAL:
            side = -1 if c["n"] % 2 == 0 else 1
            nx, ny = self.dir
            px, py = -ny*side*10, nx*side*10
            col = (255,220,70) if side < 0 else (255,255,255)
            fx.fists.append(_Fist(self.cx + nx*24 + px, self.cy + ny*24 + py, nx, ny, col))
            fx.particles += burst(self.cx + nx*30, self.cy + ny*30, 3, [col, (255,255,255)], 2, 5, 60, 220, 0.15, 0.35)
            self.swing(CONS_INTERVAL*1.6)
            fx.shake(3, 0.06)
            if dummy.alive and math.hypot(dummy.cx - self.cx, dummy.cy - self.cy) <= CONS_RANGE:
                dummy.take_damage(per, popup=False)
                c["dealt"] += per*buffs.mult()
            c["n"] += 1
        if c["n"] >= CONS_HITS:
            if c["dealt"] > 0: fx.add_text(dummy.cx, dummy.y - 34, f"-{round(c['dealt'], 2):g}", (255,220,80), big=True)
            else:              fx.add_text(self.cx, self.y - 30, "Too far!", (255,120,120))
            self.cons = None

    # ── Skill 3: Shove ─────────────────────────────────────
    def use_shove(self, dummy):
        if self.cd3 > 0 or self.busy or self.locked or not dummy.alive: return False
        self.shoving = {"t": 0.1}
        self.cd3 = SHOVE_CD
        self.swing(0.22, both=True)
        fx.add_text(self.cx, self.y - 30, "Shove", (255,230,90))
        return True

    def _do_shove(self, dummy):
        if not dummy.alive: return
        nx, ny, dist = unit(dummy.cx - self.cx, dummy.cy - self.cy)
        if dist > SHOVE_RANGE:
            fx.add_text(self.cx, self.y - 30, "Too far!", (255,120,120))
            return
        hx, hy = (self.cx + dummy.cx)/2, (self.cy + dummy.cy)/2
        fx.add_ring(hx, hy, 90, 0.3, (255,255,255), 5)
        fx.particles += burst(hx, hy, 14, [(255,255,255), (255,230,150)], 3, 7, 80, 320, 0.2, 0.5)
        fx.shake(8, 0.2)
        dummy.take_damage(SHOVE_DMG)
        dummy.launch(nx, ny, SHOVE_FORCE, spin=0.4, friction=3.0)      # slides back, barely spins

    # ── Skill 4: Uppercut ──────────────────────────────────
    def use_uppercut(self, dummy):
        if self.cd4 > 0 or self.busy or self.locked or not dummy.alive: return False
        self.upper = {"t": 0.12}
        self.cd4 = UPPER_CD
        self.swing(0.3, up=True)
        fx.add_text(self.cx, self.y - 30, "Uppercut", (200,160,255))
        return True

    def _do_uppercut(self, dummy):
        if not dummy.alive: return
        if math.hypot(dummy.cx - self.cx, dummy.cy - self.cy) > UPPER_RANGE:
            fx.add_text(self.cx, self.y - 30, "Too far!", (255,120,120))
            return
        uppercut_hit(self, dummy, UPPER_DMG, UPPER_FORCE)

    # ── R: Serious Mode ────────────────────────────────────
    def use_serious(self):
        if buffs.active: return False
        buffs.activate(SERIOUS_TIME, SERIOUS_PCT)
        fx.flash((255,40,40), 0.3)
        fx.shake(12, 0.45)
        fx.add_ring(self.cx, self.cy, 170, 0.5, (255,60,40), 8)
        fx.add_ring(self.cx, self.cy, 110, 0.35, (255,200,80), 4)
        fx.particles += burst(self.cx, self.cy, 40, [(255,60,40), (255,150,40), (255,230,120)], 3, 9, 80, 380, 0.4, 0.9)
        fx.add_text(self.cx, self.y - 40, f"SERIOUS MODE!  +{SERIOUS_PCT}% DMG", (255,90,60), big=True)
        return True

    def update(self, dt, keys, dummy):
        # facing
        nx, ny, _ = unit(dummy.cx - self.cx, dummy.cy - self.cy)
        self.dir = (nx, ny)

        # movement
        if not self.locked:
            dx = dy = 0.0
            if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
            if dx and dy: dx *= 0.7071; dy *= 0.7071
            self.x += dx*PLAYER_SPEED*dt
            self.y += dy*PLAYER_SPEED*dt
        self.x = clamp(self.x, AL, AR - PLAYER_SIZE)
        self.y = clamp(self.y, AT, AB - PLAYER_SIZE)

        if self.cd1 > 0:     self.cd1 -= dt
        if self.cd2 > 0:     self.cd2 -= dt
        if self.cd3 > 0:     self.cd3 -= dt
        if self.cd4 > 0:     self.cd4 -= dt
        if self.upper:
            self.upper["t"] -= dt
            if self.upper["t"] <= 0:
                self.upper = None
                self._do_uppercut(dummy)
        if buffs.active and random.random() < 0.6:                       # serious-mode flames
            fx.particles.append(Particle(self.cx + random.uniform(-18,18), self.cy + random.uniform(-12,18),
                                         random.uniform(-20,20), random.uniform(-110,-40),
                                         random.choice([(255,60,40), (255,140,40), (255,220,100)]), random.randint(3,7), 0.5, True))
        if self.shoving:
            self.shoving["t"] -= dt
            if self.shoving["t"] <= 0:
                self.shoving = None
                self._do_shove(dummy)
        if self.cons:        self._run_consecutive(dt, dummy)
        if self.swing_t > 0: self.swing_t -= dt

        if self.pending:
            self.pending["t"] -= dt
            if random.random() < 0.6:
                fx.particles.append(Particle(self.cx + random.uniform(-14,14), self.cy + random.uniform(-14,14),
                                             0, -40, (255,220,50), random.randint(3,6), 0.3, True, shape="rect"))
            if self.pending["t"] <= 0:
                variant = self.pending["variant"]
                self.pending = None
                if dummy.alive:
                    if variant == 2: face_punch_hit(self, dummy, damage=20, force=1500, crater=True)
                    else:            spawn_crater_line(self, dummy, length=900, damage=10, roll_force=700)

    def draw(self, surf):
        d = self.dir
        n = (-d[1], d[0])
        cx, cy = self.cx, self.cy
        t = pygame.time.get_ticks()*0.008
        w = math.sin(t)*3
        ser = buffs.active

        if ser:                                                                  # red glow
            pulse = 0.5 + 0.5*math.sin(t*2.2)
            R = int(46 + 8*pulse)
            g = pygame.Surface((R*2, R*2), pygame.SRCALPHA)
            pygame.draw.circle(g, (255,50,30,60), (R, R), R)
            pygame.draw.circle(g, (255,120,40,70), (R, R), int(R*0.7))
            surf.blit(g, (int(cx) - R, int(cy) - R))

        cape = [(cx - d[0]*16 + n[0]*14, cy - d[1]*16 + n[1]*14), (cx - d[0]*16 - n[0]*14, cy - d[1]*16 - n[1]*14),
                (cx - d[0]*(38+w) - n[0]*9, cy - d[1]*(38+w) - n[1]*9), (cx - d[0]*(38+w) + n[0]*9, cy - d[1]*(38+w) + n[1]*9)]
        pygame.draw.polygon(surf, (255,225,225) if ser else (235,235,240), cape)
        pygame.draw.polygon(surf, (200,80,80) if ser else (170,170,185), cape, 2)

        r = self.rect
        pygame.draw.rect(surf, (190,70,10) if ser else (170,125,10), r.inflate(4,4), border_radius=7)
        pygame.draw.rect(surf, (255,150,40) if ser else (245,205,40), r, border_radius=6)
        pygame.draw.circle(surf, (255,228,190), (int(cx), int(cy)), 12)          # bald head
        pygame.draw.circle(surf, (255,255,255), (int(cx - 4), int(cy - 4)), 3)   # shine
        for sgn in (-1, 1):                                                      # eyes
            ex, ey = cx + d[0]*6 + n[0]*4*sgn, cy + d[1]*6 + n[1]*4*sgn
            pygame.draw.circle(surf, (230,20,20) if ser else (0,0,0), (int(ex), int(ey)), 2)
            if ser:                                                              # angry brows
                p1 = (ex + n[0]*4*sgn - d[0]*2, ey + n[1]*4*sgn - d[1]*2)
                p2 = (ex - n[0]*3*sgn + d[0]*3, ey - n[1]*3*sgn + d[1]*3)
                pygame.draw.line(surf, (120,0,0), p1, p2, 2)

        ext = 0.0
        if self.swing_t > 0: ext = 34*math.sin(math.pi*(1 - self.swing_t/self.swing_dur))
        up = self.swing_up and self.swing_t > 0
        for sgn in (-1, 1):                                                      # red gloves
            e = ext if (sgn == 1 or self.swing_both) else 0
            gx = cx + d[0]*(20 + e) + n[0]*11*sgn
            gy = cy + d[1]*(20 + e) + n[1]*11*sgn
            if up and sgn == 1: gy -= e*0.9                                      # uppercut: glove swings up
            if ser: pygame.draw.circle(surf, (255,140,40), (int(gx), int(gy)), 11, 2)
            pygame.draw.circle(surf, (190,20,30), (int(gx), int(gy)), 8)
            pygame.draw.circle(surf, (255,255,255), (int(gx), int(gy)), 8, 2)


# ══════════════════════════════════════════════════════════
#  SKILL BUILDER – BLOCK DEFINITIONS
# ══════════════════════════════════════════════════════════
SB_COLORS = [(255,200,50),(80,180,255),(220,50,50),(150,50,255),(100,255,100),(255,120,50),(255,80,200),(255,255,255)]
SB_COLOR_NAMES = ["Gold","Blue","Red","Purple","Green","Orange","Pink","White"]
CAT_COL = {"Attack": (220,80,70), "Movement": (70,190,100), "Effects": (230,170,50)}


def _N(key, label, default, lo, hi, step): return dict(key=key, label=label, kind="num", default=default, lo=lo, hi=hi, step=step)
def _C(default=0):                         return dict(key="color", label="Color", kind="color", default=default)
def _O(key, label, opts):                  return dict(key=key, label=label, kind="choice", opts=opts, default=opts[0])


BLOCK_DEFS = [
    # ── Attack ──
    dict(name="Punch", cat="Attack", desc="One punch. Hurts the enemy if he is inside Range.",
         params=[_N("damage","Damage",10,1,999,1), _N("range","Range",130,40,600,10), _C(0)]),
    dict(name="Combo Punches", cat="Attack", desc="Rapid punch barrage. Each hit does Damage (needs the enemy to be close).",
         params=[_N("hits","Hits",6,1,60,1), _N("damage","Damage",3,1,999,1), _C(1)]),
    dict(name="Face Punch", cat="Attack", desc="Punch in the face: crater, damage and sends him flying. Must be close!",
         params=[_N("damage","Damage",20,1,999,1), _N("launch","Launch",1500,0,4000,100), _O("crater","Crater",["On","Off"])]),
    dict(name="Crater Line", cat="Attack", desc="Crack in the ground races toward him. Touch it once = damage + rolls back.",
         params=[_N("length","Length",900,100,1500,50), _N("damage","Damage",10,1,999,1), _N("roll","Roll Force",700,0,3000,100)]),
    dict(name="Hitbox", cat="Attack", desc="Circle around you. Anyone inside gets damage and knockback.",
         params=[_N("radius","Radius",100,20,600,10), _N("damage","Damage",15,1,999,1), _N("knock","Knockback",500,0,4000,100)]),
    dict(name="Shockwave", cat="Attack", desc="Expanding ring that damages and pushes the enemy away.",
         params=[_N("radius","Radius",250,40,800,10), _N("damage","Damage",10,1,999,1), _C(7)]),
    dict(name="Launch Enemy", cat="Attack", desc="Throws the enemy in a direction without damage.",
         params=[_N("force","Force",1200,100,4000,100), _O("dir","Direction",["Away","Toward","Up","Down"])]),
    dict(name="Uppercut", cat="Attack", desc="Punch from below: damage and sends the enemy up into the air. Must be close!",
         params=[_N("damage","Damage",15,1,999,1), _N("range","Range",120,40,400,10), _N("height","Height",900,200,2000,100)]),
    dict(name="Slam Down", cat="Attack", desc="Smashes an enemy that is in the air back to the floor (use after Uppercut).",
         params=[_N("damage","Damage",12,1,999,1), _N("force","Force",2500,500,5000,100)]),
    dict(name="Energy Blast", cat="Attack", desc="Fires an energy ball at the enemy. Hits = damage + knockback.",
         params=[_N("damage","Damage",8,1,999,1), _N("speed","Speed",1400,300,3000,100), _C(1)]),
    # ── Movement ──
    dict(name="Dash To Enemy", cat="Movement", desc="Rush toward the enemy (stops when touching him).",
         params=[_N("speed","Speed",900,100,3000,100), _N("time","Time",0.25,0.05,3,0.05)]),
    dict(name="Dash Away", cat="Movement", desc="Rush backward, away from the enemy.",
         params=[_N("speed","Speed",900,100,3000,100), _N("time","Time",0.25,0.05,3,0.05)]),
    dict(name="Teleport Back", cat="Movement", desc="Instantly appear on the other side of the enemy.", params=[]),
    dict(name="Sidestep", cat="Movement", desc="Dash sideways around the enemy.",
         params=[_N("speed","Speed",900,100,3000,100), _N("time","Time",0.2,0.05,3,0.05), _O("side","Side",["Left","Right"])]),
    dict(name="Wait", cat="Movement", desc="Pause the skill for a moment.", params=[_N("seconds","Seconds",0.5,0.05,10,0.05)]),
    # ── Effects (run in the background – the next block starts right away) ──
    dict(name="Crater", cat="Effects", desc="Make a crater in the floor under the enemy or under you.",
         params=[_N("size","Size",70,20,300,10), _O("where","Where",["Enemy","Self"])]),
    dict(name="Aura", cat="Effects", desc="Glowing particles around you. Keeps running while next blocks play.",
         params=[_N("time","Time",1.0,0.1,10,0.1), _C(0)]),
    dict(name="Screen Shake", cat="Effects", desc="Shakes the whole screen. Keeps running while next blocks play.",
         params=[_N("power","Power",12,1,40,1), _N("time","Time",0.3,0.05,5,0.05)]),
    dict(name="Flash", cat="Effects", desc="Flashes the screen with a color.",
         params=[_C(7), _N("time","Time",0.2,0.05,2,0.05)]),
    dict(name="Slow Motion", cat="Effects", desc="Slows the game down (Speed in %). Keeps running while next blocks play.",
         params=[_N("scale","Speed %",30,5,100,5), _N("time","Time",0.8,0.1,5,0.1)]),
    dict(name="Power Up", cat="Effects", desc="Serious mode: bonus damage on everything for a few seconds (same as pressing R).",
         params=[_N("percent","Bonus %",15,5,200,5), _N("time","Time",10,1,60,1)]),
    dict(name="Heal Enemy", cat="Effects", desc="Gives HP back to the enemy (handy for testing combos).",
         params=[_N("amount","Amount",50,1,100,1)]),
    dict(name="Dust Burst", cat="Effects", desc="Burst of dirt particles at the enemy or at you.",
         params=[_N("amount","Amount",30,5,100,5), _O("where","Where",["Enemy","Self"])]),
]
BDEF = {d["name"]: d for d in BLOCK_DEFS}
BG_BLOCKS = {"Crater", "Aura", "Screen Shake", "Flash", "Slow Motion", "Dust Burst"}


def default_block(name):
    return {"type": name, "p": {s["key"]: s["default"] for s in BDEF[name]["params"]}}


def mk(name, **over):
    b = default_block(name)
    b["p"].update(over)
    return b


def block_duration(b):
    t, p = b["type"], b["p"]
    if t in BG_BLOCKS: return 0.0
    if t == "Combo Punches": return p["hits"]*0.07
    if t in ("Dash To Enemy", "Dash Away", "Sidestep"): return p["time"]
    if t == "Wait": return p["seconds"]
    return {"Punch":0.18, "Face Punch":0.3, "Crater Line":0.45, "Hitbox":0.25,
            "Shockwave":0.35, "Launch Enemy":0.15, "Teleport Back":0.15, "Uppercut":0.3,
            "Slam Down":0.25, "Energy Blast":0.4, "Power Up":0.3, "Heal Enemy":0.1}.get(t, 0.2)


def fmt_val(v, step):
    return f"{int(v)}" if step >= 1 else f"{v:.2f}"


def adjust_param(b, spec, direction, mult=1):
    v = b["p"][spec["key"]] + direction*spec["step"]*mult
    v = clamp(v, spec["lo"], spec["hi"])
    b["p"][spec["key"]] = int(round(v)) if spec["step"] >= 1 else round(v, 2)


def clean_blocks(raw):
    out = []
    for b in raw or []:
        d = BDEF.get(b.get("type")) if isinstance(b, dict) else None
        if not d: continue
        p = {}
        src = b.get("p", {}) if isinstance(b.get("p", {}), dict) else {}
        for s in d["params"]:
            v = src.get(s["key"], s["default"])
            if s["kind"] == "num":
                try: v = float(v)
                except Exception: v = s["default"]
                v = clamp(v, s["lo"], s["hi"])
                v = int(round(v)) if s["step"] >= 1 else round(v, 2)
            elif s["kind"] == "color":
                try: v = int(v) % len(SB_COLORS)
                except Exception: v = s["default"]
            else:
                v = v if v in s["opts"] else s["opts"][0]
            p[s["key"]] = v
        out.append({"type": d["name"], "p": p})
    return out


EXAMPLES = [
    ("Hero Combo", [mk("Aura", time=1.2, color=0), mk("Dash To Enemy", speed=1200, time=0.3),
                    mk("Combo Punches", hits=8, damage=3, color=0), mk("Face Punch", damage=20, launch=1500),
                    mk("Screen Shake", power=14, time=0.3)]),
    ("Crater Rush", [mk("Crater Line", length=900, damage=10, roll=700), mk("Wait", seconds=0.35),
                     mk("Dash To Enemy", speed=1800, time=0.7), mk("Face Punch", damage=25, launch=1800)]),
    ("Ghost Smash", [mk("Flash", color=7, time=0.2), mk("Teleport Back"), mk("Slow Motion", scale=25, time=0.7),
                     mk("Aura", time=0.7, color=3), mk("Wait", seconds=0.3),
                     mk("Face Punch", damage=35, launch=2200), mk("Shockwave", radius=300, damage=10, color=3)]),
    ("Air Combo", [mk("Dash To Enemy", speed=1500, time=0.3), mk("Uppercut", damage=15, height=1100),
                   mk("Wait", seconds=0.3), mk("Energy Blast", damage=8, color=1),
                   mk("Slam Down", damage=15, force=3000), mk("Screen Shake", power=14, time=0.3)]),
    ("Serious Rush", [mk("Power Up", percent=15, time=10), mk("Aura", time=1.5, color=2), mk("Flash", color=2, time=0.2),
                      mk("Dash To Enemy", speed=1500, time=0.4), mk("Combo Punches", hits=8, damage=3, color=2),
                      mk("Uppercut", damage=15, height=900)]),
]


# ══════════════════════════════════════════════════════════
#  SKILL RUNNER  (plays the blocks of a custom skill, top → bottom)
# ══════════════════════════════════════════════════════════
class SkillRun:
    def __init__(self, game, blocks):
        self.g, self.player, self.dummy = game, game.player, game.dummy
        self.blocks = copy.deepcopy(blocks)
        self.idx, self.t = 0, 0.0
        self.started = False
        self.cur_dur = 0.0
        self.bg = []
        self.done = False

    def _col(self, p): return SB_COLORS[p.get("color", 0) % len(SB_COLORS)]

    def _dist(self):
        return math.hypot(self.dummy.cx - self.player.cx, self.dummy.cy - self.player.cy)

    def _dir(self):
        nx, ny, _ = unit(self.dummy.cx - self.player.cx, self.dummy.cy - self.player.cy)
        return nx, ny

    def update(self, dt):
        raw = self.g.raw_dt
        for e in self.bg[:]:
            e["t"] -= raw
            if e["kind"] == "Aura" and random.random() < 0.7:
                fx.particles.append(Particle(self.player.cx + random.uniform(-16,16), self.player.cy + random.uniform(-16,16),
                                             random.uniform(-12,12), random.uniform(-70,-20), e["col"], random.randint(4,8), 0.6, True))
            if e["t"] <= 0: self.bg.remove(e)
        slow = [e["scale"] for e in self.bg if e["kind"] == "Slow Motion"]
        self.g.time_scale = min(slow) if slow else 1.0

        spent = False
        while self.idx < len(self.blocks):
            b = self.blocks[self.idx]
            if not self.started:
                self._start(b)
                self.started, self.t = True, 0.0
            if self.cur_dur > 0:
                if spent: break
                self.t += dt
                spent = True
                self._tick(b, dt)
                if self.t < self.cur_dur: break
            self.idx += 1
            self.started = False

        if self.idx >= len(self.blocks) and not self.bg:
            self.done = True
            self.g.time_scale = 1.0

    def _start(self, b):
        t, p = b["type"], b["p"]
        pl, du = self.player, self.dummy
        self.cur_dur = block_duration(b)
        nx, ny = self._dir()
        if t == "Punch":
            pl.swing(0.18)
            fx.fists.append(_Fist(pl.cx + nx*24, pl.cy + ny*24, nx, ny, self._col(p)))
            if du.alive and self._dist() <= p["range"]:
                du.take_damage(p["damage"])
                du.launch(nx, ny, 250)
                fx.particles += burst(du.cx, du.cy, 10, [self._col(p), (255,255,255)], 3, 7, 60, 260, 0.2, 0.5)
        elif t == "Combo Punches":
            self.hits_done = 0
        elif t == "Face Punch":
            pl.swing(0.25)
            if du.alive and self._dist() <= FACE_REACH:
                face_punch_hit(pl, du, p["damage"], p["launch"], p["crater"] == "On")
            else:
                fx.add_text(pl.cx, pl.y - 30, "Too far!", (255,120,120))
        elif t == "Crater Line":
            pl.swing(0.25)
            spawn_crater_line(pl, du, p["length"], p["damage"], p["roll"])
        elif t == "Hitbox":
            fx.add_ring(pl.cx, pl.cy, p["radius"], 0.25, (255,90,90), 5)
            if du.alive and self._dist() <= p["radius"]:
                du.take_damage(p["damage"])
                du.launch(nx, ny, p["knock"])
        elif t == "Shockwave":
            col = self._col(p)
            fx.add_ring(pl.cx, pl.cy, p["radius"], 0.35, col, 6)
            fx.add_ring(pl.cx, pl.cy, p["radius"]*0.7, 0.3, (255,255,255), 3)
            fx.shake(7, 0.25)
            if du.alive and self._dist() <= p["radius"]:
                du.take_damage(p["damage"])
                du.launch(nx, ny, 600)
        elif t == "Launch Enemy":
            dx, dy = {"Away": (nx, ny), "Toward": (-nx, -ny), "Up": (0, -1), "Down": (0, 1)}[p["dir"]]
            du.launch(dx, dy, p["force"])
        elif t == "Teleport Back":
            fx.particles += burst(pl.cx, pl.cy, 16, [(255,255,255),(200,160,255)], 3, 7, 60, 260, 0.3, 0.6)
            pl.x = clamp(du.cx - nx*70 - PLAYER_SIZE//2, AL, AR - PLAYER_SIZE)
            pl.y = clamp(du.cy - ny*70 - PLAYER_SIZE//2, AT, AB - PLAYER_SIZE)
            fx.particles += burst(pl.cx, pl.cy, 16, [(255,255,255),(200,160,255)], 3, 7, 60, 260, 0.3, 0.6)
        elif t == "Uppercut":
            pl.swing(0.25, up=True)
            if du.alive and self._dist() <= p["range"]:
                uppercut_hit(pl, du, p["damage"], p["height"])
            else:
                fx.add_text(pl.cx, pl.y - 30, "Too far!", (255,120,120))
        elif t == "Slam Down":
            pl.swing(0.2, both=True)
            if du.alive and du.airborne:
                du.take_damage(p["damage"])
                du.vz = -p["force"]
                fx.add_ring(du.cx, du.cy - du.z, 90, 0.25, (255,255,255), 4)
                fx.shake(6, 0.15)
            else:
                fx.add_text(pl.cx, pl.y - 30, "Not in air!", (255,120,120))
        elif t == "Energy Blast":
            pl.swing(0.25, both=True)
            col = self._col(p)
            fx.projectiles.append(Projectile(pl.cx + nx*30, pl.cy + ny*30, nx, ny, p["speed"], p["damage"], col))
            fx.particles += burst(pl.cx + nx*30, pl.cy + ny*30, 8, [col, (255,255,255)], 3, 6, 60, 200, 0.2, 0.4)
        elif t == "Power Up":
            buffs.activate(p["time"], p["percent"])
            fx.flash((255,40,40), 0.2)
            fx.add_ring(pl.cx, pl.cy, 140, 0.4, (255,60,40), 6)
            fx.add_text(pl.cx, pl.y - 40, f"+{p['percent']}% DMG", (255,90,60), big=True)
        elif t == "Heal Enemy":
            if du.alive:
                du.hp = min(du.max_hp, du.hp + p["amount"])
                fx.add_text(du.cx, du.y - du.z - 34, f"+{p['amount']}", (110,255,120), big=True)
        elif t == "Dust Burst":
            tx, ty = (du.cx, du.cy) if p["where"] == "Enemy" else (pl.cx, pl.cy)
            fx.particles += burst(tx, ty, p["amount"], DIRT, 3, 8, 60, 320, 0.3, 0.8, 380, "rect")
        elif t == "Crater":
            tx, ty = (du.cx, du.cy) if p["where"] == "Enemy" else (pl.cx, pl.cy)
            fx.add_crater(tx, ty, p["size"])
            fx.add_ring(tx, ty, p["size"]*1.6, 0.3, (255,255,255), 4)
            fx.particles += burst(tx, ty, 14, DIRT, 3, 7, 60, 260, 0.3, 0.7, 380, "rect")
        elif t == "Aura":
            self.bg.append({"kind": "Aura", "t": p["time"], "col": self._col(p)})
        elif t == "Screen Shake":
            fx.shake(p["power"], p["time"])
        elif t == "Flash":
            fx.flash(self._col(p), p["time"])
        elif t == "Slow Motion":
            self.bg.append({"kind": "Slow Motion", "t": p["time"], "scale": p["scale"]/100.0})

    def _tick(self, b, dt):
        t, p = b["type"], b["p"]
        pl, du = self.player, self.dummy
        if t == "Combo Punches":
            while self.hits_done < p["hits"] and self.t >= self.hits_done*0.07:
                nx, ny = self._dir()
                off = random.uniform(-12, 12)
                fx.fists.append(_Fist(pl.cx + nx*24 - ny*off, pl.cy + ny*24 + nx*off, nx, ny, self._col(p)))
                pl.swing(0.07)
                if du.alive and self._dist() <= 170:
                    du.take_damage(p["damage"])
                self.hits_done += 1
        elif t == "Sidestep":
            nx, ny = self._dir()
            sx, sy = (ny, -nx) if p["side"] == "Left" else (-ny, nx)
            step = p["speed"]*dt
            pl.x = clamp(pl.x + sx*step, AL, AR - PLAYER_SIZE)
            pl.y = clamp(pl.y + sy*step, AT, AB - PLAYER_SIZE)
            fx.particles.append(Particle(pl.cx, pl.cy, 0, 0, (200,255,255), random.randint(6,12), 0.3, True, shape="rect"))
        elif t in ("Dash To Enemy", "Dash Away"):
            nx, ny = self._dir()
            sgn = 1 if t == "Dash To Enemy" else -1
            step = p["speed"]*dt
            dist = self._dist()
            if sgn == 1: step = min(step, max(0.0, dist - 52))
            pl.x = clamp(pl.x + nx*step*sgn, AL, AR - PLAYER_SIZE)
            pl.y = clamp(pl.y + ny*step*sgn, AT, AB - PLAYER_SIZE)
            fx.particles.append(Particle(pl.cx, pl.cy, 0, 0, (255,255,255), random.randint(6,12), 0.3, True, shape="rect"))


# ══════════════════════════════════════════════════════════
#  ARENA
# ══════════════════════════════════════════════════════════
class Arena:
    def __init__(self):
        self.bg = pygame.Surface((WIDTH, HEIGHT))
        self.bg.fill((25,25,30))
        ts = 60
        for tx in range(AL, AR, ts):
            for ty in range(AT, AB, ts):
                shade = (90,90,100) if ((tx//ts + ty//ts) % 2 == 0) else (70,70,78)
                pygame.draw.rect(self.bg, shade, pygame.Rect(tx, ty, min(ts, AR-tx), min(ts, AB-ty)))
        for g in (pygame.Rect(AL+5, AT+5, 90, 65), pygame.Rect(AL+5, AB-75, 90, 65),
                  pygame.Rect(AR-95, AT+5, 90, 65), pygame.Rect(AR-95, AB-75, 90, 65)):
            pygame.draw.rect(self.bg, (55,110,55), g, border_radius=4)
            pygame.draw.rect(self.bg, (45,90,45), g.inflate(-6,-6), border_radius=3)
        pygame.draw.rect(self.bg, (180,180,200), pygame.Rect(AL, AT, AW, AH), 3, border_radius=4)

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))


# ══════════════════════════════════════════════════════════
#  SKILL BUILDER UI  –  v3
#   • 16 blocks in a palette (click to add, new blocks go BELOW the selected one)
#   • every block has its own settings with  -  / +  buttons  (Shift = ×10, mouse wheel works too)
#   • move up/down, duplicate, delete, undo/redo, examples, auto-save to disk
#   • one-click Equip to the next free key (4-9, 0)
# ══════════════════════════════════════════════════════════
SLOT_KEYS = [(pygame.K_5,"5"),(pygame.K_6,"6"),(pygame.K_7,"7"),
             (pygame.K_8,"8"),(pygame.K_9,"9"),(pygame.K_0,"0")]   # 1-4 are built-in skills


class SkillBuilderUI:
    BTN   = pygame.Rect(10, 10, 210, 50)
    PANEL = pygame.Rect(60, 68, 1080, 600)
    BODY_Y = 48
    PAL_X, PAL_W   = 10, 210
    LIST_X, LIST_W = 230, 620
    RIGHT_X, RIGHT_W = 860, 210
    ROW_H, ROW_GAP = 56, 4

    def __init__(self):
        self.open = False
        self.testing = False
        self.blocks, self.sel, self.scroll = [], -1, 0
        self.name, self.name_active, self.editing_uid = "Skill 1", False, None
        self.saved, self.next_uid, self.equipped = [], 1, {}
        self.saved_scroll = 0
        self.pal_scroll = 0
        self.undo, self.redo = [], []
        self.toast, self.toast_t = "", 0.0
        self.example_i = 0
        self.pulse = 0.0
        self.load_disk()

    # ── persistence ───────────────────────────────────────
    def load_disk(self):
        try:
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for sk in data.get("saved", []):
                    self.saved.append({"uid": int(sk["uid"]), "name": str(sk["name"])[:20], "blocks": clean_blocks(sk["blocks"])})
                self.next_uid = max([s["uid"] for s in self.saved] + [int(data.get("next_uid", 1)) - 1]) + 1
                valid = [lbl for _, lbl in SLOT_KEYS]
                eq = data.get("equipped", {})
                for k, uid in eq.items():
                    if self.get_skill(uid) and k in valid: self.equipped[k] = uid
                for k, uid in eq.items():                            # old key (e.g. 4 is built-in now) -> first free slot
                    if self.get_skill(uid) and k not in valid and uid not in self.equipped.values():
                        for lbl in valid:
                            if lbl not in self.equipped: self.equipped[lbl] = uid; break
                self.name = f"Skill {self.next_uid}"
        except Exception as e:
            print(f"Could not load skills: {e}")

    def save_disk(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump({"next_uid": self.next_uid, "saved": self.saved, "equipped": self.equipped}, f, indent=1)
        except Exception as e:
            print(f"Could not save skills: {e}")

    def get_skill(self, uid):
        for s in self.saved:
            if s["uid"] == uid: return s
        return None

    def say(self, text):
        self.toast, self.toast_t = text, 3.0

    # ── undo / redo ───────────────────────────────────────
    def _snap(self):
        self.undo.append(copy.deepcopy(self.blocks))
        if len(self.undo) > 100: self.undo.pop(0)
        self.redo.clear()

    def do_undo(self):
        if self.undo:
            self.redo.append(copy.deepcopy(self.blocks))
            self.blocks = self.undo.pop()
            self.sel = min(self.sel, len(self.blocks) - 1)

    def do_redo(self):
        if self.redo:
            self.undo.append(copy.deepcopy(self.blocks))
            self.blocks = self.redo.pop()
            self.sel = min(self.sel, len(self.blocks) - 1)

    # ── block editing ─────────────────────────────────────
    def add_block(self, name):
        self._snap()
        idx = self.sel + 1 if self.sel >= 0 else len(self.blocks)
        self.blocks.insert(idx, default_block(name))
        self.sel = idx
        self._ensure_visible(idx)

    def _ensure_visible(self, i):
        area = self._list_area()
        top = i*(self.ROW_H + self.ROW_GAP)
        if top < self.scroll: self.scroll = top
        if top + self.ROW_H + 8 > self.scroll + area.h: self.scroll = top + self.ROW_H + 8 - area.h
        self._clamp_scroll()

    def _clamp_scroll(self):
        area = self._list_area()
        mx = max(0, len(self.blocks)*(self.ROW_H + self.ROW_GAP) + 8 - area.h)
        self.scroll = int(clamp(self.scroll, 0, mx))

    def delete_block(self, i):
        self._snap(); self.blocks.pop(i)
        self.sel = min(self.sel, len(self.blocks) - 1)
        self._clamp_scroll()

    def move_block(self, i, d):
        j = i + d
        if 0 <= j < len(self.blocks):
            self._snap()
            self.blocks[i], self.blocks[j] = self.blocks[j], self.blocks[i]
            self.sel = j

    def dup_block(self, i):
        self._snap()
        self.blocks.insert(i + 1, copy.deepcopy(self.blocks[i]))
        self.sel = i + 1
        self._ensure_visible(i + 1)

    def new_skill(self):
        self._snap()
        self.blocks, self.sel, self.scroll = [], -1, 0
        self.name, self.editing_uid = f"Skill {self.next_uid}", None

    def load_example(self):
        nm, blocks = EXAMPLES[self.example_i % len(EXAMPLES)]
        self.example_i += 1
        self._snap()
        self.blocks, self.sel, self.scroll = copy.deepcopy(blocks), -1, 0
        self.name, self.editing_uid = nm, None
        self.say(f"Loaded example: {nm}  (press Save to keep it)")

    def save_skill(self):
        if not self.blocks:
            self.say("Add some blocks first!"); return
        nm = self.name.strip() or f"Skill {self.next_uid}"
        sk = self.get_skill(self.editing_uid) if self.editing_uid else None
        if sk:
            sk["name"], sk["blocks"] = nm, copy.deepcopy(self.blocks)
        else:
            sk = {"uid": self.next_uid, "name": nm, "blocks": copy.deepcopy(self.blocks)}
            self.next_uid += 1
            self.saved.append(sk)
            self.editing_uid = sk["uid"]
        self.save_disk()
        self.say(f"Saved '{nm}'. Press Equip on the right to put it on a key.")

    def slot_of(self, uid):
        for k, v in self.equipped.items():
            if v == uid: return k
        return None

    def toggle_equip(self, uid):
        s = self.slot_of(uid)
        if s:
            del self.equipped[s]; self.say(f"Unequipped from [{s}]")
        else:
            for _, lbl in SLOT_KEYS:
                if lbl not in self.equipped:
                    self.equipped[lbl] = uid
                    self.say(f"Equipped! Press [{lbl}] in the arena to use it.")
                    break
            else:
                self.say("All slots are full – unequip one first.")
        self.save_disk()

    def delete_saved(self, i):
        sk = self.saved.pop(i)
        for k in [k for k, v in self.equipped.items() if v == sk["uid"]]: del self.equipped[k]
        if self.editing_uid == sk["uid"]: self.editing_uid = None
        self.save_disk()

    def edit_saved(self, i):
        sk = self.saved[i]
        self._snap()
        self.blocks, self.sel, self.scroll = copy.deepcopy(sk["blocks"]), -1, 0
        self.name, self.editing_uid = sk["name"], sk["uid"]
        self.say(f"Editing '{sk['name']}'")

    # ── layout ────────────────────────────────────────────
    def _abs(self, x, y, w, h):
        return pygame.Rect(self.PANEL.x + x, self.PANEL.y + y, w, h)

    def _list_area(self):
        return self._abs(self.LIST_X, self.BODY_Y, self.LIST_W, self.PANEL.h - self.BODY_Y - 44)

    def _saved_area(self):
        return self._abs(self.RIGHT_X, self.BODY_Y + 218, self.RIGHT_W, self.PANEL.h - self.BODY_Y - 218 - 44)

    def _pal_area(self):
        return self._abs(self.PAL_X, self.BODY_Y, self.PAL_W, self.PANEL.h - self.BODY_Y - 44)

    def _pal_content_h(self):
        return 8 + 3*22 + len(BLOCK_DEFS)*26

    def _palette_layout(self):
        items, y = [], self.BODY_Y + 4 - self.pal_scroll
        for cat in ("Attack", "Movement", "Effects"):
            items.append(("head", cat, self._abs(self.PAL_X, y, self.PAL_W - 10, 20)))
            y += 22
            for d in BLOCK_DEFS:
                if d["cat"] == cat:
                    items.append(("item", d, self._abs(self.PAL_X, y, self.PAL_W - 10, 24)))
                    y += 26
        return items

    def _right_buttons(self):
        y0 = self.BODY_Y + 4
        return {
            "test":  self._abs(self.RIGHT_X, y0,       self.RIGHT_W, 34),
            "save":  self._abs(self.RIGHT_X, y0 + 40,  self.RIGHT_W, 34),
            "undo":  self._abs(self.RIGHT_X, y0 + 80,  100, 30),
            "redo":  self._abs(self.RIGHT_X + 110, y0 + 80, 100, 30),
            "new":   self._abs(self.RIGHT_X, y0 + 116, 100, 30),
            "ex":    self._abs(self.RIGHT_X + 110, y0 + 116, 100, 30),
            "reset": self._abs(self.RIGHT_X, y0 + 152, self.RIGHT_W, 30),
        }

    def _row_widgets(self, i, b):
        area = self._list_area()
        y = area.y + 4 + i*(self.ROW_H + self.ROW_GAP) - self.scroll
        r = pygame.Rect(area.x, y, area.w - 14, self.ROW_H)
        w = {"row": r,
             "up":  pygame.Rect(r.right - 104, y + 4, 26, 22),
             "dn":  pygame.Rect(r.right - 104, y + 30, 26, 22),
             "dup": pygame.Rect(r.right - 72, y + 14, 32, 28),
             "del": pygame.Rect(r.right - 36, y + 14, 30, 28),
             "params": []}
        px = r.x + 156
        for spec in BDEF[b["type"]]["params"]:
            if spec["kind"] == "num":
                w["params"].append((spec, px, pygame.Rect(px, y + 26, 24, 24), pygame.Rect(px + 26, y + 26, 58, 24), pygame.Rect(px + 86, y + 26, 24, 24)))
            else:
                w["params"].append((spec, px, pygame.Rect(px, y + 26, 110, 24), None, None))
            px += 115
        return w

    # ── events ────────────────────────────────────────────
    def handle_event(self, ev, game):
        mx, my = pygame.mouse.get_pos()
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.BTN.collidepoint(mx, my):
            self.open = not self.open
            self.name_active = self.testing = False
            return True
        if not self.open or self.testing: return False
        P = self.PANEL
        if ev.type == pygame.KEYDOWN:
            return self._key(ev)
        if ev.type == pygame.MOUSEWHEEL:
            return self._wheel(ev, mx, my)
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if not P.collidepoint(mx, my):
                self.name_active = False
                return False
            self._click(mx, my, game)
            return True
        if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            return P.collidepoint(mx, my)
        return False

    def _key(self, ev):
        mods = pygame.key.get_mods()
        ctrl = bool(mods & pygame.KMOD_CTRL)
        if self.name_active:
            if ev.key in (pygame.K_RETURN, pygame.K_ESCAPE): self.name_active = False
            elif ev.key == pygame.K_BACKSPACE: self.name = self.name[:-1]
            elif ev.unicode and ev.unicode.isprintable() and len(self.name) < 20: self.name += ev.unicode
            return True
        if ev.key == pygame.K_ESCAPE:
            self.open = False
        elif ctrl and ev.key == pygame.K_z:
            self.do_undo()
        elif ctrl and ev.key == pygame.K_y:
            self.do_redo()
        elif ctrl and ev.key == pygame.K_d and 0 <= self.sel < len(self.blocks):
            self.dup_block(self.sel)
        elif ev.key in (pygame.K_DELETE, pygame.K_BACKSPACE) and 0 <= self.sel < len(self.blocks):
            self.delete_block(self.sel)
        return True

    def _wheel(self, ev, mx, my):
        if not self.PANEL.collidepoint(mx, my): return False
        mult = 10 if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else 1
        la = self._list_area()
        if la.collidepoint(mx, my):
            for i, b in enumerate(self.blocks):
                w = self._row_widgets(i, b)
                if not la.colliderect(w["row"]): continue
                for spec, px, mn, val, pl in w["params"]:
                    if spec["kind"] == "num" and pygame.Rect(px, w["row"].y + 26, 110, 24).collidepoint(mx, my):
                        self._snap(); adjust_param(b, spec, ev.y, mult); return True
            self.scroll -= ev.y*30
            self._clamp_scroll()
        elif self._pal_area().collidepoint(mx, my):
            mxp = max(0, self._pal_content_h() - self._pal_area().h)
            self.pal_scroll = int(clamp(self.pal_scroll - ev.y*30, 0, mxp))
        elif self._saved_area().collidepoint(mx, my):
            mxs = max(0, len(self.saved)*48 - self._saved_area().h)
            self.saved_scroll = int(clamp(self.saved_scroll - ev.y*30, 0, mxs))
        return True

    def _click(self, mx, my, game):
        P = self.PANEL
        shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
        mult = 10 if shift else 1

        if pygame.Rect(P.right - 100, P.y + 6, 88, 28).collidepoint(mx, my):
            self.open = False; self.name_active = False; return
        if pygame.Rect(P.x + 200, P.y + 6, 300, 28).collidepoint(mx, my):
            self.name_active = True; return
        self.name_active = False

        # palette
        for kind, d, r in self._palette_layout():
            if kind == "item" and r.collidepoint(mx, my) and self._pal_area().collidepoint(mx, my):
                self.add_block(d["name"]); return

        # right-hand buttons
        rb = self._right_buttons()
        if rb["test"].collidepoint(mx, my):
            if not self.blocks: self.say("Add some blocks first!")
            else:
                self.testing = True
                game.start_skill(self.blocks)
            return
        if rb["save"].collidepoint(mx, my):  self.save_skill(); return
        if rb["undo"].collidepoint(mx, my):  self.do_undo(); return
        if rb["redo"].collidepoint(mx, my):  self.do_redo(); return
        if rb["new"].collidepoint(mx, my):   self.new_skill(); return
        if rb["ex"].collidepoint(mx, my):    self.load_example(); return
        if rb["reset"].collidepoint(mx, my): game.reset_all(); self.say("Arena reset"); return

        # saved skills
        sa = self._saved_area()
        if sa.collidepoint(mx, my):
            for i, sk in enumerate(self.saved):
                ry = sa.y + i*48 - self.saved_scroll
                r = pygame.Rect(sa.x, ry, sa.w, 42)
                if not sa.colliderect(r): continue
                if pygame.Rect(r.x + 100, ry + 7, 40, 28).collidepoint(mx, my): self.edit_saved(i); return
                if pygame.Rect(r.x + 144, ry + 7, 40, 28).collidepoint(mx, my): self.toggle_equip(sk["uid"]); return
                if pygame.Rect(r.x + 188, ry + 7, 22, 28).collidepoint(mx, my): self.delete_saved(i); return
                if r.collidepoint(mx, my): self.edit_saved(i); return
            return

        # block list
        la = self._list_area()
        if la.collidepoint(mx, my):
            for i, b in enumerate(self.blocks):
                w = self._row_widgets(i, b)
                if not la.colliderect(w["row"]): continue
                if w["up"].collidepoint(mx, my): self.move_block(i, -1); return
                if w["dn"].collidepoint(mx, my): self.move_block(i, 1); return
                if w["dup"].collidepoint(mx, my): self.dup_block(i); return
                if w["del"].collidepoint(mx, my): self.delete_block(i); return
                for spec, px, a, v, c in w["params"]:
                    if spec["kind"] == "num":
                        if a.collidepoint(mx, my): self._snap(); adjust_param(b, spec, -1, mult); self.sel = i; return
                        if c.collidepoint(mx, my): self._snap(); adjust_param(b, spec, 1, mult);  self.sel = i; return
                    elif a.collidepoint(mx, my):
                        self._snap()
                        if spec["kind"] == "color":
                            b["p"]["color"] = (b["p"]["color"] + 1) % len(SB_COLORS)
                        else:
                            o = spec["opts"]; b["p"][spec["key"]] = o[(o.index(b["p"][spec["key"]]) + 1) % len(o)]
                        self.sel = i
                        return
                if w["row"].collidepoint(mx, my):
                    self.sel = -1 if self.sel == i else i
                    return

    # ── drawing ───────────────────────────────────────────
    def _btn(self, surf, rect, label, bg, fg=(255,255,255), font=None, disabled=False):
        hover = rect.collidepoint(pygame.mouse.get_pos()) and not disabled
        col = tuple(min(255, c + 35) for c in bg) if hover else bg
        if disabled: col, fg = (35,35,40), (90,90,100)
        pygame.draw.rect(surf, col, rect, border_radius=6)
        pygame.draw.rect(surf, fg, rect, 2 if hover else 1, border_radius=6)
        t = (font or F_SM).render(label, True, fg)
        surf.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))

    def draw(self, surf):
        mx, my = pygame.mouse.get_pos()
        self.pulse += 0.05
        if self.toast_t > 0: self.toast_t -= 1/60
        self._btn(surf, self.BTN, "Skill Builder", (20,95,30) if self.open else (20,70,25), (210,255,210), F_MD)

        if self.testing:
            t = F_MD.render("Testing skill...", True, (255,230,100))
            surf.blit(t, (WIDTH//2 - t.get_width()//2, 16))
            return
        if not self.open: return

        P = self.PANEL
        bg = pygame.Surface((P.w, P.h), pygame.SRCALPHA)
        bg.fill((12,12,18,244))
        surf.blit(bg, P.topleft)
        pygame.draw.rect(surf, (80,100,160), P, 2, border_radius=8)
        pygame.draw.rect(surf, (30,30,50), pygame.Rect(P.x + 2, P.y + 2, P.w - 4, 38), border_radius=6)
        surf.blit(F_TTL.render("Skill Builder", True, (180,255,180)), (P.x + 14, P.y + 9))

        nr = pygame.Rect(P.x + 200, P.y + 6, 300, 28)
        pygame.draw.rect(surf, (30,55,30) if self.name_active else (22,32,22), nr, border_radius=4)
        pygame.draw.rect(surf, (100,255,100) if self.name_active else (70,130,70), nr, 2, border_radius=4)
        cur = "_" if self.name_active and int(self.pulse*3) % 2 == 0 else ""
        surf.blit(F_SM.render(f"Name: {self.name}{cur}", True, (210,255,210)), (nr.x + 8, nr.y + 6))
        total = sum(block_duration(b) for b in self.blocks)
        surf.blit(F_SM.render(f"{len(self.blocks)} blocks  ~{total:.1f}s", True, (140,190,140)), (P.x + 520, P.y + 12))
        self._btn(surf, pygame.Rect(P.right - 100, P.y + 6, 88, 28), "Close", (90,30,30), (255,170,170))

        hover_desc = ""

        # palette
        surf.blit(F_XS.render("CLICK A BLOCK TO ADD IT", True, (120,150,120)), (P.x + self.PAL_X, P.y + self.BODY_Y - 14))
        pa = self._pal_area()
        old = surf.get_clip(); surf.set_clip(pa)
        for kind, d, r in self._palette_layout():
            if not pa.colliderect(r): continue
            if kind == "head":
                surf.blit(F_XS.render(d.upper(), True, CAT_COL[d]), (r.x + 2, r.y + 3))
            else:
                c = CAT_COL[d["cat"]]
                self._btn(surf, r, ("+ " + d["name"]), tuple(v//5 for v in c), tuple(min(255, v + 40) for v in c))
                if r.collidepoint(mx, my) and pa.collidepoint(mx, my): hover_desc = d["desc"]
        surf.set_clip(old)
        ph = self._pal_content_h()
        if ph > pa.h:
            bar_h = max(30, int(pa.h*pa.h/ph))
            frac = self.pal_scroll/max(1, ph - pa.h)
            pygame.draw.rect(surf, (45,60,45), (pa.right - 6, pa.y + 2, 5, pa.h - 4), border_radius=3)
            pygame.draw.rect(surf, (120,200,120), (pa.right - 6, pa.y + 2 + int(frac*(pa.h - 4 - bar_h)), 5, bar_h), border_radius=3)

        # block list
        la = self._list_area()
        pygame.draw.rect(surf, (16,16,24), la, border_radius=6)
        pygame.draw.rect(surf, (55,70,110), la, 1, border_radius=6)
        old = surf.get_clip(); surf.set_clip(la)
        for i, b in enumerate(self.blocks):
            w = self._row_widgets(i, b)
            r = w["row"]
            if not la.colliderect(r): continue
            d = BDEF[b["type"]]
            c = CAT_COL[d["cat"]]
            sel = (i == self.sel)
            pygame.draw.rect(surf, tuple(v//6 + (14 if sel else 6) for v in c), r, border_radius=6)
            pygame.draw.rect(surf, (255,255,255) if sel else c, r, 2 if sel else 1, border_radius=6)
            pygame.draw.rect(surf, c, (r.x, r.y, 6, r.h), border_top_left_radius=6, border_bottom_left_radius=6)
            surf.blit(F_SM.render(str(i + 1), True, (170,170,190)), (r.x + 12, r.y + 6))
            surf.blit(F_SM.render(b["type"], True, (255,255,255)), (r.x + 30, r.y + 6))
            dur = block_duration(b)
            surf.blit(F_XS.render("runs in background" if dur == 0 else f"takes {dur:.2f}s", True, (140,140,160)), (r.x + 30, r.y + 32))
            if not w["params"]:
                surf.blit(F_XS.render("no settings", True, (110,110,130)), (r.x + 156, r.y + 30))
            for spec, px, a, v, p in w["params"]:
                surf.blit(F_XS.render(spec["label"], True, (150,160,190)), (px, r.y + 8))
                if spec["kind"] == "num":
                    self._btn(surf, a, "-", (70,25,25), (255,140,140))
                    pygame.draw.rect(surf, (10,10,16), v, border_radius=4)
                    t = F_SM.render(fmt_val(b["p"][spec["key"]], spec["step"]), True, (255,255,255))
                    surf.blit(t, (v.centerx - t.get_width()//2, v.centery - t.get_height()//2))
                    self._btn(surf, p, "+", (25,70,25), (140,255,140))
                elif spec["kind"] == "color":
                    ci = b["p"]["color"] % len(SB_COLORS)
                    pygame.draw.rect(surf, SB_COLORS[ci], a, border_radius=5)
                    pygame.draw.rect(surf, (230,230,230), a, 1, border_radius=5)
                    t = F_SM.render(SB_COLOR_NAMES[ci], True, (0,0,0))
                    surf.blit(t, (a.centerx - t.get_width()//2, a.centery - t.get_height()//2))
                else:
                    self._btn(surf, a, b["p"][spec["key"]], (40,40,70), (200,210,255))
            self._btn(surf, w["up"], "▲", (40,40,65), (200,200,255), disabled=(i == 0))
            self._btn(surf, w["dn"], "▼", (40,40,65), (200,200,255), disabled=(i == len(self.blocks) - 1))
            self._btn(surf, w["dup"], "x2", (35,55,75), (150,210,255), F_XS)
            self._btn(surf, w["del"], "X", (100,25,25), (255,140,140))
            if r.collidepoint(mx, my) and not hover_desc: hover_desc = d["desc"]
        surf.set_clip(old)

        if not self.blocks:
            for k, line in enumerate(["Empty skill!", "Click blocks on the left to build one.", "Blocks play from top to bottom."]):
                t = (F_MD if k == 0 else F_SM).render(line, True, (80,110,80))
                surf.blit(t, (la.centerx - t.get_width()//2, la.centery - 30 + k*26))
        content_h = len(self.blocks)*(self.ROW_H + self.ROW_GAP) + 8
        if content_h > la.h:
            bar_h = max(30, int(la.h*la.h/content_h))
            frac = self.scroll/max(1, content_h - la.h)
            pygame.draw.rect(surf, (45,60,45), (la.right - 9, la.y + 2, 6, la.h - 4), border_radius=3)
            pygame.draw.rect(surf, (120,200,120), (la.right - 9, la.y + 2 + int(frac*(la.h - 4 - bar_h)), 6, bar_h), border_radius=3)

        # right column
        rb = self._right_buttons()
        self._btn(surf, rb["test"],  "►  TEST SKILL", (110,80,0), (255,220,90), F_MD)
        self._btn(surf, rb["save"],  "SAVE SKILL" if not self.editing_uid else "SAVE CHANGES", (0,85,30), (150,255,160), F_MD)
        self._btn(surf, rb["undo"],  "Undo", (45,45,60), (200,200,230), disabled=not self.undo)
        self._btn(surf, rb["redo"],  "Redo", (45,45,60), (200,200,230), disabled=not self.redo)
        self._btn(surf, rb["new"],   "New", (45,45,60), (200,200,230))
        self._btn(surf, rb["ex"],    "Examples", (60,45,75), (230,190,255))
        self._btn(surf, rb["reset"], "Reset Arena", (60,35,35), (255,190,190))

        sa = self._saved_area()
        surf.blit(F_XS.render("SAVED SKILLS  (click = edit)", True, (120,150,180)), (sa.x, sa.y - 16))
        pygame.draw.rect(surf, (16,16,24), sa, border_radius=6)
        pygame.draw.rect(surf, (55,70,110), sa, 1, border_radius=6)
        old = surf.get_clip(); surf.set_clip(sa)
        for i, sk in enumerate(self.saved):
            ry = sa.y + i*48 - self.saved_scroll
            r = pygame.Rect(sa.x, ry, sa.w, 42)
            if not sa.colliderect(r): continue
            editing = (sk["uid"] == self.editing_uid)
            pygame.draw.rect(surf, (30,60,30) if editing else (24,24,38), r, border_radius=5)
            pygame.draw.rect(surf, (100,220,100) if editing else (60,70,110), r, 1, border_radius=5)
            nm = sk["name"] if len(sk["name"]) <= 9 else sk["name"][:8] + "."
            surf.blit(F_SM.render(nm, True, (230,240,230)), (r.x + 6, ry + 5))
            slot = self.slot_of(sk["uid"])
            surf.blit(F_XS.render(f"[{slot}] key" if slot else f"{len(sk['blocks'])} blocks", True, (255,220,100) if slot else (120,150,120)), (r.x + 6, ry + 25))
            self._btn(surf, pygame.Rect(r.x + 100, ry + 7, 40, 28), "Edit", (35,45,75), (180,200,255), F_XS)
            self._btn(surf, pygame.Rect(r.x + 144, ry + 7, 40, 28), "Un" if slot else "Equip", (80,60,10) if slot else (30,75,30), (255,220,100) if slot else (150,255,150), F_XS)
            self._btn(surf, pygame.Rect(r.x + 188, ry + 7, 22, 28), "X", (100,25,25), (255,140,140), F_XS)
        surf.set_clip(old)
        if not self.saved:
            surf.blit(F_XS.render("Nothing saved yet", True, (90,110,90)), (sa.x + 10, sa.y + 12))

        # bottom bar
        bar = pygame.Rect(P.x + 10, P.bottom - 36, P.w - 20, 28)
        pygame.draw.rect(surf, (20,22,34), bar, border_radius=5)
        if self.toast_t > 0:      msg, col = self.toast, (255,230,120)
        elif hover_desc:          msg, col = hover_desc, (200,220,255)
        else:                     msg, col = "Tips:  new blocks go BELOW the selected one  |  wheel over the block list scrolls it (over the palette too)  |  Shift+click - / + = x10  |  Ctrl+Z undo", (130,140,170)
        surf.blit(F_SM.render(msg, True, col), (bar.x + 10, bar.y + 6))


# ══════════════════════════════════════════════════════════
#  HOTBAR
# ══════════════════════════════════════════════════════════
class Hotbar:
    def draw(self, surf, player, game):
        gap = 10
        slots = [("[1]", "Normal Punch", player.cd1, Player.PUNCH_CD, (255,210,60), player.pending is not None),
                 ("[2]", "Consecutive Punches", player.cd2, CONS_CD, (255,150,60), player.cons is not None),
                 ("[3]", "Shove", player.cd3, SHOVE_CD, (120,200,255), player.shoving is not None),
                 ("[4]", "Uppercut", player.cd4, UPPER_CD, (200,160,255), player.upper is not None)]
        running = isinstance(game.cinematic, SkillRun)
        for key, lbl in SLOT_KEYS:
            uid = game.skill_ui.equipped.get(lbl)
            sk = game.skill_ui.get_skill(uid) if uid else None
            if sk:
                slots.append((f"[{lbl}]", sk["name"], game.custom_cds.get(key, 0.0), CUSTOM_CD,
                              (100,255,100), running and game.active_key == key))
        sw = int(min(130, (WIDTH - 40 - (len(slots)-1)*gap)/len(slots)))
        sh = 62
        total_w = len(slots)*sw + (len(slots)-1)*gap
        sx0, y = WIDTH//2 - total_w//2, HEIGHT - 85
        for i, (kb, name, cd, max_cd, col, active) in enumerate(slots):
            sx = sx0 + i*(sw + gap)
            s = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.rect(s, (40,30,80,220) if active else (20,20,30,210), (0, 0, sw, sh), border_radius=9)
            pygame.draw.rect(s, (*col, 255) if active else (70,70,110,255), (0, 0, sw, sh), 2, border_radius=9)
            if cd > 0:
                frac = 1 - cd/max_cd
                pygame.draw.rect(s, (60,60,80,180), (2, sh-8, sw-4, 6), border_radius=3)
                pygame.draw.rect(s, (*col, 200), (2, sh-8, int((sw-4)*clamp(frac, 0, 1)), 6), border_radius=3)
            surf.blit(s, (sx, y))
            surf.blit(F_MD.render(kb, True, col if active else (170,170,210)), (sx + 8, y + 6))
            nm = F_SM.render(name, True, (230,230,255))
            if nm.get_width() > sw - 14: nm = F_XS.render(name, True, (230,230,255))
            while nm.get_width() > sw - 14 and len(name) > 4:
                name = name[:-2]
                nm = F_XS.render(name + "..", True, (230,230,255))
            surf.blit(nm, (sx + 8, y + 32))


# ══════════════════════════════════════════════════════════
#  GAME
# ══════════════════════════════════════════════════════════
class Game:
    def __init__(self):
        self.arena    = Arena()
        self.player   = Player()
        self.dummy    = Dummy()
        self.hotbar   = Hotbar()
        self.skill_ui = SkillBuilderUI()
        self.cinematic = None
        self.active_key = None
        self.custom_cds = {}
        self.time_scale = 1.0
        self.raw_dt = 1/60
        self.ko_timer = self.respawn_timer = 0.0
        self.ko_showing = False
        self.running = True

    def reset_dummy(self):
        self.dummy.reset()
        self.ko_showing = False
        self.ko_timer = self.respawn_timer = 0.0

    def reset_all(self):
        self.reset_dummy()
        self.player.reset()
        fx.clear()
        self.cinematic = None
        self.time_scale = 1.0
        self.skill_ui.testing = False
        buffs.clear()

    def start_skill(self, blocks, key=None):
        if not self.dummy.alive: self.reset_dummy()
        self.time_scale = 1.0
        self.active_key = key
        self.cinematic = SkillRun(self, blocks)

    def run(self):
        while self.running:
            dt = min(clock.tick(FPS)/1000.0, 0.05)
            self._events()
            self._update(dt)
            self._draw()
        pygame.quit(); sys.exit()

    def _events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            if self.skill_ui.handle_event(ev, self): continue
            if ev.type == pygame.KEYDOWN:
                k = ev.key
                if k == pygame.K_1:
                    self.player.use_normal_punch(self.dummy)
                elif k == pygame.K_2:
                    self.player.use_consecutive_punches(self.dummy)
                elif k == pygame.K_3:
                    self.player.use_shove(self.dummy)
                elif k == pygame.K_4:
                    self.player.use_uppercut(self.dummy)
                elif k == pygame.K_r:
                    self.player.use_serious()
                elif k == pygame.K_t:
                    self.reset_all()
                else:
                    for key, lbl in SLOT_KEYS:
                        if k == key: self._custom_skill(key, lbl)

    def _custom_skill(self, key, lbl):
        if self.cinematic or self.player.busy: return
        uid = self.skill_ui.equipped.get(lbl)
        sk = self.skill_ui.get_skill(uid) if uid else None
        if not sk: return
        if self.custom_cds.get(key, 0) <= 0:
            self.start_skill(sk["blocks"], key)
            self.custom_cds[key] = CUSTOM_CD

    def _update(self, raw_dt):
        self.raw_dt = raw_dt
        if not self.cinematic: self.time_scale = 1.0
        dt = raw_dt*self.time_scale
        keys = pygame.key.get_pressed()
        buffs.update(dt)

        self.player.locked = isinstance(self.cinematic, SkillRun) or (self.skill_ui.open and not self.skill_ui.testing)
        if self.cinematic:
            self.cinematic.update(dt)
            if self.cinematic.done:
                self.cinematic = None
                self.time_scale = 1.0
        self.player.update(dt, keys, self.dummy)
        self.dummy.update(dt)
        fx.update(dt, self.dummy)

        for k in self.custom_cds:
            if self.custom_cds[k] > 0: self.custom_cds[k] -= dt
        if self.skill_ui.testing and not self.cinematic:
            self.skill_ui.testing = False

        if not self.dummy.alive and not self.ko_showing:
            self.ko_showing, self.ko_timer, self.respawn_timer = True, 3.5, 2.0
        if self.ko_showing:
            self.ko_timer -= dt
            if self.ko_timer <= 0: self.ko_showing = False
        if self.respawn_timer > 0:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0: self.reset_dummy()

    def _draw(self):
        self.arena.draw(world)
        fx.draw_under(world)
        self.dummy.draw(world)
        self.player.draw(world)
        fx.draw_over(world)

        ox, oy = fx.shake_offset()
        screen.fill((0, 0, 0))
        screen.blit(world, (ox, oy))
        fx.draw_flash(screen)

        self._draw_hud()
        self.hotbar.draw(screen, self.player, self)
        self.skill_ui.draw(screen)
        if self.ko_showing: self._draw_ko()
        pygame.display.flip()

    def _draw_serious_hud(self):
        if not buffs.active: return
        bw, bh = 300, 16
        bx, by = WIDTH//2 - bw//2, 12
        pulse = 0.5 + 0.5*math.sin(pygame.time.get_ticks()*0.012)
        pygame.draw.rect(screen, (50,12,12), (bx, by, bw, bh), border_radius=5)
        pygame.draw.rect(screen, (255, int(70 + 80*pulse), 40), (bx, by, int(bw*buffs.t/buffs.dur), bh), border_radius=5)
        pygame.draw.rect(screen, (255,200,180), (bx, by, bw, bh), 1, border_radius=5)
        lbl = F_SM.render(f"SERIOUS MODE  +{buffs.pct:g}% DMG   {buffs.t:.1f}s", True, (255,230,220))
        screen.blit(lbl, (WIDTH//2 - lbl.get_width()//2, by + bh + 3))

    def _draw_hud(self):
        self._draw_serious_hud()
        if not self.skill_ui.open:
            screen.blit(F_MD.render("THE STRONGEST HERO", True, (255,210,60)), (AL + 4, AT + 4))
            hint = F_SM.render("[1] Normal Punch:  CLOSE = Face Smash (20 dmg, flying)   FAR = Crater Line (10 dmg)   [4] Uppercut: 15 dmg, sends him up", True, (190,190,150))
            screen.blit(hint, (AL + 4, AT + 30))
        ctrl = F_SM.render("WASD Move  1 Normal Punch  2 Consecutive  3 Shove  4 Uppercut  R Serious Mode  T Reset  5-9/0 Your skills", True, (110,110,140))
        screen.blit(ctrl, (WIDTH//2 - ctrl.get_width()//2, HEIGHT - 22))

    def _draw_ko(self):
        t = max(0.0, self.ko_timer/3.5)
        shake_x = int(5*math.sin(self.ko_timer*28)) if self.ko_timer > 3.0 else 0
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((180, 0, 0, max(0, int(100*(1.0 - abs(t - 0.5)/0.5)))))
        screen.blit(ov, (0, 0))
        ko = F_XL.render("K.O.", True, (255,50,50)); shadow = F_XL.render("K.O.", True, (80,0,0))
        sx, sy = WIDTH//2 - ko.get_width()//2 + shake_x, HEIGHT//2 - ko.get_height()//2
        screen.blit(shadow, (sx + 5, sy + 5)); screen.blit(ko, (sx, sy))
        sub = F_MD.render(f"Respawning in {max(0.0, self.respawn_timer):.1f}s...", True, (220,180,180))
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, sy + 95))


# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    Game().run()
