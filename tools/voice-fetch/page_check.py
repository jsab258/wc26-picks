#!/usr/bin/env python3
"""Drive the listening page in a phone-sized browser and assert it works.

WHY THIS EXISTS. Jafar said "nothing happens when I click copy picks". There
was no copy button on the generated page at all — the one he had came from a
throwaway that was never folded back in — and the page had no viewport tag
either, so a phone rendered it at desktop width. Both faults were invisible
from the Python that wrote the HTML, and would have stayed invisible to any
amount of re-reading it.

Driving it found three more the moment it ran:

  1. The fixed bottom bar SAT ON TOP of the last section's controls, so they
     could not be tapped. The browser said so in as many words: "<div id=bar>
     intercepts pointer events".
  2. `.meta` was flex-basis 100% plus a left indent under content-box, which
     is 394px inside a 390px phone — the page scrolled sideways.
  3. The whole row was a <label> WRAPPING THE AUDIO, so tapping play also cast
     the vote. Every candidate you listened to would have selected itself.

None of those are exotic. All three are the kind of thing you only find by
opening the page, which is why this is a script and not a paragraph of care.

    python page_check.py            # builds a fixture page and drives it
"""
import asyncio
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# WHICHEVER CHROMIUM IS ACTUALLY HERE. The dev image ships one at a fixed
# path and blocks downloading another; a CI runner installs its own and has
# nothing at that path. Probing beats hard-coding either, and beats a CI step
# that rewrites this line with sed.
_PINNED = "/opt/pw-browsers/chromium"
CHROMIUM = _PINNED if os.path.exists(_PINNED) else None
PHONE = {"width": 390, "height": 844}

_fails = []


def check(ok, what, got=""):
    print(("  ok   " if ok else "  FAIL ") + what + ("" if ok else f" — {got}"))
    if not ok:
        _fails.append(what)


def fixture(out):
    """A page with the shape the real one has: some characters full, one empty."""
    import ledger_voice_fetch as L
    L.PICKS = out / "picks.txt"
    made = {}
    for i, c in enumerate(L.CAST):
        made[c["id"]] = [] if i == 3 else [
            dict(n=k, file=f'{c["id"]}/candidate-{k:02d}.wav',
                 speaker=f"p2{k}{i}", age=str(22 + k), accent="English",
                 onbrief=(k == 2), seconds=8.4)
            for k in range(1, 4)]
    L.build_page(L.CAST, made, out, "vctk")
    return out / "listen.html", made


async def drive(page_path):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=CHROMIUM)
        ctx = await browser.new_context(viewport=PHONE, is_mobile=True,
                                        has_touch=True)
        pg = await ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        await pg.goto(page_path.as_uri())

        # 1. IT FITS A PHONE. The whole point of the viewport tag.
        width = await pg.evaluate("document.documentElement.scrollWidth")
        check(width <= PHONE["width"], "the page does not scroll sideways on a phone",
              f"scrollWidth {width} > {PHONE['width']}")

        # 2. THE TAP TARGET IS A TARGET. Apple's own floor is 44px.
        box = await pg.locator(".pickbox").first.bounding_box()
        check(box and box["height"] >= 40,
              "the pick control is big enough to hit with a thumb",
              f"{box and round(box['height'])}px")

        # 3. PLAY DOES NOT VOTE. The <audio> must not be inside the <label>.
        first = pg.locator(".cand").first
        check(await first.locator("label.pickbox audio").count() == 0,
              "the play control is outside the label, so listening is not picking")

        # 4. PICKING WORKS AND IS COUNTED.
        for cid, n in (("lena", 2), ("rocco", 1), ("sam", 3)):
            await pg.locator(f'input[name="pick-{cid}"][value="{n}"]').check()
        count = await pg.locator("#count").inner_text()
        check(count.startswith("3"), "three picks read back as three", count)

        # 5. THE BUTTON THAT DID NOTHING. It must say something either way.
        await pg.locator("#copy").click()
        await pg.wait_for_timeout(300)
        said = (await pg.locator("#said").inner_text()).strip()
        body = await pg.locator("#out").input_value()
        check(said != "", "the copy button says out loud what happened", repr(said))
        check(body == "lena 2\nrocco 1\nsam 3",
              "and the text it copied is the picks, one per line", repr(body))

        # 6. THE BAR DOES NOT SIT ON THE CONTENT. Ask the browser what is
        #    actually on top at the last section's control, rather than
        #    trusting a padding value.
        clear = pg.locator('button[data-clear="crowd_f3"]')
        await clear.scroll_into_view_if_needed()
        await pg.wait_for_timeout(120)
        cb = await clear.bounding_box()
        top = await pg.evaluate(
            "([x, y]) => { const e = document.elementFromPoint(x, y);"
            " return e ? (e.tagName + (e.id ? '#' + e.id : '')) : 'none'; }",
            [cb["x"] + cb["width"] / 2, cb["y"] + cb["height"] / 2])
        check(top.startswith("BUTTON"),
              "the bottom bar is not covering the last section's controls", top)

        # 7. PICKS SURVIVE CLOSING THE PAGE. An hour of listening on a train
        #    must not be lost to a reload.
        await pg.reload()
        await pg.wait_for_timeout(200)
        check(await pg.locator('input[name="pick-lena"][value="2"]').is_checked(),
              "picks survive a reload")

        # 8. CLEAR CLEARS ONE, NOT ALL.
        await pg.locator('button[data-clear="rocco"]').click()
        await pg.wait_for_timeout(120)
        after = await pg.locator("#out").input_value()
        check(after == "lena 2\nsam 3", "clear removes one pick and leaves the rest",
              repr(after))

        # 9. ONE CLIP AT A TIME.
        check(await pg.evaluate(
            "!!document.querySelector('audio') && "
            "document.querySelectorAll('audio').length > 1"),
            "there is more than one clip, so the pause-others rule matters")

        check(not errors, "no JavaScript errors on the page", "; ".join(errors[:3]))
        await browser.close()


def main():
    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(tmp)
        page, made = fixture(out)
        print(f"LEDGER listening-page check — {sum(len(v) for v in made.values())} "
              f"fixture clips, {PHONE['width']}x{PHONE['height']} phone")
        asyncio.run(drive(page))
    print(f"\n{9 + 1 - len(_fails)} passed, {len(_fails)} failed")
    return 1 if _fails else 0


if __name__ == "__main__":
    sys.exit(main())
