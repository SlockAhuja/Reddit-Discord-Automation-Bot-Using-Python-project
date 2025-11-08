import praw
import requests
import os
from dotenv import load_dotenv
import time
import threading

# --- SETUP ---

# Load credentials from your .env file
load_dotenv()

# Securely get credentials using os.getenv()
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# --- COMMENT RESPONSE FUNCTION ---

def respond_to_comment(comment):
    """Checks if a comment contains trigger words and responds accordingly."""
    trigger_words = ["help", "bot", "assist"]  # <--- CHANGE THESE to your desired triggers
    body_lower = comment.body.lower()
    if any(word in body_lower for word in trigger_words):
        reply_text = "Hello! I'm a Reddit bot. How can I assist you? For more info, visit [our Discord](https://discord.gg/example)."  # <--- CUSTOMIZE REPLY
        try:
            comment.reply(reply_text)
            print(f"Replied to comment by u/{comment.author.name}: '{comment.body[:50]}...'")
            time.sleep(10)  # Rate limiting: wait 10 seconds between replies to avoid spam
        except Exception as e:
            print(f"Error replying to comment: {e}")

# --- DISCORD FUNCTION ---

def post_to_discord(submission):
    """Formats and sends a Reddit submission to a Discord webhook."""
    
    # Create a nice-looking embed for Discord
    data = {
        "embeds": [
            {
                "title": f"New Post in r/{submission.subreddit.display_name}",
                "description": f"**{submission.title}**",
                "url": f"https://www.reddit.com{submission.permalink}",
                "color": 16729344,  # Reddit Orange-Red color
                "author": {
                    "name": f"u/{submission.author.name}",
                    "url": f"https://www.reddit.com/user/{submission.author.name}",
                    "icon_url": submission.author.icon_img if hasattr(submission.author, 'icon_img') else ""
                },
                "fields": [
                    {"name": "⬆️ Score", "value": str(submission.score), "inline": True},
                    {"name": "💬 Comments", "value": str(submission.num_comments), "inline": True}
                ],
                "footer": {
                    "text": "Reddit Bridge Bot"
                }
            }
        ]
    }
    
    try:
        # Send the request to the Discord webhook
        result = requests.post(DISCORD_WEBHOOK_URL, json=data)
        result.raise_for_status() # This will raise an error for a bad response (like 404 or 500)
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not post to Discord. {e}")
    else:
        print(f"Successfully posted submission: '{submission.title}'")

# --- MAIN BOT LOGIC ---

def run_bot():
    """Initializes and runs the bot."""
    print("Attempting to authenticate with Reddit...")
    try:
        # Initialize the Reddit instance with your credentials
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD,
        )
        # Check if login was successful
        print(f"Successfully authenticated as Reddit user: {reddit.user.me()}")
    except Exception as e:
        print(f"Error: Failed to authenticate with Reddit. Check your credentials. {e}")
        return # Stop the script if authentication fails

    # --- CHOOSE YOUR SUBREDDIT HERE ---
    target_subreddit = "Python" # <--- CHANGE THIS to the subreddit you want to follow

    subreddit = reddit.subreddit(target_subreddit)
    print(f"✅ Setup complete. Now monitoring r/{target_subreddit} for new posts and comments...")

    # Function to monitor submissions
    def monitor_submissions():
        while True:
            try:
                for submission in subreddit.stream.submissions(skip_existing=True):
                    post_to_discord(submission)
            except Exception as e:
                print(f"Warning: An error occurred in submissions stream: {e}. Reconnecting in 30 seconds...")
                time.sleep(30)

    # Function to monitor comments
    def monitor_comments():
        while True:
            try:
                for comment in subreddit.stream.comments(skip_existing=True):
                    respond_to_comment(comment)
            except Exception as e:
                print(f"Warning: An error occurred in comments stream: {e}. Reconnecting in 30 seconds...")
                time.sleep(30)

    # Start both streams in separate threads
    submission_thread = threading.Thread(target=monitor_submissions)
    comment_thread = threading.Thread(target=monitor_comments)
    submission_thread.start()
    comment_thread.start()

    # Keep the main thread alive
    submission_thread.join()
    comment_thread.join()

# --- START THE BOT ---
if __name__ == "__main__":
    run_bot()