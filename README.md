# notify-reviewer
This is bot for notify reviewers for code review in channel of Employment Hero

# How to setup
Create .env file on this project to define

```
GITHUB_TOKEN=Your personal git hub token with permission to view Pull Request, View User info
BOT_TOKEN=Token of Slack Bot
CHANNEL_ID=The ID of channel you want to send message
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

# How to create github token

Please follow the link:

https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

# How to get USER_ID on Slack
Click on your profile, select Profile

![image](https://github.com/user-attachments/assets/06da88a3-ff68-453d-8eb2-c0bca7bfca66)

Click to three dots on profile

![image](https://github.com/user-attachments/assets/a639287b-0a76-4617-bcb1-63509879be11)

Select Copy Member ID

![image](https://github.com/user-attachments/assets/6b554446-262c-4846-9c18-5874cd7d4360)

# How to get CHANNEL_ID

Go to the Channel you want to send message. Click to the name of channel on the top

![image](https://github.com/user-attachments/assets/bfc4cf2e-b799-4468-b28e-81ad5f7a9a0e)
