.PHONY: init-env

# Команда для создания .env из .env.example
init-env:
	cp -n env.example .env || echo ".env уже существует"