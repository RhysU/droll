#!/usr/bin/env python3
"""Automated beta-tester: play droll 100 times with TTY, capture everything."""

import pexpect
import random
import re
import sys
import os

HEROES = [
    "Crusader", "Enchantress", "HalfGoblin", "Knight",
    "Mercenary", "Minstrel", "Occultist", "Spellsword",
]

MONSTERS = ["goblin", "skeleton", "ooze"]
PARTY = ["fighter", "cleric", "mage", "thief", "champion", "scroll"]
TREASURES = ["sword", "talisman", "sceptre", "tools", "scroll", "elixir", "bait", "portal", "ring", "scale"]

# Which party member defeats all of which monster type
DEFEATS_ALL = {
    "fighter": "goblin",
    "cleric": "skeleton",
    "mage": "ooze",
}
# Champion defeats all of any type
# Thief defeats one of any type

def parse_line(line):
    """Extract info from a status line."""
    # Remove ANSI codes
    clean = re.sub(r'\x1b\[[0-9;]*m', '', line)
    return clean.strip()

def parse_counts(text):
    """Parse 'fighter×2 cleric mage' into dict."""
    counts = {}
    # Match patterns like 'name×N~D', 'name×N', 'name~D', or just 'name'
    for m in re.finditer(r'(\w+)(?:×(\d+))?(?:~(\d+))?', text):
        name = m.group(1)
        n = int(m.group(2)) if m.group(2) else 1
        if name in ('None',):
            continue
        counts[name] = n
    return counts

def play_game(seed, hero, log_file):
    """Play one game, return (score, raw_output_with_colors)."""
    cmd = f"droll --seed {seed} {hero}"
    raw_output = []

    try:
        child = pexpect.spawn(cmd, timeout=30, encoding='utf-8', env={**os.environ, 'TERM': 'xterm-256color'})
        child.setwinsize(50, 200)

        moves = 0
        max_moves = 300  # safety limit

        while moves < max_moves:
            try:
                idx = child.expect([r'\d+ \w+> ', pexpect.EOF, pexpect.TIMEOUT], timeout=10)
            except (pexpect.EOF, pexpect.TIMEOUT):
                break

            if idx == 1:  # EOF - game over
                break
            if idx == 2:  # TIMEOUT
                break

            # Capture all output including color codes
            before = child.before + child.after
            raw_output.append(before)

            # Parse state from output
            clean = re.sub(r'\x1b\[[0-9;]*m', '', before)
            lines = clean.strip().split('\n')

            # Find key info
            consider_line = ""
            party_line = ""
            dungeon_line = ""
            score_line = ""
            treasure_line = ""

            for line in lines:
                line = line.strip()
                if line.startswith("Consider:"):
                    consider_line = line
                elif line.startswith("Party:"):
                    party_line = line
                elif line.startswith("Dungeon:"):
                    dungeon_line = line
                elif line.startswith("Score"):
                    score_line = line
                elif line.startswith("Treasure:"):
                    treasure_line = line

            # Extract consider options
            consider_opts = consider_line.replace("Consider:", "").strip().split()

            # Extract party
            party_text = party_line.replace("Party:", "").strip()
            party = parse_counts(party_text)

            # Extract dungeon
            dungeon_text = dungeon_line.replace("Dungeon:", "").strip()
            dungeon = parse_counts(dungeon_text)

            # Extract treasure
            treasure_text = treasure_line.replace("Treasure:", "").strip()
            treasures = parse_counts(treasure_text)

            # Determine what monsters are present
            monsters_present = {k: v for k, v in dungeon.items() if k in MONSTERS}
            has_monsters = sum(monsters_present.values()) > 0
            has_chest = dungeon.get("chest", 0) > 0
            has_potion = dungeon.get("potion", 0) > 0
            has_dragon = dungeon.get("dragon", 0) >= 3

            # Simple strategy: pick an action
            action = None

            # If "descend" is available and no monsters, descend (unless deep)
            if "descend" in consider_opts and not has_monsters:
                # Decide: descend or retire based on party size and depth
                retire_opt = [o for o in consider_opts if o.startswith("retire")]
                depth_match = re.search(r'depth (\d+)', score_line)
                depth = int(depth_match.group(1)) if depth_match else 0
                party_size = sum(party.values())

                if retire_opt and depth >= 5 and party_size <= 3:
                    action = "retire"
                elif retire_opt and depth >= 7:
                    action = "retire"
                elif "descend" in consider_opts:
                    action = "descend"

            if action is None and "descend" in consider_opts and not has_monsters and not action:
                action = "descend"

            # Handle monsters
            if action is None and has_monsters:
                # Try to use the best party member
                for party_member, fav_monster in DEFEATS_ALL.items():
                    if party.get(party_member, 0) > 0 and monsters_present.get(fav_monster, 0) > 0:
                        action = f"{party_member} {fav_monster}"
                        break

                if action is None and party.get("champion", 0) > 0:
                    # Champion defeats all of any type
                    for monster in MONSTERS:
                        if monsters_present.get(monster, 0) > 0:
                            action = f"champion {monster}"
                            break

                if action is None:
                    # Use any party member against any monster (defeats one)
                    for pm in ["fighter", "cleric", "mage", "thief"]:
                        if party.get(pm, 0) > 0:
                            for monster in MONSTERS:
                                if monsters_present.get(monster, 0) > 0:
                                    action = f"{pm} {monster}"
                                    break
                        if action:
                            break

                # Use treasure as party member against monster
                if action is None:
                    treasure_as_party = {
                        "sword": "goblin",  # acts as fighter
                        "talisman": "skeleton",  # acts as cleric
                        "sceptre": "ooze",  # acts as mage
                    }
                    for t, fav in treasure_as_party.items():
                        if treasures.get(t, 0) > 0 and monsters_present.get(fav, 0) > 0:
                            action = f"{t} {fav}"
                            break
                    if action is None:
                        for t in ["sword", "talisman", "sceptre", "tools"]:
                            if treasures.get(t, 0) > 0:
                                for monster in MONSTERS:
                                    if monsters_present.get(monster, 0) > 0:
                                        action = f"{t} {monster}"
                                        break
                            if action:
                                break

            # Handle dragon (3+)
            if action is None and has_dragon:
                # Need 3 distinct party members
                distinct = [pm for pm in PARTY if party.get(pm, 0) > 0 and pm != "scroll"]
                if len(distinct) >= 3:
                    dragon_team = distinct[:3]
                    action = f"{dragon_team[0]} dragon {dragon_team[1]} {dragon_team[2]}"
                else:
                    # Try retreat
                    retreat_opt = [o for o in consider_opts if o.startswith("retreat")]
                    if retreat_opt:
                        action = "retreat"

            # Open chests if no monsters
            if action is None and has_chest and not has_monsters:
                if party.get("thief", 0) > 0:
                    action = "thief chest"
                elif party.get("champion", 0) > 0:
                    action = "champion chest"
                else:
                    for pm in ["fighter", "cleric", "mage"]:
                        if party.get(pm, 0) > 0:
                            action = f"{pm} chest"
                            break

            # Quaff potions if no monsters
            if action is None and has_potion and not has_monsters:
                n_potions = dungeon.get("potion", 0)
                # Need to specify what to recover
                drinker = None
                for pm in ["fighter", "cleric", "mage", "thief", "champion"]:
                    if party.get(pm, 0) > 0:
                        drinker = pm
                        break
                if drinker:
                    targets = []
                    for _ in range(n_potions):
                        targets.append("champion")
                    action = f"{drinker} potion " + " ".join(targets)

            # Handle ability
            if action is None and "ability" in consider_opts:
                if hero == "Knight":
                    if has_monsters:
                        action = "ability"
                elif hero == "Minstrel":
                    if dungeon.get("dragon", 0) > 0:
                        action = "ability"
                elif hero == "Crusader":
                    action = "ability"
                elif hero == "Spellsword":
                    action = "ability"
                elif hero == "Enchantress":
                    for monster in MONSTERS:
                        if monsters_present.get(monster, 0) > 0:
                            action = f"ability {monster}"
                            break
                elif hero == "HalfGoblin":
                    if monsters_present.get("goblin", 0) > 0:
                        action = "ability"
                elif hero == "Occultist":
                    if monsters_present.get("skeleton", 0) > 0:
                        action = "ability"
                elif hero == "Mercenary":
                    targets = []
                    for monster in MONSTERS:
                        for _ in range(min(monsters_present.get(monster, 0), 2 - len(targets))):
                            targets.append(monster)
                        if len(targets) >= 2:
                            break
                    if targets:
                        action = "ability " + " ".join(targets[:2])

            # Retire if possible and we have decent depth
            if action is None:
                retire_opt = [o for o in consider_opts if o.startswith("retire")]
                if retire_opt:
                    action = "retire"

            # Retreat as last resort
            if action is None:
                retreat_opt = [o for o in consider_opts if o.startswith("retreat")]
                if retreat_opt:
                    action = "retreat"

            # Descend as fallback
            if action is None and "descend" in consider_opts:
                action = "descend"

            if action is None:
                # Try just pressing enter or something
                action = "retreat"

            log_file.write(f"  ACTION: {action}\n")
            child.sendline(action)
            moves += 1

        # Get any remaining output
        try:
            child.expect(pexpect.EOF, timeout=5)
            raw_output.append(child.before)
        except:
            pass

        child.close()

        # Extract final score from output
        all_output = "".join(raw_output)
        clean_output = re.sub(r'\x1b\[[0-9;]*m', '', all_output)

        # Find the "Game Over" or final score
        score_matches = re.findall(r'Score (\d+)', clean_output)
        final_score = int(score_matches[-1]) if score_matches else 0

        return final_score, all_output, clean_output

    except Exception as e:
        return -1, str(e), str(e)


def main():
    random.seed(42)
    results = []
    all_raw = []

    log = open("/home/user/droll/game_log.txt", "w")
    color_log = open("/home/user/droll/color_log.txt", "wb")

    for game_num in range(100):
        seed = game_num  # Use game number as seed for reproducibility
        hero = HEROES[game_num % len(HEROES)]

        log.write(f"\n{'='*60}\n")
        log.write(f"GAME {game_num}: Hero={hero}, Seed={seed}\n")
        log.write(f"{'='*60}\n")

        score, raw, clean = play_game(seed, hero, log)

        log.write(f"FINAL SCORE: {score}\n")
        log.write(f"CLEAN OUTPUT:\n{clean}\n")

        # Save raw output with color codes
        color_log.write(f"\n{'='*60}\nGAME {game_num}: {hero} seed={seed}\n{'='*60}\n".encode())
        color_log.write(raw.encode('utf-8', errors='replace'))

        results.append((game_num, hero, seed, score))

        if game_num % 10 == 0:
            print(f"Game {game_num}: {hero} -> Score {score}")

    log.close()
    color_log.close()

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY OF 100 GAMES")
    print(f"{'='*60}")

    scores_by_hero = {}
    for gnum, hero, seed, score in results:
        scores_by_hero.setdefault(hero, []).append(score)

    for hero in HEROES:
        scores = scores_by_hero.get(hero, [])
        if scores:
            valid = [s for s in scores if s >= 0]
            errors = len(scores) - len(valid)
            if valid:
                avg = sum(valid) / len(valid)
                print(f"{hero:15s}: avg={avg:5.1f}  min={min(valid):3d}  max={max(valid):3d}  games={len(valid):2d}  errors={errors}")
            else:
                print(f"{hero:15s}: ALL ERRORS ({errors})")

    all_scores = [s for _, _, _, s in results if s >= 0]
    errors = sum(1 for _, _, _, s in results if s < 0)
    if all_scores:
        print(f"\nOverall: avg={sum(all_scores)/len(all_scores):.1f}  min={min(all_scores)}  max={max(all_scores)}  errors={errors}")

    # Dump first few game color outputs for review
    print(f"\nDetailed logs in: /home/user/droll/game_log.txt")
    print(f"Color output in: /home/user/droll/color_log.txt")


if __name__ == "__main__":
    main()
