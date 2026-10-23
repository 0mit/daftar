"""reach — what a relation reaches: the one walk of every cycle check and every walk up a hierarchy (D7, D8).

A relation is given as a step: `step(x)` gives the beings one step on from x, in the order they are taken. `Reach` walks
it from a start, nearest first, and reaches each being once; what it met a second time it keeps in `again`, where a
cycle shows itself. Every question below is that one walk, asked differently:

    for x, via in Reach(start, step): ...       each being reached, nearest first, and the one it was reached from
    way(start, target, step)   -> [...]          the beings from start (not itself) to target, target last; [] for none
    reaches(start, target, step) -> bool         whether target is reached — start itself, where the relation loops back
    chain(start, step)         -> ([...], x)     a relation that gives one being a step: start and every being on, in
                                                 order, and the being where it came back to one already on it (or None)

The gate's order and life, the law's ladder, the cursor, a scheme's parents, the groupings' wholes, the layers' chain, a
crosswalk's path and a volume's folders all walk this; a store's SQL walks its own until its check is a reading."""
import collections


class Reach:
    """A walk of a relation from `start`, breadth first: iterating it gives (being, the being it was reached from) for
    each being one step or more away, once. `further(x)`, where given, says whether to step on from x; x is reached
    either way. `again` holds (being, from) for each being met a second time, in the order met: the start among them
    where the relation leads back to it."""

    def __init__(self, start, step, further=None):
        self.start, self.step, self.further = start, step, further
        self.back = {start: None}
        self.again = []

    def __iter__(self):
        todo = collections.deque([self.start])
        first = True
        while todo:
            n = todo.popleft()
            if not first and self.further is not None and not self.further(n):
                continue
            first = False
            for m in self.step(n):
                if m in self.back:
                    self.again.append((m, n))
                    continue
                self.back[m] = n
                yield m, n
                todo.append(m)

    def path(self, x, via=None):
        """The beings from the start (not itself) to `x`, `x` last, by the way it was first reached — or, with `via`,
        through `via` (the way a being met again was met)."""
        steps, n = [x], (via if via is not None else self.back.get(x))
        while n is not None and n != self.start:
            steps.append(n)
            n = self.back[n]
        return steps[::-1]


def way(start, target, step):
    """The beings from `start` (not itself) to `target`, `target` last, nearest first; [] where there is no way."""
    r = Reach(start, step)
    for x, _via in r:
        if x == target:
            return r.path(x)
    hit = next((via for x, via in r.again if x == target), None)
    return r.path(target, hit) if hit is not None else []


def reaches(start, target, step):
    """Whether the relation reaches `target` from `start` in one step or more: `start` itself where it loops back."""
    r = Reach(start, step)
    if any(x == target for x, _via in r):
        return True
    return any(x == target for x, _via in r.again)


def chain(start, step):
    """A relation that gives each being at most one being one step on (a parent, what a layer stands on), walked from
    `start`: ([start, then each being on, in order], the being it came back to — a loop — or None)."""
    r = Reach(start, step)
    out = [start] + [x for x, _via in r]
    return out, (r.again[0][0] if r.again else None)
