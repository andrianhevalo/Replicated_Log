from enum import Enum


class NodeHealth(Enum):
    HEALTHY = 0
    SUSPECTED = 1
    UNHEALTHY = 2

    def next(self):
        if self == NodeHealth.HEALTHY:
            return NodeHealth.SUSPECTED
        if self == NodeHealth.SUSPECTED:
            return NodeHealth.UNHEALTHY
        return self




