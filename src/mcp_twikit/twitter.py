from fastmcp import FastMCP, Context
import twikit
import os
from pathlib import Path
import logging

# Create an MCP server
mcp = FastMCP("mcp-twikit")
logger = logging.getLogger(__name__)
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

USERNAME = os.getenv('TWITTER_USERNAME')
EMAIL = os.getenv('TWITTER_EMAIL')
PASSWORD = os.getenv('TWITTER_PASSWORD')
USER_AGENT = os.getenv('USER_AGENT')
COOKIES_PATH = Path.home() / '.mcp-twikit' / 'cookies.json'

async def get_twitter_client() -> twikit.Client:
    """Initialize and return an authenticated Twitter client."""
    client = twikit.Client('en-US', user_agent=USER_AGENT)
    
    if COOKIES_PATH.exists():
        client.load_cookies(COOKIES_PATH)
    else:
        try:
            await client.login(
                auth_info_1=USERNAME,
                auth_info_2=EMAIL,
                password=PASSWORD
            )
        except Exception as e:
            logger.error(f"Failed to login: {e}")
            raise
        COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)
        client.save_cookies(COOKIES_PATH)
    
    return client

# Add an addition tool
@mcp.tool()
async def search_twitter(query: str, sort_by: str = 'Top', count: int = 10, ctx: Context = None) -> str:
    """Search twitter with a query. Sort by 'Top' or 'Latest'"""
    try:
        client = await get_twitter_client()
        tweets = await client.search_tweet(query, product=sort_by, count=count)
        return convert_tweets_to_markdown(tweets)
    except Exception as e:
        logger.error(f"Failed to search tweets: {e}")
        return f"Failed to search tweets: {e}"

@mcp.tool()
async def get_user_tweets(username: str, tweet_type: str = 'Tweets', count: int = 10, ctx: Context = None) -> str:
    """Get tweets from a specific user's timeline.
    
    Args:
        username: Twitter username (with or without @)
        tweet_type: Type of tweets to retrieve - 'Tweets', 'Replies', 'Media', or 'Likes'
        count: Number of tweets to retrieve (default 10)
    """
    
    try:
        client = await get_twitter_client()
        
        # Remove @ if present in username
        username = username.lstrip('@')
        
        # First get user ID from screen name
        user = await client.get_user_by_screen_name(username)
        if not user:
            return f"Could not find user {username}"
            
        # Then get their tweets
        tweets = await client.get_user_tweets(
            user_id=user.id,
            tweet_type=tweet_type,
            count=count
        )
        return convert_tweets_to_markdown(tweets)
    except Exception as e:
        logger.error(f"Failed to get user tweets: {e}")
        return f"Failed to get user tweets: {e}"

@mcp.tool()
async def get_timeline(count: int = 20) -> str:
    """Get tweets from your home timeline (For You).
    
    Args:
        count: Number of tweets to retrieve (default 20)
    """
    try:
        client = await get_twitter_client()
        tweets = await client.get_timeline(count=count)
        return convert_tweets_to_markdown(tweets)
    except Exception as e:
        logger.error(f"Failed to get timeline: {e}")
        return f"Failed to get timeline: {e}"

@mcp.tool() 
async def get_latest_timeline(count: int = 20) -> str:
    """Get tweets from your home timeline (Following).
    
    Args:
        count: Number of tweets to retrieve (default 20)
    """
    try:
        client = await get_twitter_client()
        tweets = await client.get_latest_timeline(count=count)
        return convert_tweets_to_markdown(tweets)
    except Exception as e:
        logger.error(f"Failed to get latest timeline: {e}")
        return f"Failed to get latest timeline: {e}"


def convert_tweets_to_markdown(tweets: list[twikit.Tweet]) -> str:
    markdown_tweets = []
    for tweet in tweets:
        tweet_text = f"**@{tweet.user.screen_name}** - {tweet.created_at}\n{tweet.text}"
        markdown_tweets.append(tweet_text)
    return '\n\n'.join(markdown_tweets)

@mcp.tool()
async def create_tweet(text: str, media_ids: list[str] | None = None, poll_uri: str | None = None,  ctx: Context = None) -> str:
    """Creates a new tweet.

    Args:
        text: The text content of the tweet.
        media_ids: A list of media IDs to attach to the tweet.
        poll_uri: The URI of a Twitter poll card to attach to the tweet.
    """
    try:
        client = await get_twitter_client()
        tweet = await client.create_tweet(text=text, media_ids=media_ids, poll_uri=poll_uri)
        return f"Tweet created successfully: {tweet.id}"
    except Exception as e:
        logger.error(f"Failed to create tweet: {e}")
        return f"Failed to create tweet: {e}"

@mcp.tool()
async def reply_to_tweet(tweet_id: str, text: str, media_ids: list[str] | None = None, ctx: Context = None) -> str:
    """Replies to a specific tweet.

    Args:
        tweet_id: The ID of the tweet to reply to.
        text: The text content of the reply.
        media_ids: A list of media IDs to attach to the reply.
    """
    try:
        client = await get_twitter_client()
        tweet = await client.create_tweet(text=text, media_ids=media_ids, reply_to=tweet_id)
        return f"Reply sent successfully: {tweet.id}"
    except Exception as e:
        logger.error(f"Failed to reply to tweet: {e}")
        return f"Failed to reply to tweet: {e}"

@mcp.tool()
async def like_tweet(tweet_id: str, ctx: Context = None) -> str:
    """Likes a specific tweet.

    Args:
        tweet_id: The ID of the tweet to like.
    """
    try:
        client = await get_twitter_client()
        await client.favorite_tweet(tweet_id)
        return f"Tweet {tweet_id} liked successfully."
    except Exception as e:
        logger.error(f"Failed to like tweet: {e}")
        return f"Failed to like tweet: {e}"

# @mcp.tool()
# async def unlike_tweet(tweet_id: str, ctx: Context = None) -> str:
#     """Unlikes a specific tweet.

#     Args:
#         tweet_id: The ID of the tweet to unlike.
#     """
#     try:
#         client = await get_twitter_client()
#         await client.unfavorite_tweet(tweet_id)
#         return f"Tweet {tweet_id} unliked successfully."
#     except Exception as e:
#         logger.error(f"Failed to unlike tweet: {e}")
#         return f"Failed to unlike tweet: {e}"

@mcp.tool()
async def retweet(tweet_id: str, ctx: Context = None) -> str:
    """Retweets a specific tweet.

    Args:
        tweet_id: The ID of the tweet to retweet.
    """
    try:
        client = await get_twitter_client()
        await client.retweet(tweet_id)
        return f"Tweet {tweet_id} retweeted successfully."
    except Exception as e:
        logger.error(f"Failed to retweet: {e}")
        return f"Failed to retweet: {e}"

# @mcp.tool()
# async def delete_retweet(tweet_id: str, ctx: Context = None) -> str:
#     """Deletes a retweet.

#     Args:
#         tweet_id: The ID of the tweet to delete the retweet for.
#     """
#     try:
#         client = await get_twitter_client()
#         await client.delete_retweet(tweet_id)
#         return f"Retweet of tweet {tweet_id} deleted successfully."
#     except Exception as e:
#         logger.error(f"Failed to delete retweet: {e}")
#         return f"Failed to delete retweet: {e}"

@mcp.tool()
async def follow_user(username: str, ctx: Context = None) -> str:
    """Follows a user.

    Args:
        username: The username of the user to follow (with or without @).
    """
    try:
        client = await get_twitter_client()
        username = username.lstrip('@')
        user = await client.get_user_by_screen_name(username)
        if not user:
            return f"Could not find user {username}"
        await client.follow_user(user.id)
        return f"Successfully followed user {username}"
    except Exception as e:
        logger.error(f"Failed to follow user: {e}")
        return f"Failed to follow user: {e}"

@mcp.tool()
async def unfollow_user(username: str, ctx: Context = None) -> str:
    """Unfollows a user.

    Args:
        username: The username of the user to unfollow (with or without @).
    """
    try:
        client = await get_twitter_client()
        username = username.lstrip('@')
        user = await client.get_user_by_screen_name(username)
        if not user:
            return f"Could not find user {username}"
        await client.unfollow_user(user.id)
        return f"Successfully unfollowed user {username}"
    except Exception as e:
        logger.error(f"Failed to unfollow user: {e}")
        return f"Failed to unfollow user: {e}"

@mcp.tool()
async def block_user(username: str, ctx: Context = None) -> str:
    """Blocks a user.

    Args:
        username: The username of the user to block (with or without @).
    """
    try:
        client = await get_twitter_client()
        username = username.lstrip('@')
        user = await client.get_user_by_screen_name(username)
        if not user:
            return f"Could not find user {username}"
        await client.block_user(user.id)
        return f"Successfully blocked user {username}"
    except Exception as e:
        logger.error(f"Failed to block user: {e}")
        return f"Failed to block user: {e}"

@mcp.tool()
async def unblock_user(username: str, ctx: Context = None) -> str:
    """Unblocks a user.

    Args:
        username: The username of the user to unblock (with or without @).
    """
    try:
        client = await get_twitter_client()
        username = username.lstrip('@')
        user = await client.get_user_by_screen_name(username)
        if not user:
            return f"Could not find user {username}"
        await client.unblock_user(user.id)
        return f"Successfully unblocked user {username}"
    except Exception as e:
        logger.error(f"Failed to unblock user: {e}")
        return f"Failed to unblock user: {e}"

# @mcp.tool()
# async def mute_user(username: str, ctx: Context = None) -> str:
#     """Mutes a user.

#     Args:
#         username: The username of the user to mute (with or without @).
#     """
#     try:
#         client = await get_twitter_client()
#         username = username.lstrip('@')
#         user = await client.get_user_by_screen_name(username)
#         if not user:
#             return f"Could not find user {username}"
#         await client.mute_user(user.id)
#         return f"Successfully muted user {username}"
#     except Exception as e:
#         logger.error(f"Failed to mute user: {e}")
#         return f"Failed to mute user: {e}"

# @mcp.tool()
# async def unmute_user(username: str, ctx: Context = None) -> str:
#     """Unmutes a user.

#     Args:
#         username: The username of the user to unmute (with or without @).
#     """
#     try:
#         client = await get_twitter_client()
#         username = username.lstrip('@')
#         user = await client.get_user_by_screen_name(username)
#         if not user:
#             return f"Could not find user {username}"
#         await client.unmute_user(user.id)
#         return f"Successfully unmuted user {username}"
#     except Exception as e:
#         logger.error(f"Failed to unmute user: {e}")
#         return f"Failed to unmute user: {e}"
    
@mcp.tool()
async def get_user_by_screen_name(username: str, ctx: Context = None) -> str:
    """
    Retrieves a user by their screen name.
    """
    try:
        client = await get_twitter_client()
        username = username.lstrip('@')
        user = await client.get_user_by_screen_name(username)
        if not user:
            return f"Could not find user with screen name {username}"
        
        user_info = (
            f"ID: {user.id}\n"
            f"Name: {user.name}\n"
            f"Screen Name: {user.screen_name}\n"
            f"Description: {user.description}\n"
            f"Verified: {user.verified}\n"
            f"Followers Count: {user.followers_count}\n"
            f"Following Count: {user.following_count}\n"
            f"Location: {user.location}\n"
            f"Created At: {user.created_at}\n"
            f"Profile Image URL: {user.profile_image_url}\n"
            f"Profile Banner URL: {user.profile_banner_url}\n"
        )
        return user_info
    except Exception as e:
        logger.error(f"Failed to retrieve user by screen name: {e}")
        return f"Failed to retrieve user by screen name: {e}"

@mcp.tool()
async def get_user_followers(username: str, count: int = 20, ctx: Context = None) -> str:
    """
    Retrieves a list of followers for a given user.
    """
    try:
        client = await get_twitter_client()
        username = username.lstrip('@')
        user = await client.get_user_by_screen_name(username)
        if not user:
            return f"Could not find user {username}"

        followers = await client.get_user_followers(user.id, count=count)
        followers_info = "\n".join([f"  - @{follower.screen_name} (ID: {follower.id})" for follower in followers])
        return f"Followers of {username}:\n{followers_info}"
    except Exception as e:
        logger.error(f"Failed to get followers for user {username}: {e}")
        return f"Failed to get followers for user {username}: {e}"

@mcp.tool()
async def get_user_following(username: str, count: int = 20, ctx: Context = None) -> str:
    """
    Retrieves a list of users that a given user is following.
    """
    try:
        client = await get_twitter_client()
        username = username.lstrip('@')
        user = await client.get_user_by_screen_name(username)
        if not user:
            return f"Could not find user {username}"

        following = await client.get_user_following(user.id, count=count)
        following_info = "\n".join([f"  - @{followed_user.screen_name} (ID: {followed_user.id})" for followed_user in following])
        return f"Users followed by {username}:\n{following_info}"
    except Exception as e:
        logger.error(f"Failed to get following list for user {username}: {e}")
        return f"Failed to get following list for user {username}: {e}"
        
@mcp.tool()
async def send_dm(user_id: str, text: str, media_id: str | None = None, ctx: Context = None) -> str:
    """Sends a direct message to a user.

    Args:
        user_id: The ID of the user to whom the direct message will be sent.
        text: The text content of the direct message.
        media_id: The media ID associated with any media content.
    """
    try:
        client = await get_twitter_client()
        message = await client.send_dm(user_id, text, media_id=media_id)
        return f"Direct message sent successfully: {message.id}"
    except Exception as e:
        logger.error(f"Failed to send DM: {e}")
        return f"Failed to send DM: {e}"

# @mcp.tool()
# async def get_dm_history(user_id: str, max_id: str | None = None, ctx: Context = None) -> str:
#     """Retrieves the DM conversation history with a specific user.

#     Args:
#         user_id: The ID of the user with whom the DM conversation history will be retrieved.
#         max_id: If specified, retrieves messages older than the specified max_id.
#     """
#     try:
#         client = await get_twitter_client()
#         messages = await client.get_dm_history(user_id, max_id=max_id)
#         messages_info = "\n".join([f"  - {message.text} (ID: {message.id})" for message in messages])
#         return f"DM history with user {user_id}:\n{messages_info}"
#     except Exception as e:
#         logger.error(f"Failed to get DM history: {e}")
#         return f"Failed to get DM history: {e}"

# @mcp.tool()
# async def send_dm_to_group(group_id: str, text: str, media_id: str | None = None, reply_to: str | None = None, ctx: Context = None) -> str:
#     """Sends a message to a group.

#     Args:
#         group_id: The ID of the group in which the direct message will be sent.
#         text: The text content of the direct message.
#         media_id: The media ID associated with any media content.
#         reply_to: Message ID to reply to.
#     """
#     try:
#         client = await get_twitter_client()
#         message = await client.send_dm_to_group(group_id, text, media_id=media_id, reply_to=reply_to)
#         return f"Group message sent successfully: {message.id}"
#     except Exception as e:
#         logger.error(f"Failed to send group DM: {e}")
#         return f"Failed to send group DM: {e}"

# @mcp.tool()
# async def get_group_dm_history(group_id: str, max_id: str | None = None, ctx: Context = None) -> str:
#     """Retrieves the DM conversation history in a group.

#     Args:
#         group_id: The ID of the group in which the DM conversation history will be retrieved.
#         max_id: If specified, retrieves messages older than the specified max_id.
#     """
#     try:
#         client = await get_twitter_client()
#         messages = await client.get_group_dm_history(group_id, max_id=max_id)
#         messages_info = "\n".join([f"  - {message.text} (ID: {message.id})" for message in messages])
#         return f"DM history of group {group_id}:\n{messages_info}"
#     except Exception as e:
#         logger.error(f"Failed to get group DM history: {e}")
#         return f"Failed to get group DM history: {e}"

# @mcp.tool()
# async def add_reaction_to_message(message_id: str, conversation_id: str, emoji: str, ctx: Context = None) -> str:
#     """Adds a reaction emoji to a specific message in a conversation.

#     Args:
#         message_id: The ID of the message to which the reaction emoji will be added.
#         conversation_id: The ID of the conversation containing the message.
#         emoji: The emoji to be added as a reaction.
#     """
#     try:
#         client = await get_twitter_client()
#         await client.add_reaction_to_message(message_id, conversation_id, emoji)
#         return f"Reaction {emoji} added to message {message_id} in conversation {conversation_id}."
#     except Exception as e:
#         logger.error(f"Failed to add reaction to message: {e}")
#         return f"Failed to add reaction to message: {e}"
        
# @mcp.tool()
# async def remove_reaction_from_message(message_id: str, conversation_id: str, emoji: str, ctx: Context = None) -> str:
#     """Removes a reaction from a message.

#     Args:
#         message_id: The ID of the message from which to remove the reaction.
#         conversation_id: The ID of the conversation where the message is located.
#         emoji: The emoji to remove as a reaction.
#     """
#     try:
#         client = await get_twitter_client()
#         await client.remove_reaction_from_message(message_id, conversation_id, emoji)
#         return f"Reaction {emoji} removed from message {message_id} in conversation {conversation_id}."
#     except Exception as e:
#         logger.error(f"Failed to remove reaction from message: {e}")
#         return f"Failed to remove reaction from message: {e}"

@mcp.tool()
async def get_trends(category: str = 'trending', count: int = 20, ctx: Context = None) -> str:
    """Retrieves trending topics on Twitter.

    Args:
        category: The category of trends to retrieve. Valid options include:
                  'trending', 'for-you', 'news', 'sports', 'entertainment'
        count: The number of trends to retrieve.
    """
    try:
        client = await get_twitter_client()
        trends = await client.get_trends(category=category, count=count)
        trends_info = "\n".join([f"  - {trend.name} (Tweets: {trend.tweets_count})" for trend in trends])
        return f"Trends in {category}:\n{trends_info}"
    except Exception as e:
        logger.error(f"Failed to get trends: {e}")
        return f"Failed to get trends: {e}"

# @mcp.tool()
# async def get_place_trends(woeid: int, ctx: Context = None) -> str:
#     """Retrieves the top 50 trending topics for a specific id (location).

#     Args:
#         woeid: Where On Earth ID of the location for which to get trends.
#     """
#     try:
#         client = await get_twitter_client()
#         place_trends = await client.get_place_trends(woeid)
#         trends_info = "\n".join([f"  - {trend.name} (Volume: {trend.tweet_volume})" for trend in place_trends.trends])
#         return f"Trends for WOEID {woeid}:\n{trends_info}"
#     except Exception as e:
#         logger.error(f"Failed to get place trends: {e}")
#         return f"Failed to get place trends: {e}"

