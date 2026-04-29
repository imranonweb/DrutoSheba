from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import random
from typing import Iterable, Optional


class CellType(str, Enum):
    ROAD = "road"
    OBSTACLE = "obstacle"
    TRAFFIC = "traffic"
    START = "start"
    GOAL = "goal"


@dataclass(frozen=True)
class Position:
    row: int
    col: int


class GridMap:
    def __init__(self, rows: int = 20, cols: int = 20, obstacle_density: float = 0.18, traffic_density: float = 0.10):
        self.rows = rows
        self.cols = cols
        self.obstacle_density = obstacle_density
        self.traffic_density = traffic_density
        self.cells = [[CellType.ROAD for _ in range(cols)] for _ in range(rows)]
        self.start = Position(0, 0)
        self.goal = Position(rows - 1, cols - 1)
        self.reset()

    def reset(self) -> None:
        self.cells = [[CellType.ROAD for _ in range(self.cols)] for _ in range(self.rows)]
        self.start = Position(0, 0)
        self.goal = Position(self.rows - 1, self.cols - 1)
        self._set_special_cells()

    def randomize(self, obstacle_density: Optional[float] = None, traffic_density: Optional[float] = None) -> None:
        obstacle_density = self.obstacle_density if obstacle_density is None else obstacle_density
        traffic_density = self.traffic_density if traffic_density is None else traffic_density

        self.reset()
        # Keep start and goal fixed while generating a fresh mix of roads,
        # obstacles, and weighted traffic cells for the simulation.
        for row in range(self.rows):
            for col in range(self.cols):
                pos = Position(row, col)
                if pos in (self.start, self.goal):
                    continue
                roll = random.random()
                if roll < obstacle_density:
                    self.cells[row][col] = CellType.OBSTACLE
                elif roll < obstacle_density + traffic_density:
                    self.cells[row][col] = CellType.TRAFFIC
                else:
                    self.cells[row][col] = CellType.ROAD
        self._set_special_cells()

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.row < self.rows and 0 <= pos.col < self.cols

    def get_cell(self, pos: Position) -> CellType:
        return self.cells[pos.row][pos.col]

    def set_cell(self, pos: Position, cell_type: CellType) -> None:
        if pos == self.start or pos == self.goal:
            return
        self.cells[pos.row][pos.col] = cell_type

    def set_start(self, pos: Position) -> bool:
        if not self.in_bounds(pos) or pos == self.goal:
            return False
        old_start = self.start
        self.start = pos
        if old_start != self.goal:
            self.cells[old_start.row][old_start.col] = CellType.ROAD
        self._set_special_cells()
        return True

    def set_goal(self, pos: Position) -> bool:
        if not self.in_bounds(pos) or pos == self.start:
            return False
        old_goal = self.goal
        self.goal = pos
        if old_goal != self.start:
            self.cells[old_goal.row][old_goal.col] = CellType.ROAD
        self._set_special_cells()
        return True

    def toggle_obstacle(self, pos: Position) -> None:
        if pos in (self.start, self.goal):
            return
        self.cells[pos.row][pos.col] = (
            CellType.ROAD if self.cells[pos.row][pos.col] == CellType.OBSTACLE else CellType.OBSTACLE
        )

    def toggle_traffic(self, pos: Position) -> None:
        if pos in (self.start, self.goal):
            return
        self.cells[pos.row][pos.col] = (
            CellType.ROAD if self.cells[pos.row][pos.col] == CellType.TRAFFIC else CellType.TRAFFIC
        )

    def neighbors(self, pos: Position) -> Iterable[Position]:
        # Four-direction movement keeps the search behavior easy to compare.
        directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
        for dr, dc in directions:
            nxt = Position(pos.row + dr, pos.col + dc)
            if self.in_bounds(nxt) and self.get_cell(nxt) != CellType.OBSTACLE:
                yield nxt

    def move_cost(self, pos: Position) -> int:
        return 3 if self.get_cell(pos) == CellType.TRAFFIC else 1

    def obstacle_ratio(self) -> float:
        blocked = sum(cell == CellType.OBSTACLE for row in self.cells for cell in row)
        return blocked / (self.rows * self.cols)

    def traffic_ratio(self) -> float:
        traffic = sum(cell == CellType.TRAFFIC for row in self.cells for cell in row)
        return traffic / (self.rows * self.cols)

    def is_weighted(self) -> bool:
        return any(cell == CellType.TRAFFIC for row in self.cells for cell in row)

    def _set_special_cells(self) -> None:
        self.cells[self.start.row][self.start.col] = CellType.START
        self.cells[self.goal.row][self.goal.col] = CellType.GOAL
