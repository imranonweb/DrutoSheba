from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import heapq
import time
from typing import Dict, List, Optional, Set, Tuple

from grid import GridMap, Position


@dataclass
class SearchResult:
    algorithm: str
    path: List[Position]
    visited_order: List[Position]
    nodes_explored: int
    execution_time_ms: float
    total_cost: int


def reconstruct_path(came_from: Dict[Position, Optional[Position]], goal: Position) -> List[Position]:
    if goal not in came_from:
        return []

    path: List[Position] = []
    current: Optional[Position] = goal
    while current is not None:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path


def compute_path_cost(grid: GridMap, path: List[Position]) -> int:
    if not path:
        return 0
    return sum(grid.move_cost(pos) for pos in path[1:])


def bfs(grid: GridMap) -> SearchResult:
    start_time = time.perf_counter()
    queue = deque([grid.start])
    came_from: Dict[Position, Optional[Position]] = {grid.start: None}
    visited_order: List[Position] = []

    while queue:
        current = queue.popleft()
        visited_order.append(current)
        if current == grid.goal:
            break

        for neighbor in grid.neighbors(current):
            if neighbor not in came_from:
                came_from[neighbor] = current
                queue.append(neighbor)

    path = reconstruct_path(came_from, grid.goal)
    end_time = time.perf_counter()
    return SearchResult(
        algorithm="BFS",
        path=path,
        visited_order=visited_order,
        nodes_explored=len(visited_order),
        execution_time_ms=(end_time - start_time) * 1000,
        total_cost=compute_path_cost(grid, path),
    )


def dfs(grid: GridMap) -> SearchResult:
    start_time = time.perf_counter()
    stack = [grid.start]
    came_from: Dict[Position, Optional[Position]] = {grid.start: None}
    visited: Set[Position] = set()
    visited_order: List[Position] = []

    while stack:
        current = stack.pop()
        if current in visited:
            continue

        visited.add(current)
        visited_order.append(current)
        if current == grid.goal:
            break

        neighbors = list(grid.neighbors(current))
        neighbors.reverse()
        for neighbor in neighbors:
            if neighbor not in visited and neighbor not in came_from:
                came_from[neighbor] = current
                stack.append(neighbor)

    path = reconstruct_path(came_from, grid.goal)
    end_time = time.perf_counter()
    return SearchResult(
        algorithm="DFS",
        path=path,
        visited_order=visited_order,
        nodes_explored=len(visited_order),
        execution_time_ms=(end_time - start_time) * 1000,
        total_cost=compute_path_cost(grid, path),
    )


def manhattan(a: Position, b: Position) -> int:
    return abs(a.row - b.row) + abs(a.col - b.col)


def astar(grid: GridMap) -> SearchResult:
    start_time = time.perf_counter()
    frontier: List[Tuple[int, int, Position]] = []
    heapq.heappush(frontier, (0, 0, grid.start))
    came_from: Dict[Position, Optional[Position]] = {grid.start: None}
    g_score: Dict[Position, int] = {grid.start: 0}
    visited_order: List[Position] = []
    closed: Set[Position] = set()
    sequence = 0

    while frontier:
        _, _, current = heapq.heappop(frontier)
        if current in closed:
            continue

        closed.add(current)
        visited_order.append(current)
        if current == grid.goal:
            break

        for neighbor in grid.neighbors(current):
            # Traffic cells cost more, so A* can prefer a longer but faster road.
            tentative_g = g_score[current] + grid.move_cost(neighbor)
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                sequence += 1
                priority = tentative_g + manhattan(neighbor, grid.goal)
                heapq.heappush(frontier, (priority, sequence, neighbor))

    path = reconstruct_path(came_from, grid.goal)
    total_cost = compute_path_cost(grid, path)
    end_time = time.perf_counter()
    return SearchResult(
        algorithm="A*",
        path=path,
        visited_order=visited_order,
        nodes_explored=len(visited_order),
        execution_time_ms=(end_time - start_time) * 1000,
        total_cost=total_cost,
    )


ALGORITHMS = {
    "BFS": bfs,
    "DFS": dfs,
    "A*": astar,
}
