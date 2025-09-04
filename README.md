# 🤖 Rasa Pro - Python Setup

This project uses **Rasa Pro**. Follow these steps to install it using **Python and pip** (no `uv` required).

---

## ✅ Requirements

- Python 3.10 or 3.11  
- pip
- pip3
- [Rasa Pro license key →](https://rasa.com/rasa-pro-developer-edition-license-key-request/)

---

## ⚙️ Setup

```bash
# 1. Clone the project
git clone https://github.com/your-username/your-project.git
cd your-project

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate

# 3. Export your license key
export RASA_PRO_LICENSE=your_license_key  # Windows PowerShell: $env:RASA_PRO_LICENSE="your_license_key"

# 4. Install Rasa Pro
pip install --upgrade pip
pip install rasa-pro
pip install -r requirements.txt

# 5. Create .env File (Database Config)
DB_HOST=your_host_here
DB_USER=your_user_here
DB_PASSWORD=your_password_here
DB_NAME=your_db_name
DB_PORT=3306

# 5. Train the assistant
rasa train

# 6.1. Test with Rasa Inspect
rasa inspect

# 6.2. Running the Assistant
rasa run --enable-api --cors "*" --debug

# The assistant will be accessible at:
http://localhost:5005

