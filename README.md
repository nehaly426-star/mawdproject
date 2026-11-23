# 🐾 PawAdopt: A Pet Adoption Platform

**Live site:** https://nehaly426-star.github.io/mawdproject/

Hi! I'm Nehal Yadav, and this is PawAdopt, a pet adoption website I built as part of my college project.

## Why I made this

Every year, a lot of animals wait in shelters for a home, and a lot of people want to adopt but don't know where to start. Information is scattered across WhatsApp groups, posters and phone calls, and nobody can tell which pets are still available or what happened to the request they sent.

I wanted to build one simple place where:

- someone can **browse the pets** that need a home,
- an adopter can **ask to adopt** with one click,
- and a shelter admin can **see every request and answer it**, without a pile of messages.

It's a small project, but I wanted it to feel like something a real shelter could use.

## What the website looks like

PawAdopt has two pages, and what you see depends on who you are.

**For visitors (no login needed)**
- A home page with a card for each pet: photo, name and adoption fee.
- A **Support & Announcements** section with adoption guidelines and updates from the shelter.
- Login and Register forms.

**For adopters (after signing up/registering)** (You can do adopter login by username and password of your choice)
- A **Request Adoption** button appears on every pet.
- A dashboard that shows my requests and whether each one is *pending*, *approved* or *rejected*.
- I can't send a second request for the same pet while one is already active.

**For the admin** (You can do admin login by the username: adminmeow and password:admin123 given in code)
- Add, edit and delete pets.
- See every adoption request with the adopter's name, username and phone number, then **approve or reject** it.
- Post and update support announcements.

## How it's built

| Part | What I used |
|---|---|
| Frontend | HTML, CSS and plain JavaScript (no frameworks) |
| Backend | Python with FastAPI |
| Database | SQLite |
| Login | Password hashing (PBKDF2) and JWT tokens |
| Hosting | GitHub Pages (frontend) and Render (backend) |

Access is controlled by roles: only admins can change pets and requests, and only adopters can submit adoption requests. The server checks this on every request, not just in the browser.

## Project files

```
index.html       Home page: pets, announcements, login and register
dashboard.html   Dashboard for admins and adopters
style.css        All the styling
app.js           Frontend logic and calls to the backend
main.py          FastAPI backend and database setup
requirements.txt Python packages needed to run the backend
HLD.md / LLD.md  High-level and low-level design documents
```

## Running it on your own computer

1. Install the Python packages:
   ```
   pip install -r requirements.txt
   ```
2. Start the backend:
   ```
   uvicorn main:app --reload --port 8000
   ```
3. Open `index.html` in your browser (or with the Live Server extension in VS Code).

The first time the backend starts, it creates the database and one default admin account. Check `main.py` for the details and change the password before sharing the project anywhere.

API documentation is available at `/docs` on the running backend.

## Good to know

The backend runs on a free hosting plan on render, so it goes to sleep when nobody uses it. The first page load after a quiet period can take up to a minute. The free plan also resets the database now and then, so pets added there may need to be added again. Though I have entered a few pets for demo in the code itself.   

## What I learned

This project taught me how a frontend, a backend and a database talk to each other, how login and roles work, and how many small things (file paths, hosting, CORS) can break a site that worked perfectly on my own laptop.

Thanks for visiting. If you ever adopt a pet, I hope it's a great one. 🐶🐱
