# Continuum
A robust habit-tracking engine designed for power users. Track daily routines, visualize long-term trends, and master your habits with ease.

## 🏗️ The Stack: Continuum Core
Continuum is built with a decoupled architecture, prioritizing developer experience, type safety, and high-performance reactivity.

### Backend: The Logic Engine
- Django: A high-level Python web framework that encourages rapid development and clean, pragmatic design.

- Django REST Framework (DRF): A powerful toolkit for building Web APIs, handling the serialization of our Habit models into clean JSON.

- CORS Headers: Middleware used to securely manage Cross-Origin Resource Sharing, allowing our Vue frontend to communicate with the Django API.

- SQLite: Used as the primary **development** database for lightweight, file-based persistence.

- PostgreSQL: Used as the primary **production** database for scalability and efficiency.

### Frontend: The Reactive Interface
- Vue.js 3: The Progressive JavaScript Framework, utilizing the Composition API ```(<script setup>)``` for modular and readable component logic.

- Vite: A lightning-fast build tool that provides a near-instant Hot Module Replacement (HMR) during development.

- Tailwind CSS v4: A utility-first CSS framework for rapid UI styling directly within HTML, used to create Continuum’s modern, high-radius card aesthetic.

- Axios: A promise-based HTTP client used to perform asynchronous requests to the Django backend.

- Lucide Vue Next: A library of beautiful, consistent icons used for habit tracking visualization (Flame, Activity, Check, etc.).

### The Connection
The frontend and backend communicate via a RESTful API. Data flows from the Django Admin/API &rarr; JSON Serialization &rarr; Axios Fetch &rarr; Vue Reactive State.

# Installation
Upcoming Docker Compose installation steps.

# Contributing
TBD

# Star History

[![Star History Chart](https://api.star-history.com/svg?repos=continuum-app/continuum&type=date&legend=top-left)](https://www.star-history.com/#continuum-app/continuum&type=date&legend=top-left)