# 🤖 Rasa Pro - Python Setup

This project uses **Rasa Pro**. Follow these steps to install it using **Python and pip** (no `uv` required).

---

## ✅ Requirements

- Python 3.10 or 3.11  
- pip  
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

# 5. Train and run the assistant
rasa train
rasa inspect