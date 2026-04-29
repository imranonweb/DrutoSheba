# 🚑 DrutoSheba - Emergency Path Finder

An intelligent emergency route optimization system that simulates how emergency services (ambulance, fire, police) find the fastest path using advanced pathfinding algorithms and real-time visualization. 

---

## 📌 Overview

**DrutoSheba** is a Python-based interactive simulation that demonstrates how emergency vehicles can efficiently navigate through traffic-heavy environments using algorithmic intelligence.

The system uses:

* Grid-based map representation
* Traffic-aware cost system
* Multiple emergency scenarios
* Real-time visualization using Pygame

---

## 🎥 Project Demo

[![Watch Demo](https://img.youtube.com/vi/uR9CZ7iDfNc/0.jpg)](https://youtu.be/uR9CZ7iDfNc)

---

## ✨ Key Features

* 🚀 A* pathfinding algorithm (optimal route)
* BFS DFS A* Algorithm Comparison
* Agent Auto Mode Supported
* 🚦 Traffic-aware weighted path calculation
* 🧱 Obstacle handling (blocked roads)
* 🎮 Interactive grid-based UI
* 🚑 Multiple emergency scenarios:

  * Medical Emergency
  * Fire Rescue
  * Police Response
* 🔄 Dynamic path visualization (visited nodes + final path)
* 🚗 Animated agent (ambulance/police/fire unit movement)
* 🎯 Scenario-based dispatch & success messages
* 🖥️ Executable build support (`.exe`)

---

## 🛠️ Tech Stack

| Category   | Technology                 |
| ---------- | -------------------------- |
| Language   | Python                     |
| Library    | pygame / pygame-ce         |
| Concepts   | Graph Theory, Pathfinding  |
| Build Tool | PyInstaller (.exe support) |

---

## 📂 Project Structure

```bash
PythonProject/
│
├── main.py              # Entry point + UI + simulation control
├── agent.py             # Emergency vehicle logic (movement, animation)
├── algorithms.py        # Pathfinding algorithms (A*, etc.)
├── grid.py              # Grid system, cell types, map logic
│
├── requirements.txt     # Dependencies
├── main.spec            # PyInstaller build config
│
├── build/               # Build artifacts
├── dist/
│   └── main.exe         # Executable version
│
└── README.md
```

---

## ⚙️ Installation Guide

### 🔹 1. Clone Repository

```bash
git clone https://github.com/your-username/drutosheba.git
cd drutosheba
```

---

### 🔹 2. Install Python

* Recommended: **Python 3.11**
* OR Latest Python → use `pygame-ce`

Check version:

```bash
python --version
```

---

### 🔹 3. Install Dependencies

#### Option A (Python 3.11)

```bash
pip install pygame
```

#### Option B (Latest Python)

```bash
pip install pygame-ce
```

Or install all:

```bash
pip install -r requirements.txt
```

---

### 🔹 4. Run the Project

```bash
python main.py
```

---

## 🎮 How to Use

1. Launch the application
2. Choose scenario (Ambulance / Fire / Police)
3. Select:

   * Start point
   * Destination
4. Add:

   * Obstacles (blocked roads)
   * Traffic zones (higher cost)
5. Run simulation
6. Watch:

   * Nodes being explored
   * Final optimal path
   * Agent moving step-by-step

---

## ⚙️ System Workflow

1. Grid map is initialized
2. User inputs start & goal
3. Selected algorithm runs (A*)
4. Nodes are explored (visualized)
5. Cost calculation includes:

   * Distance
   * Traffic weight
6. Optimal path is computed
7. Agent follows path in real-time

---

## 🎯 Scenarios Implemented

* 🚑 **Medical Emergency** → Ambulance → Patient
* 🔥 **Fire Rescue** → Firefighters → Fire location
* 🚓 **Police Response** → Police → Incident

Each scenario includes:

* Custom labels
* Messages
* UI accents

---

## 📊 Complexity Analysis

| Metric | Value      |
| ------ | ---------- |
| Time   | O(E log V) |
| Space  | O(V)       |

---

## 🧪 Build Executable (.exe)

You already included PyInstaller config.

To build:

```bash
pip install pyinstaller
pyinstaller main.spec
```

Output:

```
dist/main.exe
```

---

## 🚀 Future Improvements

* 🔁 Add Dijkstra, Bellman Ford comparison
* 🗺️ Real-world map integration (Google Maps API)
* 🤖 AI-based traffic prediction
* 🌐 Web version (React + FastAPI)
* 📱 Mobile version

---

## 🤝 Contributing

1. Fork repository
2. Create a branch
3. Make changes
4. Submit pull request

---

## 📜 License

This project is licensed under the MIT License.
You are free to use and modify this project with proper credit.

---

## 👨‍💻 Author

**Md. Al Imran Emon**

* 💻 Competitive Programmer
* 🎯 Aspiring Software Engineer

---

## ⭐ Support

If you like this project:

* ⭐ Star the repository
* 🍴 Fork it
* 📢 Share it

---

## 💡 Real-World Impact

This project demonstrates how algorithmic solutions can improve emergency response systems — especially in traffic-heavy regions where every second matters.

---
