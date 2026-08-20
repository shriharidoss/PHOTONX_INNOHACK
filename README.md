# 🏥 Mobile Telemedicine Kiosk for Rural Healthcare Access

**INNOHACK 2.0 | Team PHOTONX**

A solar-powered telemedicine kiosk that combines **IoT health monitoring, machine learning, digital patient records, and remote doctor consultation** to improve healthcare access in rural and underserved areas.

---

## 🎯 Problem Statement

Rural communities often have limited access to doctors, diagnostic facilities, and timely medical consultation. Patients may need to travel long distances even for basic health assessments.

---

## 💡 Our Solution

We developed a **mobile healthcare kiosk** that enables patients to perform basic health assessments using IoT sensors and receive remote medical assistance through a digital healthcare platform.

The system collects physiological data through connected sensors, processes the data using a backend and ML pipeline, stores patient information, and enables remote doctor/video consultation.

### Workflow

**Patient → IoT Sensors → ESP32 → Backend → ML/Health Analysis → Patient Records → Doctor Consultation**

---

## ⭐ Key Features

* 🩺 **IoT-based health monitoring**
* ❤️ **PPG-based blood pressure analysis**
* 🤖 **Machine-learning health analysis**
* 👤 **Digital patient health records**
* 👨‍⚕️ **Remote doctor consultation**
* 🎥 **Video consultation**
* ☀️ **Solar-powered kiosk**
* 🔌 **Modular sensor architecture**

---

## 🔧 Hardware

* **ESP32** – IoT controller
* **MAX30102 / PPG sensor** – PPG signal acquisition
* **Temperature sensor**
* **Solar panel**
* **Solar charging/regulation circuit**
* **Battery**
* Additional diagnostic sensors

---

## 💻 Technologies Used

* **Python**
* **Flask**
* **HTML / CSS / JavaScript**
* **Machine Learning**
* **NumPy / Pandas**
* **ESP32**
* **Database**
* **IoT / Sensor Communication**

---

## 🧠 Machine Learning

The `BP_ML_Model_UCI` module contains the PPG/BP analysis pipeline.

```text
PPG Data
   ↓
Preprocessing
   ↓
Feature / Signal Processing
   ↓
Model Training
   ↓
Model Evaluation
   ↓
Prediction
```

---

## 📂 Project Structure

```text
PHOTONX_INNOHACK/
│
├── BP_ML_Model_UCI/          # BP/PPG machine-learning module
├── frontend/                 # Healthcare kiosk interface
├── health_kiosk_backend/     # Main backend
├── medical_sensor_backend/   # Sensor and medical-data processing
├── INNOHACK/                 # Database and application modules
├── .gitignore
└── README.md
```

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/shriharidoss/PHOTONX_INNOHACK.git
cd PHOTONX_INNOHACK
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

Navigate to the required module and install its dependencies:

```bash
pip install -r requirements.txt
```

### 4. Run the backend

```bash
cd health_kiosk_backend
python app.py
```

Open the displayed local address in your browser.

### 5. Hardware

Connect the ESP32 and required sensors using the appropriate USB/data connections and configure the serial/COM port for the system.

---

## 🖼️ Screenshots

### Healthcare Kiosk Interface

**Add your frontend screenshot here.**

### Hardware / Sensor Setup

**Add your ESP32 + sensor setup photograph here.**

### Health Analysis

**Add your ML/health-result screenshot here.**

### System Architecture

**Add your architecture diagram here.**

---

## 🚀 Future Scope

* Integration of additional medical sensors
* ECG and SpO₂ monitoring
* Improved ML-based health prediction
* Regional-language support
* Offline-first operation
* Cloud-based healthcare records
* AI-assisted preliminary health assessment
* Expansion to more rural healthcare centers

---

## 🏆 INNOHACK 2.0

**Project:** Mobile Telemedicine Kiosk for Rural Healthcare Access
**Team:** PHOTONX

> **Bringing healthcare closer to rural communities through IoT, AI, and telemedicine.**
