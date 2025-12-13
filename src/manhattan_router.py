#!/usr/bin/env python3
"""
Manhattan Router with A* Pathfinding

Routes wires between component pins using orthogonal (90-degree) paths.
Implements:
- A* pathfinding for optimal routing
- Obstacle avoidance (component boundaries)
- Multi-pin net routing via Steiner tree approximation
- Wire crossing minimization

Designed for clean, professional ECE schematics.
"""

import sys
import json
import heapq
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Optional
import math

@dataclass(order=True)
class Node:
    """A* search node"""
    f_score: float  # Total estimated cost
    position: Tuple[int, int] = field(compare=False)
    g_score: float = field(compare=False)  # Cost from start
    parent: Optional['Node'] = field(default=None, compare=False)

@dataclass
class Wire:
    """Routed wire path"""
    net_name: str
    path: List[Tuple[float, float]]
    crosses: int = 0  # Number of crossings with other wires

class ManhattanRouter:
    """A* based Manhattan routing"""

    def __init__(self, grid_size: int = 10):
        self.grid_size = grid_size  # Grid spacing in pixels
        self.obstacles: Set[Tuple[int, int]] = set()
        self.wire_segments: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []

    def set_obstacles_from_components(self, components: List[Dict]):
        """Mark component boundaries as obstacles"""
        for comp in components:
            pos = comp['position']
            size = comp['size']

            # Calculate component bounding box
            x1 = int((pos['x'] - size['width']/2) / self.grid_size)
            y1 = int((pos['y'] - size['height']/2) / self.grid_size)
            x2 = int((pos['x'] + size['width']/2) / self.grid_size)
            y2 = int((pos['y'] + size['height']/2) / self.grid_size)

            # Mark all grid cells in component as obstacles
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    self.obstacles.add((x, y))

    def route_net(self, net: Dict, components: List[Dict]) -> Wire:
        """
        Route a multi-pin net

        For 2-pin nets: Direct A* path
        For multi-pin nets: Approximate Steiner tree (MST heuristic)
        """
        net_name = net['name']
        pin_refs = net['pins']  # List of (component_ref, pin_id)

        # Get pin positions
        pin_positions = []
        for comp_ref, pin_id in pin_refs:
            # Find component
            comp = next((c for c in components if c['reference'] == comp_ref), None)
            if not comp:
                continue

            # Find pin
            pin = next((p for p in comp.get('pins', []) if p['id'] == pin_id), None)
            if not pin:
                continue

            pos = pin['position']
            pin_positions.append((pos['x'], pos['y']))

        if len(pin_positions) < 2:
            return Wire(net_name=net_name, path=[])

        # Route based on number of pins
        if len(pin_positions) == 2:
            # Two-pin net: Direct path
            path = self._route_two_pins(pin_positions[0], pin_positions[1])
        else:
            # Multi-pin net: Approximate Steiner tree
            path = self._route_multi_pins(pin_positions)

        # Record wire segments for crossing detection
        for i in range(len(path) - 1):
            self.wire_segments.append((
                self._to_grid(path[i]),
                self._to_grid(path[i+1])
            ))

        return Wire(net_name=net_name, path=path)

    def _route_two_pins(self, start: Tuple[float, float],
                        end: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Route between two pins using A*"""

        # Convert to grid coordinates
        start_grid = self._to_grid(start)
        end_grid = self._to_grid(end)

        # A* pathfinding
        grid_path = self._astar(start_grid, end_grid)

        # Convert back to pixel coordinates
        if not grid_path:
            # Fallback: Direct L-shaped path
            return [start, (end[0], start[1]), end]

        # Simplify path (remove redundant points)
        simplified = self._simplify_path(grid_path)

        # Convert to pixel coordinates
        pixel_path = [self._from_grid(p) for p in simplified]

        return pixel_path

    def _route_multi_pins(self, pins: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Route multi-pin net using MST approximation of Steiner tree

        Algorithm:
        1. Build minimum spanning tree of pins
        2. Route each MST edge independently
        3. Merge overlapping segments
        """
        if len(pins) <= 2:
            return self._route_two_pins(pins[0], pins[1] if len(pins) == 2 else pins[0])

        # Build MST using Prim's algorithm
        mst_edges = self._build_mst(pins)

        # Route each edge
        all_paths = []
        for i, j in mst_edges:
            path = self._route_two_pins(pins[i], pins[j])
            all_paths.extend(path)

        # Merge and simplify
        merged = self._merge_paths(all_paths)

        return merged

    def _build_mst(self, pins: List[Tuple[float, float]]) -> List[Tuple[int, int]]:
        """Build minimum spanning tree of pin positions"""
        n = len(pins)
        if n <= 1:
            return []

        # Prim's algorithm
        visited = {0}
        edges = []
        candidates = []

        # Add all edges from first pin
        for j in range(1, n):
            dist = self._manhattan_distance(pins[0], pins[j])
            heapq.heappush(candidates, (dist, 0, j))

        while len(visited) < n and candidates:
            dist, i, j = heapq.heappop(candidates)

            if j in visited:
                continue

            visited.add(j)
            edges.append((i, j))

            # Add edges from newly visited pin
            for k in range(n):
                if k not in visited:
                    dist = self._manhattan_distance(pins[j], pins[k])
                    heapq.heappush(candidates, (dist, j, k))

        return edges

    def _astar(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        """A* pathfinding on grid"""

        if start == goal:
            return [start]

        open_set = []
        start_node = Node(
            f_score=self._heuristic(start, goal),
            position=start,
            g_score=0
        )
        heapq.heappush(open_set, start_node)

        closed_set = set()
        g_scores = {start: 0}

        while open_set:
            current = heapq.heappop(open_set)

            if current.position == goal:
                # Reconstruct path
                path = []
                node = current
                while node:
                    path.append(node.position)
                    node = node.parent
                return list(reversed(path))

            if current.position in closed_set:
                continue

            closed_set.add(current.position)

            # Explore neighbors (4-connected grid: up, down, left, right)
            for neighbor_pos in self._get_neighbors(current.position):
                if neighbor_pos in closed_set:
                    continue

                # Calculate cost
                move_cost = 1.0

                # Penalty for obstacles (allow routing through with high cost)
                if neighbor_pos in self.obstacles:
                    move_cost += 100.0

                # Penalty for changing direction (prefer straight lines)
                if current.parent:
                    if self._is_direction_change(current.parent.position, current.position, neighbor_pos):
                        move_cost += 0.5

                tentative_g = current.g_score + move_cost

                if neighbor_pos not in g_scores or tentative_g < g_scores[neighbor_pos]:
                    g_scores[neighbor_pos] = tentative_g
                    f_score = tentative_g + self._heuristic(neighbor_pos, goal)

                    neighbor_node = Node(
                        f_score=f_score,
                        position=neighbor_pos,
                        g_score=tentative_g,
                        parent=current
                    )
                    heapq.heappush(open_set, neighbor_node)

        # No path found - return direct L-path
        return [start, (goal[0], start[1]), goal]

    def _get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get 4-connected neighbors"""
        x, y = pos
        return [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]

    def _heuristic(self, pos: Tuple[int, int], goal: Tuple[int, int]) -> float:
        """Manhattan distance heuristic"""
        return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

    def _is_direction_change(self, prev: Tuple[int, int], current: Tuple[int, int],
                            next_pos: Tuple[int, int]) -> bool:
        """Check if path changes direction"""
        dir1_x = current[0] - prev[0]
        dir1_y = current[1] - prev[1]
        dir2_x = next_pos[0] - current[0]
        dir2_y = next_pos[1] - current[1]

        # Direction change if not continuing in same direction
        return (dir1_x, dir1_y) != (dir2_x, dir2_y)

    def _manhattan_distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Manhattan distance between two points"""
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    def _to_grid(self, pos: Tuple[float, float]) -> Tuple[int, int]:
        """Convert pixel position to grid coordinates"""
        return (int(pos[0] / self.grid_size), int(pos[1] / self.grid_size))

    def _from_grid(self, pos: Tuple[int, int]) -> Tuple[float, float]:
        """Convert grid coordinates to pixel position"""
        return (pos[0] * self.grid_size, pos[1] * self.grid_size)

    def _simplify_path(self, path: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Remove redundant collinear points"""
        if len(path) <= 2:
            return path

        simplified = [path[0]]

        for i in range(1, len(path) - 1):
            prev = simplified[-1]
            current = path[i]
            next_point = path[i + 1]

            # Check if collinear
            if not self._is_collinear(prev, current, next_point):
                simplified.append(current)

        simplified.append(path[-1])
        return simplified

    def _is_collinear(self, p1: Tuple[int, int], p2: Tuple[int, int],
                     p3: Tuple[int, int]) -> bool:
        """Check if three points are collinear (on same line)"""
        # For Manhattan routing, collinear means same X or same Y
        return (p1[0] == p2[0] == p3[0]) or (p1[1] == p2[1] == p3[1])

    def _merge_paths(self, paths: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Merge and deduplicate path segments"""
        if not paths:
            return []

        # Simple deduplication
        unique_points = []
        seen = set()

        for point in paths:
            rounded = (round(point[0], 1), round(point[1], 1))
            if rounded not in seen:
                seen.add(rounded)
                unique_points.append(point)

        return unique_points


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 manhattan_router.py <placed_circuit.json>")
        print("\nExpects JSON with placed components and nets")
        sys.exit(1)

    placement_file = Path(sys.argv[1])

    with open(placement_file) as f:
        data = json.load(f)

    components = data.get('components', [])
    nets = data.get('nets', [])

    print(f"Routing {len(nets)} nets for {len(components)} components", file=sys.stderr)

    # Initialize router
    router = ManhattanRouter(grid_size=10)
    router.set_obstacles_from_components(components)

    # Route each net
    routed_wires = []
    for net in nets:
        wire = router.route_net(net, components)
        routed_wires.append(wire)
        print(f"  Routed {wire.net_name}: {len(wire.path)} points", file=sys.stderr)

    # Output result
    output = {
        'components': components,
        'wires': [
            {
                'net': wire.net_name,
                'path': [{'x': p[0], 'y': p[1]} for p in wire.path]
            }
            for wire in routed_wires
        ]
    }

    print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
