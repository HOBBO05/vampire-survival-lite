import tkinter as tk
import math
import time
import random
from pathlib import Path

PLAYER_SIZE = 26
PLAYER_SPEED = 10

TILE_SIZE = 160
BG_COLOR = "black"
TILE_COLOR_1 = "#181818"
TILE_COLOR_2 = "#101010"

GEM_SIZE = 16
GEM_XP_VALUE = 5
XP_BAR_HEIGHT = 24
XP_BASE_REQ = 50
GEM_PICKUP_RADIUS = 60  # 최소 줍기 반경(픽셀)

PLAYER_MAX_HP = 100
MONSTER_CONTACT_DAMAGE = 12
PLAYER_DAMAGE_COOLDOWN = 0.6  # 연속 피격 간 최소 간격(초)
POTION_SIZE = 18
POTION_HEAL = 12
POTION_DROP_CHANCE = 0.08
POTION_PICKUP_RADIUS = 60
POTION_IMG_NAMES = ["potion.png", "힐팩.png"]
POTION_TARGET_SIZE = 40

SPRITE_TARGET_SIZE = None  # 픽셀로 강제 크기(가장 긴 변 기준). None이면 SCALE만 사용
SPRITE_SCALE = 0.3         # 1.0은 원본, 0.5는 절반, 2.0은 2배(정수 배 확대/축소만 지원)

MONSTER_TARGET_SIZE = 90
MONSTER_SCALE = 0.6
MONSTER_ANIM_INTERVAL = 0.18
MONSTER_IMG_1 = "zombie1.png"
MONSTER_IMG_2 = "zombie2.png"

ELITE_IMG = "golem.png"
ELITE_SIZE = 150
ELITE_SPEED = 1.8
ELITE_MAX_HP = 16
ELITE_SPAWN_INTERVAL = 9.0
ELITE_SPAWN_CHANCE = 0.1  # 몬스터 생성 시 이 확률로 정예 등장 (기존의 약 1/3)

BOSS_IMG = "boss.png"
BOSS_SIZE = 140
BOSS_SPEED = 2.8
BOSS_MAX_HP = 120
BOSS_SPAWN_TIME = 45.0  # 게임 시작 후 45초에 등장

UPGRADE_IMG_DAGGER = "upgrade_dagger.png"
UPGRADE_IMG_BIBLE = "upgrade_bible.png"

PROJECTILE_SPEED = 16
PROJECTILE_LIFETIME = 3.0
PROJECTILE_SIZE = 15
DAGGER_DAMAGE = 2          # 단검 데미지
PROJECTILE_TARGET_SIZE = 60
DAGGER_IMG_RIGHT_NAMES = ["dagger.png", "단검.png"]
DAGGER_IMG_LEFT_NAMES = ["dagger_left.png", "단검_left.png"]

MONSTER_SIZE = 32
MONSTER_SPEED = 4.5
MONSTER_SPAWN_INTERVAL = 0.6   # 몬스터 생성 주기 (초)
MAX_MONSTERS = 40              # 화면에 동시에 존재할 최대 몬스터 수
MONSTER_MAX_HP = 2             # 몬스터 체력(기본값 2)

BIBLE_COUNT = 2
BIBLE_ORBIT_RADIUS = 140
BIBLE_INNER_RADIUS = 25
BIBLE_SIZE_ACTIVE = 24
BIBLE_SIZE_COOLDOWN = 10
BIBLE_ANGULAR_SPEED = 0.075    # 약간 더 느리게
BIBLE_ACTIVE_TIME = 3.0
BIBLE_FADE_OUT_TIME = 0.7      # 나선형으로 스르륵 사라지는 시간
BIBLE_COOLDOWN_TIME = 1.5
BIBLE_FADE_IN_TIME = 0.7       # 캐릭터에서 퍼져나오며 생기는 시간
BIBLE_DAMAGE = 2
BIBLE_TARGET_SIZE = 43
BIBLE_IMG_NAMES = ["bible.png", "바이블.png"]

KNOCKBACK_DISTANCE_DAGGER = 0.0   # 단검 넉백 제거
KNOCKBACK_DISTANCE_BIBLE = 30.0   # 바이블 넉백 약화

BOSS_IMG = "boss.png"
BOSS_SIZE = 140
BOSS_SPEED_EARLY = 4.3   # 웨이브 1~2
BOSS_SPEED_LATE = 5.3    # 웨이브 3+
BOSS_MAX_HP = 120
BOSS_SPAWN_TIME = 45.0   # 첫 웨이브 시작 시간(초)
MAX_WAVE = 5
WAVE_BANNER_DURATION = 2.5
BOSS_BULLET_SPEED = 6.5
BOSS_BULLET_SIZE = 12
BOSS_BULLET_DAMAGE = 20
BOSS_BULLET_LIFETIME = 8.0
BOSS_SHOT_INTERVAL = 4.0
BIBLE_BLOCK_CHANCE = 0.35

def get_wave_scalars_static(wave):
    speed_mult = 1.0
    spawn_mult = 1.0
    hp_mult = 1.0
    dmg_bonus = 0
    if wave >= 3:
        hp_mult = 2.0  # 2방 정도에 사망
        speed_mult = 1.15    # 웨이브3 약간 빠르게
        spawn_mult += 0.5
    if wave >= 4:
        speed_mult = 5.3 / MONSTER_SPEED  # 속도 5.3
        spawn_mult += 0.8
        dmg_bonus += 4
    return speed_mult, spawn_mult, hp_mult, dmg_bonus


def boss_speed_for_wave(wave):
    if wave <= 2:
        return BOSS_SPEED_EARLY
    return BOSS_SPEED_LATE


class VampireSurvivorLite:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Vampire Survivor Lite - Homing & Pause")

        self.root.attributes("-fullscreen", True)

        self.root.bind("<Escape>", self.toggle_pause)

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(
            root,
            width=self.screen_width,
            height=self.screen_height,
            bg=BG_COLOR,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)

        base_dir = Path(__file__).resolve().parent
        self.bg_image = tk.PhotoImage(file=str(base_dir / "background.png"))
        self.bg_w = self.bg_image.width()
        self.bg_h = self.bg_image.height()

        self.upgrade_imgs = {
            "dagger": self._safe_load_image(base_dir / UPGRADE_IMG_DAGGER),
            "bible": self._safe_load_image(base_dir / UPGRADE_IMG_BIBLE),
        }

        self.dagger_image_right = self._load_first_image(base_dir, DAGGER_IMG_RIGHT_NAMES, PROJECTILE_TARGET_SIZE, SPRITE_SCALE)
        self.dagger_image_left = self._load_first_image(base_dir, DAGGER_IMG_LEFT_NAMES, PROJECTILE_TARGET_SIZE, SPRITE_SCALE)
        self.dagger_image = self.dagger_image_right or self.dagger_image_left
        self.bible_image = self._load_first_image(base_dir, BIBLE_IMG_NAMES, BIBLE_TARGET_SIZE, SPRITE_SCALE)
        self.potion_image = self._load_first_image(base_dir, POTION_IMG_NAMES, POTION_TARGET_SIZE, SPRITE_SCALE)

        self.player_image = self._scale_image(
            self._safe_load_image(base_dir / "player.png"),
            SPRITE_TARGET_SIZE,
            SPRITE_SCALE,
        )
        frame_names_right = ["player_run1.png", "player_run2.png", "player_run3.png", "player_run4.png"]
        frame_names_left = ["player_run_left1.png", "player_run_left2.png", "player_run_left3.png", "player_run_left4.png"]
        self.player_frames_right = []
        self.player_frames_left = []
        for fname in frame_names_right:
            img = self._scale_image(self._safe_load_image(base_dir / fname), SPRITE_TARGET_SIZE, SPRITE_SCALE)
            if img:
                self.player_frames_right.append(img)
        for fname in frame_names_left:
            img = self._scale_image(self._safe_load_image(base_dir / fname), SPRITE_TARGET_SIZE, SPRITE_SCALE)
            if img:
                self.player_frames_left.append(img)
        self.player_anim_index = 0
        self.player_anim_timer = 0.0
        self.player_anim_interval = 0.12  # 초당 프레임 전환 속도
        self.last_move_dir = "right"

        self.monster_frames = []
        for fname in [MONSTER_IMG_1, MONSTER_IMG_2]:
            img = self._scale_image(self._safe_load_image(base_dir / fname), MONSTER_TARGET_SIZE, MONSTER_SCALE)
            if img:
                self.monster_frames.append(img)
        self.elite_image = self._scale_image(self._safe_load_image(base_dir / ELITE_IMG), ELITE_SIZE, 1.0)
        self.boss_image = self._scale_image(self._safe_load_image(base_dir / BOSS_IMG), BOSS_SIZE, 1.0)
        self.monster_anim_timer = 0.0
        self.monster_anim_index = 0

        self.world_x = 0.0
        self.world_y = 0.0
        self.hp_max = PLAYER_MAX_HP
        self.hp = self.hp_max
        self.last_damage_time = -999.0

        self.player_screen_x = self.screen_width // 2
        self.player_screen_y = self.screen_height // 2

        self.facing_x = 1.0
        self.facing_y = 0.0
        self.dagger_count = 1  # 기본 단검 수
        self.bible_count = 0   # 기본 바이블 수(초기에는 없음)

        self.keys_pressed = set()
        root.bind("<KeyPress>", self.on_key_press)
        root.bind("<KeyRelease>", self.on_key_release)

        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self.is_moving = False

        self.projectiles = []

        self.monsters = []

        self.bibles = []

        self.gems = []
        self.xp = 0
        self.level = 1
        self.xp_to_next = XP_BASE_REQ
        self.level_up_active = False
        self.level_up_choice_boxes = []

        self.potions = []

        self.game_over = False
        self.game_over_text = "GAME OVER"

        self.game_time = 0.0                  # 게임 안에서 흐르는 시간
        self.last_real_time = time.time()     # 실제 세계 시간(초)
        self.paused = False                   # 일시정지 여부

        self.last_shot = self.game_time
        self.shot_interval = 0.9

        self.last_monster_spawn = self.game_time
        self.last_elite_spawn = self.game_time
        self.wave = 0
        self.max_wave = MAX_WAVE
        self.next_wave_time = BOSS_SPAWN_TIME
        self.wave_banner_time = 0.0
        self.wave_banner_text = ""
        self.game_finished = False
        self.timer_elapsed = 0.0
        self.wave = 0
        self.spawn_speed_mult = 1.0
        self.boss_bullets = []

        self.init_bibles()

        self.game_loop()

    def _safe_load_image(self, path: Path):
        try:
            return tk.PhotoImage(file=str(path))
        except Exception:
            return None

    def _scale_image(self, img: tk.PhotoImage, target_size: float = None, scale: float = 1.0):
        """tk.PhotoImage 크기 조절 helper.
        - target_size: 가장 긴 변을 이 크기로 맞추기 (축소/확대 모두 지원, 정수배)
        - scale: 배율(1.0 원본, 0.5 절반, 2.0 두배). target_size가 None일 때만 적용.
        확대/축소는 정수배 단위로 처리됩니다(zoom/subsample)."""
        if img is None:
            return None

        if target_size:
            max_dim = max(img.width(), img.height())
            if max_dim == 0:
                return img
            if max_dim == target_size:
                return img
            if max_dim > target_size:
                factor = max(1, math.ceil(max_dim / target_size))
                return img.subsample(factor, factor)
            else:
                factor = max(1, math.ceil(target_size / max_dim))
                return img.zoom(factor, factor)

        if scale == 1.0:
            return img
        if scale < 1.0:
            factor = max(1, round(1 / scale))
            return img.subsample(factor, factor)
        else:
            factor = max(1, round(scale))
            return img.zoom(factor, factor)

    def _get_current_frames(self):
        if self.last_move_dir == "left" and self.player_frames_left:
            return self.player_frames_left
        if self.player_frames_right:
            return self.player_frames_right
        return None

    def _load_first_image(self, base_dir: Path, names, target_size=None, scale=1.0):
        for name in names:
            img = self._scale_image(self._safe_load_image(base_dir / name), target_size, scale)
            if img:
                return img
        return None

    def get_wave_scalars(self):
        return get_wave_scalars_static(self.wave)

    def spawn_boss_bullets(self, boss):
        for ring in range(2):
            base_angle = 0.0 + (math.pi / 8) * ring
            for i in range(8):
                ang = base_angle + (math.pi / 4) * i
                vx = math.cos(ang) * BOSS_BULLET_SPEED
                vy = math.sin(ang) * BOSS_BULLET_SPEED
                self.boss_bullets.append({
                    "x": boss["x"],
                    "y": boss["y"],
                    "vx": vx,
                    "vy": vy,
                    "birth": self.game_time,
                })

    def update_boss_bullets(self):
        if not self.boss_bullets:
            return
        now = self.game_time
        alive = []
        for b in self.boss_bullets:
            b["x"] += b["vx"]
            b["y"] += b["vy"]
            if now - b["birth"] > BOSS_BULLET_LIFETIME:
                continue
            blocked = False
            for bible in self.bibles:
                if bible["state"] != "active":
                    continue
                dx = (bible["wx"] - b["x"])
                dy = (bible["wy"] - b["y"])
                rad = (BIBLE_SIZE_ACTIVE / 2) + (BOSS_BULLET_SIZE / 2)
                if dx * dx + dy * dy <= rad * rad:
                    if random.random() < BIBLE_BLOCK_CHANCE:
                        blocked = True
                        break
            if blocked:
                continue

            dx = b["x"] - self.world_x
            dy = b["y"] - self.world_y
            rad = (PLAYER_SIZE / 2) + (BOSS_BULLET_SIZE / 2)
            if dx * dx + dy * dy <= rad * rad:
                self.hp -= BOSS_BULLET_DAMAGE
                if self.hp <= 0:
                    self.hp = 0
                    self.trigger_game_over()
                continue

            alive.append(b)
        self.boss_bullets = alive

    def separate_bosses(self):
        bosses = [m for m in self.monsters if m.get("type") == "boss"]
        if len(bosses) < 2:
            return
        min_dist = BOSS_SIZE * 0.8
        min_dist_sq = min_dist * min_dist
        for i in range(len(bosses)):
            for j in range(i + 1, len(bosses)):
                b1 = bosses[i]
                b2 = bosses[j]
                dx = b2["x"] - b1["x"]
                dy = b2["y"] - b1["y"]
                dist_sq = dx * dx + dy * dy
                if dist_sq < 1e-6:
                    dx, dy = 1.0, 0.0
                    dist_sq = 1.0
                if dist_sq < min_dist_sq:
                    dist = math.sqrt(dist_sq)
                    overlap = (min_dist - dist) / 2
                    nx = dx / dist
                    ny = dy / dist
                    b1["x"] -= nx * overlap
                    b1["y"] -= ny * overlap
                    b2["x"] += nx * overlap
                    b2["y"] += ny * overlap

    def toggle_pause(self, event=None):
        self.paused = not self.paused

    def on_key_press(self, event):
        self.keys_pressed.add(event.keysym)

    def on_key_release(self, event):
        if event.keysym in self.keys_pressed:
            self.keys_pressed.remove(event.keysym)

    def on_canvas_click(self, event):
        if self.level_up_active:
            for idx, box in enumerate(self.level_up_choice_boxes):
                x0, y0, x1, y1 = box
                if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                    self.apply_level_up_choice(idx)
                    return
        if self.game_over:
            if hasattr(self, "game_over_buttons"):
                for name, (x0, y0, x1, y1) in self.game_over_buttons.items():
                    if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                        if name == "restart":
                            self.restart_game()
                        elif name == "quit":
                            self.root.destroy()
                        return

    def update_player_position(self):
        dir_x = 0
        dir_y = 0
        if "Left" in self.keys_pressed or "a" in self.keys_pressed or "A" in self.keys_pressed:
            dir_x -= 1
        if "Right" in self.keys_pressed or "d" in self.keys_pressed or "D" in self.keys_pressed:
            dir_x += 1
        if "Up" in self.keys_pressed or "w" in self.keys_pressed or "W" in self.keys_pressed:
            dir_y -= 1
        if "Down" in self.keys_pressed or "s" in self.keys_pressed or "S" in self.keys_pressed:
            dir_y += 1

        if dir_x == 0 and dir_y == 0:
            self.is_moving = False
            return
        else:
            self.is_moving = True

        length = math.hypot(dir_x, dir_y)
        dx = (dir_x / length) * PLAYER_SPEED
        dy = (dir_y / length) * PLAYER_SPEED

        self.world_x += dx
        self.world_y += dy

        self.facing_x = dir_x / length
        self.facing_y = dir_y / length
        if dir_x < 0:
            self.last_move_dir = "left"
        elif dir_x > 0:
            self.last_move_dir = "right"

    def spawn_dagger(self):
        """가장 가까운 몬스터를 향해 날아가는 단검 생성.
        몬스터가 없으면 바라보는 방향으로 직선 발사.
        """
        count = max(1, int(self.dagger_count))
        fx = self.facing_x
        fy = self.facing_y
        length = math.hypot(fx, fy)
        if length == 0:
            fx, fy = 1.0, 0.0
            length = 1.0

        target_dir_x = fx
        target_dir_y = fy
        if self.monsters:
            min_dist_sq = None
            for m in self.monsters:
                dx = m["x"] - self.world_x
                dy = m["y"] - self.world_y
                dist_sq = dx * dx + dy * dy
                if min_dist_sq is None or dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    target_dir_x = dx
                    target_dir_y = dy

        length = math.hypot(target_dir_x, target_dir_y)
        if length == 0:
            target_dir_x, target_dir_y = fx, fy
            length = math.hypot(target_dir_x, target_dir_y)
            if length == 0:
                target_dir_x, target_dir_y = 1.0, 0.0
                length = 1.0

        vx = (target_dir_x / length) * PROJECTILE_SPEED
        vy = (target_dir_y / length) * PROJECTILE_SPEED

        base_angle = math.atan2(vy, vx)
        spread = 0.12  # 라디안 간격
        start_idx = -(count - 1) / 2
        for i in range(count):
            ang = base_angle + spread * (start_idx + i)
            pvx = math.cos(ang) * PROJECTILE_SPEED
            pvy = math.sin(ang) * PROJECTILE_SPEED
            projectile = {
                "x": float(self.world_x),
                "y": float(self.world_y),
                "vx": pvx,
                "vy": pvy,
                "birth": self.game_time,
            }
            self.projectiles.append(projectile)

    def update_projectiles(self):
        now = self.game_time
        alive = []
        for p in self.projectiles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if now - p["birth"] <= PROJECTILE_LIFETIME:
                alive.append(p)
        self.projectiles = alive

    def spawn_monster(self):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(400, 800)
        mx = self.world_x + math.cos(angle) * distance
        my = self.world_y + math.sin(angle) * distance
        speed_mult, _, hp_mult, _ = self.get_wave_scalars()
        monster = {
            "x": mx,
            "y": my,
            "hp": int(MONSTER_MAX_HP * hp_mult),
            "max_hp": int(MONSTER_MAX_HP * hp_mult),
            "base_speed": MONSTER_SPEED,
            "speed": MONSTER_SPEED * speed_mult,
            "size": MONSTER_SIZE,
            "type": "normal",
        }
        self.monsters.append(monster)

    def spawn_elite(self):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(500, 900)
        mx = self.world_x + math.cos(angle) * distance
        my = self.world_y + math.sin(angle) * distance
        speed_mult, _, hp_mult, _ = self.get_wave_scalars()
        monster = {
            "x": mx,
            "y": my,
            "hp": int(ELITE_MAX_HP * hp_mult),
            "max_hp": int(ELITE_MAX_HP * hp_mult),
            "base_speed": ELITE_SPEED,
            "speed": ELITE_SPEED * speed_mult,
            "size": ELITE_SIZE,
            "type": "elite",
        }
        self.monsters.append(monster)

    def spawn_boss_wave(self, count):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(600, 1000)
            mx = self.world_x + math.cos(angle) * distance
            my = self.world_y + math.sin(angle) * distance
            boss = {
                "x": mx,
                "y": my,
                "hp": BOSS_MAX_HP,
                "max_hp": BOSS_MAX_HP,
                "base_speed": boss_speed_for_wave(self.wave + 1),  # wave는 곧 증가하므로 +1
                "speed": boss_speed_for_wave(self.wave + 1),
                "size": BOSS_SIZE,
                "type": "boss",
                "last_shot": self.game_time,
            }
            self.monsters.append(boss)

    def update_monsters(self):
        now = self.game_time
        timer_now = self.timer_elapsed
        speed_mult, spawn_mult, hp_mult, dmg_bonus = self.get_wave_scalars()
        if self.monster_frames:
            if hasattr(self, "_last_monster_anim_time"):
                dt_anim = now - self._last_monster_anim_time
            else:
                dt_anim = 0.0
            self._last_monster_anim_time = now
            self.monster_anim_timer += dt_anim
            if self.monster_anim_timer >= MONSTER_ANIM_INTERVAL:
                self.monster_anim_timer = 0.0
                frame_count = len(self.monster_frames)
                if frame_count > 0:
                    self.monster_anim_index = (self.monster_anim_index + 1) % frame_count

        if (not self.game_finished) and self.wave < self.max_wave and timer_now >= self.next_wave_time:
            self.monsters = [m for m in self.monsters if m.get("type") == "boss"]
            self.wave += 1
            self.spawn_boss_wave(self.wave)
            self.wave_banner_time = WAVE_BANNER_DURATION
            self.wave_banner_text = f"{self.wave} WAVE"
            self.next_wave_time += BOSS_SPAWN_TIME

        boss_alive = any(m.get("type") == "boss" for m in self.monsters)

        spawn_interval = MONSTER_SPAWN_INTERVAL / spawn_mult
        extra_cap = 0
        if self.wave >= 1:
            extra_cap += 6
        if self.wave >= 2:
            extra_cap += 8
        if self.wave >= 3:
            extra_cap += 12
        if self.wave >= 4:
            extra_cap += 15
        effective_max = MAX_MONSTERS + extra_cap

        if not self.game_finished and not boss_alive and now - self.last_monster_spawn >= spawn_interval:
            if len(self.monsters) < effective_max:
                if random.random() < ELITE_SPAWN_CHANCE:
                    self.spawn_elite()
                else:
                    self.spawn_monster()
            self.last_monster_spawn = now
            self.last_elite_spawn = now

        for m in self.monsters:
            dx = self.world_x - m["x"]
            dy = self.world_y - m["y"]
            dist = math.hypot(dx, dy)
            m_type = m.get("type")
            if m_type == "boss":
                m["speed"] = m.get("base_speed", boss_speed_for_wave(self.wave))
                spd = m["speed"]
            else:
                base_spd = m.get("base_speed", MONSTER_SPEED)
                m["speed"] = base_spd * speed_mult
                spd = m["speed"]
            if dist > 0:
                m["x"] += (dx / dist) * spd
                m["y"] += (dy / dist) * spd

            if m.get("type") == "boss":
                if now - m.get("last_shot", 0) >= BOSS_SHOT_INTERVAL:
                    m["last_shot"] = now
                    self.spawn_boss_bullets(m)

        self.separate_bosses()

    def init_bibles(self):
        self.bibles = []
        now = self.game_time
        count = max(0, int(self.bible_count))
        if count == 0:
            return
        for i in range(count):
            angle = (2 * math.pi / count) * i
            bible = {
                "angle": angle,
                "state": "active",       # "active", "fading_out", "cooldown", "fading_in"
                "phase_start": now,
                "radius": BIBLE_ORBIT_RADIUS,
                "size": BIBLE_SIZE_ACTIVE,
                "fade": 1.0,
                "wx": self.world_x + math.cos(angle) * BIBLE_ORBIT_RADIUS,
                "wy": self.world_y + math.sin(angle) * BIBLE_ORBIT_RADIUS,
            }
            self.bibles.append(bible)

    def update_bibles(self):
        now = self.game_time
        for b in self.bibles:
            state = b["state"]
            t = now - b["phase_start"]

            if state == "active":
                if t >= BIBLE_ACTIVE_TIME:
                    b["state"] = "fading_out"
                    b["phase_start"] = now
                    state = "fading_out"
                    t = 0.0
            if state == "fading_out":
                progress = min(1.0, t / BIBLE_FADE_OUT_TIME)
                if progress >= 1.0:
                    b["state"] = "cooldown"
                    b["phase_start"] = now
                    state = "cooldown"
                    t = 0.0
            if state == "cooldown":
                progress = 0.0
                if t >= BIBLE_COOLDOWN_TIME:
                    b["state"] = "fading_in"
                    b["phase_start"] = now
                    state = "fading_in"
                    t = 0.0
            if state == "fading_in":
                progress = min(1.0, t / BIBLE_FADE_IN_TIME)
                if progress >= 1.0:
                    b["state"] = "active"
                    b["phase_start"] = now
                    state = "active"
                    t = 0.0

            if state == "active":
                radius = BIBLE_ORBIT_RADIUS
                size = BIBLE_SIZE_ACTIVE
                fade = 1.0
            elif state == "fading_out":
                progress = min(1.0, (now - b["phase_start"]) / BIBLE_FADE_OUT_TIME)
                radius = BIBLE_ORBIT_RADIUS + (BIBLE_INNER_RADIUS - BIBLE_ORBIT_RADIUS) * progress
                size = BIBLE_SIZE_ACTIVE + (BIBLE_SIZE_COOLDOWN - BIBLE_SIZE_ACTIVE) * progress
                fade = 1.0 + (0.1 - 1.0) * progress
            elif state == "cooldown":
                radius = BIBLE_INNER_RADIUS
                size = BIBLE_SIZE_COOLDOWN
                fade = 0.1
            elif state == "fading_in":
                progress = min(1.0, (now - b["phase_start"]) / BIBLE_FADE_IN_TIME)
                radius = BIBLE_INNER_RADIUS + (BIBLE_ORBIT_RADIUS - BIBLE_INNER_RADIUS) * progress
                size = BIBLE_SIZE_COOLDOWN + (BIBLE_SIZE_ACTIVE - BIBLE_SIZE_COOLDOWN) * progress
                fade = 0.1 + (1.0 - 0.1) * progress
            else:
                radius = BIBLE_ORBIT_RADIUS
                size = BIBLE_SIZE_ACTIVE
                fade = 1.0

            b["radius"] = radius
            b["size"] = size
            b["fade"] = fade

            if state in ("active", "fading_out", "fading_in"):
                b["angle"] += BIBLE_ANGULAR_SPEED

            b["wx"] = self.world_x + math.cos(b["angle"]) * radius
            b["wy"] = self.world_y + math.sin(b["angle"]) * radius

    def apply_knockback(self, monster, distance):
        dx = monster["x"] - self.world_x
        dy = monster["y"] - self.world_y
        length = math.hypot(dx, dy)
        if length == 0:
            return
        monster["x"] += (dx / length) * distance
        monster["y"] += (dy / length) * distance

    def handle_collisions(self):
        if not self.monsters:
            return

        projectile_alive = [True] * len(self.projectiles)

        bible_collision_radius = (BIBLE_SIZE_ACTIVE / 2) + (MONSTER_SIZE / 2)
        bible_collision_radius_sq = bible_collision_radius * bible_collision_radius

        projectile_collision_radius = (PROJECTILE_SIZE / 2) + (MONSTER_SIZE / 2)
        projectile_collision_radius_sq = projectile_collision_radius * projectile_collision_radius

        new_monsters = []

        for m in self.monsters:
            mx = m["x"]
            my = m["y"]
            hp = m["hp"]
            m_size = m.get("size", MONSTER_SIZE)
            bible_collision_radius = (BIBLE_SIZE_ACTIVE / 2) + (m_size / 2)
            bible_collision_radius_sq = bible_collision_radius * bible_collision_radius
            projectile_collision_radius = (PROJECTILE_SIZE / 2) + (m_size / 2)
            projectile_collision_radius_sq = projectile_collision_radius * projectile_collision_radius
            dead = False

            if self.projectiles:
                for i, p in enumerate(self.projectiles):
                    if not projectile_alive[i]:
                        continue
                    dx = p["x"] - mx
                    dy = p["y"] - my
                    if dx * dx + dy * dy <= projectile_collision_radius_sq:
                        hp -= DAGGER_DAMAGE
                        projectile_alive[i] = False
                        if hp <= 0:
                            dead = True
                            break

            if hp > 0 and not dead:
                for b in self.bibles:
                    if b["state"] != "active":
                        continue
                    dx = b["wx"] - mx
                    dy = b["wy"] - my
                    if dx * dx + dy * dy <= bible_collision_radius_sq:
                        hp -= BIBLE_DAMAGE
                        self.apply_knockback(m, KNOCKBACK_DISTANCE_BIBLE)
                        if hp <= 0:
                            dead = True
                            break

            if hp > 0 and not dead:
                m["hp"] = hp
                new_monsters.append(m)
            else:
                self.spawn_gem(mx, my)
                drop_chance = POTION_DROP_CHANCE
                if m.get("type") == "elite":
                    drop_chance = max(POTION_DROP_CHANCE, 0.25)
                if random.random() < drop_chance:
                    self.spawn_potion(mx, my)

        self.monsters = new_monsters
        self.projectiles = [
            p for i, p in enumerate(self.projectiles) if projectile_alive[i]
        ]

        if self.wave >= self.max_wave and not self.game_finished:
            boss_alive = any(m.get("type") == "boss" for m in self.monsters)
            if not boss_alive:
                self.game_finished = True
                self.trigger_game_over(text="게임 끝!")

        self.update_boss_bullets()

    def check_player_damage(self):
        if not self.monsters:
            return
        now = self.game_time
        if now - self.last_damage_time < PLAYER_DAMAGE_COOLDOWN:
            return

        for m in self.monsters:
            m_size = m.get("size", MONSTER_SIZE)
            player_radius = PLAYER_SIZE / 2
            monster_radius = m_size / 2
            radius = player_radius + monster_radius
            radius_sq = radius * radius
            dx = m["x"] - self.world_x
            dy = m["y"] - self.world_y
            if dx * dx + dy * dy <= radius_sq:
                if m.get("type") == "boss":
                    self.hp = 0
                    self.trigger_game_over(text="GAME OVER")
                    return
                _, _, _, dmg_bonus = self.get_wave_scalars()
                self.hp -= (MONSTER_CONTACT_DAMAGE + dmg_bonus)
                self.last_damage_time = now
                if self.hp <= 0:
                    self.hp = 0
                    self.trigger_game_over()
                break

    def spawn_gem(self, x, y):
        self.gems.append(
            {
                "x": x,
                "y": y,
                "size": GEM_SIZE,
                "xp": GEM_XP_VALUE,
            }
        )

    def collect_gems(self):
        half = GEM_SIZE / 2
        player_half = PLAYER_SIZE / 2
        radius = max(half + player_half, GEM_PICKUP_RADIUS)
        radius_sq = radius * radius

        kept = []
        gained = 0
        for g in self.gems:
            dx = g["x"] - self.world_x
            dy = g["y"] - self.world_y
            if dx * dx + dy * dy <= radius_sq:
                gained += g["xp"]
            else:
                kept.append(g)
        self.gems = kept

        if gained:
            self.xp += gained
            self.handle_level_up()

    def handle_level_up(self):
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            factor = 1.4 ** (self.level - 1)
            if self.level >= 3:
                factor *= 1.2  # 고레벨 보정은 약하게
            self.xp_to_next = int(XP_BASE_REQ * factor)
            if not self.level_up_active:
                self.trigger_level_up()

    def trigger_level_up(self):
        self.level_up_active = True
        self.level_up_choice_boxes = []
        self.paused = True  # 업데이트 정지

    def apply_level_up_choice(self, index):
        if index == 0:
            self.dagger_count = min(self.dagger_count + 1, 8)
        elif index == 1:
            self.bible_count = min(self.bible_count + 1, 8)
            self.init_bibles()

        self.level_up_active = False
        self.level_up_choice_boxes = []
        self.paused = False

    def update_player_animation(self, dt):
        frames = self._get_current_frames()
        if not frames:
            self.player_anim_index = 0
            self.player_anim_timer = 0.0
            return
        if self.player_anim_index >= len(frames):
            self.player_anim_index = 0
        if self.is_moving:
            self.player_anim_timer += dt
            if self.player_anim_timer >= self.player_anim_interval:
                self.player_anim_timer = 0.0
                self.player_anim_index = (self.player_anim_index + 1) % len(frames)
        else:
            self.player_anim_index = 0
            self.player_anim_timer = 0.0

    def spawn_potion(self, x, y):
        self.potions.append(
            {
                "x": x,
                "y": y,
                "size": POTION_SIZE,
                "heal": POTION_HEAL,
            }
        )

    def collect_potions(self):
        half = POTION_SIZE / 2
        player_half = PLAYER_SIZE / 2
        radius = max(half + player_half, POTION_PICKUP_RADIUS)
        radius_sq = radius * radius

        kept = []
        heal_total = 0
        for p in self.potions:
            dx = p["x"] - self.world_x
            dy = p["y"] - self.world_y
            if dx * dx + dy * dy <= radius_sq:
                heal_total += p["heal"]
            else:
                kept.append(p)
        self.potions = kept

        if heal_total:
            self.hp = min(self.hp + heal_total, self.hp_max)

    def draw_background(self):
        self.canvas.delete("all")
        world_left = self.world_x - self.player_screen_x
        world_top = self.world_y - self.player_screen_y
        world_right = self.world_x + (self.screen_width - self.player_screen_x)
        world_bottom = self.world_y + (self.screen_height - self.player_screen_y)

        tile_left = math.floor(world_left / self.bg_w) - 1
        tile_top = math.floor(world_top / self.bg_h) - 1
        tile_right = math.floor(world_right / self.bg_w) + 1
        tile_bottom = math.floor(world_bottom / self.bg_h) + 1

        for ty in range(tile_top, tile_bottom + 1):
            for tx in range(tile_left, tile_right + 1):
                tile_world_x = tx * self.bg_w
                tile_world_y = ty * self.bg_h
                sx = self.player_screen_x + (tile_world_x - self.world_x)
                sy = self.player_screen_y + (tile_world_y - self.world_y)
                self.canvas.create_image(sx, sy, image=self.bg_image, anchor="nw")

    def draw_gems(self):
        half = GEM_SIZE / 2
        for g in self.gems:
            sx = self.player_screen_x + (g["x"] - self.world_x)
            sy = self.player_screen_y + (g["y"] - self.world_y)
            self.canvas.create_oval(
                sx - half, sy - half,
                sx + half, sy + half,
                fill="#33ccff",
                outline="#a0f0ff"
            )

    def draw_potions(self):
        size = POTION_SIZE
        for p in self.potions:
            sx = self.player_screen_x + (p["x"] - self.world_x)
            sy = self.player_screen_y + (p["y"] - self.world_y)
            if self.potion_image:
                self.canvas.create_image(
                    sx,
                    sy,
                    image=self.potion_image,
                    anchor="center"
                )
            else:
                x0 = sx - size / 2
                y0 = sy - size / 4
                x1 = sx + size / 2
                y1 = sy + size / 2
                points = [
                    sx, y1,          # 아래 꼭짓점
                    x0, sy,          # 왼쪽
                    sx, y0,          # 위쪽 중앙
                    x1, sy           # 오른쪽
                ]
                self.canvas.create_polygon(
                    points,
                    fill="#ff4d6d",
                    outline="#ff99ad",
                    smooth=True
                )

    def draw_hp_bar(self):
        bar_width = 80
        bar_height = 10
        frames = self._get_current_frames()
        img = frames[self.player_anim_index] if frames else self.player_image
        img_h = img.height() if img else PLAYER_SIZE
        y_offset = img_h / 2 + 6
        x0 = self.player_screen_x - bar_width / 2
        y0 = self.player_screen_y + y_offset
        x1 = x0 + bar_width
        y1 = y0 + bar_height

        self.canvas.create_rectangle(
            x0, y0, x1, y1,
            fill="#333333",
            outline="#777777"
        )
        ratio = max(0.0, min(1.0, self.hp / self.hp_max))
        self.canvas.create_rectangle(
            x0, y0, x0 + bar_width * ratio, y1,
            fill="#33cc33",
            outline=""
        )

    def draw_xp_bar(self):
        bar_height = XP_BAR_HEIGHT
        margin = 0
        x0, y0 = 0 + margin, 0 + margin
        x1, y1 = self.screen_width - margin, bar_height

        self.canvas.create_rectangle(
            x0, y0, x1, y1,
            fill="#222222",
            outline="#555555",
            width=2
        )

        progress = 0.0
        if self.xp_to_next > 0:
            progress = max(0.0, min(1.0, self.xp / self.xp_to_next))
        fill_width = (x1 - x0) * progress
        self.canvas.create_rectangle(
            x0, y0, x0 + fill_width, y1,
            fill="#5dd65d",
            outline=""
        )

        self.canvas.create_text(
            (x0 + x1) / 2,
            (y0 + y1) / 2,
            text=f"Lv {self.level}  {self.xp:.0f} / {self.xp_to_next}",
            fill="white",
            font=("Arial", 14, "bold")
        )

    def draw_timer(self):
        elapsed = int(self.timer_elapsed)
        text = f"{elapsed:02d}s"
        self.canvas.create_text(
            self.screen_width // 2,
            XP_BAR_HEIGHT + 16,
            text=text,
            fill="white",
            font=("Arial", 16, "bold")
        )

    def draw_wave_banner(self):
        if self.wave_banner_time > 0 and self.wave_banner_text:
            self.canvas.create_text(
                self.screen_width // 2,
                self.screen_height // 2,
                text=self.wave_banner_text,
                fill="red",
                font=("Arial", 48, "bold")
            )

    def draw_level_up_overlay(self):
        self.canvas.create_rectangle(
            0, 0, self.screen_width, self.screen_height,
            fill="#000000", stipple="gray50", outline=""
        )

        popup_w = self.screen_width * 0.8
        popup_h = self.screen_height * 0.55
        px0 = (self.screen_width - popup_w) / 2
        py0 = (self.screen_height - popup_h) / 2
        px1 = px0 + popup_w
        py1 = py0 + popup_h

        self.canvas.create_rectangle(
            px0, py0, px1, py1,
            fill="#2f3d76",
            outline="#6f83d4",
            width=4
        )

        self.canvas.create_text(
            self.screen_width / 2,
            py0 + 40,
            text="레벨 업!",
            fill="white",
            font=("Arial", 28, "bold")
        )

        max_img_w = 0
        max_img_h = 0
        for key in ["dagger", "bible"]:
            img = self.upgrade_imgs.get(key)
            if img:
                max_img_w = max(max_img_w, img.width())
                max_img_h = max(max_img_h, img.height())
        if max_img_w == 0:
            max_img_w = 120
        if max_img_h == 0:
            max_img_h = 120

        padding_w = 60
        padding_h = 90  # 여유 공간 + 텍스트 공간
        card_w = max(popup_w * 0.22, max_img_w + padding_w)
        card_h = max(popup_h * 0.5, max_img_h + padding_h)
        gap = popup_w * 0.04
        opts = [
            ("dagger", f"단검을 1개 더 투척합니다. (현재 {self.dagger_count})"),
            ("bible", f"바이블을 1개 더 생성합니다. (현재 {self.bible_count})"),
        ]
        count = len(opts)
        total_w = card_w * count + gap * (count - 1)
        start_x = px0 + (popup_w - total_w) / 2
        y0 = py0 + 80

        self.level_up_choice_boxes = []

        for i, (key, text) in enumerate(opts):
            x0 = start_x + i * (card_w + gap)
            x1 = x0 + card_w
            y1 = y0 + card_h

            self.level_up_choice_boxes.append((x0, y0, x1, y1))
            cx = (x0 + x1) / 2
            cy = (y0 + y1) / 2

            self.canvas.create_rectangle(
                x0, y0, x1, y1,
                fill="#4b5bb1",
                outline="#c9d2ff",
                width=3
            )

            img = self.upgrade_imgs.get(key)
            if img:
                self.canvas.create_image(
                    cx,
                    y0 + card_h * 0.4,
                    image=img,
                    anchor="center"
                )
            else:
                size = min(card_w, card_h) * 0.3
                self.canvas.create_rectangle(
                    cx - size / 2, y0 + 10,
                    cx + size / 2, y0 + 10 + size,
                    fill="#1f2b5f",
                    outline="#9bb3ff"
                )

            self.canvas.create_text(
                cx,
                y0 + card_h * 0.78,
                text=text,
                fill="white",
                font=("Arial", 16, "bold"),
                anchor="center"
            )

    def draw_game_over_overlay(self):
        self.canvas.create_rectangle(
            0, 0, self.screen_width, self.screen_height,
            fill="#000000", stipple="gray75", outline=""
        )

        box_w = self.screen_width * 0.4
        box_h = self.screen_height * 0.3
        bx0 = (self.screen_width - box_w) / 2
        by0 = (self.screen_height - box_h) / 2
        bx1 = bx0 + box_w
        by1 = by0 + box_h

        self.canvas.create_rectangle(
            bx0, by0, bx1, by1,
            fill="#222232",
            outline="#8888aa",
            width=3
        )

        self.canvas.create_text(
            (bx0 + bx1) / 2,
            by0 + box_h * 0.3,
            text=getattr(self, "game_over_text", "GAME OVER"),
            fill="white",
            font=("Arial", 28, "bold")
        )

        btn_w = box_w * 0.32
        btn_h = 40
        gap = box_w * 0.05
        start_x = (self.screen_width - (btn_w * 2 + gap)) / 2
        y0 = by0 + box_h * 0.6

        self.game_over_buttons = {}
        labels = [("restart", "다시하기"), ("quit", "종료")]
        for i, (name, text) in enumerate(labels):
            x0 = start_x + i * (btn_w + gap)
            x1 = x0 + btn_w
            y1 = y0 + btn_h
            self.game_over_buttons[name] = (x0, y0, x1, y1)

            self.canvas.create_rectangle(
                x0, y0, x1, y1,
                fill="#4455aa",
                outline="#c0c8ff",
                width=2
            )
            self.canvas.create_text(
                (x0 + x1) / 2,
                (y0 + y1) / 2,
                text=text,
                fill="white",
                font=("Arial", 16, "bold")
            )

    def trigger_game_over(self, text="GAME OVER"):
        self.game_over = True
        self.game_over_text = text
        self.paused = True

    def restart_game(self):
        self.world_x = 0.0
        self.world_y = 0.0
        self.hp_max = PLAYER_MAX_HP
        self.hp = self.hp_max
        self.last_damage_time = -999.0

        self.projectiles = []
        self.monsters = []
        self.bibles = []
        self.gems = []
        self.potions = []
        self.boss_bullets = []

        self.xp = 0
        self.level = 1
        self.xp_to_next = XP_BASE_REQ
        self.level_up_active = False
        self.level_up_choice_boxes = []
        self.dagger_count = 1
        self.bible_count = 0

        self.game_time = 0.0
        self.last_real_time = time.time()
        self.last_shot = self.game_time
        self.last_monster_spawn = self.game_time
        self.last_elite_spawn = self.game_time
        self.wave = 0
        self.next_wave_time = BOSS_SPAWN_TIME
        self.wave_banner_time = 0.0
        self.wave_banner_text = ""
        self.game_finished = False
        self.timer_elapsed = 0.0
        self.boss_bullets = []

        self.init_bibles()
        self.game_over = False
        self.paused = False

    def draw_projectiles(self):
        for p in self.projectiles:
            sx = self.player_screen_x + (p["x"] - self.world_x)
            sy = self.player_screen_y + (p["y"] - self.world_y)
            img = None
            if p.get("vx", 0) < 0 and self.dagger_image_left:
                img = self.dagger_image_left
            elif p.get("vx", 0) >= 0 and self.dagger_image_right:
                img = self.dagger_image_right
            elif self.dagger_image:
                img = self.dagger_image

            if img:
                self.canvas.create_image(sx, sy, image=img, anchor="center")
            else:
                half = PROJECTILE_SIZE // 2
                self.canvas.create_oval(
                    sx - half, sy - half,
                    sx + half, sy + half,
                    fill="cyan",
                    outline=""
                )

    def draw_monsters(self):
        half = MONSTER_SIZE // 2
        for m in self.monsters:
            sx = self.player_screen_x + (m["x"] - self.world_x)
            sy = self.player_screen_y + (m["y"] - self.world_y)
            m_type = m.get("type")
            img = None
            if m_type == "elite" and self.elite_image:
                img = self.elite_image
            elif m_type == "boss" and self.boss_image:
                img = self.boss_image
            else:
                frames = self.monster_frames
                if frames:
                    img = frames[self.monster_anim_index]

            if img:
                self.canvas.create_image(
                    sx,
                    sy,
                    image=img,
                    anchor="center"
                )
                if m_type == "boss" and m.get("max_hp"):
                    bar_w = m.get("size", BOSS_SIZE)
                    bar_w = max(80, min(180, bar_w))
                    bar_h = 10
                    x0 = sx - bar_w / 2
                    x1 = sx + bar_w / 2
                    y0 = sy + (m.get("size", MONSTER_SIZE) / 2) + 8
                    y1 = y0 + bar_h
                    ratio = max(0.0, min(1.0, m["hp"] / m["max_hp"]))
                    self.canvas.create_rectangle(x0, y0, x1, y1, fill="#333333", outline="#777777")
                    self.canvas.create_rectangle(x0, y0, x0 + bar_w * ratio, y1, fill="#d74c4c", outline="")
            else:
                m_size = m.get("size", MONSTER_SIZE)
                half_m = m_size / 2
                self.canvas.create_oval(
                    sx - half_m, sy - half_m,
                    sx + half_m, sy + half_m,
                    fill="red",
                    outline=""
                )

    def draw_bibles(self):
        for b in self.bibles:
            sx = self.player_screen_x + (b["wx"] - self.world_x)
            sy = self.player_screen_y + (b["wy"] - self.world_y)

            size = b["size"]
            half = size / 2
            fade = max(0.0, min(1.0, b["fade"]))

            if fade < 0.35:
                continue

            if self.bible_image:
                self.canvas.create_image(
                    sx,
                    sy,
                    image=self.bible_image,
                    anchor="center"
                )
            else:
                if fade > 0.8:
                    fill_color = "gold"
                    outline_color = "#ffffaa"
                elif fade > 0.4:
                    fill_color = "#807000"
                    outline_color = "#a09040"
                else:
                    fill_color = "#202010"
                    outline_color = "#101008"

                self.canvas.create_oval(
                    sx - half, sy - half,
                    sx + half, sy + half,
                    fill=fill_color,
                    outline=outline_color
                )

    def draw_boss_bullets(self):
        if not self.boss_bullets:
            return
        half = BOSS_BULLET_SIZE / 2
        for b in self.boss_bullets:
            sx = self.player_screen_x + (b["x"] - self.world_x)
            sy = self.player_screen_y + (b["y"] - self.world_y)
            self.canvas.create_oval(
                sx - half, sy - half,
                sx + half, sy + half,
                fill="#ffdd33",
                outline="#ffcc00"
            )

    def draw_player(self):
        frames = self._get_current_frames()
        if frames:
            if self.player_anim_index >= len(frames):
                self.player_anim_index = 0
            img = frames[self.player_anim_index]
        else:
            img = self.player_image
        if img:
            self.canvas.create_image(
                self.player_screen_x,
                self.player_screen_y,
                image=img,
                anchor="center"
            )
        else:
            half = PLAYER_SIZE // 2
            x = self.player_screen_x
            y = self.player_screen_y
            self.canvas.create_rectangle(
                x - half, y - half,
                x + half, y + half,
                fill="white",
                outline="#cccccc"
            )

    def draw_pause_overlay(self):
        """일시정지 상태일 때 중앙에 표시."""
        self.canvas.create_rectangle(
            0, 0, self.screen_width, self.screen_height,
            fill="#000000", stipple="gray50", outline=""
        )

        self.canvas.create_text(
            self.screen_width // 2,
            self.screen_height // 2 - 40,
            text="PAUSED",
            fill="white",
            font=("Arial", 40, "bold")
        )

        btn_width = 200
        btn_height = 60
        x0 = self.screen_width // 2 - btn_width // 2
        y0 = self.screen_height // 2 + 10
        x1 = x0 + btn_width
        y1 = y0 + btn_height

        self.canvas.create_rectangle(
            x0, y0, x1, y1,
            fill="#303030", outline="#aaaaaa", width=2,
            tags="exit_btn"
        )
        self.canvas.create_text(
            (x0 + x1) // 2,
            (y0 + y1) // 2,
            text="게임 나가기",
            fill="white",
            font=("Arial", 18, "bold"),
            tags="exit_btn_text"
        )

        self.canvas.tag_bind("exit_btn", "<Button-1>", lambda e: self.root.destroy())
        self.canvas.tag_bind("exit_btn_text", "<Button-1>", lambda e: self.root.destroy())

        
    def game_loop(self):
        real_now = time.time()
        dt = real_now - self.last_real_time
        self.last_real_time = real_now

        boss_alive = any(m.get("type") == "boss" for m in self.monsters)

        if not self.paused and not self.game_over:
            self.game_time += dt
            if not boss_alive:
                self.timer_elapsed += dt

            if self.wave_banner_time > 0:
                self.wave_banner_time -= dt
                if self.wave_banner_time < 0:
                    self.wave_banner_time = 0

            self.update_player_position()
            self.update_player_animation(dt)

            now = self.game_time

            if now - self.last_shot >= self.shot_interval:
                self.spawn_dagger()
                self.last_shot = now

            if not self.level_up_active:
                self.update_projectiles()
                self.update_monsters()
                self.check_player_damage()
                self.update_bibles()
                self.handle_collisions()
                self.collect_gems()
                self.collect_potions()

        self.draw_background()
        self.draw_projectiles()
        self.draw_monsters()
        self.draw_gems()
        self.draw_potions()
        self.draw_bibles()
        self.draw_boss_bullets()
        self.draw_player()
        self.draw_hp_bar()
        self.draw_xp_bar()
        self.draw_timer()
        self.draw_wave_banner()

        if self.paused and not self.game_over and not self.level_up_active:
            self.draw_pause_overlay()
        if self.level_up_active:
            self.draw_level_up_overlay()
        if self.game_over:
            self.draw_game_over_overlay()

        self.root.after(16, self.game_loop)


def main():
    root = tk.Tk()
    game = VampireSurvivorLite(root)
    root.mainloop()


if __name__ == "__main__":
    main()  

