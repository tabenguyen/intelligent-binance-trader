nohup uv run python main.py >> output.log 2>&1 & echo $! > nohup.pid
# pkill -f "python main.py"