mkdir -p ~/.streamlit/
echo "[general]\n" > ~/.streamlit/config.toml
echo "email = \"$STREAMLIT_EMAIL\"\n" >> ~/.streamlit/config.toml
echo "server.headless = true\n" >> ~/.streamlit/config.toml
echo "port = $PORT\n" >> ~/.streamlit/config.toml
echo "enableCORS = false\n" >> ~/.streamlit/config.toml