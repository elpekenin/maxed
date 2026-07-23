"""DialgaDex connector."""

from __future__ import annotations

import typing as t
from dataclasses import dataclass

from playwright.async_api import async_playwright

if t.TYPE_CHECKING:
    from maxed import pokedex

EXPECTED_COLUMNS = 7


def url_for(typ: pokedex.Type) -> str:
    return f"https://www.dialgadex.com/?strongest=&t={typ}"


@dataclass
class Counter:
    name: str
    dps: float
    fast: str
    charged: str


async def best_counters(typ: pokedex.Type) -> list[Counter]:
    url = url_for(typ)

    counters: list[Counter] = []

    async with async_playwright() as playwright:
        chromium = playwright.chromium
        browser = await chromium.launch()

        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_selector("#strongest-header")

        rows: list[list[str]] = await page.locator("tbody tr").evaluate_all(
            """
            (trs) => trs.map(
                tr => Array
                    .from(tr.querySelectorAll("td"))
                    .map(td => td.textContent?.trim() ?? "")
            )
            """,
        )

        for row in rows:
            if len(row) != EXPECTED_COLUMNS:
                continue

            _, _order, name, fast, charged, dps, _perc = row

            if name is None or fast is None or charged is None or dps is None:
                continue

            counters.append(
                Counter(
                    name.strip(),
                    float(dps.removeprefix("eDPS ")),
                    fast,
                    charged,
                ),
            )

    return counters
