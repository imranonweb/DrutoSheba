from __future__ import annotations

from dataclasses import dataclass

from algorithms import SearchResult, astar, bfs, dfs
from grid import GridMap


@dataclass
class AgentDecision:
    algorithm_name: str
    reason: str


class Agent:
    def __init__(self) -> None:
        self.last_decision: AgentDecision | None = None

    def perceive(self, grid: GridMap) -> dict:
        return {
            "rows": grid.rows,
            "cols": grid.cols,
            "obstacle_ratio": grid.obstacle_ratio(),
            "traffic_ratio": grid.traffic_ratio(),
            "is_weighted": grid.is_weighted(),
        }

    def decide(self, perception: dict) -> AgentDecision:
        size = perception["rows"] * perception["cols"]
        obstacle_ratio = perception["obstacle_ratio"]
        traffic_ratio = perception["traffic_ratio"]

        # Prefer guaranteed shortest paths on simple maps, switch to A* when
        # weights or higher complexity make heuristic guidance more useful.
        if not perception["is_weighted"] and obstacle_ratio <= 0.15:
            decision = AgentDecision("BFS", "Small simple map favors guaranteed shortest path")
        elif perception["is_weighted"] or obstacle_ratio > 0.20 or traffic_ratio > 0.08:
            decision = AgentDecision("A*", "Weighted or complex map detected")
        elif obstacle_ratio < 0.10:
            decision = AgentDecision("DFS", "Low obstacle density favors quick depth exploration")
        else:
            decision = AgentDecision("A*", "Larger map benefits from heuristic guidance")

        self.last_decision = decision
        return decision

    def act(self, grid: GridMap) -> SearchResult:
        if self.last_decision is None:
            self.decide(self.perceive(grid))

        algorithm_name = self.last_decision.algorithm_name
        if algorithm_name == "BFS":
            return bfs(grid)
        if algorithm_name == "DFS":
            return dfs(grid)
        return astar(grid)
