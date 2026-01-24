# SmartConnect Manager

SmartConnect Manager is a comprehensive resource and mission management application built with Python and Flet. It is designed to streamline the coordination of employees, vehicles, and tools/equipment for various operational missions. The application leverages Firebase Firestore for a robust, real-time backend.

## 🚀 Features

### 📊 Dashboard
- **Real-time Statistics**: View key metrics at a glance, including total/active employees, active/completed missions, vehicle availability, and equipment status.
- **Activity Feed**: Track recent system activities and user actions.

### 👥 Employee Management
- **Directory**: View a list of all employees with their roles and departments.
- **Profiles**: Detailed view of employee information.
- **Management**: Add new employees, edit details, and manage their status (Active/Inactive).
- **Mission Status**: Track who is currently assigned to a mission (Available/In Mission).

### 🚗 Vehicle Management
- **Fleet Overview**: Track all vehicles, their models, and license plates.
- **Status Tracking**: Monitor which vehicles are Available, In Use, or under Maintenance.
- **Assignment**: Automatically update vehicle status when assigned to a mission.

### 🛠️ Tools & Equipment
- **Inventory**: Manage a catalog of tools and equipment.
- **Quantity Tracking**: Monitor total vs. available quantities.
- **Condition Monitoring**: Track the condition of equipment.
- **Assignment**: specific tools can be assigned to missions, deducting from the available stock.

### 🎯 Mission Management
- **Create Missions**: distinct workflows to create missions with titles, descriptions, and locations.
- **Resource Allocation**: Assign a team leader, team members, a vehicle, and necessary tools to a mission in one go.
- **Status Workflow**: Manage mission lifecycle (Pending -> In Progress -> Completed/Cancelled).
- **History & Logs**: View detailed activity logs for each mission.
- **Smart Validation**: The system prevents assigning unavailable resources or personnel.

### 🔒 Security & Auth
- **User Authentication**: Secure login system.
- **Role-Based Access**: Different capabilities based on user roles (Administrator, Manager, etc.).
- **Audit Logging**: All critical actions are logged for accountability.

## 🛠️ Tech Stack

- **Frontend**: [Flet](https://flet.dev/) (Flutter for Python) - Provides a responsive and modern UI.
- **Backend**: [Firebase Firestore](https://firebase.google.com/docs/firestore) - NoSQL database for real-time data syncing.
- **Authentication**: Custom implementation using Firebase.
- **Language**: Python 3.x

## 📋 Prerequisites

- **Python 3.7+** installed on your machine.
- A **Firebase Project** with Firestore enabled.

## ⚙️ Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-username/smartconnect-manager.git
    cd smartconnect-manager
    ```

2.  **Create a Virtual Environment (Recommended)**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Firebase Configuration**
    - Go to your Firebase Console > Project Settings > Service Accounts.
    - Generate a new private key.
    - Download the JSON file and rename it to `Service.json`.
    - Place `Service.json` in the root directory of the project.

    *Alternatively, you can set an environment variable:*
    ```bash
    export FIREBASE_SERVICE_ACCOUNT_PATH="/path/to/your/service-account-key.json"
    ```

## 🚀 Usage

To start the application, simply run the `main.py` file:

```bash
python main.py
```

The application will launch in a new window.

**Default Login** (If you used the default data initialization):
- You may need to create a user manually via the `create_user` function in `db.py` or check the database if sample data was seeded.

## 📂 Project Structure

```
smartconnect-manager/
├── assets/                 # Static assets (images, icons)
├── tests/                  # Unit tests
├── views/                  # UI Screens (Flet Views)
│   ├── dashboard_view.py   # Main dashboard
│   ├── missions_view.py    # Mission list and management
│   ├── employees_view.py   # Employee directory
│   ├── ...                 # Other specific views
├── db.py                   # Database layer (Firebase interactions)
├── main.py                 # Application entry point and router
├── requirements.txt        # Python dependencies
└── Service.json            # Firebase Credentials (DO NOT COMMIT)
```

## 🧪 Running Tests

To run the unit tests:

```bash
python -m unittest discover tests
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

[MIT License](LICENSE)
