# Lab Sync 🔄

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/platform-windows-lightgrey)
![Status](https://img.shields.io/badge/status-active-success)
![License](https://img.shields.io/badge/license-MIT-green)

**A Desktop Dashboard for Git Automation and Lab Management**

![Main Dashboard](Docs/main_Screenshot.png)


---

## 📋 Overview
**Lab Sync** is a robust Python-based desktop application designed to streamline the management of multiple Git repositories across various workstations. It replaces complex command-line operations with a modern, user-friendly GUI.

The tool allows lab managers to monitor connection status, synchronize changes, and manage file systems across a hierarchical network of computers. It is specifically designed for testing environments like **QA Automation**, **Integration Labs**, and **Staging Environments**.

---

## ✨ Key Features
* **Visual Dashboard:** Real-time status indication for connected computers.
* **Git Automation:** One-click synchronization (Clone, Pull, Push) without using the CLI.
* **Hierarchical Management:** Organize computers by **Workspaces** and **Zones**.
* **Favorites Dashboard:** Pin frequently used zones for immediate access.
* **Global Quick Search:** Instantly locate any computer and navigate directly to its specific location using the top search bar.
* **Customizable Startup:** Configure your preferred default landing page to match your daily workflow.
* **Standalone Deployment:** Packaged as a portable `.exe` file using PyInstaller.
* **Persistence:** Automatic state saving using Python's `pickle` module.

---

## 🏗️ System Architecture
The application follows a modular architecture separating the Presentation Layer (GUI) from the Business Logic and Infrastructure.

```mermaid
graph TD
    %% הגדרות עיצוב
    classDef user fill:#ffcc80,stroke:#e65100,stroke-width:2px,color:black;
    classDef gui fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:black;
    classDef logic fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:black;
    classDef storage fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:black;
    classDef external fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:black;

    %% --- משתמש ---
    User((User / QA)):::user

    %% --- שכבת הממשק ---
    subgraph Frontend ["Frontend (GUI Layer)"]
        UI["Main Window & Tabs<br>(CustomTkinter)"]:::gui
        Popups["Dialogs & Alerts<br>(CTkMessagebox)"]:::gui
    end

    %% --- שכבת הלוגיקה והנתונים ---
    subgraph Backend ["Backend & Logic Layer"]
        Manager["DataManager / Controller"]:::logic
        
        subgraph Models ["Data Models (In-Memory)"]
            Root[SystemRoot]:::logic
            WS[WorkSpaces]:::logic
            Zn[Zones]:::logic
            PC[Computers]:::logic
        end
    end

    %% --- שכבת האחסון ---
    subgraph Persistence ["Storage Layer"]
        PKL[("data.pkl File")]:::storage
    end

    %% --- מערכות חיצוניות ---
    subgraph Integrations ["External Systems"]
        Git["Git Engine<br>(GitPython)"]:::external
        OS["File System & CMD<br>(os / subprocess)"]:::external
        SSH["Remote Connection<br>(paramiko)"]:::external
    end

    %% --- החיבורים (Flow) ---
    
    %% משתמש לממשק
    User -->|Clicks / Inputs| UI
    
    %% ממשק ללוגיקה
    UI -->|Triggers Action| Manager
    Manager -->|Updates UI| UI
    
    %% לוגיקה למודלים
    Manager -->|Reads/Writes| Root
    Root --- WS --- Zn --- PC
    
    %% לוגיקה לאחסון
    Manager -->|Load on Startup| PKL
    Manager -->|Save State| PKL

    %% לוגיקה למערכות חיצוניות
    Manager -->|Sync / Clone| Git
    Manager -->|Copy / Check Paths| OS
    Manager -->|Connect Remote| SSH
```

---

## 🏛️ Data Model Architecture
The system uses a hierarchical data structure to organize lab resources. The **Settings** module manages global configurations and favorites, while the **Workspace** tree manages the physical entities.

```mermaid
classDiagram
    direction TB

    %% --- הגדרת סגנונות וצבעים ---
    classDef rootStyle fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:black;
    classDef settingsStyle fill:#ffe0b2,stroke:#f57c00,stroke-width:2px,color:black;
    classDef wsStyle fill:#bbdefb,stroke:#1976d2,stroke-width:2px,color:black;
    classDef zoneStyle fill:#b2ebf2,stroke:#0097a7,stroke-width:2px,color:black;
    classDef pcStyle fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:black;

    %% --- השורש: מבנה הנתונים הראשי ---
    class SystemRoot:::rootStyle {
        <<pklDict>>
        +Settings settings
        +dict data (WorkSpaces)
    }

    %% --- מחלקת הגדרות (יחיד) ---
    class Settings:::settingsStyle {
        +String startHomePage
        +String theme
        +String dataPath
        +dict favorites
        +addFav(Zone_obj)
        +removeFav(Zone_obj)
    }

    %% --- מחלקת העל: WorkSpace ---
    class WorkSpace:::wsStyle {
        +String WorkSpace_name
        +dict Zones
        +addZone(Zone_obj)
        +removeZone(Zone_obj)
        +get_Zone_by_name(name)
    }

    %% --- מחלקת ביניים: Zone ---
    class Zone:::zoneStyle {
        +String Zone_name
        +boolean isFav
        +String repoPath
        +dict computers
        +addComputer(Computer_obj)
        +removeComputer(Computer_obj)
        +editRepoPath(path)
    }

    %% --- האובייקט הסופי: Computer ---
    class Computer:::pcStyle {
        +String pc_name
        +String host_name
        +String user_name
        +String password
        +dict pathFiles
        +boolean isChecked
        +addPathFile(input, output, type)
        +pathfilesLens()
    }

    %% --- הקשרים המדויקים (Multiplicity) ---
    
    %% ה-Root מכיל בדיוק Settings אחד (1 בצד ימין)
    SystemRoot "1" *-- "1" Settings : contains

    %% ה-Root מכיל הרבה WorkSpaces
    SystemRoot "1" *-- "0..*" WorkSpace : contains ('data')

    %% היררכיית ההכלה
    WorkSpace "1" *-- "0..*" Zone : contains
    Zone "1" *-- "0..*" Computer : contains

    %% הצבעה למועדפים
    Settings --> "0..*" Zone : references
```
---

## 🚀 How to Use

1.  **Create Structure:** Start by creating a `Workspace` (e.g., "Building A") and adding `Zones` (e.g., "QA Automation").
2.  **Add Computers:** Inside a zone, add computers by providing their IP/Hostname and credentials.
3.  **Search & Navigate:** Use the **Global Search** bar to instantly jump to any machine.
4.  **Sync:** Select a computer (or a whole zone) and click "Sync Git" to update repositories instantly.

## 🔮 Future Roadmap
- [ ] Add support for Linux/Mac remote machines.
- [ ] Implement SSH Key authentication management.
- [ ] Add "Dark/Light" mode toggle in real-time.
- [ ] Cloud backup integration.

---

## 📷 Gallery / Screenshots

![Search Function](Docs/search_Screenshot.png)
![Favorites Screen](Docs/favs_Screenshot.png)

| Zone Management | Settings & Favorites | Git Operations |
|:---:|:---:|:---:|
| ![Zone View](images/zone_view.png) | ![Settings](images/settingsss.png) | ![Git Sync](images/git_sync.png) |
| *View and manage lab zones* | *Favorites & Startup Config* | *Live synchronization status* |


---
**Author:** [Your Name]
