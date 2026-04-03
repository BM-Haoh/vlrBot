# VlrBot

## Summary:
- Valorant bot. Using webscrapping with selenium in vlr.gg to archive some informartions about vct matches and analyzing it, making it available to visualize through a discord bot. We use .json as a "database" of the information about teams, players and matches (Available in v1.0, from v2.0 onwards we use SQL, archived on neon.tech)

---

## Archives:
| Archives | Type | Summary |
| :------- | :--: | :------ |
| [Auto](./src/auto.ipynb) | `.ipynb` | Testing the webscrapping - auto.py functions and class's methods prototypes. |
| [Migrar](./src/migrar.ipynb) | `.ipynb` | Transforming .json into SQL (for v2.0). |
| [Auto](./src/auto.py) | `.py` | Webscrapping logic with classes vlr_stealer and stats_manager (not used in this version). |
| [New_Api_Handler](./src/new_api_handler.py) | `.py` | Used to transform the dictionary created by vlr_stealer into a new item of partidas.json (referes to matches). |
| [Disc_buttons](./src/disc_buttons.py) | `.py` | Creates interactable buttons used to "switch pages" into discord embed. |
| [Main](./src/main.py) | `.py` | Discord bot logic. |
| botAPI | `dir / .json` | All the .json used as "database". |

---

## How to run
1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your `DISCORD_TOKEN`
4. Run `python src/main.py`