# notify-reviewer
This is bot for notify reviewers for code review in channel of Employment Hero

# How to setup
Create .env file on this project to define 

```
GITHUB_TOKEN=Your personal git hub token with permission to view Pull Request, View User info
BOT_TOKEN=Token of Slack Bot
CHANNEL_ID=The ID of channel you want to send message
USER_ID=The ID of user on Slack request for review
```

# Setup alias on zshrc

Run command 
```
vi ~/.zshrc
```

Add alias at the end of file

```
alias notifyreviewer="python {path to file notify_review.py}"
```

After that run command

```
source ~/.zshrc
```
Now, you can execute the notifyreviewer command in your terminal to run the Python script.
