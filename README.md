# CPU Scheduling Algorithm Simulator

A web-based **CPU Scheduling Algorithm Simulator** developed using **Python Flask**.  
The application allows users to simulate and analyze different CPU scheduling algorithms, visualize execution through a **Gantt Chart**, and evaluate performance metrics.
---
deployed on render [(https://cpu-scheduler-851d.onrender.com/)]

## 📌 Project Overview

CPU scheduling is a fundamental concept in Operating Systems. This project provides an interactive platform where users can input process details and observe how various scheduling algorithms handle process execution. The simulator calculates key performance metrics such as **Turnaround Time**, **Waiting Time**, and **Response Time** to help compare algorithm efficiency.

---

## 🎯 Objectives

- Simulate different CPU scheduling algorithms  
- Visualize process execution using a Gantt chart  
- Calculate and compare scheduling performance metrics  
- Understand preemptive and non-preemptive scheduling techniques  

---

## ⚙️ Features

- Web-based interface using Flask  
- Supports multiple CPU scheduling algorithms  
- Dynamic Gantt chart visualization  
- Automatic calculation of:
  - Turnaround Time (TAT)
  - Waiting Time (WT)
  - Response Time (RT)
- Displays average scheduling metrics  
- Handles CPU idle time correctly  

---

## 🧠 Scheduling Algorithms Implemented

- First Come First Serve (FCFS)
- Shortest Job First (Non-Preemptive)
- Shortest Job First (Preemptive / SRTF)
- Round Robin Scheduling (user-defined time quantum)
- Priority Scheduling (Non-Preemptive)
- Priority Scheduling (Preemptive)

---

## 🛠️ Technologies Used

- **Backend:** Python, Flask  
- **Frontend:** HTML, CSS, JavaScript (Jinja2 Templates)  
- **Data Handling:** Python Dataclasses, JSON  
- **Visualization:** Gantt Chart  
- **Version Control:** Git and GitHub  

---

# Project Built as an internal project for college subjects
