# HomeDrive ☁️

A secure, self-hosted cloud storage web application built with Python and Flask. HomeDrive provides a localized alternative to commercial cloud drives, allowing users to securely manage their files, share directories, and administrators to strictly control user environments.

## 🚀 Key Features

* **Role-Based Access Control (RBAC):** Three-tier architecture including Host (Superadmin), Admin, and Standard User roles.
* **Dynamic Storage Quotas:** Admins can allocate and manage specific storage limits (in GB) for each user.
* **Public & Private Spaces:** Isolated personal directories for users and a unified public space for seamless file sharing.
* **Advanced File Operations:** Live upload tracking, instant file previewing, favorite marking, and full directory downloads as `.zip` archives.
* **i18n & Theming:** Built-in English and Turkish language support with a responsive Dark/Light UI powered by Tailwind CSS.

## 🛡️ Defensive Security Measures

Security is a primary focus of this project. The architecture includes specific mitigations against common web vulnerabilities:

* **Path Traversal Protection:** Implemented strict directory bounding using `os.path.commonpath` to prevent unauthorized file system access.
* **Cross-Site Request Forgery (CSRF):** Fully integrated `Flask-WTF` CSRF token validation across all state-changing endpoints.
* **Stored XSS Prevention:** Forced safe MIME-sniffing boundaries (`X-Content-Type-Options: nosniff`) and enforced `Content-Security-Policy: sandbox` for inline file previews.
* **Secure Session & Hashing:** Utilizes Werkzeug's robust password hashing and secure, persistent Flask sessions.

## ⚙️ Quick Installation Guide

Follow these steps to deploy HomeDrive on your local machine or server.

**1. Clone the repository:**
git clone [https://github.com/YOUR_USERNAME/HomeDrive.git](https://github.com/Iterth/HomeDrive.git)
cd HomeDrive

**2. Install required dependencies:**
pip install -r requirements.txt

**3. Configure Environment Variables:**
Rename `.env.example` to `.env` and replace the placeholder with a strong, random secret key.
(Example: `SECRET_KEY=your_super_secret_key`)

**4. Run the Setup Wizard:**
Initialize the database and create your Host (Superadmin) account using the interactive setup script.
python setup.py

**5. Start the Server:**
python main.py

The server will start on `[http://0.0.0.0:8080](http://0.0.0.0:8080)`. You can now log in using the credentials you created in step 4.
