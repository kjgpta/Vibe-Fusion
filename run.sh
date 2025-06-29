#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# 🌟 Vibe-to-Attribute Clothing Recommendation System Launcher 🌟
# -----------------------------------------------------------------------------

print_banner() {
  cat <<'EOF'

╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           🌟 Vibe-to-Attribute Clothing Recommendation System 🌟            ║
║                                                                              ║
║  Transform your style ideas into perfect outfit recommendations using AI!    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

EOF
}

check_python_version() {
  required_major=3
  required_minor=8

  # get major and minor
  read -r py_major py_minor _ < <(python3 - <<'PYCODE'
import sys
print(*sys.version_info[:3])
PYCODE
  )

  if (( py_major < required_major || (py_major == required_major && py_minor < required_minor) )); then
    echo "❌ Python ${required_major}.${required_minor}+ is required. Current version: ${py_major}.${py_minor}"
    return 1
  fi

  echo "✅ Python version: ${py_major}.${py_minor}"
  return 0
}

install_requirements() {
  echo -e "\n📦 Installing required packages..."
  if python3 -m pip install -r requirements.txt; then
    echo "✅ Requirements installed successfully!"
  else
    echo "❌ Failed to install requirements, continuing with existing packages..."
  fi
}

create_sample_catalog() {
  echo -e "\n📊 Creating sample product catalog..."
  if python3 create_catalog.py; then
    echo "✅ Sample catalog created successfully!"
  else
    echo "❌ Failed to create sample catalog."
  fi
}

check_environment() {
  echo -e "\n🔧 Checking environment configuration..."
  if [[ ! -f .env ]]; then
    if [[ -f env.example ]]; then
      cat <<EOF
⚠️  No .env file found. Please:
   1. Copy env.example to .env
   2. Edit .env with your API keys
   3. Set your OpenAI API key for GPT features

   Example:
   cp env.example .env
   # Then edit .env with your actual API keys

💡 The system will work with limited functionality without API keys.
   GPT inference will be disabled, but rule-based matching will work.
EOF
    else
      echo "⚠️  No environment configuration found."
      echo "💡 The system will work with limited functionality without API keys."
    fi
  else
    echo "✅ Environment file found!"
  fi
}

start_streamlit() {
  echo -e "\n🚀 Starting Streamlit application..."
  echo "📍 The app will open in your default web browser"
  echo -e "\n⏹️  Press Ctrl+C to stop the application"
  python3 -m streamlit run streamlit_app.py
}

main() {
  print_banner

  echo "🔍 System Check..."

  # Python version
  check_python_version || exit 1

  # Directory check
  if [[ ! -f requirements.txt ]]; then
    echo "❌ Please run this script from the project root directory."
    exit 1
  fi
  echo "✅ In correct directory"

  # Install dependencies
  install_requirements

  # Create catalog
  create_sample_catalog

  # Env check
  check_environment

  echo -e "\n$(printf '=%.0s' {1..80})"
  echo "🎉 Setup complete! Starting the application..."
  echo "$(printf '=%.0s' {1..80})"

  # Launch
  start_streamlit
}

main "$@"
