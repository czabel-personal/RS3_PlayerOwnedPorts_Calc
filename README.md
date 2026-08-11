# 🚢 Player-Owned Ports: Ship Crew Optimizer

A lightweight, standalone desktop tool designed to optimize ship crew and captain assignments for RuneScape's **Player-Owned Ports** minigame. 

Built from scratch as a local application, this tool evaluates tens of thousands of potential crew loadouts in milliseconds to find optimal configurations for target **Morale**, **Combat**, and **Seafaring** thresholds—taking into account trait percentage multipliers, ship parts, building upgrades, and single-voyage consumables.

---

## 🌟 Acknowledgements & Inspiration

This project was built out of deep appreciation for the RuneScape community tools and guides that came before it:

* **[Tip.It](https://www.tip.it/):** Special thanks to the Tip.It team for their classic Ports calculator tool, which served as the primary inspiration for building a fast, offline local alternative.
* **Kags:** Sincere credit to **Kags** and his legendary *Player-Owned Ports Encyclopedia* for all the statistics, information, and examples.

---

## ✨ Features

* **Instant Math Engine:** Leverages Python combinatorial optimization (`itertools.combinations`) to evaluate all 53,000+ crew permutations in under 30ms.
* **Full Modifier Support:**
  * **Captain Traits:** Percentage and flat modifiers (e.g., *Leader*, *Tactician*, *Seafriend*).
  * **Ship Upgrades:** Flat bonuses to Deck, Hull, and Ram slots.
  * **Building Upgrades:** Global percentage multipliers.
  * **Consumable Buffs:** Single-voyage temporary flat or percentage boosts.
* **Native Desktop GUI:** Built with modern Tailwind CSS and served locally inside a native OS window via **PyWebView** (no browser tabs required).
* **Custom JSON Storage:** Store and manage your own custom captain roster, crew lists, ship setups, and voyage presets completely offline in human-readable JSON files.

---

## 🛠️ Tech Stack

* **Backend:** Python 3.10+, Flask
* **Desktop Wrapper:** PyWebView
* **Frontend:** HTML5, Tailwind CSS (via CDN), Vanilla JavaScript
* **Data Serialization:** Python `dataclasses` & native `json`

---

## 📂 Project Structure

ship_optimizer/
├── app.py              # Flask server & PyWebView desktop launcher
├── solver.py           # Optimization engine & combinatorial math
├── models.py           # Dataclasses for Units, Stats, Ship, & Voyage
├── PLAN.md             # Development roadmap & phased acceptance criteria
├── STATUS.md           # Test logs & current phase progress
├── data/
│   ├── roster.json     # Saved captains and crew members
│   └── ship.json       # Saved ship parts, building bonuses, & consumables
└── templates/
    └── index.html      # Local Tailwind CSS web interface

---

## 🚀 Getting Started

### Prerequisites

* **Python 3.10+** installed on your system.

### Installation

1. **Clone the repository:**
   git clone https://github.com/your-username/ports-crew-optimizer.git
   cd ports-crew-optimizer

2. **Install dependencies:**
   pip install flask pywebview

3. **Run the application:**
   python app.py
   *The application will automatically launch in its own standalone desktop window.*

---

## 📐 How the Calculations Work

Stat calculations follow the exact mechanics documented in Kags' POP guides:

1. **Base Sum:** 
   Base Sum = Captain Stats + Sum(Crew Stats) + Ship Upgrades + Flat Consumables

2. **Percentage Multipliers:**
   Final Stat = floor(Base Sum * (1 + Sum(Trait Multipliers) + Sum(Building Bonuses) + Sum(Consumable %)))

3. **Validation:**
   A combination is flagged as valid only if:
   * Final Morale >= Target Morale
   * Final Combat >= Target Combat
   * Final Seafaring >= Target Seafaring

---

## 📜 Development Workflow

This project is developed using a phased, test-driven approach. 
* Check [`PLAN.md`](PLAN.md) to see the roadmap of development phases.
* Check [`STATUS.md`](STATUS.md) to view current test logs and verification benchmarks.

---

## 📄 License

This project is open-source and intended for personal educational and gaming use. All RuneScape asset references and game mechanics belong to **Jagex Ltd.**