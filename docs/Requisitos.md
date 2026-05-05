# Requirements Especification
## Functional Requirements (FR):
|  ID | Requirement | Description | Status |
| :-: | :---------: | :---------: | :----: |
| FR01 | Team Tags List | The System shall list all available research tags of each professinal team | Implemented |
| FR02 | Team Stats metrics | The System must calculate the team avarage stats based on each player performance | Implemented |
| FR03 | Maps Performance Analysis | The System must calculate overall win rates, including specific Attack and Defense win rates, for every map and composition used by a team | Implemented |
| FR04 | Team Profile Display | The System shall allow users to retrieve and display a comprehensive profile for a selected team. | Implemented (Pending Refactor) |
| FR05 | Player Performance Benchmarking | The System shall allow users to compare a specific player's stats against VCT league averages | Proposed |
| FR06 | Head-to-Head Comparison | The System shall allow users to select two teams for a direct comparison of map performance and roster average stats | Proposed |
| FR07 | Map Composition Explorer | The System shall allow users to browse all agent compositions used on a specific map across different VCT leagues. | Proposed |
| FR08 | Agent-Specific Filter | Within the Composition Explorer, the System shall allow users to filter by a specific agent to see relevant compositions | Proposed |
| FR09 | GenAi Pick/Ban Prediction | The System shall utilize genrative AI to predict pick/ban outcomes for upcoming matches | Proposed |

## Non-Functional Requirements (NFR):
|  ID | Categoria | Description |
| :-: | :-------: | :---------: |
| NFR01 | Data Visualization | Data shall be presented using graphical elements (e.g., embeds, charts) to enhance information readability. |
| NFR02 | Responsiveness | All bot commands must initiate a response within 3 seconds to comply with Discord's interaction limits. |
| NFR03 | Data Persistence & Integrity | The System must ensure reliable data persistance using a cloud-hosted PostgreSQL database (Neon Tech), maintaining referential integrity even during automated high-frequency updates from GitHub Actions. |
| NFR04 | Concurrency | The System must implement asynchronous database drivers (psycopg3) to ensure non-blocking execution of the event loop |
| NFR05 | Scalability | The System must be able to handle request peaks during global events (Internationals) without performance degradation |
| NFR06 | Security | The System must ensure that environment variables and database credentials are never exposed in logs or source code |
