 # 🛠️ Simple DevOps Monitoring Tool

A CLI-based simulation tool for managing virtual machine instances.  
Built for DevOps practice and designed to mimic real-world infrastructure operations — with simplicity, structure, and extensibility in mind.

---

## 📚 Overview

This tool allows users to simulate managing virtual machines (VMs) using a clean, interactive CLI interface. It supports validating configurations, editing machine data, displaying statistics, and safely updating the system — all while maintaining logs and backup integrity.

---

## 🔧 Features

- ✅ Validate VM configurations using Pydantic  
- ✅ Add, edit, or delete VM instances  
- ✅ Real-time CLI feedback with simulated delays  
- ✅ Display full list of machines  
- ✅ Generate system statistics (e.g., total machines, by OS, by status)  
- ✅ Full logging with INFO/WARNING/ERROR levels  
- ✅ Automatic JSON backup before every change  
- ✅ Modular structure for future integrations (Docker, AWS, etc.)

---

## 🚀 How to Run

### 1. Clone the repository:


### 2. Run the tool:
```bash
python src/main.py
```

> **Note:** You must run the script from the **root folder** so internal paths resolve correctly.

---

## 📁 Project Structure

```
simple-devops-monitoring-tool/
├── src/
│   └── main.py               # Entry point
│   └── machine_model.py      # VM validation model
│   └── logger.py             # Logging setup
├── configs/
│   └── instances.json        # VM data (ignored in Git)
├── logs/
│   └── app.log               # Log output
├── README.md
└── .gitignore
```

---

## ⚠️ Important Notes

- `configs/instances.json` is ignored via `.gitignore`.
- To get started, create the file manually with this content:
```json
{
  "instances": []
}
```

- A backup is automatically created as `instances_backup.json` before each write operation.

---

## 🧱 Future Plans

- Docker support
- Flask-based REST API
- AWS EC2 integration with boto3
- GUI interface with Tkinter/Streamlit

---

## 📄 License

Open-source for learning purposes.  
Use it, fork it, build on top of it.
