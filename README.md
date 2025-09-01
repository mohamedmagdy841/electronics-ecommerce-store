# ElectroShop – Multi-Vendor E-Commerce (Django DRF)

ElectroShop is a **containerized multi-vendor e-commerce platform** built with **Django REST Framework**.
It supports user authentication, vendor management, cart and checkout workflows, and integrates multiple payment gateways.
The system is designed with scalability and maintainability in mind, using **PostgreSQL**, **Redis**, **Celery**, and **Nginx** in a production-ready deployment on a VPS.

---

## Deployment Architecture

ElectroShop is deployed using **Docker containers** on a VPS, with a **central Nginx reverse proxy** routing traffic to internal services.

### Request Flow (Subdomain to Application)

**Step 1: Client Request**

* User visits: `https://electroshop.mo-magdy.com`

**Step 2: Central Reverse Proxy (Nginx)**

* Terminates TLS (Let’s Encrypt certs).
* Inspects Host header.
* Routes requests for `electroshop.mo-magdy.com` → ElectroShop’s internal Nginx container.

**Step 3: Application Gateway (ElectroShop Nginx)**

* Serves static (`/static/`) and media (`/media/`) directly from mounted volumes.
* For dynamic requests, forwards traffic → Gunicorn over Docker internal network.

**Step 4: Application Execution (Gunicorn)**

* Runs multiple worker processes.
* Executes Django REST Framework API logic.
* Handles authentication, serialization, and business logic.

**Step 5: Data Layer Integration**

* PostgreSQL (Global):

  * Stores ElectroShop schema (users, products, orders, payments).
  * Data is isolated per project schema.
* Redis (Global):

  * Caching API responses & sessions.
  * DRF throttling (rate limits).
  * Task queues (Celery jobs).

---

## Architecture Diagram

<img width="681" height="337" alt="Untitled Diagram123 drawio" src="https://github.com/user-attachments/assets/eb76834d-b705-4b58-8a80-be55703d8fe1" />

## Database Schema (High-Level)
[View Here](https://drive.google.com/file/d/1NokZ_9K538UVBYaiUkb-G8N7De5PDdZG/view?usp=drive_link)

---

## Features

* Containerized & deployed on VPS with Docker.
* Redis for caching, throttling, and background task queues.
* Celery for sending async emails (e.g., order confirmation, password reset).
* Multiple payment gateways – Stripe, PayPal, and Paymob.
* API Documentation – Swagger UI + Postman collection.
* Full JWT Authentication (access/refresh with rotation & blacklist).

  * Social login (Google & GitHub).
  * OTP-based authentication.
* Rate limiting – at both application level (Django DRF) and server level (Nginx).
* Cart system – supports guest carts and logged-in carts.
* Strategy Design Pattern for payments integration.
* Class-Based Views with custom permission mixins.
* Nginx – serves static/media files and handles SSL termination.
* Simple CI/CD with GitHub Actions.

---

## Technologies Used

| Technology     | Purpose                                      |
| -------------- | -------------------------------------------- |
| Django         | Web framework for business logic & API layer |
| DRF            | Django REST Framework for APIs               |
| PostgreSQL     | Relational database backend                  |
| Redis          | Caching, throttling, task queues             |
| Nginx          | Reverse proxy, static/media serving, SSL     |
| Docker         | Containerization & deployment                |
| GitHub Actions | CI/CD pipeline automation                    |

---

## Demo

* Swagger Docs: [https://electroshop.mo-magdy.com/api/v1/schema/swagger-ui/](https://electroshop.mo-magdy.com/api/v1/schema/swagger-ui/)
* Postman Collection: [View Here](https://documenter.getpostman.com/view/38857071/2sB3HhtNhu)
