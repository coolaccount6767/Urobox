import pygame, sys, math, random, os

pygame.init()
pygame.font.init()

# ──────────────────────────────────────────────────────────
#  Screen / FPS & Icon
# ──────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1200, 720
FPS           = 60

# Custom Icon Logic
icon_path = os.path.join('internal', 'icon.ico')
try:
    if os.path.exists(icon_path):
        icon_image = pygame.image.load(icon_path)
        pygame.display.set_icon(icon_image)
except Exception as e:
    print(f"Could not load icon: {e}")

screen        = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TSB Arena – Dimensional Edition")
clock         = pygame.time.Clock()

# ──────────────────────────────────────────────────────────
#  Fonts
# ──────────────────────────────────────────────────────────
F_SM  = pygame.font.SysFont("consolas", 15, bold=True)
F_MD  = pygame.font.SysFont("consolas", 20, bold=True)
F_LG  = pygame.font.SysFont("consolas", 30, bold=True)
F_XL  = pygame.font.SysFont("consolas", 80, bold=True)
F_TTL = pygame.font.SysFont("consolas", 22, bold=True)
F_EPIC = pygame.font.SysFont("impact", 120, bold=True)
F_EPIC2 = pygame.font.SysFont("impact", 60, bold=False)

# ──────────────────────────────────────────────────────────
#  Arena geometry
# ──────────────────────────────────────────────────────────
AL, AR, AT, AB = 55, WIDTH-55, 55, HEIGHT-115   # left right top bottom
AW = AR - AL
AH = AB - AT

PLAYER_SIZE  = 40
DUMMY_SIZE   = 44
PLAYER_SPEED = 230
PUNCH_RANGE  = 190

DIMENSIONS = ["Battlegrounds", "Lava Realm"]
DIM_IDX    = 0          

# ══════════════════════════════════════════════════════════
#  PARTICLE
# ══════════════════════════════════════════════════════════
class Particle:
    __slots__ = ("x","y","vx","vy","color","radius","life","max_life","fade","grav","alive", "shape")
    def __init__(self, x, y, vx, vy, color, radius, life, fade=True, grav=0, shape="circle"):
        self.x,self.y     = x,y
        self.vx,self.vy   = vx,vy
        self.color        = color
        self.radius       = radius
        self.life         = life
        self.max_life     = life
        self.fade         = fade
        self.grav         = grav
        self.shape        = shape
        self.alive        = True

    def update(self, dt):
        self.x  += self.vx*dt
        self.y  += self.vy*dt
        self.vy += self.grav*dt
        self.life -= dt
        if self.life <= 0: self.alive = False

    def draw(self, surf):
        if not self.alive: return
        t = max(0.0, self.life/self.max_life)
        a = int(255*t) if self.fade else 255
        r = max(1, int(self.radius*t))
        if r <= 0: r = 1
        s = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
        if self.shape == "circle":
            pygame.draw.circle(s, (*self.color[:3], a), (r,r), r)
        else:
            pygame.draw.rect(s, (*self.color[:3], a), (0,0,r*2,r*2))
        surf.blit(s, (int(self.x)-r, int(self.y)-r))

def burst(cx, cy, count, colors, rmin=3, rmax=9,
          smin=40, smax=300, lmin=0.3, lmax=1.0, grav=0, shape="circle"):
    out = []
    for _ in range(count):
        a  = random.uniform(0, math.tau)
        sp = random.uniform(smin, smax)
        out.append(Particle(cx, cy, math.cos(a)*sp, math.sin(a)*sp,
                            random.choice(colors),
                            random.randint(rmin,rmax),
                            random.uniform(lmin,lmax), True, grav, shape))
    return out

# ══════════════════════════════════════════════════════════
#  WATER BLOB  (Walking Barrage)
# ══════════════════════════════════════════════════════════
class WaterBlob:
    def __init__(self, x, y, dx, dy):
        self.x, self.y = float(x), float(y)
        self.vx = dx * random.uniform(320, 480)
        self.vy = dy * random.uniform(320, 480) + random.uniform(-40,40)
        self.life = 0.65
        self.max_life = 0.65
        self.r = random.randint(12, 22)
        self.alive = True
        self.hit   = False

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 80 * dt     
        self.life -= dt
        if self.life <= 0: self.alive = False

    def draw(self, surf):
        if not self.alive: return
        t = max(0.0, self.life / self.max_life)
        a = int(220 * t)
        r = max(1, int(self.r * (0.5 + 0.5*t)))
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (80, 180, 255, a),   (r,r), r)
        pygame.draw.circle(s, (180,230,255, a//2), (r,r), max(1,r-3))
        surf.blit(s, (int(self.x)-r, int(self.y)-r))

    @property
    def rect(self): return pygame.Rect(int(self.x)-self.r, int(self.y)-self.r, self.r*2, self.r*2)

# ══════════════════════════════════════════════════════════
#  HELPER & FISTS
# ══════════════════════════════════════════════════════════
class Helper:
    SIZE   = 28
    SPEED  = 210
    PUNCH_RANGE = 60
    PUNCH_INTERVAL = 0.22
    FOLLOW_OFFSET  = 55

    def __init__(self):
        self.active = False
        self.life = 0.0
        self.x = 0.0
        self.y = 0.0
        self.punch_timer = 0.0
        self.particles: list[Particle] = []
        self.fists: list = []
        self.bob_t = 0.0

    def spawn(self, x, y):
        self.active = True
        self.life = 10.0
        self.x = float(x)
        self.y = float(y)
        self.particles = []
        self.fists = []

    @property
    def cx(self): return self.x + self.SIZE//2
    @property
    def cy(self): return self.y + self.SIZE//2
    @property
    def rect(self): return pygame.Rect(int(self.x), int(self.y), self.SIZE, self.SIZE)

    def update(self, dt, player, dummy, global_particles):
        if not self.active: return
        self.life -= dt
        if self.life <= 0:
            self.active = False
            global_particles += burst(self.cx, self.cy, 60, [(255,255,255),(180,220,255),(100,180,255)], 4, 12, 60, 400, 0.4, 1.2, grav=200, shape="rect")
            return

        self.bob_t += dt * 4.0
        player_to_dummy = (math.hypot(dummy.cx - player.cx, dummy.cy - player.cy) if dummy.alive else 9999.0)

        if dummy.alive and player_to_dummy < 200:
            target_x = dummy.cx - self.SIZE // 2 - 36
            target_y = dummy.cy - self.SIZE // 2
        else:
            target_x = player.cx - self.FOLLOW_OFFSET - self.SIZE // 2
            target_y = player.cy - self.SIZE // 2 + 6

        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        if dist > 8:
            speed = min(self.SPEED * (1 + dist / 100), self.SPEED * 2.8)
            self.x += (dx / dist) * speed * dt
            self.y += (dy / dist) * speed * dt
            
        self.x = max(AL, min(AR - self.SIZE, self.x))
        self.y = max(AT, min(AB - self.SIZE, self.y))

        if dummy.alive:
            ddx = dummy.cx - self.cx
            ddy = dummy.cy - self.cy
            d_dist = math.hypot(ddx, ddy)
            self.punch_timer -= dt
            if d_dist <= self.PUNCH_RANGE and self.punch_timer <= 0:
                self.punch_timer = self.PUNCH_INTERVAL
                ndx = ddx / d_dist; ndy = ddy / d_dist
                fx = self.cx + ndx * (self.SIZE // 2 + 4)
                fy = self.cy + ndy * (self.SIZE // 2 + 4)
                self.fists.append(_Fist(fx, fy, ndx, ndy, (80,180,255)))
                dummy.take_damage(4)
                self.particles += burst(dummy.cx, dummy.cy, 6, [(80,180,255),(200,240,255)], 2, 5, 40, 120, 0.15, 0.35)

        for f in self.fists[:]:
            f.update(dt)
            if not f.alive: self.fists.remove(f)
        for p in self.particles[:]:
            p.update(dt)
            if not p.alive: self.particles.remove(p)

    def draw(self, surf):
        if not self.active: return
        for p in self.particles: p.draw(surf)
        bob = math.sin(self.bob_t) * 2
        r = pygame.Rect(int(self.x), int(self.y + bob), self.SIZE, self.SIZE)
        gs = pygame.Surface((self.SIZE + 20, self.SIZE + 20), pygame.SRCALPHA)
        pygame.draw.rect(gs, (60, 140, 230, 40), (0, 0, self.SIZE+20, self.SIZE+20), border_radius=8)
        surf.blit(gs, (r.x - 10, r.y - 10))
        pygame.draw.rect(surf, (20, 80, 180), r.inflate(4, 4), border_radius=6)
        pygame.draw.rect(surf, (60, 140, 230), r, border_radius=5)
        ey = r.y + self.SIZE // 4
        pygame.draw.circle(surf, (0, 0, 0), (r.x + self.SIZE//4, ey), 3)
        pygame.draw.circle(surf, (0, 0, 0), (r.x + self.SIZE*3//4, ey), 3)
        pygame.draw.circle(surf, (255, 255, 255), (r.x + self.SIZE//4 + 1, ey - 1), 1)
        pygame.draw.circle(surf, (255, 255, 255), (r.x + self.SIZE*3//4 + 1, ey - 1), 1)
        lbl = F_SM.render("H", True, (180, 220, 255))
        surf.blit(lbl, (r.x + self.SIZE//2 - lbl.get_width()//2, r.y + self.SIZE//2 - 1))
        for f in self.fists: f.draw(surf)

class _Fist:
    def __init__(self, x,y,dx,dy,col):
        self.x,self.y   = x,y
        self.dx,self.dy = dx,dy
        self.col = col
        self.life = self.max_life = 0.14
        self.alive = True
        self.w,self.h = 20,13

    def update(self, dt):
        self.x += self.dx*dt*400; self.y += self.dy*dt*400
        self.life -= dt
        if self.life <= 0: self.alive = False

    def draw(self, surf):
        if not self.alive: return
        a = int(255*(self.life/self.max_life))
        s = pygame.Surface((self.w+10,self.h+10), pygame.SRCALPHA)
        pygame.draw.rect(s, (*self.col[:3], a//2), (0,0,self.w+10,self.h+10), border_radius=4)
        pygame.draw.rect(s, (*self.col[:3], a),    (5,5,self.w,self.h),        border_radius=3)
        surf.blit(s, (int(self.x)-self.w//2, int(self.y)-self.h//2))

# ══════════════════════════════════════════════════════════
#  DUMMY
# ══════════════════════════════════════════════════════════
class Dummy:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x, self.y   = float(WIDTH//2 - DUMMY_SIZE//2), float((AT+AB)//2 - DUMMY_SIZE//2)
        self.hp          = 100.0
        self.max_hp      = 100.0
        self.alive       = True
        self.vx = self.vy = 0.0
        self.kb_timer    = 0.0
        self.flash_timer = 0.0
        self.particles: list[Particle] = []
        self.lava_death  = False
        self.dead_timer  = 0.0
        self.galaxy_death = False
        self.galaxy_timer = 0.0
        self.galaxy_scale = 1.0
        self.is_marked    = False

    @property
    def cx(self): return self.x + DUMMY_SIZE//2
    @property
    def cy(self): return self.y + DUMMY_SIZE//2
    @property
    def rect(self): return pygame.Rect(int(self.x), int(self.y), DUMMY_SIZE, DUMMY_SIZE)

    def take_damage(self, dmg):
        if not self.alive: return
        self.hp = max(0.0, self.hp - dmg)
        self.flash_timer = 0.09
        if self.hp <= 0: 
            self.hp = 0.0
            self.alive = False

    def apply_kb(self, vx, vy, dur):
        self.vx, self.vy = vx, vy
        self.kb_timer = dur

    def trigger_lava_death(self):
        if self.lava_death: return
        self.lava_death = True
        self.alive = False
        self.hp = 0.0
        self.dead_timer = 1.4
        self.particles += burst(self.cx, self.cy, 70,
            [(220,60,10),(255,130,0),(255,220,0),(255,255,200)], 4,13, 60,290, 0.4,1.1, 80)

    def trigger_galaxy_death(self):
        if self.galaxy_death: return
        self.galaxy_death = True
        self.alive = False
        self.hp = 0.0
        self.galaxy_timer = 2.0
        self.galaxy_scale = 1.0
        self.particles += burst(self.cx, self.cy, 80,
            [(180,100,255),(80,200,255),(255,255,255),(120,0,200),(255,180,255)],
            4,12, 80,320, 0.5,1.2)

    def update(self, dt, dim_idx):
        for p in self.particles[:]:
            p.update(dt)
            if not p.alive: self.particles.remove(p)
        if self.flash_timer > 0: self.flash_timer -= dt

        if self.kb_timer > 0:
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.kb_timer -= dt
            if self.y < AT:                   self.y = AT;               self.vy *= -0.4
            if self.y+DUMMY_SIZE > AB:        self.y = AB-DUMMY_SIZE;    self.vy *= -0.4
            if self.x < AL:                   self.x = AL;               self.vx *= -0.4
            if self.x+DUMMY_SIZE > AR:        self.x = AR-DUMMY_SIZE;    self.vx *= -0.4

        if dim_idx == 1 and self.alive:
            lava_rect = pygame.Rect(AL, AT, AW, AH)
            if lava_rect.colliderect(self.rect):
                self.trigger_lava_death()

        if self.lava_death and self.dead_timer > 0: self.dead_timer -= dt
        if self.galaxy_death and self.galaxy_timer > 0:
            self.galaxy_timer -= dt
            self.galaxy_scale = max(0.0, self.galaxy_timer / 2.0)

    def draw(self, surf):
        for p in self.particles: p.draw(surf)

        if self.lava_death:
            sc = max(0.0, self.dead_timer / 1.4)
            sz = int(DUMMY_SIZE * sc)
            if sz > 2:
                s = pygame.Surface((sz,sz), pygame.SRCALPHA)
                pygame.draw.rect(s, (255,80,0, int(255*sc)), (0,0,sz,sz), border_radius=4)
                surf.blit(s, (int(self.cx)-sz//2, int(self.cy)-sz//2))
            return

        if self.galaxy_death:
            sc = self.galaxy_scale
            sz = int(DUMMY_SIZE * sc)
            if sz > 2:
                s = pygame.Surface((sz,sz), pygame.SRCALPHA)
                a = int(255 * sc)
                pygame.draw.rect(s, (150,50,255,a), (0,0,sz,sz), border_radius=4)
                for i in range(5):
                    ang = pygame.time.get_ticks()*0.003 + i*1.25
                    px = sz//2 + int(sz*0.4*math.cos(ang))
                    py = sz//2 + int(sz*0.4*math.sin(ang))
                    pygame.draw.circle(s, (255,255,255,a), (px,py), 2)
                surf.blit(s, (int(self.cx)-sz//2, int(self.cy)-sz//2))
            return

        if not self.alive: return

        col = (255,255,255) if self.flash_timer > 0 else (210,90,90)
        out = (255,255,255) if self.flash_timer > 0 else (160,50,50)
        r = self.rect
        pygame.draw.rect(surf, out, r.inflate(4,4), border_radius=6)
        pygame.draw.rect(surf, col, r,              border_radius=5)
        ey = int(self.y)+12
        pygame.draw.circle(surf, (0,0,0),   (int(self.x)+12, ey), 5)
        pygame.draw.circle(surf, (0,0,0),   (int(self.x)+DUMMY_SIZE-12, ey), 5)
        pygame.draw.circle(surf, (255,255,255),(int(self.x)+14, ey-1), 2)
        pygame.draw.circle(surf, (255,255,255),(int(self.x)+DUMMY_SIZE-10,ey-1),2)

        if self.is_marked:
            pygame.draw.line(surf, (220, 20, 40), (self.cx - 15, self.y - 25), (self.cx + 15, self.y - 5), 4)
            pygame.draw.line(surf, (220, 20, 40), (self.cx + 15, self.y - 25), (self.cx - 15, self.y - 5), 4)

        bw, bh = 82, 10
        bx = int(self.cx - bw//2)
        by = int(self.y) - 24
        pygame.draw.rect(surf, (50,15,15), (bx,by,bw,bh), border_radius=3)
        fw = int(bw * self.hp / self.max_hp)
        if fw > 0:
            pygame.draw.rect(surf, (70,210,70), (bx,by,fw,bh), border_radius=3)
        pygame.draw.rect(surf, (200,200,200), (bx,by,bw,bh), 1, border_radius=3)
        lbl = F_SM.render(f"{self.hp:.1f}/{self.max_hp:.0f} HP", True, (255,255,255))
        surf.blit(lbl, (bx+bw//2-lbl.get_width()//2, by-17))

# ══════════════════════════════════════════════════════════
#  PLAYER
# ══════════════════════════════════════════════════════════
class Player:
    def __init__(self):
        self.x = float(AL + 90)
        self.y = float((AT+AB)//2 - PLAYER_SIZE//2)
        self.state = "NORMAL" 
        
        self.stars:   list[Particle] = []
        self.nebula:  list[Particle] = []
        self.star_t   = 0.0
        self.nebula_t = 0.0
        self.cosmic_pulse = 0.0
        
        self.punch_active   = False
        self.punch_hits     = 0
        self.punch_timer    = 0.0
        self.punch_interval = 0.09
        self.fists:  list  = []
        self.aura_p: list[Particle] = []
        
        self.water_active  = False
        self.water_timer   = 0.0
        self.water_blobs:  list[WaterBlob] = []
        self.water_wave    = 0
        self.water_total   = 40    
        
        self.galaxy_cd  = 0.0      
        self.push_cd    = 0.0      
        self.skill1_cd  = 0.0
        self.skill2_cd  = 0.0
        self.skill3_cd  = 0.0
        
        self.rush_timer = 0.0
        self.rush_particles: list[Particle] = []

    @property
    def cx(self): return self.x + PLAYER_SIZE//2
    @property
    def cy(self): return self.y + PLAYER_SIZE//2
    @property
    def rect(self): return pygame.Rect(int(self.x), int(self.y), PLAYER_SIZE, PLAYER_SIZE)

    def go_cosmic(self): self.state = "COSMIC"
    def go_reaper(self): self.state = "REAPER"
    def go_normal(self): self.state = "NORMAL"
    def go_projection(self): self.state = "PROJECTION"

    def use_skill1(self):
        if self.state == "NORMAL":
            if not self.punch_active and self.skill1_cd <= 0:
                self.punch_active = True
                self.punch_hits   = 0
                self.punch_timer  = 0.0
                self.skill1_cd    = 1.2
        elif self.state == "COSMIC":  
            return "GALACTIC_PUSH"
        elif self.state == "REAPER":
            return "SOUL_DRAIN"
        elif self.state == "PROJECTION":
            return "DECISIVE_STRIKE"

    def use_skill2(self):
        if self.state == "NORMAL":
            if not self.water_active and self.skill2_cd <= 0:
                self.water_active = True
                self.water_timer  = 0.0
                self.water_wave   = 0
                self.skill2_cd    = 3.5
        elif self.state == "COSMIC":  
            return "GALAXY_PULL"
        elif self.state == "REAPER":
            if self.skill2_cd <= 0:
                self.rush_timer = 3.0
                self.skill2_cd = 6.0
                return "RUSH_STARTED"
        elif self.state == "PROJECTION":
            return None

    def use_skill3(self):
        if self.state == "NORMAL":
            return "WHIRLWIND_WATER"
        elif self.state == "COSMIC":
            return "PORTAL_NAUSEA"
        elif self.state == "REAPER":
            return "REAPER_MARK"
        elif self.state == "PROJECTION":
            return None

    def update(self, dt, keys, dummy):
        dx = dy = 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        if dx and dy: dx *= 0.7071; dy *= 0.7071
        
        speed = PLAYER_SPEED
        if self.rush_timer > 0:
            speed = PLAYER_SPEED * 2.5
            self.rush_timer -= dt
            self.rush_particles.append(Particle(
                self.cx+random.uniform(-10,10), self.cy+random.uniform(-10,10),
                0, 0, (140, 20, 30), random.randint(6,12), 0.4, True, shape="rect"
            ))
            if self.rect.colliderect(dummy.rect) and dummy.alive:
                self.rush_timer = 0.0
                return "MENACING_CUTSCENE"
        else:
            speed = PLAYER_SPEED

        for p in self.rush_particles[:]:
            p.update(dt)
            if not p.alive: self.rush_particles.remove(p)

        self.x = max(AL, min(AR-PLAYER_SIZE, self.x + dx*speed*dt))
        self.y = max(AT, min(AB-PLAYER_SIZE, self.y + dy*speed*dt))

        if self.skill1_cd > 0: self.skill1_cd -= dt
        if self.skill2_cd > 0: self.skill2_cd -= dt
        if self.skill3_cd > 0: self.skill3_cd -= dt

        if self.state == "COSMIC":
            self.cosmic_pulse = (self.cosmic_pulse + dt*3) % math.tau
            self.star_t -= dt
            if self.star_t <= 0:
                self.star_t = 0.03
                a = random.uniform(0, math.tau)
                d = random.uniform(4, PLAYER_SIZE*0.8)
                self.stars.append(Particle(
                    self.cx + math.cos(a)*d, self.cy + math.sin(a)*d,
                    math.cos(a)*random.uniform(15,70), math.sin(a)*random.uniform(15,70),
                    random.choice([(255,255,255),(200,160,255),(150,100,255)]),
                    random.randint(2,5), random.uniform(0.25,0.7), True))
            self.nebula_t -= dt
            if self.nebula_t <= 0:
                self.nebula_t = 0.07
                a = random.uniform(0,math.tau)
                self.nebula.append(Particle(
                    self.cx + math.cos(a)*PLAYER_SIZE*0.6,
                    self.cy + math.sin(a)*PLAYER_SIZE*0.6,
                    math.cos(a)*random.uniform(8,30), math.sin(a)*random.uniform(8,30),
                    random.choice([(80,0,200),(120,0,160),(200,80,255),(60,0,120)]),
                    random.randint(6,14), random.uniform(0.5,1.0), True))
        
        if self.state == "REAPER":
            if random.random() < 0.3:
                self.aura_p.append(Particle(
                    self.cx+random.uniform(-15,15), self.cy+random.uniform(-15,15),
                    0, random.uniform(-40, -10), (120, 10, 20), random.randint(4,8), 0.6, True, shape="rect"
                ))
                
        if self.state == "PROJECTION":
            if random.random() < 0.4:
                self.aura_p.append(Particle(
                    self.cx+random.uniform(-10,10), self.cy+random.uniform(-10,10),
                    random.uniform(-10, 10), random.uniform(-10, 10), (255, 220, 50), random.randint(3,6), 0.5, True, shape="rect"
                ))

        for p in self.stars[:]:
            p.update(dt)
            if not p.alive: self.stars.remove(p)
        for p in self.nebula[:]:
            p.update(dt)
            if not p.alive: self.nebula.remove(p)

        if self.punch_active:
            self.punch_timer += dt
            ddx = dummy.cx - self.cx
            ddy = dummy.cy - self.cy
            dist = math.hypot(ddx,ddy) or 1
            ndx,ndy = ddx/dist, ddy/dist
            if self.punch_timer >= self.punch_hits * self.punch_interval:
                off = (-10 if self.punch_hits%2==0 else 10)
                px = -ndy*off; py = ndx*off
                col = (80,180,255) if self.punch_hits%2==0 else (160,220,255)
                fx = self.cx + ndx*22 + px
                fy = self.cy + ndy*22 + py
                self.fists.append(_Fist(fx, fy, ndx, ndy, col))
                for _ in range(6):
                    ang2 = random.uniform(0,math.tau)
                    self.aura_p.append(Particle(
                        self.cx+random.uniform(-6,6), self.cy+random.uniform(-6,6),
                        math.cos(ang2)*random.uniform(30,100), math.sin(ang2)*random.uniform(30,100),
                        (80,180,255), random.randint(3,7), 0.22, True))
                if dist <= PUNCH_RANGE and dummy.alive:
                    dummy.take_damage(8)
                self.punch_hits += 1
                if self.punch_hits >= 9:
                    self.punch_active = False

        for f in self.fists[:]:
            f.update(dt)
            if not f.alive: self.fists.remove(f)
        for p in self.aura_p[:]:
            p.update(dt)
            if not p.alive: self.aura_p.remove(p)

        if self.water_active:
            self.water_timer += dt
            interval = 0.05 
            if self.water_timer >= self.water_wave * interval:
                ddx = dummy.cx - self.cx
                ddy = dummy.cy - self.cy
                dist = math.hypot(ddx,ddy) or 1
                ndx,ndy = ddx/dist, ddy/dist
                
                for k in range(2):
                    spread = (k - 0.5) * 0.4
                    bx = self.cx + ndx*24 + (-ndy)*spread*30
                    by = self.cy + ndy*24 + (ndx)*spread*30
                    blob = WaterBlob(bx, by, ndx+(-ndy)*spread, ndy+(ndx)*spread)
                    self.water_blobs.append(blob)
                self.water_wave += 1
                if self.water_wave >= self.water_total:
                    self.water_active = False

        for b in self.water_blobs[:]:
            b.update(dt)
            if not b.alive:
                self.water_blobs.remove(b)
                continue
            if not b.hit and dummy.alive and b.rect.colliderect(dummy.rect):
                dummy.take_damage(3)
                b.hit = True
                b.alive = False
                dummy.particles += burst(b.x, b.y, 8,
                    [(80,180,255),(150,220,255),(200,240,255)], 2,5, 30,120, 0.2,0.5)

    def draw(self, surf):
        for p in self.nebula: p.draw(surf)
        for p in self.stars:  p.draw(surf)
        for p in self.aura_p: p.draw(surf)
        for p in self.rush_particles: p.draw(surf)

        r = self.rect
        if self.state == "NORMAL":
            pygame.draw.rect(surf, (30,100,200),  r.inflate(4,4), border_radius=7)
            pygame.draw.rect(surf, (60,160,240),  r,              border_radius=6)
            sh = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE//2), pygame.SRCALPHA)
            pygame.draw.rect(sh, (255,255,255,40), (0,0,PLAYER_SIZE,PLAYER_SIZE//2), border_radius=5)
            surf.blit(sh, (r.x, r.y))
        elif self.state == "COSMIC":
            pulse = int(12 * math.sin(self.cosmic_pulse))
            for expand, col, a in [
                (16+pulse, (120,0,255), 30),
                (10,       (80,0,200),  60),
                (5,        (60,0,160),  100),
            ]:
                s = pygame.Surface((PLAYER_SIZE+expand*2, PLAYER_SIZE+expand*2), pygame.SRCALPHA)
                pygame.draw.rect(s, (*col, a), (0,0,PLAYER_SIZE+expand*2,PLAYER_SIZE+expand*2), border_radius=8+expand//2)
                surf.blit(s, (r.x-expand, r.y-expand))
            
            pygame.draw.rect(surf, (150, 80, 255), r, 2, border_radius=2)
            pygame.draw.rect(surf, (20, 0, 50), r.inflate(-4,-4))
            
            t = pygame.time.get_ticks() * 0.002
            ins = int(PLAYER_SIZE * (0.4 + 0.2*math.sin(t*3)))
            ir = pygame.Rect(0,0,ins,ins)
            ir.center = (int(self.cx), int(self.cy))
            pygame.draw.rect(surf, (200, 150, 255), ir, 2, border_radius=1)
            
            pygame.draw.line(surf, (150, 80, 255), r.topleft, ir.topleft, 1)
            pygame.draw.line(surf, (150, 80, 255), r.topright, ir.topright, 1)
            pygame.draw.line(surf, (150, 80, 255), r.bottomleft, ir.bottomleft, 1)
            pygame.draw.line(surf, (150, 80, 255), r.bottomright, ir.bottomright, 1)

            for i in range(4):
                ang = t + i*math.pi/2
                ox = self.cx + int((PLAYER_SIZE*0.75)*math.cos(ang))
                oy = self.cy + int((PLAYER_SIZE*0.75)*math.sin(ang))
                pygame.draw.circle(surf, (255,255,255), (int(ox),int(oy)), 3)
                pygame.draw.circle(surf, (180,120,255), (int(ox),int(oy)), 5, 1)
        elif self.state == "REAPER":
            pygame.draw.rect(surf, (80, 0, 0),  r.inflate(4,4), border_radius=2)
            pygame.draw.rect(surf, (140, 20, 30),  r,           border_radius=2)
            ey = int(self.y) + 10
            pygame.draw.circle(surf, (0,0,0),   (int(self.x)+12, ey), 4)
            pygame.draw.circle(surf, (0,0,0),   (int(self.x)+PLAYER_SIZE-12, ey), 4)
            pygame.draw.circle(surf, (255,0,0), (int(self.x)+12, ey), 1)
            pygame.draw.circle(surf, (255,0,0), (int(self.x)+PLAYER_SIZE-12, ey), 1)
        elif self.state == "PROJECTION":
            pygame.draw.rect(surf, (200, 160, 0),  r.inflate(4,4), border_radius=0)
            pygame.draw.rect(surf, (255, 200, 50), r,              border_radius=0)
            pygame.draw.line(surf, (255, 255, 255), r.topleft, r.bottomright, 2)
            pygame.draw.line(surf, (255, 255, 255), r.topright, r.bottomleft, 2)

        for f in self.fists: f.draw(surf)
        for b in self.water_blobs: b.draw(surf)

# ══════════════════════════════════════════════════════════
#  CUBE-LIKE CHARACTERS
# ══════════════════════════════════════════════════════════
def draw_cube_guy(surf, cx, cy, size, body_col, outline_col, glow_col=None, glow_radius=0, hand_extend=0, is_blue=True, has_scythe=False):
    if glow_col and glow_radius > 0:
        gs = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
        for i in range(5):
            r2 = glow_radius - i*8
            if r2 > 0:
                a2 = 30 + i*15
                pygame.draw.circle(gs, (*glow_col, a2), (glow_radius, glow_radius), r2)
        surf.blit(gs, (int(cx) - glow_radius, int(cy) - glow_radius))

    box_size = int(size * 0.7)
    r = pygame.Rect(int(cx) - box_size//2, int(cy) - box_size//2, box_size, box_size)
    pygame.draw.rect(surf, outline_col, r.inflate(6,6), border_radius=4)
    pygame.draw.rect(surf, body_col, r, border_radius=4)
    
    ey = int(cy) - box_size//4
    pygame.draw.rect(surf, (0,0,0), (int(cx) - box_size//4 - 4, ey, 8, 8))
    pygame.draw.rect(surf, (0,0,0), (int(cx) + box_size//4 - 4, ey, 8, 8))

    if has_scythe:
        sx = int(cx) + box_size//2 + 10
        sy = int(cy)
        pygame.draw.line(surf, (60,40,20), (sx, sy+40), (sx, sy-60), 8)
        pygame.draw.polygon(surf, (180,180,180), [(sx-4, sy-50), (sx+60, sy-50), (sx+40, sy-30), (sx, sy-20)])
        pygame.draw.polygon(surf, (220,220,220), [(sx-4, sy-50), (sx+55, sy-47), (sx+35, sy-28), (sx, sy-20)])

# ══════════════════════════════════════════════════════════
#  CINEMATICS & SEQUENCES
# ══════════════════════════════════════════════════════════
class CustomSkillSequence:
    def __init__(self, player, dummy, blocks):
        self.player = player
        self.dummy = dummy
        self.blocks = blocks
        self.current_idx = 0
        self.timer = 0.0
        self.done = False
        self.particles = []
        self.fists = []

    def update(self, dt):
        if self.current_idx >= len(self.blocks):
            self.done = True
            return
            
        b = self.blocks[self.current_idx]
        btype = b['type']
        self.timer += dt
        
        if btype == 'Wait':
            if self.timer >= float(b['val']): self._next()
        elif btype == 'Movement':
            speed = float(b['val'])
            dir_x = 1 if self.player.x < self.dummy.x else -1
            self.player.x += speed * dir_x * dt
            if self.timer >= 0.3: self._next()
        elif btype == 'Visual':
            vt = b['v_type']
            col = b['color']
            val = float(b['val'])
            
            if vt in ('Aura', 'Cosmic Aura'):
                if random.random() < 0.4:
                    self.particles.append(Particle(
                        self.player.cx+random.uniform(-15,15), self.player.cy+random.uniform(-15,15),
                        random.uniform(-10,10), random.uniform(-40,-10), col, random.randint(4,8), 0.6, True
                    ))
            elif vt == 'Punches':
                if self.timer < 0.4 and int(self.timer*30) % 3 == 0:
                    ndx = 1 if self.dummy.cx > self.player.cx else -1
                    self.fists.append(_Fist(self.player.cx+ndx*20, self.player.cy+random.uniform(-15,15), ndx*1.5, 0, col))
                    if math.hypot(self.dummy.cx - self.player.cx, self.dummy.cy - self.player.cy) < PUNCH_RANGE:
                        self.dummy.take_damage(val/15.0) 
                        
            if self.timer >= 0.5:
                if vt == 'Hitbox':
                    if math.hypot(self.dummy.cx - self.player.cx, self.dummy.cy - self.player.cy) <= val:
                        self.dummy.take_damage(15)
                        self.dummy.apply_kb(300 * (1 if self.dummy.cx > self.player.cx else -1), 0, 0.2)
                self._next()

        for p in self.particles[:]:
            p.update(dt)
            if not p.alive: self.particles.remove(p)
        for f in self.fists[:]:
            f.update(dt)
            if not f.alive: self.fists.remove(f)

    def _next(self):
        self.current_idx += 1
        self.timer = 0.0

    def draw(self, surf):
        for p in self.particles: p.draw(surf)
        for f in self.fists: f.draw(surf)
        if self.current_idx < len(self.blocks):
            b = self.blocks[self.current_idx]
            if b['type'] == 'Visual' and b['v_type'] == 'Hitbox':
                pygame.draw.circle(surf, b['color']+(100,), (int(self.player.cx), int(self.player.cy)), int(b['val']), 3)

class CosmicCutscene:
    PHASE_WALK   = 0; PHASE_REACH  = 1; PHASE_TOUCH  = 2; PHASE_VOICE  = 3; PHASE_BEAM   = 4; PHASE_FADEOUT= 5
    def __init__(self):
        self.timer = 0.0
        self.phase = self.PHASE_WALK
        self.done  = False
        self.bg_particles: list[Particle] = []
        self.beam_particles: list[Particle] = []
        self.comet_trail_b: list[Particle] = []
        self.comet_trail_r: list[Particle] = []
        # Animated star field — (x, y, base_r, phase_offset, twinkle_speed)
        self.star_field = [
            (random.randint(0,WIDTH), random.randint(0,HEIGHT),
             random.uniform(0.8,2.8), random.uniform(0,math.tau),
             random.uniform(1.5,4.0))
            for _ in range(340)
        ]
        # Shooting stars — (x, y, vx, vy, life, max_life)
        self.shooting_stars: list[list] = []
        self.shooting_star_timer = 0.0
        self.cosmic_bg_alpha = 0
        self.blue_x = -120.0; self.red_x  = WIDTH + 120.0
        self.blue_y = HEIGHT // 2 + 40; self.red_y  = HEIGHT // 2 + 40
        self.person_size = 100
        self.hand_extend_blue = 0; self.hand_extend_red  = 0
        # Voice text — character-by-character reveal
        self.voice_text  = "GAROOOUUUUU"
        self.voice_index = 0; self.voice_timer = 0.0
        self.voice_char_interval = 0.11
        self.voice_letters_revealed = 0   # how many chars visible
        self.title_alpha  = 0             # "Cosmic Power Awakening" fade-in
        self.blue_sky_y = float(HEIGHT//2 + 40)
        self.beam_alpha = 0; self.beam_width = 0; self.flash_alpha = 0; self.fadeout_alpha = 0
        self.screen_shake = 0.0
        self.reflection_alpha = 0; self.cosmic_player_alpha = 0
        self.impact_particles: list[Particle] = []
        # Shockwave rings spawned on touch
        self.shockwaves: list[dict] = []   # {cx,cy,r,max_r,alpha}
        self.beam_pulse = 0.0
        self.scanline_alpha = 0
        # Nebula clouds for background depth
        self.nebula_clouds = [
            (random.randint(0,WIDTH), random.randint(60,HEIGHT-60),
             random.randint(80,200), random.choice([(40,0,100),(0,20,80),(80,0,60)]),
             random.uniform(0,math.tau))
            for _ in range(14)
        ]

    def _spawn_shooting_star(self):
        x = random.randint(0, WIDTH)
        vx = random.uniform(200, 450) * random.choice([-1,1])
        vy = random.uniform(60, 160) * (1 if vx > 0 else -1)
        life = random.uniform(0.4, 0.9)
        self.shooting_stars.append([float(x), random.randint(60, HEIGHT-60),
                                     vx, vy, life, life])

    def update(self, dt):
        self.timer += dt
        self.beam_pulse += dt * 6

        for p in self.bg_particles[:]:
            p.update(dt); 
            if not p.alive: self.bg_particles.remove(p)
        for p in self.beam_particles[:]:
            p.update(dt)
            if not p.alive: self.beam_particles.remove(p)
        for p in self.impact_particles[:]:
            p.update(dt)
            if not p.alive: self.impact_particles.remove(p)
        for p in self.comet_trail_b[:]:
            p.update(dt)
            if not p.alive: self.comet_trail_b.remove(p)
        for p in self.comet_trail_r[:]:
            p.update(dt)
            if not p.alive: self.comet_trail_r.remove(p)

        for sw in self.shockwaves[:]:
            sw["r"] += 260 * dt
            sw["alpha"] = max(0, sw["alpha"] - 340 * dt)
            if sw["alpha"] <= 0: self.shockwaves.remove(sw)

        for ss in self.shooting_stars[:]:
            ss[0] += ss[2]*dt; ss[1] += ss[3]*dt; ss[4] -= dt
            if ss[4] <= 0: self.shooting_stars.remove(ss)
        self.shooting_star_timer -= dt
        if self.shooting_star_timer <= 0 and self.phase >= self.PHASE_TOUCH:
            self._spawn_shooting_star()
            self.shooting_star_timer = random.uniform(0.4, 1.2)

        if self.screen_shake > 0:
            self.screen_shake -= dt * 8
            if self.screen_shake < 0: self.screen_shake = 0

        if self.phase == self.PHASE_WALK:
            speed = 160
            target_bx = WIDTH//2 - 180; target_rx = WIDTH//2 + 180
            # Comet trails while walking
            if self.blue_x < target_bx:
                self.comet_trail_b.append(Particle(
                    self.blue_x, self.blue_y, random.uniform(-20,20), random.uniform(-20,20),
                    (60,120,220), random.randint(4,9), 0.35, True))
            if self.red_x > target_rx:
                self.comet_trail_r.append(Particle(
                    self.red_x, self.red_y, random.uniform(-20,20), random.uniform(-20,20),
                    (200,60,60), random.randint(4,9), 0.35, True))
            self.blue_x = min(target_bx, self.blue_x + speed * dt)
            self.red_x  = max(target_rx, self.red_x  - speed * dt)
            self.cosmic_bg_alpha = min(60, self.cosmic_bg_alpha + 40 * dt)
            if self.blue_x >= target_bx and self.red_x <= target_rx:
                self.phase = self.PHASE_REACH; self.timer = 0.0

        elif self.phase == self.PHASE_REACH:
            self.hand_extend_red = min(80, self.hand_extend_red + 120 * dt)
            if self.timer > 0.4:
                self.blue_x = min(WIDTH//2 - 100, self.blue_x + 40 * dt)
            self.cosmic_bg_alpha = min(100, self.cosmic_bg_alpha + 60 * dt)
            if self.timer >= 1.5:
                self.phase = self.PHASE_TOUCH; self.timer = 0.0

        elif self.phase == self.PHASE_TOUCH:
            self.hand_extend_blue = min(90, self.hand_extend_blue + 200 * dt)
            self.hand_extend_red  = min(90, self.hand_extend_red  + 30  * dt)
            self.blue_x = min(WIDTH//2 - 85, self.blue_x + 60 * dt)
            self.cosmic_bg_alpha = min(180, self.cosmic_bg_alpha + 300 * dt)
            self.scanline_alpha  = min(60, self.scanline_alpha + 120 * dt)
            if self.timer >= 1.8:
                self.phase = self.PHASE_VOICE; self.timer = 0.0
                self.voice_index = 0; self.voice_timer = 0.0; self.voice_letters_revealed = 0
                hand_meet_x = WIDTH//2 - 10; hand_meet_y = self.blue_y - 20
                self.impact_particles += burst(hand_meet_x, hand_meet_y, 60,
                    [(255,255,255),(200,150,255),(100,200,255)], 3,10, 60,250, 0.3,0.8)
                for _ in range(3):
                    self.shockwaves.append({"cx":hand_meet_x,"cy":hand_meet_y,"r":10,"alpha":220})
                self.screen_shake = 0.5

        elif self.phase == self.PHASE_VOICE:
            self.cosmic_bg_alpha = min(230, self.cosmic_bg_alpha + 80 * dt)
            self.voice_timer += dt
            # reveal letters one by one
            self.voice_letters_revealed = min(len(self.voice_text),
                int(self.voice_timer / self.voice_char_interval))
            # spawn particle burst on each new letter
            if self.voice_letters_revealed > self.voice_index:
                self.voice_index = self.voice_letters_revealed
                cx = WIDTH//2 - 220 + self.voice_index * 38
                self.bg_particles += burst(cx, HEIGHT//2 - 80, 8,
                    [(200,150,255),(100,200,255),(255,255,255)], 2,5, 30,120, 0.2,0.6)
            # title fade in after letters done
            if self.voice_letters_revealed >= len(self.voice_text):
                self.title_alpha = min(255, self.title_alpha + 220 * dt)
            if self.voice_timer >= len(self.voice_text) * self.voice_char_interval + 2.0:
                self.phase = self.PHASE_BEAM; self.timer = 0.0

        elif self.phase == self.PHASE_BEAM:
            self.beam_alpha = min(255, self.beam_alpha + 600 * dt)
            self.beam_width = min(90, self.beam_width + 160 * dt)
            # continuous beam sparks
            if self.timer < 2.0 and random.random() < 0.5:
                bx = WIDTH//2 + random.uniform(-self.beam_width/2, self.beam_width/2)
                self.beam_particles.append(Particle(bx, random.randint(0,HEIGHT),
                    random.uniform(-40,40), random.uniform(-60,60),
                    random.choice([(200,150,255),(100,200,255),(255,255,255)]),
                    random.randint(2,5), random.uniform(0.2,0.6), True))
            if self.timer < 1.5:
                self.blue_sky_y = self.blue_y - (self.timer / 1.5) * (HEIGHT//2 + 80)
            elif self.timer < 2.0:
                self.blue_sky_y = -100
                self.flash_alpha = min(255, self.flash_alpha + 500 * dt)
                self.shockwaves.append({"cx":WIDTH//2,"cy":HEIGHT//2,"r":20,"alpha":80})
            elif self.timer < 3.5:
                t2 = (self.timer - 2.0) / 1.5
                self.blue_sky_y = -100 + t2 * (HEIGHT//2 + 140)
                self.flash_alpha = max(0, self.flash_alpha - 400 * dt)
            else:
                self.phase = self.PHASE_FADEOUT; self.timer = 0.0
                self.blue_sky_y = float(self.blue_y)

        elif self.phase == self.PHASE_FADEOUT:
            self.fadeout_alpha = min(255, self.fadeout_alpha + 280 * dt)
            if self.timer >= 1.0: self.done = True

    def _draw_cosmic_bg(self, surf, alpha, t):
        """Gradient sky + nebula clouds + animated twinkle star field + shooting stars."""
        cos_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(0, HEIGHT, 3):
            frac = y / HEIGHT
            r2 = int(4 + 18*frac); g2 = int(0 + 4*frac); b2 = int(18 + 38*frac)
            pygame.draw.line(cos_surf, (r2,g2,b2,alpha), (0,y), (WIDTH,y))
        surf.blit(cos_surf, (0,0))

        # Nebula clouds
        neb_a = int(alpha * 0.35)
        if neb_a > 0:
            for (nx,ny,nr,nc,nph) in self.nebula_clouds:
                pulse = 0.7 + 0.3*math.sin(t*0.8 + nph)
                ns = pygame.Surface((nr*2, nr*2), pygame.SRCALPHA)
                pygame.draw.circle(ns, (*nc, neb_a), (nr,nr), int(nr*pulse))
                surf.blit(ns, (nx-nr, ny-nr))

        # Animated twinkling stars
        star_a_base = min(255, int(alpha * 1.4))
        for (sx, sy, sr, sph, sspd) in self.star_field:
            twinkle = 0.4 + 0.6 * abs(math.sin(t * sspd + sph))
            a_star  = int(star_a_base * twinkle)
            if a_star < 10: continue
            r_draw = max(1, int(sr * twinkle))
            ss = pygame.Surface((r_draw*2+2, r_draw*2+2), pygame.SRCALPHA)
            pygame.draw.circle(ss, (220,220,255,a_star), (r_draw+1,r_draw+1), r_draw)
            surf.blit(ss, (sx-r_draw-1, sy-r_draw-1))

        # Shooting stars
        for ss in self.shooting_stars:
            x,y,vx,vy,life,mlife = ss
            t_ss  = life/mlife
            a_ss  = int(240*t_ss)
            tail  = 14
            tx = x - vx*0.04; ty = y - vy*0.04
            sss = pygame.Surface((abs(int(x-tx))+10,abs(int(y-ty))+10), pygame.SRCALPHA)
            pygame.draw.line(sss, (200,220,255,a_ss), (5,5),(5+int(x-tx),5+int(y-ty)), 2)
            surf.blit(sss, (min(x,tx)-5, min(y,ty)-5))

    def _draw_scanlines(self, surf, alpha):
        if alpha <= 0: return
        sl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(0, HEIGHT, 3):
            pygame.draw.line(sl, (0,0,0, int(alpha)), (0,y),(WIDTH,y))
        surf.blit(sl, (0,0))

    def draw(self, surf):
        shk = int(self.screen_shake * 9 * math.sin(self.timer * 62)) if self.screen_shake > 0 else 0
        t = self.timer

        # Background
        surf.fill((2, 2, 8))
        if self.cosmic_bg_alpha > 0:
            self._draw_cosmic_bg(surf, self.cosmic_bg_alpha, pygame.time.get_ticks()*0.001)

        # Cinematic letterbox bars (with scan lines on top)
        BAR_H = 64
        pygame.draw.rect(surf, (0,0,0), (0, 0, WIDTH, BAR_H))
        pygame.draw.rect(surf, (0,0,0), (0, HEIGHT-BAR_H, WIDTH, BAR_H))
        self._draw_scanlines(surf, self.scanline_alpha)

        # --- Shockwave rings ---
        for sw in self.shockwaves:
            sr = int(sw["r"]); sa = int(sw["alpha"])
            if sr < 2 or sa <= 0: continue
            ss = pygame.Surface((sr*2+4,sr*2+4), pygame.SRCALPHA)
            pygame.draw.circle(ss, (200,150,255,sa), (sr+2,sr+2), sr, 2)
            surf.blit(ss, (int(sw["cx"])-sr-2, int(sw["cy"])-sr-2))

        # --- WALK phase ---
        if self.phase == self.PHASE_WALK:
            for p in self.comet_trail_b: p.draw(surf)
            for p in self.comet_trail_r: p.draw(surf)
            draw_cube_guy(surf, self.blue_x, self.blue_y, self.person_size,
                          (60,140,230), (20,80,180), is_blue=True)
            draw_cube_guy(surf, self.red_x, self.red_y, self.person_size,
                          (210,80,80), (160,40,40), is_blue=False)

        # --- REACH phase ---
        elif self.phase == self.PHASE_REACH:
            draw_cube_guy(surf, self.blue_x, self.blue_y, self.person_size,
                          (60,140,230), (20,80,180), hand_extend=self.hand_extend_blue, is_blue=True)
            draw_cube_guy(surf, self.red_x, self.red_y, self.person_size,
                          (210,80,80), (160,40,40), hand_extend=self.hand_extend_red, is_blue=False)

        # --- TOUCH + VOICE phases ---
        elif self.phase in (self.PHASE_TOUCH, self.PHASE_VOICE):
            for p in self.bg_particles: p.draw(surf)
            for p in self.impact_particles: p.draw(surf)
            draw_cube_guy(surf, self.blue_x+shk, self.blue_y, self.person_size,
                          (60,140,230), (20,80,180), glow_col=(100,200,255), glow_radius=55,
                          hand_extend=self.hand_extend_blue, is_blue=True)
            draw_cube_guy(surf, self.red_x+shk, self.red_y, self.person_size,
                          (210,80,80), (160,40,40), glow_col=(255,100,100), glow_radius=55,
                          hand_extend=self.hand_extend_red, is_blue=False)

            # --- Voice text: character-by-character ---
            if self.phase == self.PHASE_VOICE:
                revealed = self.voice_text[:self.voice_letters_revealed]
                # dramatic shadow
                v_shad = F_EPIC.render(revealed, True, (60,0,120))
                v_surf = F_EPIC.render(revealed, True, (220,160,255))
                # slight per-letter wave
                vx0 = WIDTH//2 - F_EPIC.size(revealed)[0]//2
                vy0 = HEIGHT//2 - 80
                surf.blit(v_shad, (vx0+5+shk, vy0+5))
                surf.blit(v_surf, (vx0+shk, vy0))

                # flicker effect on last char
                if self.voice_letters_revealed < len(self.voice_text):
                    flick = F_EPIC.render(self.voice_text[self.voice_letters_revealed], True, (255,255,255))
                    char_x = vx0 + F_EPIC.size(revealed)[0]
                    if int(pygame.time.get_ticks()*0.02) % 3 != 0:
                        surf.blit(flick, (char_x+shk, vy0))

                # "Cosmic Power Awakening" subtitle
                if self.title_alpha > 0:
                    sub = F_EPIC2.render("COSMIC POWER AWAKENING", True, (180,120,255))
                    sub.set_alpha(int(self.title_alpha))
                    surf.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 60))

        # --- BEAM phase ---
        elif self.phase == self.PHASE_BEAM:
            for p in self.beam_particles: p.draw(surf)
            draw_cube_guy(surf, self.red_x, self.red_y, self.person_size,
                          (210,80,80), (160,40,40), hand_extend=self.hand_extend_red, is_blue=False)

            if self.beam_alpha > 0:
                bw = int(self.beam_width)
                pulse_add = int(8 * math.sin(self.beam_pulse))
                # multi-layer beam with edge glow
                for layer_i, (lw_frac, la_frac, lcol) in enumerate([
                    (1.0,   1.0,   (150,60,255)),
                    (0.65,  0.85,  (180,100,255)),
                    (0.35,  0.70,  (230,200,255)),
                ]):
                    lw = max(2, int((bw+pulse_add) * lw_frac))
                    la = int(self.beam_alpha * la_frac)
                    bs = pygame.Surface((lw, HEIGHT), pygame.SRCALPHA)
                    bs.fill((*lcol, la))
                    surf.blit(bs, (WIDTH//2 - lw//2, 0))

            # the player ascending / descending
            by2 = int(self.blue_sky_y)
            if self.timer < 2.0:
                draw_cube_guy(surf, WIDTH//2+shk, by2, self.person_size,
                              (60,140,230), (20,80,180), glow_col=(100,200,255), glow_radius=65, is_blue=True)
            else:
                # transformed cosmic version
                draw_cube_guy(surf, WIDTH//2+shk, by2, self.person_size,
                              (20,0,60), (150,80,255), glow_col=(160,80,255), glow_radius=90, is_blue=True)
                # "COSMIC" stamp
                cs = F_EPIC2.render("COSMIC", True, (200,160,255))
                surf.blit(cs, (WIDTH//2 - cs.get_width()//2, HEIGHT//2 + 30))

        # --- FADEOUT phase ---
        elif self.phase == self.PHASE_FADEOUT:
            # keep the last beam state frozen
            pass

        # --- Flash overlay ---
        if self.flash_alpha > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255,255,255, int(self.flash_alpha)))
            surf.blit(fs,(0,0))

        # --- Fade to black ---
        if self.fadeout_alpha > 0:
            fo = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fo.fill((0,0,0, int(self.fadeout_alpha)))
            surf.blit(fo,(0,0))

        # Redraw bars on top always
        pygame.draw.rect(surf, (0,0,0), (0, 0, WIDTH, BAR_H))
        pygame.draw.rect(surf, (0,0,0), (0, HEIGHT-BAR_H, WIDTH, BAR_H))

class ReaperAwakening:
    P_FALL    = 0; P_SMASH   = 1; P_PILLAR  = 2; P_POSE    = 3; P_JUMPOFF = 4
    def __init__(self):
        self.timer = 0.0; self.phase = self.P_FALL; self.done  = False
        self.cube_y = -100; self.cube_x = WIDTH // 2; self.pillar_y = HEIGHT
        self.particles: list[Particle] = []; self.screen_shake = 0.0; self.cracks = [] 

    def update(self, dt):
        self.timer += dt
        for p in self.particles[:]:
            p.update(dt)
            if not p.alive: self.particles.remove(p)
        if self.screen_shake > 0:
            self.screen_shake -= dt * 10
            if self.screen_shake < 0: self.screen_shake = 0

        if self.phase == self.P_FALL:
            self.cube_y += 1200 * dt
            if self.cube_y >= HEIGHT // 2 + 50:
                self.cube_y = HEIGHT // 2 + 50
                self.phase = self.P_SMASH; self.timer = 0.0; self.screen_shake = 1.0
                for _ in range(8):
                    ang = random.uniform(0, math.tau); r_dist = random.randint(100, 300)
                    self.cracks.append({"end": (self.cube_x + math.cos(ang)*r_dist, self.cube_y + math.sin(ang)*r_dist), "width": random.randint(2, 6)})
                self.particles += burst(self.cube_x, self.cube_y, 60, [(30,30,30), (80,20,20), (140,30,40)], 4, 15, 60, 400, 0.5, 1.5, grav=200, shape="rect")
        elif self.phase == self.P_SMASH:
            if self.timer > 1.0: self.phase = self.P_PILLAR; self.timer = 0.0; self.screen_shake = 0.5
        elif self.phase == self.P_PILLAR:
            self.pillar_y = max(HEIGHT // 2 - 50, self.pillar_y - 500 * dt)
            if self.timer > 1.2: self.phase = self.P_POSE; self.timer = 0.0; self.cube_y = self.pillar_y - 40 
        elif self.phase == self.P_POSE:
            if self.timer > 2.0: self.phase = self.P_JUMPOFF; self.timer = 0.0
        elif self.phase == self.P_JUMPOFF:
            self.cube_y -= 800 * dt
            if self.timer > 0.8: self.done = True

    def draw(self, surf):
        shk = int(self.screen_shake * 12 * math.sin(self.timer * 60)) if self.screen_shake > 0 else 0
        surf.fill((10, 5, 5))
        if self.phase >= self.P_SMASH:
            for c in self.cracks: pygame.draw.line(surf, (0,0,0), (self.cube_x+shk, HEIGHT//2+50+shk), (c["end"][0]+shk, c["end"][1]+shk), c["width"])
        if self.phase >= self.P_PILLAR:
            pw, ph = 100, HEIGHT - self.pillar_y
            pygame.draw.rect(surf, (40, 40, 45), (WIDTH//2 - pw//2 + shk, self.pillar_y + shk, pw, ph))
            pygame.draw.rect(surf, (20, 20, 25), (WIDTH//2 - pw//2 + shk, self.pillar_y + shk, pw, ph), 4)

        for p in self.particles: p.draw(surf)
        has_scythe = (self.phase == self.P_POSE)
        draw_cube_guy(surf, self.cube_x + shk, self.cube_y + shk, 80, (140,20,30), (80,0,0), glow_col=(255,50,50), glow_radius=40, is_blue=False, has_scythe=has_scythe)

        pygame.draw.rect(surf, (0,0,0), (0, 0, WIDTH, 60))
        pygame.draw.rect(surf, (0,0,0), (0, HEIGHT - 60, WIDTH, 60))

class WhirlwindWaterStrike:
    def __init__(self, player, dummy):
        self.player = player; self.dummy = dummy; self.timer = 0.0; self.done = False; self.particles = []
    def update(self, dt):
        self.timer += dt
        for p in self.particles[:]:
            p.update(dt)
            if not p.alive: self.particles.remove(p)
        if self.timer < 1.0:
            self.player.x += 400 * dt
            self.player.x = min(AR - PLAYER_SIZE, self.player.x)
            self.dummy.x = self.player.x + PLAYER_SIZE + 10
            self.dummy.y = self.player.y
            self.particles += burst(self.player.cx, self.player.cy, 3, [(80,180,255),(180,230,255),(200,240,255)], 3, 7, 50, 100, 0.2, 0.6)
        elif self.timer < 1.4:
            if self.timer - dt < 1.0:
                self.dummy.take_damage(15)
                self.dummy.apply_kb(600, 0, 0.4)
                self.particles += burst(self.dummy.cx, self.dummy.cy, 30, [(80,180,255),(200,240,255),(255,255,255)], 4, 10, 80, 200, 0.3, 0.8)
        else: self.done = True
    def draw(self, surf):
        for p in self.particles: p.draw(surf)

class PortalNausea:
    def __init__(self, player, dummy):
        self.player = player; self.dummy = dummy; self.timer = 0.0; self.done = False
        self.start_y = 100; self.end_y = HEIGHT - 100
        self.dummy.x = WIDTH // 2 - DUMMY_SIZE//2; self.dummy.y = self.start_y
    def update(self, dt):
        self.timer += dt
        self.dummy.y += 1800 * dt
        if self.dummy.y > self.end_y: self.dummy.y = self.start_y
        if self.timer >= 3.0: self.dummy.take_damage(999); self.done = True
    def draw(self, surf):
        pygame.draw.ellipse(surf, (255, 150, 50), (WIDTH//2 - 60, self.start_y - 20, 120, 40), 5)
        pygame.draw.ellipse(surf, (50, 150, 255), (WIDTH//2 - 60, self.end_y - 20, 120, 40), 5)

class ReaperMarkSequence:
    def __init__(self, player, dummy):
        self.player = player; self.dummy = dummy; self.timer = 0.0; self.done = False; self.start_x = player.x
    def update(self, dt):
        self.timer += dt
        if self.timer < 0.2: self.player.x += (self.dummy.x - self.player.x) * (dt / 0.2)
        elif self.timer - dt < 0.2: self.dummy.is_marked = True
        elif self.timer > 0.6: self.done = True
    def draw(self, surf):
        if 0.2 <= self.timer <= 0.4:
            pygame.draw.line(surf, (220, 20, 40), (self.dummy.cx - 30, self.dummy.cy - 30), (self.dummy.cx + 30, self.dummy.cy + 30), 8)

class DecisiveStrikeSequence:
    def __init__(self, player, dummy):
        self.player = player; self.dummy = dummy; self.timer = 0.0; self.punches = 0; self.done = False; self.fists = []
    def update(self, dt):
        self.timer += dt
        for f in self.fists[:]:
            f.update(dt)
            if not f.alive: self.fists.remove(f)
        target_punches = int(self.timer / 0.04)
        while self.punches < target_punches and self.punches < 50:
            self.punches += 1; self.dummy.take_damage(2)
            fx = self.player.cx + random.uniform(5, 30); fy = self.player.cy + random.uniform(-20, 20)
            self.fists.append(_Fist(fx, fy, 1.2, random.uniform(-0.1, 0.1), (50, 150, 255)))
        if self.timer > 2.5: self.done = True
    def draw(self, surf):
        for f in self.fists: f.draw(surf)

class SoulDrainSequence:
    P_PULL = 0; P_SLASH = 1; P_BARRAGE = 2; P_SHATTER = 3
    def __init__(self, player, dummy, game):
        self.player = player; self.dummy = dummy; self.game = game; self.timer = 0.0; self.phase = self.P_PULL; self.done = False
        self._pull_start_x = dummy.x; self._pull_start_y = dummy.y; self.particles = []
        self.blue_cube_offset = 100; self.barrage_hits = 0; self.screen_shake = 0.0
    def update(self, dt):
        self.timer += dt
        for p in self.particles[:]:
            p.update(dt)
            if not p.alive: self.particles.remove(p)
        if self.screen_shake > 0:
            self.screen_shake -= dt * 10
            if self.screen_shake < 0: self.screen_shake = 0

        if self.phase == self.P_PULL:
            t = min(1.0, self.timer / 0.3)
            tx = self.player.cx - DUMMY_SIZE//2 + 40; ty = self.player.cy - DUMMY_SIZE//2
            self.dummy.x = self._pull_start_x + (tx - self._pull_start_x)*t
            self.dummy.y = self._pull_start_y + (ty - self._pull_start_y)*t
            if self.timer >= 0.3: self.phase = self.P_SLASH; self.timer = 0.0
        elif self.phase == self.P_SLASH:
            if self.timer >= 0.2 and self.timer - dt < 0.2:
                self.dummy.take_damage(50); self.screen_shake = 0.6
                self.particles += burst(self.dummy.cx, self.dummy.cy, 30, [(255,50,50), (180,0,0)], 3, 8, 100, 300, 0.2, 0.5)
            if self.timer >= 0.8:
                if self.dummy.hp <= 0: self.phase = self.P_BARRAGE; self.timer = 0.0
                else: self._check_helper(); self.done = True
        elif self.phase == self.P_BARRAGE:
            expected_hits = int(self.timer / 0.15)
            if expected_hits > self.barrage_hits and self.barrage_hits < 5:
                self.barrage_hits += 1; self.screen_shake = 0.4
                self.particles += burst(self.dummy.cx, self.dummy.cy, 15, [(80,180,255), (200,240,255)], 2, 6, 80, 200, 0.2, 0.4)
                self.dummy.flash_timer = 0.1
            if self.timer > 1.2:
                self.phase = self.P_SHATTER; self.timer = 0.0; self.screen_shake = 0.8
                self.particles += burst(self.dummy.cx + self.blue_cube_offset, self.dummy.cy, 80, [(180,220,255), (255,255,255), (100,180,255)], 4, 12, 100, 500, 0.5, 1.2, grav=300, shape="rect")
                self._check_helper()
        elif self.phase == self.P_SHATTER:
            if self.timer > 1.0: self.done = True
    def _check_helper(self):
        if self.dummy.is_marked: self.game.helper.spawn(self.player.cx, self.player.cy); self.dummy.is_marked = False
    def draw(self, surf):
        shk = int(self.screen_shake * 8 * math.sin(self.timer * 60)) if self.screen_shake > 0 else 0
        if self.phase == self.P_SLASH and 0.2 < self.timer < 0.4:
            pygame.draw.line(surf, (200, 0, 0), (self.player.cx - 50, self.player.cy - 50), (self.dummy.cx + 50, self.dummy.cy + 50), 15)
        if self.phase == self.P_BARRAGE:
            bx = self.dummy.cx + self.blue_cube_offset; by = self.dummy.cy + math.sin(self.timer * 20) * 10
            draw_cube_guy(surf, bx + shk, by + shk, 60, (60,140,230), (20,80,180), is_blue=True)
        for p in self.particles: p.draw(surf)

class MenacingCutscene:
    P_STAND = 0; P_SLICE = 1; P_DONE = 2
    def __init__(self, dummy):
        self.timer = 0.0; self.phase = self.P_STAND; self.done = False; self.dummy = dummy; self.slice_offset = 0
    def update(self, dt):
        self.timer += dt
        if self.phase == self.P_STAND:
            if self.timer > 1.5: self.phase = self.P_SLICE; self.timer = 0.0
        elif self.phase == self.P_SLICE:
            self.slice_offset += 150 * dt
            if self.timer > 2.0: self.dummy.take_damage(100); self.done = True
    def draw(self, surf):
        surf.fill((15, 0, 5)); dx, dy = WIDTH//2, HEIGHT//2 - 20
        if self.phase == self.P_STAND: draw_cube_guy(surf, dx, dy, 70, (210,90,90), (160,50,50))
        elif self.phase == self.P_SLICE:
            top_offset = self.slice_offset
            pygame.draw.rect(surf, (210,90,90), (dx - 25, dy, 50, 35))
            pygame.draw.rect(surf, (210,90,90), (dx - 25 + top_offset, dy - 35 + top_offset*0.5, 50, 35))
            if self.timer < 0.2: pygame.draw.line(surf, (255, 0, 0), (0, dy + 20), (WIDTH, dy - 20), 12)
        draw_cube_guy(surf, WIDTH//2 - 80, HEIGHT//2 + 80, 150, (100,0,10), (50,0,0), glow_col=(255,0,0), glow_radius=60)

# ══════════════════════════════════════════════════════════
#  ARENA / DIMENSION RENDERER
# ══════════════════════════════════════════════════════════
class Arena:
    def __init__(self):
        self.time = 0.0
        self._build_battlegrounds()
        self.lava_seeds = [(random.randint(AL,AR), random.randint(AT,AB)) for _ in range(30)]

    def _build_battlegrounds(self):
        ts = 60
        self.bg_tiles = []
        for tx in range(AL, AR, ts):
            for ty in range(AT, AB, ts):
                shade = (90,90,100) if ((tx//ts+ty//ts)%2==0) else (70,70,78)
                self.bg_tiles.append((pygame.Rect(tx,ty,ts,ts), shade))
        self.bg_grass = [
            pygame.Rect(AL+5,  AT+5,  90, 65), pygame.Rect(AL+5,  AB-75, 90, 65),
            pygame.Rect(AR-95, AT+5,  90, 65), pygame.Rect(AR-95, AB-75, 90, 65),
        ]

    def update(self, dt): self.time += dt

    def draw(self, surf, dim_idx):
        t = self.time
        if   dim_idx == 0: self._draw_battlegrounds(surf)
        elif dim_idx == 1: self._draw_lava(surf, t)
        pygame.draw.rect(surf, (180,180,200), pygame.Rect(AL,AT,AR-AL,AB-AT), 3, border_radius=4)

    def _draw_battlegrounds(self, surf):
        surf.fill((25,25,30))
        for rect,col in self.bg_tiles: pygame.draw.rect(surf, col, rect)
        for g in self.bg_grass:
            pygame.draw.rect(surf, (55,110,55), g, border_radius=4)
            pygame.draw.rect(surf, (45,90,45), g.inflate(-6,-6), border_radius=3)

    def _draw_lava(self, surf, t):
        surf.fill((80,10,5))
        for i,seed in enumerate(self.lava_seeds):
            phase = t*1.8 + i*0.31; r2 = int(200+40*math.sin(phase)); g2 = int(60+30*math.sin(phase+1))
            pygame.draw.circle(surf, (r2,g2,5), seed, random.randint(30,70))
        lbl = F_LG.render("☠ LAVA REALM ☠", True,(255,220,50))
        surf.blit(lbl,(WIDTH//2-lbl.get_width()//2, AT+8))
        vg = pygame.Surface((AW,AH),pygame.SRCALPHA)
        for edge,col in [((0,0,AW,20),(0,0,0,180)),((0,AH-20,AW,20),(0,0,0,180)), ((0,0,20,AH),(0,0,0,180)),((AW-20,0,20,AH),(0,0,0,180))]:
            pygame.draw.rect(vg,col,edge)
        surf.blit(vg,(AL,AT))

class GalaxyPull:
    P_PULL = 0; P_VORTEX = 1; P_DONE = 2
    def __init__(self, player: Player, dummy: Dummy):
        self.player = player; self.dummy  = dummy; self.phase  = self.P_PULL; self.timer  = 0.0; self.done   = False
        self.vortex_particles: list[Particle] = []; self._pull_start_x = dummy.x; self._pull_start_y = dummy.y
        self.stars_bg = [(random.randint(0,WIDTH), random.randint(0,HEIGHT), random.uniform(2,8)) for _ in range(200)]
    def _spawn_vortex(self):
        cx, cy = WIDTH//2, HEIGHT//2
        for _ in range(200):
            ang  = random.uniform(0, math.tau); dist = random.uniform(20, 300)
            vx   = -math.cos(ang)*random.uniform(40,250) - math.sin(ang)*random.uniform(100,300)
            vy   = -math.sin(ang)*random.uniform(40,250) + math.cos(ang)*random.uniform(100,300)
            col  = random.choice([(180,100,255),(80,200,255),(255,255,255), (120,0,200),(255,180,255),(200,120,255)])
            self.vortex_particles.append(Particle(cx+math.cos(ang)*dist, cy+math.sin(ang)*dist, vx, vy, col, random.randint(3,8), random.uniform(0.6,1.8), True))
    def update(self, dt):
        self.timer += dt
        for p in self.vortex_particles[:]:
            p.update(dt)
            if not p.alive: self.vortex_particles.remove(p)
        if self.phase == self.P_PULL:
            t = min(1.0, self.timer / 0.5)
            self.dummy.x = self._pull_start_x + ((self.player.cx - DUMMY_SIZE//2) - self._pull_start_x)*t
            self.dummy.y = self._pull_start_y + ((self.player.cy - DUMMY_SIZE//2) - self._pull_start_y)*t
            if self.timer >= 0.5:
                self.phase = self.P_VORTEX; self.timer = 0.0; self.dummy.x = WIDTH//2 - DUMMY_SIZE//2; self.dummy.y = HEIGHT//2 - DUMMY_SIZE//2; self._spawn_vortex()
        elif self.phase == self.P_VORTEX and self.timer >= 2.0:
            self.dummy.trigger_galaxy_death(); self.phase = self.P_DONE; self.done  = True
    def draw(self, surf):
        if self.phase == self.P_PULL:
            a = int(200 * min(1.0, self.timer/0.3))
            for width,col2 in [(12,(80,0,200,a//2)),(4,(200,100,255,a))]:
                s = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
                pygame.draw.line(s,col2, (int(self.player.cx),int(self.player.cy)), (int(self.dummy.cx),int(self.dummy.cy)), width)
                surf.blit(s,(0,0))
        if self.phase == self.P_VORTEX:
            ov = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((5,0,15,int(255 * min(1.0, self.timer/0.3)))); surf.blit(ov,(0,0))
            for (sx,sy,ssp) in self.stars_bg:
                pygame.draw.circle(surf, (200,200,255,int((min(1.0, self.timer/2.0)) * 255)), (int((sx - WIDTH//2) * (1.0 + self.timer*ssp) + WIDTH//2),int((sy - HEIGHT//2) * (1.0 + self.timer*ssp) + HEIGHT//2)), max(1, int(ssp)))
            for ring in range(6):
                radius = int((ring+1)*30*(1-(self.timer/2.0)*0.4)); a3 = max(0, 200-ring*30)
                s2 = pygame.Surface((radius*2,radius*2),pygame.SRCALPHA); pygame.draw.circle(s2,(150,50,255,a3),(radius,radius),radius,2)
                surf.blit(s2,(WIDTH//2-radius, HEIGHT//2-radius))
        for p in self.vortex_particles: p.draw(surf)

class GalacticPush:
    P_DIM = 0; P_PUSH = 1; P_DONE = 2
    def __init__(self, player: Player, dummy: Dummy, dim_switch_fn):
        self.player  = player; self.dummy = dummy; self.dim_switch = dim_switch_fn; self.phase = self.P_DIM; self.timer = 0.0; self.done = False
        self.particles: list[Particle] = []
        for _ in range(120):
            a = random.uniform(0,math.tau); sp = random.uniform(80,400); col = random.choice([(180,100,255),(80,200,255),(255,255,255),(120,0,200)])
            self.particles.append(Particle(random.randint(0,WIDTH),random.randint(0,HEIGHT), math.cos(a)*sp,math.sin(a)*sp, col, random.randint(3,9), 0.7, True))
    def update(self, dt):
        self.timer += dt
        for p in self.particles[:]:
            p.update(dt)
            if not p.alive: self.particles.remove(p)
        if self.phase == self.P_DIM and self.timer >= 0.7:
            self.phase = self.P_PUSH; self.timer = 0.0; self.dim_switch(1); self.dummy.apply_kb(1900, 0, 1.3)
        elif self.phase == self.P_PUSH and self.timer >= 1.6:
            self.dummy.trigger_lava_death(); self.phase = self.P_DONE; self.done  = True
    def draw(self, surf):
        if self.phase == self.P_DIM:
            t = self.timer/0.7; ov = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((5,0,20,int(200*min(1.0,t*2)))); surf.blit(ov,(0,0))
            for p in self.particles: p.draw(surf)
        elif self.phase == self.P_PUSH:
            for p in self.particles: p.draw(surf)

class DimTransition:
    def __init__(self, name):
        self.name  = name; self.timer = 0.0; self.done  = False
        if name == "Lava Realm": self.sub = "Lethal Dimension Hazard"; self.col = (255,60,20)
        else: self.sub = "Origin Dimension"; self.col = (150,100,255)
    def update(self, dt):
        self.timer += dt
        if self.timer >= 1.8: self.done = True
    def draw(self, surf):
        t = self.timer / 1.8
        a = max(0,min(255, int(255*(t/0.2)) if t < 0.2 else 255 if t < 0.5 else int(255*(1-(t-0.5)/0.5))))
        ov = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((220,200,255,a)); surf.blit(ov,(0,0))
        if 0.25 < t < 0.9:
            lbl = F_LG.render(f"↯  {self.name}  ↯", True, (60,0,120)); lbl.set_alpha(int(255*min(1.0,(t-0.25)/0.2))); surf.blit(lbl,(WIDTH//2-lbl.get_width()//2,HEIGHT//2-20))

# ══════════════════════════════════════════════════════════
#  SKILL BUILDER UI  –  v2 (Upgraded)
# ══════════════════════════════════════════════════════════
_SB_COLORS = [(80,180,255),(150,50,255),(220,50,50),(255,200,50),(100,255,100),(255,120,50),(255,80,200)]
_SB_COLOR_NAMES = ["Blue","Purple","Red","Gold","Green","Orange","Pink"]

class SkillBuilderUI:
    BTN_W = 210; BTN_H = 50
    BTN_X = 10 + 280 + 10
    BTN_Y = 10
    PANEL_W = 580
    PANEL_H = 520
    SCROLL_AREA_H = 340   # rows visible in CREATE block list

    def __init__(self):
        self.state        = "CLOSED"   # CLOSED | MAIN | CREATE | LOAD | RENAME
        self.blocks       = []
        self.saved_skills = []
        self.editing_name = "New Skill"
        self.selected_skill_idx = -1
        self.scroll_off   = 0          # pixel scroll in CREATE block list
        self._dragging    = None       # (block_index, start_y) for drag-reorder
        self._hov_block   = -1
        self._rename_target = -1       # index of skill being renamed in LOAD
        self._rename_buf  = ""
        self._name_active = False      # is the skill-name field focused
        self._pulse       = 0.0        # animation timer

    # ── helpers ────────────────────────────────────────────
    def _panel_rect(self):
        return pygame.Rect(self.BTN_X - 5, self.BTN_Y + self.BTN_H + 6,
                           self.PANEL_W, self.PANEL_H)

    def _block_row_y(self, i):
        return self._panel_rect().y + 156 + i * 52 - self.scroll_off

    def _draw_btn(self, surf, rect, label, bg, fg=(255,255,255), icon=None, hover=False, radius=6):
        rs = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        shade = tuple(min(255, c+30) for c in bg) if hover else bg
        rs.fill((*shade, 230))
        pygame.draw.rect(rs, (255,255,255,60 if hover else 30), (0,0,rect.w,rect.h), border_radius=radius)
        surf.blit(rs, (rect.x, rect.y))
        pygame.draw.rect(surf, (*fg[:3], 200), rect, 2, border_radius=radius)
        lbl_surf = F_SM.render(label, True, fg)
        ox = rect.x + rect.w//2 - lbl_surf.get_width()//2
        oy = rect.y + rect.h//2 - lbl_surf.get_height()//2
        if icon:
            surf.blit(F_SM.render(icon, True, fg), (rect.x + 8, oy))
            ox = rect.x + 30
        surf.blit(lbl_surf, (ox, oy))

    def _draw_panel_bg(self, surf):
        pr = self._panel_rect()
        bg = pygame.Surface((pr.w, pr.h), pygame.SRCALPHA)
        bg.fill((12, 12, 18, 235))
        surf.blit(bg, pr.topleft)
        pygame.draw.rect(surf, (80,100,160), pr, 2, border_radius=8)
        # header bar
        hdr = pygame.Surface((pr.w, 38), pygame.SRCALPHA)
        hdr.fill((30, 30, 50, 255))
        surf.blit(hdr, pr.topleft)
        pygame.draw.rect(surf, (80,100,160), pygame.Rect(pr.x, pr.y, pr.w, 38), 2, border_radius=8)

    # ── event handler ─────────────────────────────────────
    def handle_event(self, ev, game):
        mx, my = pygame.mouse.get_pos()
        self._pulse += 0.03

        # ── Toggle button ──────────────────────────────────
        btn_r = pygame.Rect(self.BTN_X, self.BTN_Y, self.BTN_W, self.BTN_H)
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if btn_r.collidepoint(mx, my):
                if self.state == "CLOSED":
                    self.state = "MAIN"
                else:
                    self.state = "CLOSED"
                    self._name_active = False
                return True

        if self.state == "CLOSED":
            return False

        pr = self._panel_rect()

        # ── Mouse wheel scroll in CREATE ───────────────────
        if ev.type == pygame.MOUSEWHEEL and self.state == "CREATE":
            if pr.collidepoint(mx, my):
                max_scroll = max(0, len(self.blocks) * 52 - self.SCROLL_AREA_H)
                self.scroll_off = max(0, min(max_scroll, self.scroll_off - ev.y * 20))
                return True

        if ev.type == pygame.KEYDOWN:
            # skill-name field
            if self._name_active and self.state == "CREATE":
                if ev.key == pygame.K_BACKSPACE:
                    self.editing_name = self.editing_name[:-1]
                elif ev.key == pygame.K_RETURN:
                    self._name_active = False
                elif ev.unicode and len(self.editing_name) < 18:
                    self.editing_name += ev.unicode
                return True
            # rename field in LOAD
            if self._rename_target >= 0 and self.state == "LOAD":
                if ev.key == pygame.K_BACKSPACE:
                    self._rename_buf = self._rename_buf[:-1]
                elif ev.key == pygame.K_RETURN:
                    if self._rename_buf.strip():
                        self.saved_skills[self._rename_target]["name"] = self._rename_buf.strip()
                    self._rename_target = -1; self._rename_buf = ""
                elif ev.unicode and len(self._rename_buf) < 18:
                    self._rename_buf += ev.unicode
                return True

        if ev.type != pygame.MOUSEBUTTONDOWN or ev.button != 1:
            return pr.collidepoint(mx, my)   # block clicks through panel

        # ── MAIN ──────────────────────────────────────────
        if self.state == "MAIN":
            oy = pr.y + 50
            if pygame.Rect(pr.x+20, oy, 260, 44).collidepoint(mx, my):
                self.state = "CREATE"; self.blocks = []
                self.editing_name = f"Skill {len(self.saved_skills)+1}"
                self.scroll_off = 0; return True
            if pygame.Rect(pr.x+20, oy+56, 260, 44).collidepoint(mx, my):
                self.state = "LOAD"; self.selected_skill_idx = -1
                self._rename_target = -1; return True
            if pygame.Rect(pr.x+pr.w-58, pr.y+7, 44, 24).collidepoint(mx, my):
                self.state = "CLOSED"; return True

        # ── CREATE ────────────────────────────────────────
        elif self.state == "CREATE":
            # close
            if pygame.Rect(pr.x+pr.w-58, pr.y+7, 44, 24).collidepoint(mx, my):
                self.state = "MAIN"; return True
            # name field focus
            name_r = pygame.Rect(pr.x+20, pr.y+46, 280, 30)
            if name_r.collidepoint(mx, my):
                self._name_active = True; return True
            else:
                self._name_active = False

            # add-block row
            add_y = pr.y + 84
            if pygame.Rect(pr.x+10, add_y, 100, 28).collidepoint(mx, my):
                self.blocks.append({"type":"Visual","v_type":"Punches","color":(80,180,255),"val":10}); return True
            if pygame.Rect(pr.x+114, add_y, 90, 28).collidepoint(mx, my):
                self.blocks.append({"type":"Wait","val":0.5}); return True
            if pygame.Rect(pr.x+208, add_y, 100, 28).collidepoint(mx, my):
                self.blocks.append({"type":"Movement","val":400}); return True
            if pygame.Rect(pr.x+312, add_y, 100, 28).collidepoint(mx, my):
                self.blocks.append({"type":"Visual","v_type":"Hitbox","color":(220,50,50),"val":80}); return True

            # action row (Test / Save / Back)
            act_y = pr.y + 118
            if pygame.Rect(pr.x+10, act_y, 100, 28).collidepoint(mx, my):
                if self.blocks: game.cinematic = CustomSkillSequence(game.player, game.dummy, self.blocks)
                return True
            if pygame.Rect(pr.x+114, act_y, 120, 28).collidepoint(mx, my):
                if self.blocks:
                    self.saved_skills.append({"name": self.editing_name.strip() or f"Skill {len(self.saved_skills)+1}",
                                              "blocks": [dict(b) for b in self.blocks]})
                    self.state = "MAIN"; return True
            if pygame.Rect(pr.x+240, act_y, 80, 28).collidepoint(mx, my):
                self.state = "MAIN"; return True

            # block rows
            clip_top = pr.y + 154; clip_bot = clip_top + self.SCROLL_AREA_H
            for i, b in enumerate(self.blocks):
                row_y = self._block_row_y(i)
                if row_y + 46 < clip_top or row_y > clip_bot: continue
                row_r = pygame.Rect(pr.x+10, row_y, self.PANEL_W - 20, 46)

                # delete
                del_r = pygame.Rect(row_r.right - 36, row_y+8, 30, 30)
                if del_r.collidepoint(mx, my):
                    self.blocks.pop(i)
                    self.scroll_off = max(0, min(self.scroll_off,
                        max(0, len(self.blocks)*52 - self.SCROLL_AREA_H)))
                    return True

                # move up/down
                up_r  = pygame.Rect(row_r.right - 72, row_y+4,  28, 18)
                dn_r  = pygame.Rect(row_r.right - 72, row_y+24, 28, 18)
                if up_r.collidepoint(mx, my) and i > 0:
                    self.blocks[i], self.blocks[i-1] = self.blocks[i-1], self.blocks[i]; return True
                if dn_r.collidepoint(mx, my) and i < len(self.blocks)-1:
                    self.blocks[i], self.blocks[i+1] = self.blocks[i+1], self.blocks[i]; return True

                if not row_r.collidepoint(mx, my): continue

                if b["type"] == "Visual":
                    # cycle v_type — matches drawn vt_r at row_r.x+80
                    vt_r = pygame.Rect(row_r.x+80, row_y+6, 100, 20)
                    if vt_r.collidepoint(mx, my):
                        vts = ["Punches","Aura","Cosmic Aura","Hitbox"]
                        b["v_type"] = vts[(vts.index(b["v_type"])+1) % len(vts)]; return True
                    # cycle color — matches drawn col_r at row_r.x+185
                    col_r = pygame.Rect(row_r.x+185, row_y+6, 70, 20)
                    if col_r.collidepoint(mx, my):
                        try: ci = _SB_COLORS.index(b["color"])
                        except ValueError: ci = -1
                        b["color"] = _SB_COLORS[(ci+1) % len(_SB_COLORS)]; return True
                    # val – / + — matches drawn buttons at row_r.x+112/168, row_y+25
                    minus_r = pygame.Rect(row_r.x+112, row_y+25, 22, 18)
                    plus_r  = pygame.Rect(row_r.x+168, row_y+25, 22, 18)
                    if minus_r.collidepoint(mx, my): b["val"] = max(5,  b["val"] - 10); return True
                    if plus_r.collidepoint(mx, my):  b["val"] = min(500,b["val"] + 10); return True

                elif b["type"] == "Wait":
                    minus_r = pygame.Rect(row_r.x+130, row_y+8, 22, 22)
                    plus_r  = pygame.Rect(row_r.x+190, row_y+8, 22, 22)
                    if minus_r.collidepoint(mx, my): b["val"] = round(max(0.1, b["val"]-0.1),1); return True
                    if plus_r.collidepoint(mx, my):  b["val"] = round(min(5.0, b["val"]+0.1),1); return True

                elif b["type"] == "Movement":
                    minus_r = pygame.Rect(row_r.x+130, row_y+8, 22, 22)
                    plus_r  = pygame.Rect(row_r.x+200, row_y+8, 22, 22)
                    if minus_r.collidepoint(mx, my): b["val"] = max(100, b["val"]-100); return True
                    if plus_r.collidepoint(mx, my):  b["val"] = min(1500,b["val"]+100); return True

        # ── LOAD ──────────────────────────────────────────
        elif self.state == "LOAD":
            if pygame.Rect(pr.x+pr.w-58, pr.y+7, 44, 24).collidepoint(mx, my):
                self.state = "MAIN"; self._rename_target = -1; return True

            list_y = pr.y + 50
            for i, sk in enumerate(self.saved_skills):
                row_r  = pygame.Rect(pr.x+14, list_y + i*50, 200, 40)
                del_r  = pygame.Rect(pr.x+230, list_y + i*50, 30, 40)
                ren_r  = pygame.Rect(pr.x+265, list_y + i*50, 60, 40)
                if row_r.collidepoint(mx, my):
                    self.selected_skill_idx = i; self._rename_target = -1; return True
                if del_r.collidepoint(mx, my):
                    self.saved_skills.pop(i)
                    if self.selected_skill_idx >= len(self.saved_skills):
                        self.selected_skill_idx = len(self.saved_skills)-1
                    return True
                if ren_r.collidepoint(mx, my):
                    self._rename_target = i
                    self._rename_buf = sk["name"]; return True

            # equip slots
            if self.selected_skill_idx >= 0:
                eq_keys = [("5",pygame.K_5),("6",pygame.K_6),("7",pygame.K_7),
                           ("8",pygame.K_8),("9",pygame.K_9),("0",pygame.K_0)]
                eq_x = pr.x + 340; eq_y = pr.y + 50
                for ki, (ks, pk) in enumerate(eq_keys):
                    if pygame.Rect(eq_x, eq_y + ki*40, 120, 32).collidepoint(mx, my):
                        game.custom_equipped[pk] = self.saved_skills[self.selected_skill_idx]
                        self.state = "CLOSED"; return True

            # Back button at bottom of LOAD panel
            if pygame.Rect(pr.x+20, pr.y+pr.h-44, 120, 34).collidepoint(mx, my):
                self.state = "MAIN"; self._rename_target = -1; return True

        return pr.collidepoint(mx, my)

    # ── draw ─────────────────────────────────────────────
    def draw(self, surf):
        # ── Main button ──────────────────────────────────
        mx, my = pygame.mouse.get_pos()
        btn_r = pygame.Rect(self.BTN_X, self.BTN_Y, self.BTN_W, self.BTN_H)
        hover_btn = btn_r.collidepoint(mx, my)
        bg_col = (20,70,20) if self.state == "CLOSED" else (20,100,20)
        self._draw_btn(surf, btn_r, "Skill Builder", bg_col, fg=(200,255,200),
                       hover=hover_btn, radius=8)
        # pencil icon
        px, py = self.BTN_X + 12, self.BTN_Y + 12
        pygame.draw.polygon(surf, (200,200,160), [(px,py+16),(px+12,py+4),(px+22,py+14),(px+10,py+26)])
        pygame.draw.polygon(surf, (255,200,80),  [(px,py+16),(px+10,py+26),(px-4,py+30)])
        pygame.draw.line(surf, (100,100,80), (px+2,py+22),(px+8,py+16), 2)

        if self.state == "CLOSED": return

        pr = self._panel_rect()
        self._draw_panel_bg(surf)

        # close X
        cx_r = pygame.Rect(pr.x+pr.w-58, pr.y+7, 44, 24)
        self._draw_btn(surf, cx_r, "✕ Close", (80,30,30), fg=(255,160,160), radius=5)

        # ── MAIN ─────────────────────────────────────────
        if self.state == "MAIN":
            ttl = F_TTL.render("⚡  Skill Builder", True, (180,255,180))
            surf.blit(ttl, (pr.x+14, pr.y+8))

            oy = pr.y + 50
            self._draw_btn(surf, pygame.Rect(pr.x+20, oy, 260, 44),
                           "✏  Create New Skill", (20,80,20), fg=(200,255,200),
                           hover=pygame.Rect(pr.x+20,oy,260,44).collidepoint(mx,my), radius=8)
            self._draw_btn(surf, pygame.Rect(pr.x+20, oy+56, 260, 44),
                           "📂  Load / Equip Skill", (20,20,80), fg=(160,200,255),
                           hover=pygame.Rect(pr.x+20,oy+56,260,44).collidepoint(mx,my), radius=8)

            if self.saved_skills:
                cnt = F_SM.render(f"{len(self.saved_skills)} saved skill{'s' if len(self.saved_skills)!=1 else ''}", True, (120,180,120))
                surf.blit(cnt, (pr.x+20, oy+110))
            else:
                hint = F_SM.render("No skills saved yet — create one!", True, (80,100,80))
                surf.blit(hint, (pr.x+20, oy+110))

        # ── CREATE ───────────────────────────────────────
        elif self.state == "CREATE":
            ttl = F_TTL.render("✏  Create Skill", True, (180,255,180))
            surf.blit(ttl, (pr.x+14, pr.y+8))

            # name field
            name_r = pygame.Rect(pr.x+20, pr.y+46, 280, 30)
            nfg = pygame.Surface((name_r.w, name_r.h), pygame.SRCALPHA)
            nfg.fill((30,50,30,200) if self._name_active else (20,30,20,180))
            surf.blit(nfg, name_r.topleft)
            bc = (100,255,100) if self._name_active else (60,120,60)
            pygame.draw.rect(surf, bc, name_r, 2, border_radius=4)
            cursor = ("_" if int(self._pulse*4)%2==0 else "") if self._name_active else ""
            surf.blit(F_SM.render(f"Name: {self.editing_name}{cursor}", True, (200,255,200)),
                      (name_r.x+8, name_r.y+7))

            block_cnt = F_SM.render(f"Blocks: {len(self.blocks)}", True, (140,180,140))
            surf.blit(block_cnt, (pr.x+320, pr.y+54))

            # add-block buttons
            add_y = pr.y + 84
            self._draw_btn(surf, pygame.Rect(pr.x+10, add_y, 100, 28), "+ Punches", (40,40,100), fg=(150,200,255),
                           hover=pygame.Rect(pr.x+10,add_y,100,28).collidepoint(mx,my))
            self._draw_btn(surf, pygame.Rect(pr.x+114, add_y, 90, 28), "+ Wait", (50,40,20), fg=(255,200,100),
                           hover=pygame.Rect(pr.x+114,add_y,90,28).collidepoint(mx,my))
            self._draw_btn(surf, pygame.Rect(pr.x+208, add_y, 100, 28), "+ Move", (30,50,30), fg=(120,255,120),
                           hover=pygame.Rect(pr.x+208,add_y,100,28).collidepoint(mx,my))
            self._draw_btn(surf, pygame.Rect(pr.x+312, add_y, 100, 28), "+ Hitbox", (80,20,20), fg=(255,130,130),
                           hover=pygame.Rect(pr.x+312,add_y,100,28).collidepoint(mx,my))

            # action row
            act_y = pr.y + 118
            self._draw_btn(surf, pygame.Rect(pr.x+10, act_y, 100, 28), "▶ Test", (80,60,0), fg=(255,210,80),
                           hover=pygame.Rect(pr.x+10,act_y,100,28).collidepoint(mx,my))
            self._draw_btn(surf, pygame.Rect(pr.x+114, act_y, 120, 28), "💾 Save Skill", (0,70,20), fg=(150,255,150),
                           hover=pygame.Rect(pr.x+114,act_y,120,28).collidepoint(mx,my))
            self._draw_btn(surf, pygame.Rect(pr.x+240, act_y, 80, 28), "← Back", (50,50,50), fg=(180,180,180),
                           hover=pygame.Rect(pr.x+240,act_y,80,28).collidepoint(mx,my))

            # separator
            pygame.draw.line(surf, (60,80,60), (pr.x+10, pr.y+152), (pr.right-10, pr.y+152), 1)

            # clip rect for scrollable block list
            clip_top = pr.y + 154
            clip_bot = clip_top + self.SCROLL_AREA_H
            old_clip = surf.get_clip()
            surf.set_clip(pygame.Rect(pr.x, clip_top, pr.w, self.SCROLL_AREA_H))

            for i, b in enumerate(self.blocks):
                row_y = self._block_row_y(i)
                if row_y + 46 < clip_top or row_y > clip_bot: continue

                row_r = pygame.Rect(pr.x+10, row_y, self.PANEL_W-20, 46)
                hov = row_r.collidepoint(mx, my)

                # row bg
                TYPE_COLS = {"Visual":(20,30,60),"Wait":(40,30,10),"Movement":(15,40,15)}
                rs = pygame.Surface((row_r.w, row_r.h), pygame.SRCALPHA)
                rs.fill((*TYPE_COLS.get(b["type"],(30,30,30)), 230 if hov else 200))
                surf.blit(rs, row_r.topleft)
                bdr = (120,160,255) if b["type"]=="Visual" else (255,200,80) if b["type"]=="Wait" else (100,220,100)
                pygame.draw.rect(surf, bdr, row_r, 1, border_radius=5)

                # type badge
                TYPE_ICONS = {"Visual":"👊","Wait":"⏱","Movement":"💨"}
                badge_col = (60,100,200) if b["type"]=="Visual" else (160,120,20) if b["type"]=="Wait" else (30,120,30)
                pygame.draw.rect(surf, badge_col, (row_r.x+4, row_y+4, 70, 38), border_radius=4)
                icon_l = F_SM.render(TYPE_ICONS.get(b["type"],"?"), True, (255,255,255))
                surf.blit(icon_l, (row_r.x+8, row_y+6))
                type_l = F_SM.render(b["type"][:4].upper(), True, (220,220,220))
                surf.blit(type_l, (row_r.x+8, row_y+22))

                # block content
                if b["type"] == "Visual":
                    # cycle v_type button
                    vt_r = pygame.Rect(row_r.x+80, row_y+6, 100, 20)
                    self._draw_btn(surf, vt_r, b["v_type"], (30,30,60), fg=(180,200,255), radius=4)
                    # color swatch cycle
                    try: ci = _SB_COLORS.index(b["color"])
                    except ValueError: ci = 0
                    col_r = pygame.Rect(row_r.x+185, row_y+6, 70, 20)
                    pygame.draw.rect(surf, b["color"], col_r, border_radius=4)
                    pygame.draw.rect(surf, (200,200,200), col_r, 1, border_radius=4)
                    col_name = F_SM.render(_SB_COLOR_NAMES[ci % len(_SB_COLOR_NAMES)], True, (0,0,0))
                    surf.blit(col_name, (col_r.x+4, col_r.y+3))
                    # val
                    val_lbl = F_SM.render(f"Val:", True, (160,160,160))
                    surf.blit(val_lbl, (row_r.x+80, row_y+28))
                    self._draw_btn(surf, pygame.Rect(row_r.x+112, row_y+25, 22, 18), "−", (60,20,20), fg=(255,120,120), radius=3)
                    vnum = F_SM.render(str(int(b["val"])), True, (255,255,255))
                    surf.blit(vnum, (row_r.x+140, row_y+26))
                    self._draw_btn(surf, pygame.Rect(row_r.x+168, row_y+25, 22, 18), "+", (20,60,20), fg=(120,255,120), radius=3)

                elif b["type"] == "Wait":
                    wlbl = F_SM.render("Duration:", True, (160,160,160))
                    surf.blit(wlbl, (row_r.x+80, row_y+14))
                    self._draw_btn(surf, pygame.Rect(row_r.x+130, row_y+8, 22, 28), "−", (60,20,20), fg=(255,120,120), radius=3)
                    wnum = F_MD.render(f"{b['val']:.1f}s", True, (255,210,80))
                    surf.blit(wnum, (row_r.x+158, row_y+12))
                    self._draw_btn(surf, pygame.Rect(row_r.x+190, row_y+8, 22, 28), "+", (20,60,20), fg=(120,255,120), radius=3)

                elif b["type"] == "Movement":
                    mlbl = F_SM.render("Speed:", True, (160,160,160))
                    surf.blit(mlbl, (row_r.x+80, row_y+14))
                    self._draw_btn(surf, pygame.Rect(row_r.x+130, row_y+8, 22, 28), "−", (60,20,20), fg=(255,120,120), radius=3)
                    mnum = F_MD.render(str(int(b["val"])), True, (120,255,120))
                    surf.blit(mnum, (row_r.x+158, row_y+12))
                    self._draw_btn(surf, pygame.Rect(row_r.x+200, row_y+8, 22, 28), "+", (20,60,20), fg=(120,255,120), radius=3)

                # up/down arrows
                up_r = pygame.Rect(row_r.right-72, row_y+4, 28, 18)
                dn_r = pygame.Rect(row_r.right-72, row_y+24, 28, 18)
                if i > 0:
                    self._draw_btn(surf, up_r, "▲", (40,40,60), fg=(200,200,255), radius=3)
                if i < len(self.blocks)-1:
                    self._draw_btn(surf, dn_r, "▼", (40,40,60), fg=(200,200,255), radius=3)

                # delete button
                del_r = pygame.Rect(row_r.right-36, row_y+8, 30, 30)
                self._draw_btn(surf, del_r, "✕", (100,20,20), fg=(255,120,120), radius=4)

            surf.set_clip(old_clip)

            # scroll bar
            if len(self.blocks) * 52 > self.SCROLL_AREA_H:
                total = len(self.blocks) * 52
                frac  = self.scroll_off / max(1, total - self.SCROLL_AREA_H)
                bar_h = int(self.SCROLL_AREA_H * self.SCROLL_AREA_H / total)
                bar_y = clip_top + int(frac * (self.SCROLL_AREA_H - bar_h))
                pygame.draw.rect(surf, (60,80,60), (pr.right-8, clip_top, 6, self.SCROLL_AREA_H), border_radius=3)
                pygame.draw.rect(surf, (120,200,120), (pr.right-8, bar_y, 6, bar_h), border_radius=3)

            if not self.blocks:
                hint = F_MD.render("Click + buttons above to add blocks", True, (50,80,50))
                surf.blit(hint, (pr.x + pr.w//2 - hint.get_width()//2,
                                 clip_top + self.SCROLL_AREA_H//2 - hint.get_height()//2))

        # ── LOAD ─────────────────────────────────────────
        elif self.state == "LOAD":
            ttl = F_TTL.render("📂  Load & Equip", True, (160,200,255))
            surf.blit(ttl, (pr.x+14, pr.y+8))

            list_y = pr.y + 50
            for i, sk in enumerate(self.saved_skills):
                row_r = pygame.Rect(pr.x+14, list_y + i*50, 200, 40)
                sel = (i == self.selected_skill_idx)
                rs = pygame.Surface((row_r.w, row_r.h), pygame.SRCALPHA)
                rs.fill((30,80,30,230) if sel else (20,20,40,200))
                surf.blit(rs, row_r.topleft)
                pygame.draw.rect(surf, (100,220,100) if sel else (60,100,60), row_r, 2, border_radius=5)
                nc = (220,255,220) if sel else (160,180,160)
                if self._rename_target == i:
                    curs = "_" if int(self._pulse*4)%2==0 else ""
                    surf.blit(F_SM.render(f"{self._rename_buf}{curs}", True, (255,255,100)), (row_r.x+8, row_r.y+12))
                else:
                    surf.blit(F_SM.render(sk["name"], True, nc), (row_r.x+8, row_r.y+12))
                blk_c = F_SM.render(f"{len(sk['blocks'])} blocks", True, (100,150,100))
                surf.blit(blk_c, (row_r.x+8, row_r.y+26))

                del_r = pygame.Rect(pr.x+222, list_y+i*50, 36, 40)
                self._draw_btn(surf, del_r, "🗑", (80,20,20), fg=(255,120,120), radius=4)
                ren_r = pygame.Rect(pr.x+262, list_y+i*50, 60, 40)
                self._draw_btn(surf, ren_r, "✏Ren", (30,30,60), fg=(180,200,255), radius=4)

            if not self.saved_skills:
                nm = F_MD.render("No skills saved yet", True, (60,80,60))
                surf.blit(nm, (pr.x+20, list_y+10))

            # equip column
            if self.selected_skill_idx >= 0:
                eq_x = pr.x + 340; eq_y = pr.y + 50
                eq_ttl = F_SM.render("Equip to slot:", True, (180,180,220))
                surf.blit(eq_ttl, (eq_x, eq_y - 18))
                eq_keys = [("5",pygame.K_5),("6",pygame.K_6),("7",pygame.K_7),
                           ("8",pygame.K_8),("9",pygame.K_9),("0",pygame.K_0)]
                for ki, (ks, pk) in enumerate(eq_keys):
                    er = pygame.Rect(eq_x, eq_y+ki*40, 120, 32)
                    self._draw_btn(surf, er, f"[{ks}] Slot {ks}", (50,40,10), fg=(255,200,80),
                                   hover=er.collidepoint(mx,my), radius=5)

            # back
            self._draw_btn(surf, pygame.Rect(pr.x+20, pr.y+pr.h-44, 120, 34),
                           "← Back", (40,40,40), fg=(180,180,180),
                           hover=pygame.Rect(pr.x+20,pr.y+pr.h-44,120,34).collidepoint(mx,my))


# ══════════════════════════════════════════════════════════
#  CHARACTER SELECT UI
# ══════════════════════════════════════════════════════════
class CharacterSelectUI:
    BTN_W = 280; BTN_H = 50
    BTN_X = 10;  BTN_Y = 10
    ITEM_H = 46
    CHARACTERS = [("Garou", (60, 160, 240), "NORMAL"), ("Cosmic Garou", (150, 50, 255), "COSMIC"), ("Reaper", (200, 30, 40), "REAPER"), ("Projection Sorcerer", (255, 200, 50), "PROJECTION")]

    def __init__(self):
        self.open = False; self.hovered = -1; self.code_text = ""; self.unlocked_ps = False; self.code_active = False

    def handle_event(self, ev, game):
        mx, my = pygame.mouse.get_pos()
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if pygame.Rect(self.BTN_X, self.BTN_Y, self.BTN_W, self.BTN_H).collidepoint(mx, my):
                self.open = not self.open; self.code_active = False; return True
            if self.open:
                for i, (name, col, state) in enumerate(self.CHARACTERS):
                    if pygame.Rect(self.BTN_X, self.BTN_Y + self.BTN_H + 4 + i * self.ITEM_H, self.BTN_W, self.ITEM_H).collidepoint(mx, my):
                        if state == "PROJECTION" and not self.unlocked_ps: self.code_active = False; return True
                        self.open = False; self.code_active = False
                        if state == "NORMAL": game.player.go_normal()
                        elif state == "COSMIC": game.global_cutscene = CosmicCutscene()
                        elif state == "REAPER": game.global_cutscene = ReaperAwakening()
                        elif state == "PROJECTION": game.player.go_projection()
                        return True
                bar_rect = pygame.Rect(self.BTN_X, self.BTN_Y + self.BTN_H + 4 + len(self.CHARACTERS) * self.ITEM_H, self.BTN_W, 36)
                if bar_rect.collidepoint(mx, my): self.code_active = True; return True
                else: self.code_active = False; self.open = False

        if ev.type == pygame.MOUSEMOTION:
            self.hovered = -1
            if self.open:
                for i in range(len(self.CHARACTERS)):
                    if pygame.Rect(self.BTN_X, self.BTN_Y + self.BTN_H + 4 + i * self.ITEM_H, self.BTN_W, self.ITEM_H).collidepoint(mx, my): self.hovered = i

        if ev.type == pygame.KEYDOWN and self.open and self.code_active:
            if ev.key == pygame.K_RETURN:
                if self.code_text == "12345": self.unlocked_ps = True
                self.code_text = ""; self.code_active = False
            elif ev.key == pygame.K_BACKSPACE: self.code_text = self.code_text[:-1]
            else:
                if len(self.code_text) < 15: self.code_text += ev.unicode
        return False

    def draw(self, surf):
        bx, by = self.BTN_X, self.BTN_Y
        btn_surf = pygame.Surface((self.BTN_W, self.BTN_H), pygame.SRCALPHA); btn_surf.fill((0, 0, 0, 180)); surf.blit(btn_surf, (bx, by))
        pygame.draw.rect(surf, (255, 255, 255), (bx, by, self.BTN_W, self.BTN_H), 3, border_radius=5)
        cube_sz = 30; cube_x = bx + 10; cube_y = by + (self.BTN_H - cube_sz) // 2
        pygame.draw.rect(surf, (255, 255, 255), (cube_x, cube_y, cube_sz, cube_sz), border_radius=4); pygame.draw.rect(surf, (180, 180, 180), (cube_x, cube_y, cube_sz, cube_sz), 2, border_radius=4)
        q = F_LG.render("?", True, (30, 30, 30)); surf.blit(q, (cube_x + cube_sz//2 - q.get_width()//2, cube_y + cube_sz//2 - q.get_height()//2))
        txt = F_MD.render("Characters", True, (255, 255, 255)); surf.blit(txt, (cube_x + cube_sz + 12, by + self.BTN_H//2 - txt.get_height()//2))

        if not self.open: return
        for i, (name, col, state) in enumerate(self.CHARACTERS):
            row_y = by + self.BTN_H + 4 + i * self.ITEM_H; is_hov = (self.hovered == i)
            row_surf = pygame.Surface((self.BTN_W, self.ITEM_H), pygame.SRCALPHA); row_surf.fill((0, 0, 0, 230 if is_hov else 190)); surf.blit(row_surf, (bx, row_y))
            pygame.draw.rect(surf, col if is_hov else (120, 120, 120), (bx, row_y, self.BTN_W, self.ITEM_H), 2, border_radius=4)

            if state == "PROJECTION":
                pygame.draw.rect(surf, (100, 200, 255), pygame.Rect(bx + 10, row_y + self.ITEM_H//2 - 10, 20, 20), 2); pygame.draw.rect(surf, (210, 90, 90), pygame.Rect(bx + 14, row_y + self.ITEM_H//2 - 6, 12, 12))
                lbl = F_SM.render(name + " [LOCKED]" if not self.unlocked_ps else name, True, (150, 150, 150) if not self.unlocked_ps else (255, 255, 255))
            else:
                pygame.draw.circle(surf, col, (bx + 20, row_y + self.ITEM_H//2), 8); pygame.draw.circle(surf, (255,255,255), (bx + 20, row_y + self.ITEM_H//2), 8, 1)
                lbl = F_SM.render(name, True, (255, 255, 255))
            surf.blit(lbl, (bx + 40, row_y + self.ITEM_H//2 - lbl.get_height()//2))

        bar_y = by + self.BTN_H + 4 + len(self.CHARACTERS) * self.ITEM_H
        bar_surf = pygame.Surface((self.BTN_W, 36), pygame.SRCALPHA); bar_surf.fill((20, 20, 30, 220)); surf.blit(bar_surf, (bx, bar_y))
        pygame.draw.rect(surf, (150, 255, 150) if self.code_active else (100, 150, 100), (bx, bar_y, self.BTN_W, 36), 2, border_radius=4)
        surf.blit(F_SM.render(f"Code: {self.code_text}{'_' if self.code_active else ''}", True, (200, 255, 200)), (bx + 10, bar_y + 10))


# ══════════════════════════════════════════════════════════
#  HOTBAR
# ══════════════════════════════════════════════════════════
class Hotbar:
    def __init__(self):
        self.anim1 = 0.0; self.anim2 = 0.0; self.anim3 = 0.0
        self.custom_anims = {k: 0.0 for k in [pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0]}

    def flash_skill(self, n):
        if n == 1: self.anim1 = 0.4
        elif n == 2: self.anim2 = 0.4
        elif n == 3: self.anim3 = 0.4
        elif n in self.custom_anims: self.custom_anims[n] = 0.4

    def update(self, dt):
        if self.anim1 > 0: self.anim1 -= dt
        if self.anim2 > 0: self.anim2 -= dt
        if self.anim3 > 0: self.anim3 -= dt
        for k in self.custom_anims:
            if self.custom_anims[k] > 0: self.custom_anims[k] -= dt

    def draw(self, surf, player: Player, game):
        sw = 120; sh = 62; gap = 10
        active_slots = []

        if player.state == "NORMAL":
            active_slots.extend([
                ("[1]", "Cons. Punches", player.skill1_cd, 1.2, self.anim1 > 0, (80,160,255)),
                ("[2]", "Water Barrage", player.skill2_cd, 3.5, self.anim2 > 0, (80,200,255)),
                ("[3]", "Whirlwind Water", player.skill3_cd, 4.0, self.anim3 > 0, (0,150,255))
            ])
        elif player.state == "COSMIC":
            active_slots.extend([
                ("[1]", "Galactic Push", player.skill1_cd, 3.5, self.anim1 > 0, (150,50,255)),
                ("[2]", "Galaxy Pull", player.skill2_cd, 2.5, self.anim2 > 0, (100,50,255)),
                ("[3]", "Portal Nausea", player.skill3_cd, 5.0, self.anim3 > 0, (200,80,255))
            ])
        elif player.state == "REAPER": 
            active_slots.extend([
                ("[1]", "Soul Drain", player.skill1_cd, 4.0, self.anim1 > 0, (220,50,50)),
                ("[2]", "Menacing Rush", player.skill2_cd, 6.0, self.anim2 > 0, (180,20,40)),
                ("[3]", "Mark", player.skill3_cd, 3.0, self.anim3 > 0, (255,80,80))
            ])
        else: # PROJECTION
            active_slots.extend([
                ("[1]", "Decisive Strike", player.skill1_cd, 3.0, self.anim1 > 0, (255,200,50)),
                ("[2]", "...", 0, 1.0, self.anim2 > 0, (100,100,100)),
                ("[3]", "...", 0, 1.0, self.anim3 > 0, (100,100,100))
            ])

        # Dynamic Custom Slots
        custom_keys = [("5", pygame.K_5), ("6", pygame.K_6), ("7", pygame.K_7), ("8", pygame.K_8), ("9", pygame.K_9), ("0", pygame.K_0)]
        for kb_str, p_key in custom_keys:
            skill = game.custom_equipped.get(p_key)
            if skill:
                cd = game.custom_cds.get(p_key, 0.0)
                active = self.custom_anims[p_key] > 0
                active_slots.append((f"[{kb_str}]", skill["name"], cd, 2.0, active, (100,255,100)))

        total_w = len(active_slots) * sw + max(0, len(active_slots)-1) * gap
        start_x = WIDTH//2 - total_w//2
        y = HEIGHT - 85

        for i, (kb, name, cd, max_cd, active, col) in enumerate(active_slots):
            sx = start_x + i * (sw + gap)
            bg_col = (40,30,80,220) if active else (20,20,30,210)
            s = pygame.Surface((sw,sh), pygame.SRCALPHA)
            pygame.draw.rect(s, bg_col, (0,0,sw,sh), border_radius=9)
            bdr = (*col,255) if active else (70,70,110,255)
            pygame.draw.rect(s, bdr, (0,0,sw,sh), 2, border_radius=9)
            if cd > 0:
                frac = 1 - cd/max_cd
                cdcol = (60,60,80,180)
                pygame.draw.rect(s, cdcol, (2,sh-8,sw-4,6), border_radius=3)
                pygame.draw.rect(s, (*col,180), (2,sh-8,int((sw-4)*frac),6), border_radius=3)
            surf.blit(s,(sx,y))
            kbt = F_MD.render(kb,  True, col if active else (160,160,200))
            surf.blit(kbt, (sx+8, y+6))
            
            # Truncate long names
            n_disp = name if len(name) < 13 else name[:10]+".."
            nmt = F_SM.render(n_disp, True, (230,230,255))
            surf.blit(nmt, (sx+8, y+30))


# ══════════════════════════════════════════════════════════
#  GAME
# ══════════════════════════════════════════════════════════
class Game:
    def __init__(self):
        self.arena      = Arena()
        self.player     = Player()
        self.dummy      = Dummy()
        self.helper     = Helper()
        self.hotbar     = Hotbar()
        self.char_select = CharacterSelectUI()
        self.skill_ui   = SkillBuilderUI()
        self.dim_idx    = 0   
        self.transition = None
        self.cinematic  = None   
        self.ko_timer   = 0.0
        self.ko_showing = False
        self.respawn_timer = 0.0   
        self.running    = True
        self.global_particles: list[Particle] = []
        self.global_cutscene = None
        
        # Custom skills state
        self.custom_equipped = {}
        self.custom_cds = {}

    def set_dimension(self, idx):
        self.dim_idx = idx
        self.transition = DimTransition(DIMENSIONS[idx])

    def reset_dummy(self):
        self.dummy.reset()
        self.ko_showing    = False
        self.ko_timer      = 0.0
        self.respawn_timer = 0.0

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
            if self.global_cutscene and not self.global_cutscene.done:
                continue
            
            # Intercept UI clicks so you don't attack behind them
            if self.skill_ui.handle_event(ev, self): continue
            if self.char_select.handle_event(ev, self): continue
                
            if ev.type == pygame.KEYDOWN:
                k = ev.key
                if k == pygame.K_1:  self._skill(1)
                elif k == pygame.K_2:  self._skill(2)
                elif k == pygame.K_3:  self._skill(3)
                elif k in [pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0]:
                    self._custom_skill(k)
                elif k == pygame.K_c and self.player.state == "NORMAL":
                    self.global_cutscene = CosmicCutscene()

    def _custom_skill(self, k):
        if self.cinematic or self.global_cutscene: return
        if k in self.custom_equipped:
            if self.custom_cds.get(k, 0) <= 0:
                skill = self.custom_equipped[k]
                self.cinematic = CustomSkillSequence(self.player, self.dummy, skill["blocks"])
                self.custom_cds[k] = 2.0  # Default 2s cd for custom skills
            else:
                self.hotbar.flash_skill(k)

    def _skill(self, n):
        if self.cinematic or self.global_cutscene: return
        if n == 1:
            result = self.player.use_skill1()
            if result == "GALACTIC_PUSH" and self.dummy.alive and self.player.push_cd <= 0:
                self.cinematic = GalacticPush(self.player, self.dummy, self.set_dimension)
                self.player.push_cd = 3.5; self.player.skill1_cd = 3.5
            elif result == "SOUL_DRAIN" and self.dummy.alive and self.player.skill1_cd <= 0:
                self.cinematic = SoulDrainSequence(self.player, self.dummy, self); self.player.skill1_cd = 4.0
            elif result == "DECISIVE_STRIKE" and self.dummy.alive and self.player.skill1_cd <= 0:
                self.cinematic = DecisiveStrikeSequence(self.player, self.dummy); self.player.skill1_cd = 3.0
            elif result is None: self.hotbar.flash_skill(1)
        elif n == 2:
            result = self.player.use_skill2()
            if result == "GALAXY_PULL" and self.dummy.alive and self.player.galaxy_cd <= 0:
                self.cinematic = GalaxyPull(self.player, self.dummy)
                self.player.galaxy_cd = 2.5; self.player.skill2_cd = 2.5
            elif result == "RUSH_STARTED": pass
            elif result is None: self.hotbar.flash_skill(2)
        elif n == 3:
            result = self.player.use_skill3()
            if result == "WHIRLWIND_WATER" and self.dummy.alive and self.player.skill3_cd <= 0:
                self.cinematic = WhirlwindWaterStrike(self.player, self.dummy); self.player.skill3_cd = 4.0
            elif result == "PORTAL_NAUSEA" and self.dummy.alive and self.player.skill3_cd <= 0:
                self.cinematic = PortalNausea(self.player, self.dummy); self.player.skill3_cd = 5.0
            elif result == "REAPER_MARK" and self.dummy.alive and self.player.skill3_cd <= 0:
                self.cinematic = ReaperMarkSequence(self.player, self.dummy); self.player.skill3_cd = 3.0
            elif result is None: self.hotbar.flash_skill(3)

    def _update(self, dt):
        for p in self.global_particles[:]:
            p.update(dt)
            if not p.alive: self.global_particles.remove(p)

        if self.global_cutscene:
            self.global_cutscene.update(dt)
            if self.global_cutscene.done:
                if isinstance(self.global_cutscene, CosmicCutscene): self.player.go_cosmic()
                elif isinstance(self.global_cutscene, ReaperAwakening): self.player.go_reaper()
                self.global_cutscene = None
            return  

        keys = pygame.key.get_pressed()
        self.arena.update(dt)
        
        action = self.player.update(dt, keys, self.dummy)
        if action == "MENACING_CUTSCENE": self.cinematic = MenacingCutscene(self.dummy)

        self.dummy.update(dt, self.dim_idx)
        self.helper.update(dt, self.player, self.dummy, self.global_particles)
        self.hotbar.update(dt)
        
        if self.player.galaxy_cd > 0: self.player.galaxy_cd -= dt
        if self.player.push_cd   > 0: self.player.push_cd   -= dt

        for k in self.custom_cds:
            if self.custom_cds[k] > 0: self.custom_cds[k] -= dt

        if self.cinematic:
            self.cinematic.update(dt)
            if self.cinematic.done: self.cinematic = None

        if self.transition:
            self.transition.update(dt)
            if self.transition.done: self.transition = None

        if not self.dummy.alive and not self.ko_showing:
            self.ko_showing = True; self.ko_timer = 3.5; self.respawn_timer = 2.0  

        if self.dim_idx == 1 and not self.dummy.alive:
            if self.dummy.lava_death and self.dummy.dead_timer <= 0: self.set_dimension(0)

        if self.ko_showing:
            self.ko_timer -= dt
            if self.ko_timer <= 0: self.ko_showing = False

        if self.respawn_timer > 0:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0: self.reset_dummy()

    def _draw(self):
        if self.global_cutscene:
            self.global_cutscene.draw(screen)
            pygame.display.flip()
            return

        self.arena.draw(screen, self.dim_idx)
        for p in self.global_particles: p.draw(screen)
        
        if not isinstance(self.cinematic, MenacingCutscene):
            self.dummy.draw(screen)
            self.helper.draw(screen)
            self.player.draw(screen)

        if self.cinematic: self.cinematic.draw(screen)

        self._draw_hud()
        self.hotbar.draw(screen, self.player, self)
        
        self.char_select.draw(screen)
        self.skill_ui.draw(screen)

        if self.transition: self.transition.draw(screen)
        if self.ko_showing: self._draw_ko()

        pygame.display.flip()

    def _draw_hud(self):
        col = (150,50,255) if self.player.state=="COSMIC" else (220,50,50) if self.player.state=="REAPER" else (255,200,50) if self.player.state=="PROJECTION" else (60,160,240)
        badge = F_MD.render(f"STATE: {self.player.state}", True, col)
        screen.blit(badge,(AL+4, AT+4))

        dim_name = DIMENSIONS[self.dim_idx]
        dim_cols = {0:(150,150,180), 1:(255,100,30)}
        dc = dim_cols.get(self.dim_idx,(200,200,200))
        dlbl = F_MD.render(f"DIM: {dim_name}", True, dc)
        screen.blit(dlbl,(AR-dlbl.get_width()-6, AT+4))

        ctrl = F_SM.render("WASD:Move  1/2/3:Skills  5-0:Custom Skills  C:Cosmic Cutscene", True,(100,100,130))
        screen.blit(ctrl,(WIDTH//2-ctrl.get_width()//2, HEIGHT-22))

    def _draw_ko(self):
        t = max(0.0, self.ko_timer/3.5)
        shake_x = int(5*math.sin(self.ko_timer*28)) if self.ko_timer > 3.0 else 0
        ov = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA)
        a  = int(100*(1.0-abs(t-0.5)/0.5))
        ov.fill((180,0,0,max(0,a)))
        screen.blit(ov,(0,0))
        ko  = F_XL.render("K.O.", True,(255,50,50)); shadow = F_XL.render("K.O.", True,(80,0,0))
        sx = WIDTH//2 - ko.get_width()//2 + shake_x; sy = HEIGHT//2 - ko.get_height()//2
        screen.blit(shadow,(sx+5,sy+5)); screen.blit(ko,(sx,sy))
        rtime = max(0.0, self.respawn_timer)
        sub = F_MD.render(f"Respawning in {rtime:.1f}s...", True,(220,180,180))
        screen.blit(sub,(WIDTH//2-sub.get_width()//2, sy+95))

# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    Game().run()