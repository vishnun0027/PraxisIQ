# PraxisIQ 🧠

> **An AI-powered emotional journaling assistant designed to guide self-reflection, identify cognitive traps, and foster mental clarity using Cognitive Behavioral Therapy (CBT) techniques.**

---

## 🌟 The Vision

Modern life is fast, stressful, and often leaves little room for structured self-reflection. **PraxisIQ** bridges the gap between raw thought and therapeutic clarity. It acts as an active, compassionate companion that listens to your daily journals, analyzes the underlying emotions, highlights unhelpful thinking patterns, and helps you shift your perspective in real-time.

By combining the proven efficacy of **Cognitive Behavioral Therapy (CBT)** with artificial intelligence, PraxisIQ transforms journaling from a passive record into an interactive tool for personal growth.

---

## ✨ Key Features

### 1. Seamless On-the-Go Journaling
Write a journal entry whenever inspiration strikes, right from your phone. PraxisIQ provides an instant, private channel to offload thoughts, worries, or achievements wherever you are, without friction.

### 2. Deep Emotional Analysis
The moment you share a thought, PraxisIQ instantly analyzes your entry to extract critical insights:
* **Emotion Identification**: Accurately categorizes your core feelings (e.g., overwhelm, hope, stress, calm).
* **Intensity Tracking**: Assigns a scale to map your emotional highs and lows over time.
* **Mind Trap Detection**: Flags common cognitive distortions—such as *catastrophizing*, *mind-reading*, or *all-or-nothing thinking*—that may be affecting your mood.

### 3. Real-Time Perspective Shifts
Instead of just listening, PraxisIQ provides an instant, supportive feedback loop:
* 💡 **Compassionate Guidance**: Practical, encouraging words customized to your immediate emotional state.
* 🌱 **Cognitive Reframing**: Actionable advice to help you view negative thoughts from a healthier, more balanced perspective.

### 4. Your Conversational Copilot
Have a follow-up thought? Simply reply to the feedback. PraxisIQ acts as a compassionate copilot trained in CBT-style therapeutic interaction, engaging in a natural, supportive conversation to help you talk through your feelings.

### 5. Conceptual Memory
Our minds remember ideas, not just exact words. PraxisIQ allows you to search your past journals conceptually. Looking for *"that time I felt stressed about a presentation"* retrieves relevant entries even if those exact words weren't used, helping you trace your emotional growth.

### 6. Proactive Weekly Insights
Every week, receive a beautifully compiled summary highlighting your emotional trends, recurring thinking patterns, and a supportive overarching review of the week's events.

---

## 🔄 The Growth Cycle

1. **Express**: Vent and offload your thoughts into your private chat space.
2. **Deconstruct**: The assistant analyzes the emotional layers and identifies any mental traps.
3. **Reframe**: Receive an encouraging perspective shift instantly.
4. **Dialogue**: Explore your thoughts further through conversation with your copilot.
5. **Reflect**: Review your weekly digest to understand your long-term emotional journey.

---

## 🎯 Who Is It For?

* 🧘 **Mindfulness Practitioners**: Anyone looking to build a consistent, meaningful journaling habit.
* 📈 **Growth-Minded Individuals**: People who want to trace their emotional habits and spot recurring cognitive bottlenecks.
* ⚡ **Busy Professionals**: Individuals seeking a rapid, low-friction channel to vent, reflect, and gain immediate mental clarity on the go.

---

## 🚀 Production Deployment

This project is deployed automatically to the production VM using GitHub Actions when changes are pushed to `main`.

### Automated CI/CD
The deployment workflow is configured in [.github/workflows/ci-cd.yml](file://.github/workflows/ci-cd.yml) and runs on pushes to `main`. It connects to the VM via SSH, checks out the code, and triggers the deployment script.

### Unified Deployment Script
All deployment steps are encapsulated in [scripts/deploy.sh](file://scripts/deploy.sh):
- **Dependencies**: Runs `uv sync --frozen` to prepare the isolated virtual environment.
- **Systemd User Configuration**: Templates the systemd files dynamically (resolving paths and user context) and registers them to `~/.config/systemd/user/`.
- **Linger Activation**: Keeps services running even after the SSH session disconnects.
- **Service Management**: Restarts `praxisiq-embed.service`, `praxisiq-api.service`, `praxisiq-collector.service`, and `praxisiq-weekly.timer`.
- **Health Check**: Runs a health loop against `http://localhost:8000/health` to verify success.

To trigger a manual deploy on the VM, execute:
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```