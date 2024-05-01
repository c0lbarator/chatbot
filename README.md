kuda<->tuda source code repo
how use it?
- Make sure, that you have latest Python version installed
- Create virtual environment
- In venv run "pip install -r requirements.txt"
- create .env file with API tokens of user's bot and creator's bot like:
'''
CREATOR_TOKEN=1234567890:AAH41GlT7PvLff40QF1f6CzY0_IjY7bot6M
USER_TOKEN=1234567890:AAGAI3gKXOhwwC3gEoVdm9tIBFCVRPekJek
'''
- In code replace dev's Appwrite key and server URI with your own
- run bots: python3 stable_bot.py & python3 user.py
