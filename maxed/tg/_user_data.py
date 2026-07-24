from __future__ import annotations

import dataclasses as d


@d.dataclass
class UserData:
    @d.dataclass
    class Maxed:
        """A maxed Pokemon entry."""

        pokedex: int
        shadow: bool
        legacy: bool
        count: int = 0

    maxed: list[Maxed] = d.field(default_factory=list)

    def index(
        self,
        *,
        pokedex: int,
        shadow: bool,
        legacy: bool,
    ) -> int | None:
        for index, item in enumerate(self.maxed):
            if (
                item.pokedex == pokedex
                and item.shadow == shadow
                and item.legacy == legacy
            ):
                return index

        return None

    def store(self, item: Maxed) -> bool:
        if item.count < 0:
            return False

        index = self.index(
            pokedex=item.pokedex,
            shadow=item.shadow,
            legacy=item.legacy,
        )

        if index is None:
            self.maxed.append(item)
        else:
            self.maxed[index] = item

        return True
