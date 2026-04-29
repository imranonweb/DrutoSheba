from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import sys
from typing import Optional

import pygame

from agent import Agent
from algorithms import ALGORITHMS, SearchResult
from grid import CellType, GridMap, Position


BACKGROUND = (229, 235, 242)
COLORS = {
    CellType.ROAD: (242, 244, 247),
    CellType.OBSTACLE: (75, 85, 99),
    CellType.TRAFFIC: (217, 119, 6),
    CellType.START: (22, 101, 52),
    CellType.GOAL: (185, 28, 28),
}
VISITED_COLOR = (191, 219, 254)
PATH_COLOR = (59, 130, 246)
AMBULANCE_COLOR = (14, 116, 144)
TEXT_COLOR = (25, 25, 25)
APP_TITLE = "DrutoSheba - Emergency Path Finder"
SCENARIOS = [
    {
        "name": "Medical Emergency",
        "vehicle": "Ambulance",
        "destination": "Patient",
        "success": "Ambulance served the patient.",
        "dispatch": "Ambulance dispatched to the patient.",
        "icon": "A",
        "accent": (14, 116, 144),
    },
    {
        "name": "Fire Rescue",
        "vehicle": "Firefighters",
        "destination": "Fire Site",
        "success": "Firefighters reached the fire site.",
        "dispatch": "Firefighters are heading to the fire site.",
        "icon": "F",
        "accent": (220, 38, 38),
    },
    {
        "name": "Police Response",
        "vehicle": "Police Unit",
        "destination": "Incident",
        "success": "Police unit reached the incident.",
        "dispatch": "Police unit dispatched to the incident.",
        "icon": "P",
        "accent": (37, 99, 235),
    },
    {
        "name": "Flood Rescue",
        "vehicle": "Rescue Team",
        "destination": "Safe Zone",
        "success": "Rescue team reached the safe zone.",
        "dispatch": "Rescue team moving through blocked roads.",
        "icon": "R",
        "accent": (5, 150, 105),
    },
]


@dataclass(frozen=True)
class GameConfig:
    rows: int = 20
    cols: int = 20
    cell_size: int = 32
    margin: int = 2
    info_panel_width: int = 320
    min_panel_width: int = 300
    obstacle_density: float = 0.18
    traffic_density: float = 0.10
    step_delay_ms: int = 40
    move_delay_ms: int = 110
    footer_height: int = 110
    min_window_height: int = 750

    @property
    def grid_pixel_width(self) -> int:
        return self.cols * self.cell_size

    @property
    def grid_pixel_height(self) -> int:
        return self.rows * self.cell_size

    @property
    def window_width(self) -> int:
        return self.grid_pixel_width + self.info_panel_width

    @property
    def window_height(self) -> int:
        return max(self.grid_pixel_height + self.footer_height, self.min_window_height)

    @property
    def min_window_width(self) -> int:
        return self.grid_pixel_width + self.min_panel_width


@dataclass
class VisualizationState:
    selected_algorithm: str = "BFS"
    agent_mode: bool = False
    status_message: str = "Press R to generate map, 1/2/3 to choose an algorithm."
    show_start_screen: bool = True
    scenario_index: int = 0
    result: Optional[SearchResult] = None
    benchmark_results: dict[str, SearchResult] = field(default_factory=dict)
    comparison_winner: Optional[str] = None
    visited_index: int = 0
    path_index: int = 0
    move_index: int = 0
    solving: bool = False
    animating_path: bool = False
    moving_ambulance: bool = False
    visited_nodes: set[Position] = field(default_factory=set)
    shown_path: list[Position] = field(default_factory=list)
    ambulance_pos: Optional[Position] = None
    ambulance_draw_pos: Optional[tuple[float, float]] = None
    active_explore_node: Optional[Position] = None
    active_path_node: Optional[Position] = None
    needs_replay: bool = False

    def clear_animation(self, keep_result: bool = False) -> None:
        self.visited_index = 0
        self.path_index = 0
        self.move_index = 0
        self.solving = False
        self.animating_path = False
        self.moving_ambulance = False
        self.visited_nodes.clear()
        self.shown_path.clear()
        self.ambulance_pos = None
        self.ambulance_draw_pos = None
        self.active_explore_node = None
        self.active_path_node = None
        self.needs_replay = False
        if not keep_result:
            self.result = None


class DrutoAIGame:
    def __init__(self, config: GameConfig) -> None:
        pygame.init()
        pygame.display.set_caption(APP_TITLE)
        self.config = config
        self.screen = pygame.display.set_mode((config.window_width, config.window_height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.grid = GridMap(
            rows=config.rows,
            cols=config.cols,
            obstacle_density=config.obstacle_density,
            traffic_density=config.traffic_density,
        )
        self.agent = Agent()
        self.state = VisualizationState()
        self.font = pygame.font.SysFont("consolas", 20)
        self.small_font = pygame.font.SysFont("consolas", 16)
        self.tiny_font = pygame.font.SysFont("consolas", 14)
        self.title_font = pygame.font.SysFont("consolas", 34, bold=True)
        self.badge_font = pygame.font.SysFont("consolas", 18, bold=True)
        self.last_step_time = 0
        self.step_delay_ms = config.step_delay_ms
        self.move_delay_ms = config.move_delay_ms
        self.start_buttons: dict[str, pygame.Rect] = {}
        self.panel_scroll = 0
        self.max_panel_scroll = 0
        self.grid.randomize()

    def run(self) -> None:
        while True:
            self.handle_events()
            self.update_animation()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event.key)

            if event.type == pygame.VIDEORESIZE:
                self.resize_window(event.w, event.h)

            if event.type == pygame.MOUSEWHEEL and not self.state.show_start_screen:
                self.handle_panel_scroll(event.y)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.state.show_start_screen:
                    self.handle_start_screen_click(event.pos, event.button)
                else:
                    self.handle_mouse(event.pos, event.button)

    def resize_window(self, width: int, height: int) -> None:
        min_width = self.config.min_window_width
        min_height = max(self.config.grid_pixel_height + self.config.footer_height, 520)
        width = max(width, min_width)
        height = max(height, min_height)
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)

    def handle_panel_scroll(self, wheel_delta: int) -> None:
        mouse_x, _ = pygame.mouse.get_pos()
        panel_x = self.config.grid_pixel_width
        if mouse_x < panel_x:
            return
        self.panel_scroll = max(0, min(self.panel_scroll - wheel_delta * 28, self.max_panel_scroll))

    def handle_keydown(self, key: int) -> None:
        if self.state.show_start_screen:
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.state.show_start_screen = False
                self.state.status_message = "Simulation ready. Press SPACE to visualize search."
            elif key == pygame.K_SPACE:
                self.state.show_start_screen = False
                self.start_solver()
            elif key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            return

        if key == pygame.K_r:
            self.grid.randomize()
            self.state.clear_animation()
            self.state.benchmark_results.clear()
            self.state.comparison_winner = None
            self.state.status_message = "Random map generated."
        elif key == pygame.K_c:
            self.grid.reset()
            self.state.clear_animation()
            self.state.benchmark_results.clear()
            self.state.comparison_winner = None
            self.state.status_message = "Grid reset."
        elif key == pygame.K_UP:
            self.grid.obstacle_density = min(self.grid.obstacle_density + 0.05, 0.55)
            self.state.status_message = f"Obstacle density set to {self.grid.obstacle_density:.0%}."
        elif key == pygame.K_DOWN:
            self.grid.obstacle_density = max(self.grid.obstacle_density - 0.05, 0.05)
            self.state.status_message = f"Obstacle density set to {self.grid.obstacle_density:.0%}."
        elif key == pygame.K_RIGHT:
            self.grid.traffic_density = min(self.grid.traffic_density + 0.05, 0.35)
            self.state.status_message = f"Traffic density set to {self.grid.traffic_density:.0%}."
        elif key == pygame.K_LEFT:
            self.grid.traffic_density = max(self.grid.traffic_density - 0.05, 0.0)
            self.state.status_message = f"Traffic density set to {self.grid.traffic_density:.0%}."
        elif key == pygame.K_SPACE:
            self.start_solver()
        elif key == pygame.K_1:
            self.state.selected_algorithm = "BFS"
            self.state.agent_mode = False
            self.state.status_message = "BFS selected."
        elif key == pygame.K_2:
            self.state.selected_algorithm = "DFS"
            self.state.agent_mode = False
            self.state.status_message = "DFS selected."
        elif key == pygame.K_3:
            self.state.selected_algorithm = "A*"
            self.state.agent_mode = False
            self.state.status_message = "A* selected."
        elif key == pygame.K_a:
            self.state.agent_mode = True
            self.state.status_message = "Agent auto mode enabled."
        elif key == pygame.K_BACKSPACE:
            self.state.clear_animation(keep_result=True)
            self.state.needs_replay = True
            self.state.status_message = "Replay armed. Press SPACE to replay the latest result."
        elif key == pygame.K_p:
            self.run_comparison()
        elif key == pygame.K_s:
            self.cycle_scenario()
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.step_delay_ms = min(self.step_delay_ms + 10, 250)
            self.move_delay_ms = min(self.move_delay_ms + 10, 350)
            self.state.status_message = f"Animation slowed ({self.step_delay_ms}ms / {self.move_delay_ms}ms)."
        elif key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self.step_delay_ms = max(self.step_delay_ms - 10, 5)
            self.move_delay_ms = max(self.move_delay_ms - 10, 30)
            self.state.status_message = f"Animation sped up ({self.step_delay_ms}ms / {self.move_delay_ms}ms)."
        elif key == pygame.K_h:
            self.state.show_start_screen = True
        elif key == pygame.K_PAGEUP:
            self.panel_scroll = max(self.panel_scroll - 120, 0)
        elif key == pygame.K_PAGEDOWN:
            self.panel_scroll = min(self.panel_scroll + 120, self.max_panel_scroll)

    def handle_start_screen_click(self, mouse_pos: tuple[int, int], button: int) -> None:
        if button != 1:
            return

        if self.start_buttons.get("start") and self.start_buttons["start"].collidepoint(mouse_pos):
            self.state.show_start_screen = False
            self.state.status_message = "Simulation ready. Press SPACE to visualize search."
            return
        if self.start_buttons.get("quick_run") and self.start_buttons["quick_run"].collidepoint(mouse_pos):
            self.state.show_start_screen = False
            self.start_solver()
            return
        if self.start_buttons.get("quit") and self.start_buttons["quit"].collidepoint(mouse_pos):
            pygame.quit()
            sys.exit()

    def handle_mouse(self, mouse_pos: tuple[int, int], button: int) -> None:
        if self.state.show_start_screen:
            return

        if mouse_pos[0] >= self.config.grid_pixel_width or mouse_pos[1] >= self.config.grid_pixel_height:
            return

        row = mouse_pos[1] // self.config.cell_size
        col = mouse_pos[0] // self.config.cell_size
        pos = Position(row, col)
        if not self.grid.in_bounds(pos):
            return

        self.state.clear_animation()
        self.state.benchmark_results.clear()
        self.state.comparison_winner = None
        self.panel_scroll = 0
        mods = pygame.key.get_mods()
        shift_pressed = bool(mods & pygame.KMOD_SHIFT)
        if shift_pressed and button == 1:
            if self.grid.set_start(pos):
                self.state.status_message = f"Start node set to ({row}, {col})."
            else:
                self.state.status_message = "Start node cannot overlap goal node."
        elif shift_pressed and button == 3:
            if self.grid.set_goal(pos):
                self.state.status_message = f"Goal node set to ({row}, {col})."
            else:
                self.state.status_message = "Goal node cannot overlap start node."
        elif button == 1:
            self.grid.toggle_obstacle(pos)
            self.state.status_message = f"Obstacle toggled at ({row}, {col})."
        elif button == 3:
            self.grid.toggle_traffic(pos)
            self.state.status_message = f"Traffic toggled at ({row}, {col})."

    def start_solver(self) -> None:
        if self.state.show_start_screen:
            return

        if self.state.needs_replay and self.state.result is not None:
            self.prepare_animation(self.state.result)
            self.state.status_message = f"Replaying {self.state.result.algorithm}."
            return

        if self.state.agent_mode:
            perception = self.agent.perceive(self.grid)
            decision = self.agent.decide(perception)
            result = self.agent.act(self.grid)
            self.state.selected_algorithm = decision.algorithm_name
            self.state.status_message = f"Agent chose {decision.algorithm_name}: {decision.reason}."
        else:
            result = ALGORITHMS[self.state.selected_algorithm](self.grid)
            self.state.status_message = f"{self.state.selected_algorithm} executed."

        self.prepare_animation(result)

    def cycle_scenario(self) -> None:
        self.state.scenario_index = (self.state.scenario_index + 1) % len(SCENARIOS)
        scenario = self.current_scenario
        self.state.clear_animation()
        self.state.status_message = f"Scenario changed to {scenario['name']}."

    @property
    def current_scenario(self) -> dict:
        return SCENARIOS[self.state.scenario_index]

    def run_comparison(self) -> None:
        self.state.benchmark_results = {name: algo(self.grid) for name, algo in ALGORITHMS.items()}
        self.state.comparison_winner = self.choose_winner(self.state.benchmark_results)
        if self.state.comparison_winner:
            self.state.status_message = f"Comparison updated. Winner: {self.state.comparison_winner}."
        else:
            self.state.status_message = "Comparison updated. No algorithm reached the goal."

    @staticmethod
    def choose_winner(results: dict[str, SearchResult]) -> Optional[str]:
        successful = [(name, result) for name, result in results.items() if result.path]
        if not successful:
            return None
        successful.sort(
            key=lambda item: (
                item[1].total_cost,
                len(item[1].path) - 1,
                item[1].nodes_explored,
                item[1].execution_time_ms,
            )
        )
        return successful[0][0]

    def prepare_animation(self, result: SearchResult) -> None:
        self.state.clear_animation()
        self.state.result = result
        self.state.solving = True
        self.state.ambulance_pos = self.grid.start
        self.state.ambulance_draw_pos = (float(self.grid.start.row), float(self.grid.start.col))
        self.last_step_time = pygame.time.get_ticks()
        if not result.path:
            self.state.status_message = f"{result.algorithm} could not reach the patient."

    def update_animation(self) -> None:
        if self.state.show_start_screen or self.state.result is None:
            return

        now = pygame.time.get_ticks()
        # Split the visualization into three phases so algorithm exploration,
        # chosen path, and ambulance movement remain easy to compare.
        if self.state.solving:
            while self.state.solving and now - self.last_step_time >= self.step_delay_ms:
                if self.state.visited_index < len(self.state.result.visited_order):
                    node = self.state.result.visited_order[self.state.visited_index]
                    self.state.active_explore_node = node
                    if node not in (self.grid.start, self.grid.goal):
                        self.state.visited_nodes.add(node)
                    self.state.visited_index += 1
                    self.last_step_time += self.step_delay_ms
                else:
                    self.state.solving = False
                    self.state.animating_path = True
                    self.state.active_explore_node = None
                    self.last_step_time = now
            return

        if self.state.animating_path:
            while self.state.animating_path and now - self.last_step_time >= self.step_delay_ms:
                if self.state.path_index < len(self.state.result.path):
                    node = self.state.result.path[self.state.path_index]
                    self.state.active_path_node = node
                    if node not in (self.grid.start, self.grid.goal):
                        self.state.shown_path.append(node)
                    self.state.path_index += 1
                    self.last_step_time += self.step_delay_ms
                else:
                    self.state.animating_path = False
                    self.state.moving_ambulance = bool(self.state.result.path)
                    self.state.active_path_node = None
                    self.last_step_time = now
            return

        if self.state.moving_ambulance:
            self.update_ambulance_motion(now)

    def update_ambulance_motion(self, now: int) -> None:
        if self.state.result is None or not self.state.result.path:
            self.finish_ambulance_motion()
            return

        path = self.state.result.path
        if len(path) == 1:
            self.state.ambulance_pos = path[0]
            self.state.ambulance_draw_pos = (float(path[0].row), float(path[0].col))
            self.finish_ambulance_motion()
            return

        while self.state.move_index < len(path) - 1 and now - self.last_step_time >= self.move_delay_ms:
            self.state.move_index += 1
            self.state.ambulance_pos = path[self.state.move_index]
            self.last_step_time += self.move_delay_ms

        if self.state.move_index >= len(path) - 1:
            last_node = path[-1]
            self.state.ambulance_pos = last_node
            self.state.ambulance_draw_pos = (float(last_node.row), float(last_node.col))
            self.finish_ambulance_motion()
            return

        from_node = path[self.state.move_index]
        to_node = path[self.state.move_index + 1]
        progress = max(0.0, min(1.0, (now - self.last_step_time) / max(self.move_delay_ms, 1)))
        eased = progress * progress * (3.0 - 2.0 * progress)
        draw_row = from_node.row + (to_node.row - from_node.row) * eased
        draw_col = from_node.col + (to_node.col - from_node.col) * eased
        self.state.ambulance_draw_pos = (draw_row, draw_col)

    def finish_ambulance_motion(self) -> None:
        self.state.moving_ambulance = False
        scenario = self.current_scenario
        self.state.status_message = scenario["success"] if self.state.result and self.state.result.path else "No route found for this emergency."

    def draw(self) -> None:
        self.draw_background()
        self.draw_grid()
        self.draw_footer()
        self.draw_panel()
        if self.state.show_start_screen:
            self.draw_start_screen()

    def draw_background(self) -> None:
        self.screen.fill(BACKGROUND)
        window_width, window_height = self.screen.get_size()
        pygame.draw.rect(self.screen, (239, 244, 249), pygame.Rect(0, 0, window_width, window_height))
        for y in range(0, window_height, 32):
            pygame.draw.line(self.screen, (226, 233, 240), (0, y), (window_width, y))
        for x in range(0, window_width, 32):
            pygame.draw.line(self.screen, (232, 238, 244), (x, 0), (x, window_height))

    def draw_grid(self) -> None:
        board_rect = pygame.Rect(0, 0, self.config.grid_pixel_width, self.config.grid_pixel_height)
        outer = board_rect.inflate(18, 18)
        inner = board_rect.inflate(8, 8)
        pygame.draw.rect(self.screen, (15, 23, 42), outer)
        pygame.draw.rect(self.screen, (30, 41, 59), inner)
        pygame.draw.rect(self.screen, (148, 163, 184), board_rect.inflate(2, 2), width=2)

        for row in range(self.grid.rows):
            for col in range(self.grid.cols):
                pos = Position(row, col)
                cell = self.grid.get_cell(pos)
                rect = pygame.Rect(
                    col * self.config.cell_size + self.config.margin,
                    row * self.config.cell_size + self.config.margin,
                    self.config.cell_size - self.config.margin * 2,
                    self.config.cell_size - self.config.margin * 2,
                )
                self.draw_cell(rect, self.resolve_cell_color(cell, pos), cell, pos)

        if self.state.ambulance_draw_pos is not None:
            draw_row, draw_col = self.state.ambulance_draw_pos
            center_x = int(draw_col * self.config.cell_size + self.config.cell_size // 2)
            center_y = int(draw_row * self.config.cell_size + self.config.cell_size // 2)
            accent = self.current_scenario["accent"]
            pygame.draw.circle(self.screen, (255, 255, 255), (center_x, center_y), self.config.cell_size // 3 + 2)
            pygame.draw.circle(self.screen, accent, (center_x, center_y), self.config.cell_size // 3 - 1)
            label = self.badge_font.render(self.current_scenario["icon"], True, (255, 255, 255))
            self.screen.blit(label, label.get_rect(center=(center_x, center_y)))

    def resolve_cell_color(self, cell: CellType, pos: Position) -> tuple[int, int, int]:
        if pos in self.state.shown_path:
            return PATH_COLOR
        if pos in self.state.visited_nodes:
            return VISITED_COLOR
        if pos in (self.grid.start, self.grid.goal):
            return COLORS[CellType.ROAD]
        return COLORS[cell]

    def draw_cell(self, rect: pygame.Rect, color: tuple[int, int, int], cell: CellType, pos: Position) -> None:
        tile_rect = rect.inflate(-2, -2)
        is_start = pos == self.grid.start
        is_goal = pos == self.grid.goal
        is_path = pos in self.state.shown_path
        is_visited = pos in self.state.visited_nodes
        pygame.draw.rect(self.screen, (203, 213, 225), rect, border_radius=2)
        pygame.draw.rect(self.screen, color, tile_rect, border_radius=2)
        pygame.draw.rect(self.screen, (174, 182, 194), tile_rect, width=1)

        if is_path:
            route_rect = tile_rect.inflate(-6, -6)
            pygame.draw.rect(self.screen, (37, 99, 235), route_rect, border_radius=2)
            pygame.draw.line(
                self.screen,
                (239, 246, 255),
                (route_rect.left + 4, route_rect.centery),
                (route_rect.right - 4, route_rect.centery),
                2,
            )
        elif is_visited:
            pulse_rect = tile_rect.inflate(-6, -6)
            pygame.draw.rect(self.screen, (219, 234, 254), pulse_rect, border_radius=2)
            pygame.draw.circle(self.screen, (37, 99, 235), pulse_rect.center, max(3, self.config.cell_size // 10))
        elif cell == CellType.TRAFFIC:
            center_y = tile_rect.centery
            lane_left = tile_rect.left + 6
            lane_right = tile_rect.right - 6
            pygame.draw.line(self.screen, (255, 247, 237), (lane_left, center_y), (lane_right, center_y), 2)
            dash_width = max(4, self.config.cell_size // 7)
            dash_gap = max(4, self.config.cell_size // 9)
            x = lane_left + 2
            while x < lane_right - dash_width:
                pygame.draw.line(
                    self.screen,
                    (146, 64, 14),
                    (x, center_y),
                    (min(x + dash_width, lane_right), center_y),
                    2,
                )
                x += dash_width + dash_gap
        elif cell == CellType.OBSTACLE:
            block = tile_rect.inflate(-7, -7)
            pygame.draw.rect(self.screen, (100, 116, 139), block, border_radius=3)
            pygame.draw.line(self.screen, (226, 232, 240), (block.left, block.top), (block.right, block.bottom), 2)
            pygame.draw.line(self.screen, (226, 232, 240), (block.right, block.top), (block.left, block.bottom), 2)
        elif is_start:
            pygame.draw.circle(self.screen, (220, 252, 231), tile_rect.center, max(7, self.config.cell_size // 3))
            pygame.draw.circle(self.screen, COLORS[CellType.START], tile_rect.center, max(5, self.config.cell_size // 4))
            self.draw_cell_badge(tile_rect, "S", (255, 255, 255))
        elif is_goal:
            pygame.draw.circle(self.screen, (254, 226, 226), tile_rect.center, max(7, self.config.cell_size // 3))
            pygame.draw.circle(self.screen, COLORS[CellType.GOAL], tile_rect.center, max(5, self.config.cell_size // 4))
            self.draw_cell_badge(tile_rect, "G", (255, 255, 255))

        if self.state.active_explore_node == pos:
            pygame.draw.rect(self.screen, (37, 99, 235), tile_rect.inflate(-4, -4), width=2)
        if self.state.active_path_node == pos:
            pygame.draw.rect(self.screen, (29, 78, 216), tile_rect.inflate(-4, -4), width=2)

    def draw_cell_badge(self, rect: pygame.Rect, label_text: str, color: tuple[int, int, int]) -> None:
        label = self.tiny_font.render(label_text, True, color)
        self.screen.blit(label, label.get_rect(center=rect.center))

    def draw_footer(self) -> None:
        footer_y = self.config.grid_pixel_height + 10
        window_width, window_height = self.screen.get_size()
        footer_height = max(0, min(self.config.footer_height - 18, window_height - footer_y - 10))
        if footer_height <= 0:
            return

        panel_width = self.config.grid_pixel_width - 20
        footer_rect = pygame.Rect(10, footer_y, panel_width, footer_height)
        pygame.draw.rect(self.screen, (203, 213, 225), footer_rect.move(0, 2), border_radius=8)
        pygame.draw.rect(self.screen, (248, 250, 252), footer_rect, border_radius=8)
        pygame.draw.rect(self.screen, (203, 213, 225), footer_rect, width=1, border_radius=8)

        scenario = self.current_scenario
        accent = scenario["accent"]
        badge_rect = pygame.Rect(footer_rect.left + 14, footer_rect.top + 18, 54, 54)
        pygame.draw.rect(self.screen, accent, badge_rect, border_radius=8)
        badge_label = self.font.render(str(scenario["icon"]), True, (255, 255, 255))
        self.screen.blit(badge_label, badge_label.get_rect(center=badge_rect.center))

        title = f"{scenario['name']} | {scenario['vehicle']} -> {scenario['destination']}"
        self.draw_wrapped_text(self.screen, title, self.small_font, (30, 41, 59), footer_rect.left + 84, footer_rect.top + 14, panel_width - 102)

        outcome = self.get_scenario_message()
        self.draw_wrapped_text(self.screen, outcome, self.tiny_font, (51, 65, 85), footer_rect.left + 84, footer_rect.top + 42, panel_width - 102)

        controls = "Press S to change scenario | SPACE to run | R for new map"
        self.draw_wrapped_text(self.screen, controls, self.tiny_font, (100, 116, 139), footer_rect.left + 84, footer_rect.top + 66, panel_width - 102)

    def get_scenario_message(self) -> str:
        scenario = self.current_scenario
        if self.state.result and not self.state.solving and not self.state.animating_path and not self.state.moving_ambulance:
            return scenario["success"] if self.state.result.path else "No route found. Try changing map density or clearing roads."
        if self.state.solving:
            return f"{self.state.selected_algorithm} is scanning possible routes."
        if self.state.animating_path:
            return "Best route is being highlighted for the response team."
        if self.state.moving_ambulance:
            return f"{scenario['vehicle']} is moving along the selected emergency route."
        return scenario["dispatch"]

    def draw_panel(self) -> None:
        window_width, window_height = self.screen.get_size()
        panel_x = self.config.grid_pixel_width
        panel_width = max(self.config.min_panel_width, window_width - panel_x)
        panel_rect = pygame.Rect(panel_x, 0, panel_width, window_height)
        pygame.draw.rect(self.screen, (248, 250, 252), panel_rect)
        pygame.draw.rect(self.screen, (203, 213, 225), panel_rect, width=1)

        content_x = panel_x + 12
        content_y = 10
        content_width = panel_width - 24
        content_surface = pygame.Surface((content_width, 4000), pygame.SRCALPHA)

        path_length = len(self.state.result.path) - 1 if self.state.result and self.state.result.path else 0
        y = 16
        y = self.draw_wrapped_text(
            content_surface,
            APP_TITLE,
            self.font,
            (26, 39, 55),
            0,
            y,
            content_width,
            2,
        )
        y += 6

        system_items = [
            f"- Mode: {'Agent Auto' if self.state.agent_mode else 'Manual'}",
            f"- Algorithm: {self.state.selected_algorithm}",
            f"- Grid: {self.grid.rows} x {self.grid.cols}",
            f"- Start: ({self.grid.start.row}, {self.grid.start.col})",
            f"- Goal: ({self.grid.goal.row}, {self.grid.goal.col})",
            f"- Delay: {self.step_delay_ms}ms, Move: {self.move_delay_ms}ms",
            f"- Obstacle: {self.grid.obstacle_density:.0%}, Traffic: {self.grid.traffic_density:.0%}",
        ]
        y = self.draw_panel_section(content_surface, "System", system_items, 0, y, content_width)

        perf_items = [
            f"- Nodes Explored: {self.state.result.nodes_explored if self.state.result else 0}",
            f"- Path Length: {path_length}",
            f"- Time: {self.state.result.execution_time_ms:.3f} ms" if self.state.result else "- Time: 0.000 ms",
            f"- Cost: {self.state.result.total_cost if self.state.result else 0}",
        ]
        y = self.draw_panel_section(content_surface, "Performance", perf_items, 0, y, content_width)

        control_items = [
            "- SPACE: Run selected algorithm",
            "- 1 / 2 / 3: BFS / DFS / A*",
            "- A: Agent Auto mode",
            "- R: Random map, C: Clear map",
            "- Backspace: Replay latest result",
            "- Left click: Obstacle, Right click: Traffic",
            "- Shift + Left click: Set Start",
            "- Shift + Right click: Set Goal",
            "- Up/Down: Obstacle density",
            "- Left/Right: Traffic density",
            "- +/-: Animation speed",
            "- P: Compare algorithms",
            "- H: Show start page",
            "- S: Change real-world scenario",
            "- Mouse wheel on panel: Scroll text",
        ]
        y = self.draw_panel_section(content_surface, "Controls", control_items, 0, y, content_width)

        legend_items = [
            "- Green: Start, Red: Goal, Light blue: Visited",
            "- Blue: Final path, Amber lane: Traffic",
            "- Light gray: Road, Slate block: Obstacle",
        ]
        y = self.draw_panel_section(content_surface, "Legend", legend_items, 0, y, content_width)

        if self.state.benchmark_results:
            compare_items: list[str] = []
            if self.state.comparison_winner:
                compare_items.append(f"- Winner: {self.state.comparison_winner}")
            else:
                compare_items.append("- Winner: No path found")
            for algo_name in ("BFS", "DFS", "A*"):
                result = self.state.benchmark_results.get(algo_name)
                if result is None:
                    continue
                bench_path_len = len(result.path) - 1 if result.path else 0
                compare_items.append(
                    f"- {algo_name}: N={result.nodes_explored}, L={bench_path_len}, C={result.total_cost}, T={result.execution_time_ms:.2f}ms"
                )
            y = self.draw_panel_section(content_surface, "Comparison", compare_items, 0, y, content_width)

        y = self.draw_panel_section(content_surface, "Status", [f"- {self.state.status_message}"], 0, y, content_width)
        y = self.draw_wrapped_text(
            content_surface,
            "Tip: Use PageUp/PageDown or mouse wheel over this panel.",
            self.tiny_font,
            (85, 98, 112),
            0,
            y,
            content_width,
            0,
        )

        visible_height = max(window_height - content_y * 2, 1)
        self.max_panel_scroll = max(0, y - visible_height)
        self.panel_scroll = max(0, min(self.panel_scroll, self.max_panel_scroll))

        view_rect = pygame.Rect(0, self.panel_scroll, content_width, visible_height)
        self.screen.blit(content_surface, (content_x, content_y), area=view_rect)
        if self.max_panel_scroll > 0:
            self.draw_scrollbar(panel_rect, content_y, visible_height)

    def draw_scrollbar(self, panel_rect: pygame.Rect, content_y: int, visible_height: int) -> None:
        track_width = 8
        track_x = panel_rect.right - 12
        track_rect = pygame.Rect(track_x, content_y, track_width, visible_height)
        pygame.draw.rect(self.screen, (213, 222, 232), track_rect, border_radius=4)
        thumb_height = max(36, int(visible_height * (visible_height / (visible_height + self.max_panel_scroll))))
        thumb_range = max(1, visible_height - thumb_height)
        thumb_y = content_y + int((self.panel_scroll / max(1, self.max_panel_scroll)) * thumb_range)
        thumb_rect = pygame.Rect(track_x, thumb_y, track_width, thumb_height)
        pygame.draw.rect(self.screen, (127, 146, 168), thumb_rect, border_radius=4)

    def draw_panel_section(
        self,
        surface: pygame.Surface,
        title: str,
        lines: list[str],
        x: int,
        y: int,
        width: int,
    ) -> int:
        title_surface = self.small_font.render(title, True, (15, 23, 42))
        surface.blit(title_surface, (x, y))
        y += self.small_font.get_linesize() + 2
        pygame.draw.line(surface, (226, 232, 240), (x, y), (x + width, y), width=1)
        y += 4
        for line in lines:
            y = self.draw_wrapped_text(surface, line, self.tiny_font, TEXT_COLOR, x + 4, y, width - 6, 1)
            y += 2
        return y + 4

    def draw_wrapped_text(
        self,
        target_surface: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        x: int,
        y: int,
        max_width: int,
        extra_spacing: int = 0,
    ) -> int:
        for line in self.wrap_text(text, font, max_width):
            line_surface = font.render(line, True, color)
            target_surface.blit(line_surface, (x, y))
            y += font.get_linesize() + extra_spacing
        return y

    def draw_centered_wrapped_text(
        self,
        target_surface: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        center_x: int,
        y: int,
        max_width: int,
        extra_spacing: int = 0,
    ) -> int:
        for line in self.wrap_text(text, font, max_width):
            line_surface = font.render(line, True, color)
            target_surface.blit(line_surface, line_surface.get_rect(center=(center_x, y + line_surface.get_height() // 2)))
            y += font.get_linesize() + extra_spacing
        return y

    @staticmethod
    def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        wrapped: list[str] = []
        for paragraph in text.split("\n"):
            words = paragraph.split()
            if not words:
                wrapped.append("")
                continue
            current = words[0]
            for word in words[1:]:
                trial = f"{current} {word}"
                if font.size(trial)[0] <= max_width:
                    current = trial
                else:
                    wrapped.append(current)
                    current = word
            wrapped.append(current)
        return wrapped

    def draw_start_screen(self) -> None:
        window_width, window_height = self.screen.get_size()
        overlay = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 218))
        self.screen.blit(overlay, (0, 0))

        card_width = min(760, window_width - 48)
        card_height = min(430, window_height - 48)
        card_x = (window_width - card_width) // 2
        card_y = (window_height - card_height) // 2
        card_center_x = card_x + card_width // 2
        card_inner_width = card_width - 52
        card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
        pygame.draw.rect(self.screen, (15, 23, 42), card_rect.move(0, 6), border_radius=10)
        pygame.draw.rect(self.screen, (248, 250, 252), card_rect, border_radius=10)
        pygame.draw.rect(self.screen, (203, 213, 225), card_rect, width=1, border_radius=10)

        title_y = card_y + 42
        title_y = self.draw_centered_wrapped_text(
            self.screen,
            APP_TITLE,
            self.title_font,
            (15, 23, 42),
            card_center_x,
            title_y,
            card_inner_width,
            2,
        )

        subtitle = "AI powered emergency routing for ambulances, firefighters, police units, and rescue teams."
        y = self.draw_centered_wrapped_text(
            self.screen,
            subtitle,
            self.small_font,
            (71, 85, 105),
            card_center_x,
            title_y + 18,
            card_inner_width,
            1,
        )

        y += 26
        summary = "Plan routes through road blocks and traffic, then watch the responder move through the city grid."
        y = self.draw_centered_wrapped_text(
            self.screen,
            summary,
            self.font,
            (30, 41, 59),
            card_center_x,
            y,
            card_inner_width - 40,
            2,
        )

        y += 18
        prompt = "Start the simulation, choose an algorithm, or let the agent select one automatically."
        self.draw_centered_wrapped_text(
            self.screen,
            prompt,
            self.small_font,
            (100, 116, 139),
            card_center_x,
            y,
            card_inner_width - 80,
            1,
        )

        self.draw_start_buttons(card_x, card_y, card_width, card_height)

    def draw_start_buttons(self, card_x: int, card_y: int, card_width: int, card_height: int) -> None:
        bottom_y = card_y + card_height - 66
        spacing = 10
        button_height = 38
        available_width = card_width - 52
        labels = [
            ("start", "Start"),
            ("quick_run", "Quick Run"),
            ("quit", "Exit"),
        ]

        if card_width >= 700:
            button_width = (available_width - spacing * 2) // 3
            x = card_x + 26
            rects = []
            for _ in labels:
                rects.append(pygame.Rect(x, bottom_y, button_width, button_height))
                x += button_width + spacing
        else:
            button_width = available_width
            rects = []
            y = bottom_y - (button_height + 8) * 2
            for _ in labels:
                rects.append(pygame.Rect(card_x + 26, y, button_width, button_height))
                y += button_height + 8

        mouse_pos = pygame.mouse.get_pos()
        self.start_buttons.clear()
        for (key, label), rect in zip(labels, rects):
            hovered = rect.collidepoint(mouse_pos)
            fill = (15, 118, 110) if hovered and key != "quit" else (20, 184, 166) if key != "quit" else (100, 116, 139)
            if hovered and key == "quit":
                fill = (71, 85, 105)
            pygame.draw.rect(self.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.screen, (15, 23, 42), rect, width=1, border_radius=8)
            text_surface = self.small_font.render(label, True, (247, 251, 255))
            text_rect = text_surface.get_rect(center=rect.center)
            self.screen.blit(text_surface, text_rect)
            self.start_buttons[key] = rect


def parse_args() -> GameConfig:
    parser = argparse.ArgumentParser(description="AI Emergency Path Finder")
    parser.add_argument("--rows", type=int, default=20, help="Number of grid rows")
    parser.add_argument("--cols", type=int, default=20, help="Number of grid columns")
    parser.add_argument("--cell-size", type=int, default=32, help="Pixel size of each cell")
    parser.add_argument("--obstacle-density", type=float, default=0.18, help="Random obstacle density from 0.0 to 0.55")
    parser.add_argument("--traffic-density", type=float, default=0.10, help="Random traffic density from 0.0 to 0.35")
    args = parser.parse_args()

    return GameConfig(
        rows=max(args.rows, 5),
        cols=max(args.cols, 5),
        cell_size=max(args.cell_size, 16),
        obstacle_density=min(max(args.obstacle_density, 0.0), 0.55),
        traffic_density=min(max(args.traffic_density, 0.0), 0.35),
    )


if __name__ == "__main__":
    DrutoAIGame(parse_args()).run()
