# homBrowser - Fingerprint Browser Control System

HomBrowser is a full-stack application designed to manage and control instances of `fingerprint-chromium`, a privacy-focused browser kernel. It allows users to create and manage multiple browser profiles with unique fingerprint configurations, proxy settings, and more, all through a web-based interface.

This system is built with a decoupled frontend and backend architecture.

## Features (Implemented & Planned)

*   **Profile Management:** Create, edit, delete, and launch browser profiles.
*   **Advanced Fingerprint Configuration:** Customize User-Agent, Sec-CH-UA, WebGL, AudioContext, ClientRects, Speech Voices, CPU cores, memory, timezone, language, and more per profile.
*   **Proxy Management:** Manage a list of proxies (HTTP, SOCKS5) and assign them to profiles.
*   **Group Management:** Organize profiles into groups for easier management.
*   **Plugin Management (Placeholder):** UI for managing browser plugins/extensions (backend not yet implemented).
*   **Batch Operations:** Perform actions like delete or assign group on multiple profiles at once.
*   **Dynamic Command Generation:** Backend generates the necessary command-line arguments to launch `fingerprint-chromium` with the specified profile configurations.

## Tech Stack

*   **Backend:**
    *   Framework: FastAPI
    *   Database: SQLite
    *   ORM: SQLAlchemy
    *   Schema Validation: Pydantic
    *   Testing: Pytest
*   **Frontend:**
    *   Framework: Vue 3
    *   Build Tool: Vite
    *   Language: TypeScript
    *   Routing: Vue Router
    *   State Management: Vue Reactivity (Composition API)
*   **Browser Kernel:** `fingerprint-chromium` (external dependency)

## Project Structure

```
.
├── backend/        # FastAPI backend application
│   ├── app/          # Core application logic, models, schemas, crud, api
│   ├── tests/        # Backend tests
│   ├── main.py       # Main FastAPI application entry point
│   └── requirements.txt
├── frontend/       # Vue 3 frontend application
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── views/
│   │   ├── router/
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── DEVELOPMENT_BLUEPRINT.md # System design and specifications
└── README.md                # This file
```

## Setup and Running the Application

### Prerequisites

*   Python 3.8+
*   Node.js 16+ and npm (or yarn/pnpm)
*   A `fingerprint-chromium` executable.

### 1. `fingerprint-chromium` Executable

The application needs to know the path to your `fingerprint-chromium` executable.

*   **Recommended:** Set the `FINGERPRINT_CHROMIUM_PATH` environment variable to the absolute path of your `fingerprint-chromium` executable.
    *   Example (Linux/macOS): `export FINGERPRINT_CHROMIUM_PATH="/opt/fingerprint-chromium/chrome"`
    *   Example (Windows): `set FINGERPRINT_CHROMIUM_PATH="C:\path\to\fingerprint-chromium\chrome.exe"`
*   **Alternative (Development):** If the environment variable is not set, the backend will look for the executable at a default path `/path/to/fingerprint-chromium` (defined in `backend/app/crud/crud_profile.py`) or a development fallback path relative to where the backend is run (e.g., `fingerprint-chromium/chrome` in the project root if backend is run from `backend/`). It's highly recommended to use the environment variable for reliability.

Download `fingerprint-chromium` from its official source and place it in a known location on your system.

### 2. Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment
# On Windows:
# venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the backend server (development mode with auto-reload)
# Ensure your FINGERPRINT_CHROMIUM_PATH is set, or update the default in crud_profile.py
# Note: The --app-dir app flag assumes uvicorn is run from the 'backend' directory.
# If you run from 'backend/app', then it would be 'uvicorn main:app --reload ...'
uvicorn main:app --reload --app-dir . --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`.
API documentation (Swagger UI) will be at `http://localhost:8000/docs` (or `/api/v1/docs` if `openapi_url` in `main.py` is set to `/api/v1/openapi.json` and default docs path is used).
The current `main.py` sets `openapi_url="/api/v1/openapi.json"`, so the direct schema is there. FastAPI default docs paths are `/docs` and `/redoc`.

### 3. Frontend Setup

```bash
# Open a new terminal
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install
# or yarn install / pnpm install

# Run the frontend development server
npm run dev
# or yarn dev / pnpm dev
```

The frontend application will typically be available at `http://localhost:5173` (Vite's default port, check your terminal output).

### 4. User Data Directory

Browser profile data (cookies, cache, etc.) will be stored in subdirectories under `backend/hom_browser_data/user_data_dirs/` by default (relative to where the backend is run if the default path in `crud_profile.py` is used). This path can be configured via the `HOM_BROWSER_USER_DATA_ROOT` environment variable if needed.

## Basic Usage Guide

1.  **Start Backend & Frontend:** Follow the setup instructions above to get both servers running.
2.  **Access the Application:** Open your web browser and navigate to the frontend URL (e.g., `http://localhost:5173`).
3.  **Manage Proxies (Optional):** Navigate to "Proxy Management" to add any proxy servers you intend to use.
4.  **Manage Groups (Optional):** Navigate to "Group Management" to create groups for organizing profiles.
5.  **Create Browser Profiles:**
    *   Navigate to "Browser Profiles".
    *   Click "+ Create Browser".
    *   Fill in the profile details in the modal:
        *   **Basic Settings:** Name, Group, Operating System, Browser Version, Cookies, Notes.
        *   **Proxy Settings:** Choose 'System Default', 'No Proxy', or 'Custom Proxy' (and select an existing proxy).
        *   **Advanced Settings:** Configure User-Agent, Sec-CH-UA, WebGL, AudioContext, ClientRects, Speech Voices, CPU, Memory, Timezone, Language, Hardware Acceleration, etc., as needed.
    *   Click "Create Profile".
6.  **Launch a Profile:**
    *   In the "Browser Profiles" list, find the profile you want to launch.
    *   Click the "Launch" button for that profile.
    *   A modal will appear showing the **generated command-line string**.
    *   **Important:** Currently, the system *generates* the command but does not automatically execute it. You need to copy this command and run it in your system's terminal or command prompt where the `fingerprint-chromium` executable is accessible and correctly configured via `FINGERPRINT_CHROMIUM_PATH` or default paths.
7.  **Edit/Delete Profiles:** Use the "Edit" and "Delete" buttons in the profile list.
8.  **Batch Operations:** Select multiple profiles using checkboxes and use the "Batch Delete Selected" or "Batch Assign Group" buttons.

## Development

*   The `DEVELOPMENT_BLUEPRINT.md` file contains the detailed design and specifications for the system.
*   Backend code is in the `backend/` directory.
*   Frontend code is in the `frontend/` directory.

## Future Enhancements (Potential)

*   Full implementation of Plugin Management.
*   Direct browser launching and process management from the backend.
*   Automated testing and injection of cookies/scripts into launched profiles.
*   User authentication and authorization.
*   More sophisticated fingerprint randomization and generation options.
*   Cloud synchronization of profiles.
*   Persistent storage for application settings (e.g., default `fingerprint-chromium` path).
```
