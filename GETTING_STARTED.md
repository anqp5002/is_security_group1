# 🚀 Getting Started - For Beginners

**Welcome!** This guide helps you understand this project from zero. Read this first, then dive into the detailed docs.

---

## 🎯 What Does This Project Do?

This is a **Network Intrusion Detection System (IDS)** using Machine Learning.

**In simple terms:**
- It watches network traffic (data flowing between computers)
- It detects if the traffic is **normal** or **suspicious** (attack)
- It identifies **what type of attack** it is (DDoS, port scan, botnet, etc.)

**Real-world example:**
```
Normal user browsing YouTube
  → Model says: "BENIGN ✅" (normal, safe)

Hacker trying to scan your network
  → Model says: "PortScan 🚨" (attack detected!)

Malware trying to communicate with command server
  → Model says: "Bot 🚨" (botnet infection detected!)
```

---

## 📚 5 Different Machine Learning Models

The project trains **5 different AI models** and compares them:

| Model | Accuracy | Best For | Use It? |
|-------|----------|----------|---------|
| **Random Forest** | 97.59% | **Production (Real Deployment)** | ⭐ YES |
| KNN | 98.20% | Research/Testing | Alternative |
| SVM | 97.00% | Scalability needed | Alternative |
| Logistic Regression | 93.00% | Baseline/Learning | For study |
| Naive Bayes | 83.00% | Quick filtering | Not recommended |

**Why Random Forest was chosen despite not being #1:**
- KNN has 0.61% higher accuracy BUT misses 30% more botnet attacks
- Random Forest catches 99.9% of port scans vs KNN's 84.8%
- **Security > Accuracy**: Missing attacks is worse than small accuracy loss

---

## 🗂️ Project Structure (Simple Version)

```
is_security_group1/
│
├── 📄 Docs (Read these!)
│   ├── README.md              ← Quick overview
│   ├── GETTING_STARTED.md     ← You are here
│   ├── GUIDE.md               ← Detailed walkthrough
│   ├── REPORT.md              ← Why Random Forest? Deep analysis
│
├── 🤖 Python Scripts
│   ├── phase6_demo.py         ← Demo: loads 5 models, makes predictions
│   ├── model_comparison.py    ← Generates comparison charts
│
├── 📦 demo/ (Pre-trained Models)
│   ├── logistic_regression_model.pkl    ← Model 1 (needs scaler + encoder)
│   ├── naive_bayes_model.pkl            ← Model 2 (needs scaler + encoder)
│   ├── svm_model.pkl                    ← Model 3 (needs scaler + encoder)
│   ├── knn_model.pkl                    ← Model 4 (needs scaler + encoder)
│   ├── random_forest_model.pkl          ← Model 5 (needs scaler + encoder) ⭐ DEPLOYED
│   ├── scaler.pkl                       ← Shared: Feature normalizer
│   └── label_encoder.pkl                ← Shared: Label converter
│
├── 👥 Team Member Folders
│   ├── HoangAnh_N23DCCN071/   ← Data preprocessing & feature selection
│   ├── N23DCCN001_DangKimAn/  ← Training 3 models (LR, NB, SVM)
│   └── N23DCCN138_PhamQuocAn/ ← Training 2 models (KNN, RF) + alerts
```

---

## 🔑 Key Concepts Explained

### 1. What is a `.pkl` file?

A `.pkl` file is a **saved Python object**. Think of it like saving a trained brain to a file.

```
Training process:
  Raw data → Feed to AI → AI learns patterns → Save brain to logistic_regression_model.pkl

Using it later:
  Load logistic_regression_model.pkl → Brain remembers patterns → Make predictions
```

### 2. Why 7 files in demo/ folder? (5 models + 2 shared)

**5 Different Models:**
- Each has learned slightly different patterns
- Results don't always match
- By voting (consensus), we get more reliable answers

**2 Shared Tools:**
- **scaler.pkl** — Makes numbers "clean" before feeding to models
  ```
  Raw feature: 1250 bytes/sec
  Scaled: 0.5 (normalized between -1 and 1)
  
  Without scaling, models get confused and predict wrong!
  ```

- **label_encoder.pkl** — Translates between computer language and human language
  ```
  Computer output: 2
  Human language: "PortScan" (via label_encoder)
  
  Model outputs numbers 0-5
  Encoder converts: 0→BENIGN, 1→DDoS, 2→PortScan, 3→Bot, 4→Web Attack, 5→Infiltration
  ```

### 3. What are "18 Features"?

A **feature** is one piece of information about network traffic:

```
Example network flow has 18 measurements:
  1. Protocol (TCP/UDP/ICMP)
  2. Flow Duration (how long the connection lasted)
  3. Total Forward Packets (how many packets sent forward)
  4. Total Backward Packets (how many packets sent back)
  ... (14 more features)
  
All 5 models use the SAME 18 features to make decisions
```

---

## 🚦 Three Different Ways to Use This Project

### **Option 1: Quick Demo (1 minute) ⚡**
**Goal:** See the models work without training

```bash
pip install -r requirements.txt
python phase6_demo.py
```

**What happens:**
- ✅ Loads all 5 models from demo/ folder
- ✅ Creates fake network flows
- ✅ Each model makes predictions
- ✅ Shows what they all agree on (consensus)
- ✅ Formats alerts like a real IDS

**Best for:** Quick understanding, testing, showing others

---

### **Option 2: Download Pre-trained Results (5 min) 📥**
**Goal:** See comparison charts without training

```bash
# Download from Google Drive:
# https://drive.google.com/drive/folders/11JVbhnkZmTAB5ptHeTcQ9F00Y51MoEam

# Extract to demo/ folder, then run:
python model_comparison.py
```

**What you get:**
- ✅ Bar charts (accuracy comparison)
- ✅ Radar chart (all metrics visible)
- ✅ CSV file with data
- ✅ See why Random Forest was chosen

**Best for:** Understanding the decision, presentations

---

### **Option 3: Train Everything on Kaggle (2-4 hours) 🔬**
**Goal:** See the full pipeline from raw data to models

**This is complex - read GUIDE.md first!**

Quick summary:
1. **TV1** (10-15 min): Clean raw data from Kaggle dataset
2. **TV2** (5-10 min): Select best features
3. **TV3** (30-60 min): Train 3 models on Kaggle
4. **TV4** (60-120 min): Train 2 models on Kaggle
5. **TV5** (<1 min): Compare all 5

**Best for:** Learning, research, understanding the full pipeline

---

## 📖 Documentation Roadmap

### **For Different People:**

**I just want to see it work:**
- Run Option 1 (phase6_demo.py)
- Read this file (GETTING_STARTED.md)

**I want to understand the decision:**
- Read REPORT.md (Why was Random Forest chosen?)
- Run Option 2 (python model_comparison.py)

**I want to understand everything:**
- Read GUIDE.md (complete walkthrough)
- Run Option 1, 2, or 3
- Look at code comments

**I need to use this in my app:**
- Read REPORT.md ("Integration Examples")
- Copy code from examples
- Use models from demo/ folder

**I want to train it myself:**
- Read GUIDE.md completely
- Run Option 3 step by step

---

## 🎓 Learning Path

### **Week 1: Understanding**
- [ ] Read GETTING_STARTED.md (this file) - 10 min
- [ ] Run `python phase6_demo.py` - 2 min
- [ ] Understand 5 models and why RF was chosen - 20 min
- [ ] Read README.md - 10 min

**Total: ~45 minutes**

### **Week 2: Deep Dive**
- [ ] Read GUIDE.md completely - 1 hour
- [ ] Read REPORT.md completely - 1 hour
- [ ] Download models from Google Drive - 5 min
- [ ] Run `python model_comparison.py` - 2 min
- [ ] Study code in phase6_demo.py - 1 hour

**Total: ~3 hours**

### **Week 3: Hands-On (Optional)**
- [ ] Run TV1 (preprocessing) - 15 min
- [ ] Run TV2 (feature selection) - 10 min
- [ ] Train models on Kaggle (TV3 + TV4) - 2-3 hours
- [ ] Run TV5 (comparison) - 1 min
- [ ] Modify code, experiment

---

## ❓ Common Questions

**Q: Do I need to train the models myself?**
A: No! Download pre-trained models from Google Drive (Option 2 or 3)

**Q: Why 5 models if we only use Random Forest?**
A: To show the comparison and decision process. Also, consensus voting from all 5 can be more reliable.

**Q: What if I want to use this in my own project?**
A: See code examples in REPORT.md. Load models from demo/ folder and use phase6_demo.py as a template.

**Q: How accurate is this?**
A: Random Forest: 97.59% overall, but 99.9% on PortScan (what matters most for security).

**Q: Can I improve the models?**
A: Yes! Retrain with more data, adjust hyperparameters, or use different algorithms.

**Q: What if models disagree?**
A: That's normal. phase6_demo.py shows individual predictions + consensus (majority vote).

---

## 📞 Next Steps

1. **Right Now (2 min):** Run `python phase6_demo.py` to see it work
2. **Next (10 min):** Read README.md for project overview
3. **Then (1 hour):** Read GUIDE.md or REPORT.md depending on your goal
4. **Finally:** Choose Option 1, 2, or 3 above

---

## 📚 Document Reference

| File | What's In It | Read When |
|------|-------------|-----------|
| **GETTING_STARTED.md** | Overview for beginners (you are here) | First thing |
| **README.md** | Quick project summary + quick start | Want quick overview |
| **GUIDE.md** | Complete step-by-step guide | Want to understand everything |
| **REPORT.md** | Why Random Forest? Deep analysis + code examples | Need code examples or deep analysis |
| **phase6_demo.py** | Code that demonstrates predictions | Want to see how it works |
| **model_comparison.py** | Code that compares all 5 models | Want to generate charts |

---

## 🎉 You're Ready!

Pick Option 1, 2, or 3 above and get started! 

If anything is confusing, jump to the relevant section in the docs. We wrote them to be beginner-friendly.

**Good luck! 🚀**

---

*Last Updated: May 2, 2026*  
*For questions, check the relevant .md file or look at code comments*
