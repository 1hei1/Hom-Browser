# DEVELOPMENT BLUEPRINT for homBrowser

## 1. Tech Stack Decision

### Backend Framework

**Choice:** FastAPI

**Justification:**

*   **Performance:** FastAPI is built on top of Starlette and Pydantic, offering very high performance, comparable to Node.js and Go, which is beneficial for a system that might handle many concurrent requests for browser profile management and launching.
*   **Asynchronous Support:** Its native support for asynchronous programming (async/await) is ideal for I/O-bound operations such as managing external processes (fingerprint-chromium) and handling API requests efficiently without blocking.
*   **Ease of Use & Development Speed:** FastAPI's design promotes rapid development. Automatic data validation, serialization, and documentation (via OpenAPI and Swagger UI) significantly reduce boilerplate code and development time.
*   **Data Validation:** Pydantic integration provides robust data validation, which is crucial for handling complex browser profile configurations and API inputs, ensuring data integrity.
*   **Python Ecosystem:** Being a Python framework, it allows seamless integration with other Python libraries and the existing `fingerprint-chromium` ecosystem if any Python-based tools are used for its control or scripting.
*   **Lightweight:** Compared to Django, FastAPI is more lightweight and less opinionated, providing flexibility while still offering powerful features. Flask is also lightweight but requires more extensions for features like data validation and async support, which FastAPI provides out-of-the-box.

### Frontend Framework

**Choice:** Vue 3 (Vite + TypeScript)

**Justification:**

*   **Reactivity System & Performance:** Vue 3's reactivity system is highly optimized and efficient. Its fine-grained reactivity and Composition API offer excellent performance and flexibility in managing complex state, which is expected in a feature-rich UI like a browser management system.
*   **Developer Experience & Learning Curve:** Vue is often cited for its gentle learning curve and excellent documentation. The Composition API, while powerful, can be adopted incrementally. Vite provides an extremely fast development server and optimized build process.
*   **TypeScript Support:** Vue 3 has excellent TypeScript support, which is crucial for building robust and maintainable applications, especially for a project with potentially complex data structures for browser profiles.
*   **Component-Based Architecture:** Vue's component-based architecture promotes reusability and modularity, making it easier to manage and scale the UI. The described UI (three-column layout, modals, data tables) lends itself well to this approach.
*   **Ecosystem and Community:** Vue has a strong and growing ecosystem with many available libraries and tools. While React's ecosystem is larger, Vue's is mature enough for this type of application and often more focused.
*   **Progressive Framework:** Vue can be adopted incrementally. While we are building a new system, its progressive nature means we can easily integrate it with other technologies if needed in the future.
*   **Suitability for Admin Panels:** Vue, with UI libraries like Element Plus or Quasar, is well-suited for building data-rich admin-style interfaces like the one described.

## 2. System Architecture

The system will adopt a decoupled frontend-backend architecture. The frontend will be a Single Page Application (SPA) interacting with the backend via RESTful APIs. The backend will manage browser profiles, groups, proxies, plugins, and crucially, generate command-line arguments to launch and control `fingerprint-chromium` instances.

```mermaid
graph TD
    A[Frontend UI (Vue 3)] -- API Requests (HTTPS) --> B{Management Backend (FastAPI)};
    B -- Manages/Stores --> C[SQLite Database];
    B -- Profile Data --> D[Command-Line Generator Module];
    D -- Generates Args --> E{fingerprint-chromium Kernel};
    E -- Launches --> F[Browser Instance];

    subgraph User Interaction
        A
    end

    subgraph Server-Side Logic
        B
        C
        D
    end

    subgraph Browser Kernel Interaction
        E
        F
    end
```

**Components:**

*   **Frontend UI (Vue 3):** The user interface built with Vue 3. It allows users to manage browser profiles, settings, and initiate browser launches.
*   **Management Backend (FastAPI):** The core server application built with FastAPI. It handles API requests, business logic, database interactions, and orchestrates browser launching.
*   **SQLite Database:** Stores all persistent data, including browser profiles, groups, proxy configurations, and plugin information.
*   **Command-Line Generator Module:** A critical component within the backend responsible for translating a browser profile's configuration (stored in the database) into the appropriate command-line arguments required to launch a `fingerprint-chromium` instance with the desired fingerprint and settings.
*   **fingerprint-chromium Kernel:** The pre-compiled `fingerprint-chromium` executable. The backend launches this executable with the generated command-line arguments.
*   **Browser Instance:** An individual, sandboxed browser window launched with specific fingerprint configurations.

## 3. UI/UX Functional Specification

### 3.1. Overall Layout

The application will feature a classic three-column后台管理 (backend management) layout:

*   **Left Column (Navigation Menu):**
    *   Fixed width.
    *   Vertical orientation.
    *   Top: "hom浏览器" Logo.
    *   Bottom: List of collapsible navigation menu items.
*   **Center Column (Main Content Area):**
    *   Variable width, occupying the remaining space.
    *   Displays content based on the selected navigation item.
    *   **Top Bar:** Contains Breadcrumb navigation, Notification icons, and User Avatar/Profile menu.
    *   **Bottom Bar:** Contains pagination controls (where applicable) and Copyright information (e.g., "© 2024 homBrowser").
*   **Right Column:** Not explicitly defined in the initial requirements, so it will be omitted for now. If needed for contextual information or actions in the future, it can be added.

### 3.2. Navigation Menu Items

The left-hand navigation menu will have the following structure:

*   **浏览器 (Browser)** (Main Menu Item)
    *   列表 (List) (Sub-menu Item) - Navigates to `/profiles`
*   **分组管理 (Group Management)** (Main Menu Item) - Navigates to `/groups`
*   **插件管理 (Plugin Management)** (Main Menu Item) - Navigates to `/plugins`
*   **代理管理 (Proxy Management)** (Main Menu Item) - Navigates to `/proxies`
*   **API列表 (API List)** (Main Menu Item) - Navigates to `/api-docs` (links to Swagger UI/OpenAPI documentation)

### 3.3. Page One: Browser List (`/profiles`)

This page displays a list of all configured browser profiles.

*   **Top Operations Area:**
    *   **"+ 创建浏览器" (+ Create Browser) Button:** Primary action button (e.g., blue color).
    *   **"批量操作" (Batch Actions) Dropdown Button:** Allows actions on multiple selected profiles (e.g., Batch Delete, Batch Assign Group).
    *   **"同步" (Sync) Button:** Refreshes the browser list or syncs status (specific functionality TBD, could be for future features like cloud sync).
    *   **分组筛选 (Group Filter) Dropdown:** Filters the list by selected group.
    *   **名称搜索 (Name Search) Input Box:** Allows searching for profiles by name.
*   **Data Table Columns:**
    1.  **复选框 (Checkbox):** For selecting multiple profiles for batch operations.
    2.  **序号 (ID/Serial No.):** Unique identifier or row number.
    3.  **名称 (Name):** The custom name of the browser profile.
    4.  **分组 (Group):** The group assigned to the profile.
    5.  **代理 (Proxy):** The proxy configuration used by the profile (e.g., proxy address or "None").
    6.  **备注 (Notes):** User-added notes for the profile.
    7.  **最后启动时间 (Last Launch Time):** Timestamp of the last time the profile was launched.
    8.  **启动 (Launch) Button:** A button to launch this specific browser profile.
    9.  **操作 (Actions) Column:** A group of buttons/icons, typically including:
        *   "编辑" (Edit) Button: Opens the Create/Edit Browser modal for this profile.
        *   "删除" (Delete) Button: Deletes the profile after confirmation.

### 3.4. Core Function: Create/Edit Browser (Modal/Dialog)

This is a modal dialog that appears when creating a new browser profile or editing an existing one. It will be a vertically scrollable long form.

*   **基础设置区 (Basic Settings Area):**
    *   **名称 (Name):** Text input field. (Required)
    *   **选择分组 (Select Group):** Dropdown select box (loads from Groups data).
    *   **操作系统 (Operating System):** Button group for selection. Options: `Win 7`, `Win 8`, `Win 10`, `Win 11`, `Linux`, `MacOS`. (Corresponds to `--fingerprint-platform` and potentially `--fingerprint-platform-version`).
    *   **浏览器版本 (Browser Version):** Text input field (e.g., "119.0.6045.123"). (Corresponds to `--fingerprint-brand-version`).
    *   **代理设置 (Proxy Settings):** Button group for selection. Options: `默认 (Default)`, `不使用 (No Proxy)`, `自定义 (Custom)`.
        *   If `自定义 (Custom)` is selected, fields for proxy details appear (e.g., Host, Port, Type (HTTP, SOCKS5), Username, Password).
    *   **Cookie:** Multi-line text area for pasting Cookie data.

*   **高级设置区 (Advanced Settings Area - Fingerprint Configuration):**
    Each item typically follows the pattern: `[Label] - [Mode Button Group: Default/Custom/Random] - [Input Control (if Custom)]`

    *   **启动主页 (Startup Homepage):** Text input field (e.g., `https://www.google.com`).
    *   **User-Agent:** Text input field.
    *   **Sec-CH-UA:** Text input field.
    *   **WebGL图像 (WebGL Image):** (Details on how this is customized, e.g., noise level, specific image hash - needs mapping to `fingerprint-chromium` capabilities).
    *   **WebGL元数据 (WebGL Metadata):**
        *   **厂商 (Vendor):** Dropdown select box (e.g., Google Inc., NVIDIA Corporation, Intel Inc.).
        *   **渲染器 (Renderer):** Dropdown select box (e.g., ANGLE (Intel HD Graphics 4000 Direct3D11 vs_5_0 ps_5_0), Mesa DRI Intel(R) HD Graphics 4000 (Ivy Bridge Desktop)).
    *   **AudioContext:** (Mode: Default/Noise/Off - needs mapping to `fingerprint-chromium` capabilities).
    *   **ClientRects:** (Mode: Default/Noise/Off - needs mapping to `fingerprint-chromium` capabilities).
    *   **Speech Voices:** (Mode: Default/Custom - if Custom, allow specifying voice attributes - needs mapping).
    *   **CPU核心数 (CPU Cores / `hardwareConcurrency`):** Dropdown select box (e.g., 2, 4, 8, 12, 16, Random).
    *   **内存 (Memory / `deviceMemory`):** Dropdown select box (e.g., 2GB, 4GB, 8GB, 16GB, Random).
    *   **设备名称 (Device Name):** Text input field (e.g., for mobile emulation or specific device profiles).
    *   **MAC地址 (MAC Address):** Text input field (Note: `fingerprint-chromium` docs don't explicitly list MAC address spoofing. This might be a feature request for the kernel or handled externally if possible. For now, we'll include it in the UI specs).

    *   **开关项列表 (Toggle Switches):**
        *   **Do Not Track:** Toggle switch (On/Off).
        *   **SSL (Cipher Suites / TLS):** Toggle switch (On/Off for specific strictness or profile - needs mapping).
        *   **端口扫描保护 (Port Scan Protection):** Toggle switch (On/Off, likely relates to `--disable-non-proxied-udp` or similar network privacy features).
        *   **硬件加速 (Hardware Acceleration):** Toggle switch (On/Off).

    *   **扫描端口白名单 (Scan Port Whitelist):** Text input field, for use if Port Scan Protection is active (comma-separated ports).
    *   **启动参数 (Launch Parameters):** Text input field for additional, custom command-line arguments for `fingerprint-chromium`.

*   **底部操作区 (Bottom Action Area):**
    *   **"取消" (Cancel) Button:** Closes the modal without saving changes.
    *   **"确定" (OK/Save) Button:** Primary action button. Saves the profile and closes the modal.

### 3.5. Page Two: Group Management (`/groups`)

Manages collections of browser profiles.

*   **Top Operations Area:**
    *   **"+ 创建分组" (+ Create Group) Button.**
    *   **名称搜索 (Name Search) Input Box.**
*   **Data Table Columns:**
    1.  **序号 (ID/Serial No.).**
    2.  **分组名称 (Group Name).**
    3.  **分组浏览器数 (Profile Count in Group).**
    4.  **创建时间 (Creation Time).**
    5.  **操作 (Actions):** Edit, Delete.

### 3.6. Page Three: Plugin Management (`/plugins`)

Manages browser plugins/extensions.

*   **Initial State:** If no plugins are installed/managed, display: "暂无数据" (No Data Available).
*   **Top Operations Area:**
    *   **"安装插件" (Install Plugin) Button:** Opens a modal/form to add a plugin (e.g., from a local file .crx, or from a URL - details TBD based on `fingerprint-chromium` capabilities for plugin installation).
*   **Data Table Columns (if data exists):**
    1.  **序号 (ID/Serial No.).**
    2.  **插件名称 (Plugin Name).**
    3.  **版本 (Version).**
    4.  **状态 (Status):** Enabled/Disabled.
    5.  **操作 (Actions):** Enable/Disable, Delete.

### 3.7. Page Four: Proxy Management (`/proxies`)

Manages proxy server configurations.

*   **Top Operations Area:**
    *   **"+ 添加代理" (+ Add Proxy) Button.**
    *   **批量操作 (Batch Actions) Dropdown:** (e.g., Batch Delete, Batch Test Proxies).
    *   **代理信息搜索 (Proxy Info Search) Input Box.**
*   **Data Table Columns:**
    1.  **复选框 (Checkbox).**
    2.  **序号 (ID/Serial No.).**
    3.  **代理信息 (Proxy Information):** (e.g., `type://host:port`, `socks5://127.0.0.1:1080`).
    4.  **使用次数 (Usage Count):** Number of profiles currently using this proxy.
    5.  **操作 (Actions):** Edit, Delete, **分配 (Assign)** (potentially to assign this proxy to multiple profiles or a group).

## 4. Backend Design

### 4.1. Database Schema (SQLite DDL)

```sql
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS proxies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    type TEXT NOT NULL, -- 'HTTP', 'SOCKS5'
    host TEXT NOT NULL,
    port INTEGER NOT NULL,
    username TEXT,
    password TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plugins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    version TEXT,
    source_path TEXT, -- Path to .crx file or identifier
    enabled BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    group_id INTEGER,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_launch_time DATETIME,

    -- Basic Settings
    os_platform TEXT, -- 'windows', 'linux', 'macos'
    os_version TEXT, -- e.g., '10', '11', '15.2.0'
    browser_version TEXT, -- e.g., '119.0.6045.123'
    proxy_config_type TEXT DEFAULT 'default', -- 'default', 'none', 'custom'
    custom_proxy_id INTEGER, -- FK to proxies table if proxy_config_type is 'custom'
    cookies TEXT,

    -- Advanced Settings (Fingerprint Configuration)
    startup_homepage TEXT,
    user_agent TEXT,
    sec_ch_ua TEXT,
    webgl_image_mode TEXT DEFAULT 'default', -- 'default', 'custom', 'random'
    -- webgl_image_custom_hash TEXT, -- If mode is 'custom'
    webgl_vendor TEXT,
    webgl_renderer TEXT,
    audiocontext_mode TEXT DEFAULT 'default', -- 'default', 'noise', 'off'
    clientrects_mode TEXT DEFAULT 'default', -- 'default', 'noise', 'off'
    speech_voices_mode TEXT DEFAULT 'default', -- 'default', 'custom'
    -- speech_voices_custom_data TEXT, -- If mode is 'custom'
    cpu_cores INTEGER,
    memory_gb INTEGER, -- Storing as GB, e.g., 2, 4, 8
    device_name TEXT,
    mac_address TEXT, -- As discussed, kernel support for this is uncertain

    -- Switches
    do_not_track BOOLEAN DEFAULT FALSE,
    ssl_cipher_suites_mode TEXT DEFAULT 'default', -- 'default', 'strict', 'custom'
    -- ssl_custom_suites TEXT, -- If mode is 'custom'
    port_scan_protection BOOLEAN DEFAULT TRUE,
    hardware_acceleration BOOLEAN DEFAULT TRUE,
    scan_port_whitelist TEXT, -- Comma-separated ports

    -- Misc
    custom_launch_parameters TEXT, -- Additional raw parameters
    fingerprint_seed INTEGER, -- Seed for randomization, can be auto-generated or user-defined

    FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE SET NULL,
    FOREIGN KEY (custom_proxy_id) REFERENCES proxies (id) ON DELETE SET NULL
);
```

**Notes on `profiles` table fields:**

*   Many fields correspond to UI options. `*_mode` fields will store if the setting is 'default', 'custom', or 'random'.
*   For settings like WebGL Image, AudioContext, ClientRects, if `fingerprint-chromium` uses specific values for 'noise' or 'random', these might be generated at launch time rather than stored, unless specific seeds are needed.
*   `fingerprint_seed`: This is a crucial field. If a user selects 'random' for multiple fingerprint settings, this seed can be used to derive those random values consistently for that profile. It can be auto-generated if not provided.

### 4.2. Core Logic - Command-Line Generator

This function is central to the backend's operation. It takes a profile object (retrieved from the database) and constructs the command-line string to launch `fingerprint-chromium`.

**Function Signature (Conceptual Python):**

```python
def generate_chromium_command(profile: dict, chromium_executable_path: str) -> str:
    """
    Generates the command string to launch fingerprint-chromium with a given profile.

    Args:
        profile (dict): A dictionary representing the browser profile's configuration,
                        fetched from the database (ideally a Pydantic model).
        chromium_executable_path (str): Path to the fingerprint-chromium executable.

    Returns:
        str: The fully constructed command-line string.
    """
    args = [chromium_executable_path]

    # --- Fingerprint Seed (Essential for many randomizations) ---
    if profile.get('fingerprint_seed'):
        args.append(f"--fingerprint={profile['fingerprint_seed']}")

    # --- Basic Settings ---
    if profile.get('os_platform'):
        args.append(f"--fingerprint-platform={profile['os_platform']}")

    # os_version is more complex and might need mapping to specific kernel versions
    # or might be part of the UA string if not a direct kernel parameter.
    # For now, we assume it's used in UA construction or future enhancements.
    # if profile.get('os_version'):
    #     args.append(f"--fingerprint-platform-version={profile['os_version']}") # Check if this param exists

    if profile.get('browser_version'):
        args.append(f"--fingerprint-brand-version={profile['browser_version']}")
        # Assuming default brand is Chrome. If other brands are selectable in UI:
        # if profile.get('browser_brand') and profile.get('browser_brand') != 'Chrome':
        #     args.append(f"--fingerprint-brand={profile['browser_brand']}")

    # --- Proxy Settings ---
    if profile.get('proxy_config_type') == 'custom' and profile.get('custom_proxy'): # custom_proxy would be a dict of proxy details
        proxy = profile['custom_proxy']
        proxy_type = proxy['type'].lower()
        proxy_server_val = f"{proxy_type}://{proxy['host']}:{proxy['port']}"
        # fingerprint-chromium docs state --proxy-server doesn't support auth.
        # If auth is needed, it must be handled by an intermediate proxy or if the kernel supports it via other means.
        args.append(f'--proxy-server="{proxy_server_val}"')
    elif profile.get('proxy_config_type') == 'none':
        # Chromium typically uses --no-proxy-server, but fingerprint-chromium docs don't list it.
        # It might be implicit if --proxy-server is not provided. This needs testing.
        # For now, we'll assume not adding --proxy-server means no proxy.
        pass

    # --- Advanced Settings (Fingerprint) ---
    # User-Agent and Sec-CH-UA are often derived from platform, brand, and version.
    # Direct override flags are not explicitly in the provided docs, but if they exist, they would be added here.
    # if profile.get('user_agent_mode') == 'custom' and profile.get('user_agent'):
    #    args.append(f"--user-agent='{profile['user_agent']}'")
    # if profile.get('sec_ch_ua_mode') == 'custom' and profile.get('sec_ch_ua'):
    #    args.append(f"--sec-ch-ua='{profile['sec_ch_ua']}'")

    # WebGL Vendor and Renderer: The docs state WebGL metadata modification (vendor/renderer) is currently Linux-only.
    # The exact flags are not provided, need to be found or might be part of a larger --fingerprint-webgl flag.
    # if profile.get('os_platform') == 'linux':
    #     if profile.get('webgl_vendor') and profile.get('webgl_image_mode') == 'custom':
    #         args.append(f"--webgl-vendor-override='{profile['webgl_vendor']}'") # Hypothetical
    #     if profile.get('webgl_renderer') and profile.get('webgl_image_mode') == 'custom':
    #         args.append(f"--webgl-renderer-override='{profile['webgl_renderer']}'") # Hypothetical

    # AudioContext, ClientRects, Speech Voices: These are likely controlled by the main --fingerprint seed.
    # If specific flags exist for 'noise' or 'off' modes, they would be added here.
    # Example: if profile.get('audiocontext_mode') == 'noise': args.append('--audiocontext-noise') # Hypothetical

    if profile.get('cpu_cores'):
        args.append(f"--fingerprint-hardware-concurrency={profile['cpu_cores']}")

    # Memory (`deviceMemory`): Not directly settable via a documented flag. Usually derived by the browser.
    # The value in DB is for potential future use or if a hidden flag exists.

    # Device Name, MAC Address: No documented flags. These are likely for user reference or external tools.

    # --- Switches ---
    # Do Not Track: Typically handled by browser settings, not a command-line flag for Chromium itself,
    # but might be a feature of fingerprint-chromium. If so, flag needed.
    # if profile.get('do_not_track'):
    #     args.append('--enable-do-not-track') # Hypothetical

    # SSL Cipher Suites: Complex. Usually not controlled at this granularity via command line for standard Chromium.
    # This might be a misinterpretation of 'SSL' switch, or it refers to a very specific fingerprinting aspect.

    if profile.get('port_scan_protection', True): # Default to True if not specified
        args.append('--disable-non-proxied-udp') # As per docs, this enables protection
    # else: # If explicitly set to False, we might need an enabling flag if one exists, or do nothing if default is less restrictive.

    if profile.get('hardware_acceleration') is False:
        args.append('--disable-gpu') # Standard Chromium flag
    elif profile.get('hardware_acceleration') is True:
        args.append('--enable-gpu') # Or ensure no --disable-gpu is present

    # Scan Port Whitelist: This is not a browser feature. It would be an external firewall/proxy setting.

    # --- Language and Timezone ---
    if profile.get('language'): # Should be a valid lang code like 'en-US'
        args.append(f"--lang={profile['language']}")
    if profile.get('accept_language'): # Should be a valid accept-language header string
        args.append(f"--accept-lang='{profile['accept_language']}'") # Quotes might be important
    if profile.get('timezone'): # Should be a valid Olson timezone ID like 'America/New_York'
        args.append(f"--timezone={profile['timezone']}")

    # --- User Data Directory (Isolation) ---
    # CRITICAL for profile isolation. Each profile should have its own data directory.
    # The actual path should be configurable and managed by the application.
    user_data_dir_base = "/path/to/hom_browser_profiles" # This should be a configurable base path
    user_data_dir = f"{user_data_dir_base}/profile_{profile['id']}"
    args.append(f'--user-data-dir="{user_data_dir}"')

    # --- Custom Launch Parameters from UI ---
    if profile.get('custom_launch_parameters'):
        # Simple split by space. For more complex needs, a proper shell-like parser might be better.
        args.extend(profile['custom_launch_parameters'].strip().split())

    # --- Startup Homepage (Positional Argument) ---
    # This must be the LAST argument if it's a URL to open, after all --flags.
    if profile.get('startup_homepage'):
        # Ensure it's not mistaken for a flag if it starts with --
        if not profile['startup_homepage'].startswith('-'):
            args.append(profile['startup_homepage'])

    # For execution with subprocess, it's best to return a list of arguments.
    # For display or manual execution, join them.
    # import shlex
    # command_string = ' '.join(shlex.quote(str(arg)) for arg in args)
    # return command_string
    return args # Return as a list for subprocess

```

**Key Considerations for Command-Line Generator:**

*   **Path to Executable:** The path to `fingerprint-chromium` must be configurable (e.g., via application settings or environment variable) and passed to this function.
*   **User Data Directory:** Each profile MUST launch with its own unique `--user-data-dir` to ensure complete isolation. The backend needs to manage the creation of these directories (e.g., under a common application data folder).
*   **Mapping UI Options to Flags:** This is the most critical and potentially complex part. The `fingerprint-chromium` documentation provides a good starting point, but thorough testing and possible reverse-engineering/community consultation might be needed for undocumented features or behaviors related to specific fingerprint parameters (WebGL, AudioContext, ClientRects, Speech Voices, etc.). The 'Default/Custom/Random' UI options will need careful translation into appropriate flags or value generation based on the `--fingerprint` seed.
*   **`--fingerprint` Seed:** This integer seed is fundamental. If a user selects 'Random' for multiple settings, this seed should ideally be used by `fingerprint-chromium` to generate consistent pseudo-random values for that profile. If the kernel doesn't automatically use the seed for all randomizable parameters, the backend might need to pre-generate some values based on this seed if 'Custom' mode is chosen with specific generated values.
*   **Error Handling & Validation:** The function should gracefully handle missing or malformed profile data, though Pydantic models in FastAPI would help validate upstream.
*   **Quoting and Escaping:** When constructing the command line, especially if it were to be executed via a shell, proper quoting/escaping of arguments is vital. Using a list of arguments with `subprocess` in Python avoids many of these issues.
*   **Boolean Flags:** Chromium flags are often presence-based (e.g., `--disable-gpu`). Some might have `--enable-feature` and `--disable-feature` pairs.
*   **Plugin Installation:** The mechanism for installing plugins with `fingerprint-chromium` (e.g., `--load-extension` flag) needs to be determined and integrated.
*   **Cookie Handling:** Cookies set in the UI need to be written to the appropriate `user-data-dir` for the profile before the browser launches, or potentially injected via DevTools protocol if supported and necessary.

### 4.3. API Interface Definition (RESTful)

Base URL: `/api/v1`

All request and response bodies will be in JSON format unless otherwise specified.

**Profiles (`/profiles`)**

*   **`GET /profiles`**
    *   **Description:** Retrieves a list of all browser profiles. Supports pagination, filtering, and sorting.
    *   **Query Parameters:**
        *   `page` (int, optional, default: 1): Page number for pagination.
        *   `page_size` (int, optional, default: 10): Number of items per page.
        *   `group_id` (int, optional): Filter by group ID.
        *   `name` (str, optional): Search term for profile name (partial match).
        *   `sort_by` (str, optional, default: 'created_at'): Field to sort by (e.g., 'name', 'last_launch_time').
        *   `sort_order` (str, optional, default: 'desc'): Sort order ('asc' or 'desc').
    *   **Response (200 OK):**
        ```json
        {
            "items": [
                { "id": 1, "name": "Profile A", "group_id": 1, ... },
                { "id": 2, "name": "Profile B", "group_id": null, ... }
            ],
            "total": 100,
            "page": 1,
            "page_size": 10,
            "pages": 10
        }
        ```

*   **`POST /profiles`**
    *   **Description:** Creates a new browser profile.
    *   **Request Body:** JSON object representing the profile. All fields from the `profiles` table schema (section 4.1) are potential inputs, excluding `id`, `created_at`, `last_launch_time`. `fingerprint_seed` can be optional; if not provided, the backend should generate one if any 'random' options are selected.
    *   **Response (201 Created):** JSON object of the created profile, including its new `id`.
    *   **Response (400 Bad Request):** If validation fails (e.g., missing required fields, invalid data types).

*   **`GET /profiles/{profile_id}`**
    *   **Description:** Retrieves details of a specific profile.
    *   **Path Parameters:** `profile_id` (int).
    *   **Response (200 OK):** JSON object of the profile.
    *   **Response (404 Not Found):** If profile with `profile_id` does not exist.

*   **`PUT /profiles/{profile_id}`**
    *   **Description:** Updates an existing profile.
    *   **Path Parameters:** `profile_id` (int).
    *   **Request Body:** JSON object with fields to update. Only provided fields will be updated.
    *   **Response (200 OK):** JSON object of the updated profile.
    *   **Response (404 Not Found):** If profile does not exist.
    *   **Response (400 Bad Request):** If validation fails.

*   **`DELETE /profiles/{profile_id}`**
    *   **Description:** Deletes a profile.
    *   **Path Parameters:** `profile_id` (int).
    *   **Response (204 No Content):** On successful deletion.
    *   **Response (404 Not Found):** If profile does not exist.

*   **`POST /profiles/{profile_id}/launch`**
    *   **Description:** Launches the browser instance for the specified profile.
    *   **Path Parameters:** `profile_id` (int).
    *   **Request Body:** (Optional) May include parameters like `headless: true` if such runtime options are desired.
    *   **Response (200 OK):** `{ "message": "Browser launched successfully", "pid": 12345 }` (pid might be OS-dependent or not always available/relevant).
    *   **Response (404 Not Found):** If profile does not exist.
    *   **Response (500 Internal Server Error):** If browser launch fails (e.g., executable not found, command generation error).

*   **`POST /profiles/batch`**
    *   **Description:** Performs batch operations on profiles.
    *   **Request Body:**
        ```json
        {
            "action": "delete", // or "assign_group"
            "profile_ids": [1, 2, 3],
            "group_id": 5 // Only required if action is "assign_group"
        }
        ```
    *   **Response (200 OK):** `{ "message": "Batch operation successful", "results": { ... } }` (details about individual operations).
    *   **Response (400 Bad Request):** If action is invalid or required parameters are missing.

**Groups (`/groups`)**

*   **`GET /groups`**
    *   **Description:** Lists all groups.
    *   **Response (200 OK):** `[ { "id": 1, "name": "Group A", "profile_count": 10 }, ... ]`

*   **`POST /groups`**
    *   **Description:** Creates a new group.
    *   **Request Body:** `{ "name": "New Group Name" }`
    *   **Response (201 Created):** `{ "id": 2, "name": "New Group Name", "profile_count": 0 }`
    *   **Response (400 Bad Request):** If name is missing or already exists.

*   **`GET /groups/{group_id}`**
    *   **Description:** Retrieves details of a specific group.
    *   **Path Parameters:** `group_id` (int).
    *   **Response (200 OK):** `{ "id": 1, "name": "Group A", "profile_count": 10, "created_at": "..." }`
    *   **Response (404 Not Found):** If group does not exist.

*   **`PUT /groups/{group_id}`**
    *   **Description:** Updates a group's name.
    *   **Path Parameters:** `group_id` (int).
    *   **Request Body:** `{ "name": "Updated Group Name" }`
    *   **Response (200 OK):** Updated group object.
    *   **Response (404 Not Found):** If group does not exist.
    *   **Response (400 Bad Request):** If name is missing or already exists.

*   **`DELETE /groups/{group_id}`**
    *   **Description:** Deletes a group. Profiles in this group will have their `group_id` set to `NULL`.
    *   **Path Parameters:** `group_id` (int).
    *   **Response (204 No Content):** On successful deletion.
    *   **Response (404 Not Found):** If group does not exist.

**Proxies (`/proxies`)**

*   **`GET /proxies`**
    *   **Description:** Lists all proxies (with pagination and search).
    *   **Query Parameters:** `page`, `page_size`, `search` (searches name, host).
    *   **Response (200 OK):** Paginated list of proxy objects.

*   **`POST /proxies`**
    *   **Description:** Adds a new proxy configuration.
    *   **Request Body:** JSON object for proxy (name, type, host, port, username, password, notes).
    *   **Response (201 Created):** Created proxy object.
    *   **Response (400 Bad Request):** Validation errors.

*   **`GET /proxies/{proxy_id}`**
    *   **Description:** Retrieves a specific proxy.
    *   **Response (200 OK):** Proxy object.
    *   **Response (404 Not Found).**

*   **`PUT /proxies/{proxy_id}`**
    *   **Description:** Updates a proxy.
    *   **Response (200 OK):** Updated proxy object.
    *   **Response (404 Not Found / 400 Bad Request).**

*   **`DELETE /proxies/{proxy_id}`**
    *   **Description:** Deletes a proxy. (Consider implications if proxy is in use by profiles - disallow or warn).
    *   **Response (204 No Content).**
    *   **Response (404 Not Found).**
    *   **Response (409 Conflict):** If proxy is in use and deletion is restricted.

*   **`POST /proxies/batch-delete`**
    *   **Description:** Batch delete proxies.
    *   **Request Body:** `{ "ids": [1, 2, 3] }`
    *   **Response (200 OK):** `{ "message": "Batch deletion successful" }`

**Plugins (`/plugins`)**

*   **`GET /plugins`**: List all managed plugins.
*   **`POST /plugins`**: Add/register a new plugin. (Actual installation might be manual placement + backend registration, or via upload if kernel supports command-line installation).
    *   **Request Body:** `{ "name": "My Plugin", "version": "1.0", "source_path": "path/to/plugin.crx" }`.
*   **`GET /plugins/{plugin_id}`**: Get plugin details.
*   **`PUT /plugins/{plugin_id}`**: Update plugin (e.g., enable/disable state).
    *   **Request Body:** `{ "enabled": false }`.
*   **`DELETE /plugins/{plugin_id}`**: Remove plugin from management (doesn't necessarily delete files unless managed by app).

**API List (`/api-docs`, `/openapi.json`)**

*   FastAPI will automatically generate OpenAPI documentation (Swagger UI at `/docs`, ReDoc at `/redoc` by default, can be configured to `/api-docs`).
*   `GET /openapi.json`: Serves the OpenAPI schema definition.
