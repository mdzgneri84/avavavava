import os
import json
import asyncio
import aiohttp
import logging
from datetime import datetime

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
STEAM_API_KEY = os.environ.get('STEAM_API_KEY', '')

# Steam account IDs to monitor (just the IDs, no names needed)
STEAM_ACCOUNTS = [
    '76561199849656455',
]

DATA_FILE = 'friend_data.json'
INIT_FILE = '.initialized'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SteamFriendIDMonitor")

def get_profile_link(steam_id):
    """Generate Steam profile link from Steam ID"""
    return f"steamcommunity.com/profiles/{steam_id}"

async def fetch_friend_list(session, steam_id):
    """Fetch the complete friend list for a Steam account"""
    url = f"http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key={STEAM_API_KEY}&steamid={steam_id}&relationship=friend"
    profile_link = get_profile_link(steam_id)
    
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                friends_data = data.get('friendslist', {}).get('friends', [])
                # Extract just the Steam IDs of friends
                friend_ids = [friend['steamid'] for friend in friends_data]
                return steam_id, profile_link, friend_ids
            elif resp.status == 403:
                logger.warning(f"{profile_link} is private")
                return steam_id, profile_link, None
            else:
                logger.error(f"{profile_link}: API error {resp.status}")
                return steam_id, profile_link, None
    except Exception as e:
        logger.error(f"Error fetching {profile_link}: {e}")
        return steam_id, profile_link, None

async def send_telegram_message(message):
    """Send message to Telegram, splitting if too long"""
    MAX_MESSAGE_LENGTH = 4000  # Leave some buffer under 4096 limit
    
    if len(message) <= MAX_MESSAGE_LENGTH:
        await _send_single_message(message)
    else:
        # Split message into chunks
        lines = message.split('\n')
        current_chunk = ""
        
        for line in lines:
            # If adding this line would exceed limit, send current chunk
            if len(current_chunk + line + '\n') > MAX_MESSAGE_LENGTH:
                if current_chunk:
                    await _send_single_message(current_chunk.strip())
                    current_chunk = line + '\n'
                else:
                    # Single line is too long, truncate it
                    await _send_single_message(line[:MAX_MESSAGE_LENGTH])
            else:
                current_chunk += line + '\n'
        
        # Send remaining chunk
        if current_chunk:
            await _send_single_message(current_chunk.strip())

async def _send_single_message(message):
    """Send a single message to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, data=payload) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to send message: {await resp.text()}")
                else:
                    logger.info("Telegram message sent successfully")
        except Exception as e:
            logger.error(f"Telegram error: {e}")

def load_previous_data():
    """Load previous friend data from file"""
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    """Save friend data to file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def is_first_run():
    """Check if this is the first run of the bot"""
    if os.path.exists(INIT_FILE):
        return False
    with open(INIT_FILE, 'w') as f:
        f.write(datetime.now().isoformat())
    return True

async def check_accounts():
    """Main function to check all accounts for friend changes"""
    first_run = is_first_run()
    previous_data = load_previous_data()
    current_data = {}
    all_new_friends = []  # Collect all new friends for batched notification
    
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_friend_list(session, steam_id) for steam_id in STEAM_ACCOUNTS]
        results = await asyncio.gather(*tasks)

    for steam_id, profile_link, friend_ids in results:
        if friend_ids is None:
            continue
            
        current_data[steam_id] = {
            'profile_link': profile_link,
            'friends': friend_ids,
            'count': len(friend_ids)
        }
        
        # Skip change detection on first run
        if first_run or steam_id not in previous_data:
            continue
            
        previous_friends = set(previous_data[steam_id].get('friends', []))
        current_friends = set(friend_ids)
        
        # Check for new friends only
        new_friends = current_friends - previous_friends
        if new_friends:
            for friend_id in new_friends:
                friend_profile_link = get_profile_link(friend_id)
                all_new_friends.append(friend_profile_link)
                logger.info(f"New friend detected: {friend_id} added to {steam_id}")
        
        # Log removed friends (no telegram notification)
        removed_friends = previous_friends - current_friends
        if removed_friends:
            for friend_id in removed_friends:
                logger.info(f"Friend removed: {friend_id} removed from {steam_id}")

    # Send batched notification for all new friends
    if all_new_friends and not first_run:
        if len(all_new_friends) == 1:
            msg = f"New friend: {all_new_friends[0]}"
        else:
            msg = f"New friends detected ({len(all_new_friends)}):\n\n"
            msg += "\n".join([f"• {friend_link}" for friend_link in all_new_friends])
        await send_telegram_message(msg)
        logger.info(f"Sent batched notification for {len(all_new_friends)} new friends")

    # Save current data
    save_data(current_data)

    if first_run:
        # Send initial setup message
        total_accounts = len(current_data)
        private_accounts = len(STEAM_ACCOUNTS) - total_accounts
        total_friends = sum(data['count'] for data in current_data.values())
        
        msg = f"📊 <b>Steam Friend ID Monitor Setup Complete</b>\n\n"
        msg += f"✅ Monitoring {total_accounts} accounts\n"
        msg += f"👥 Total friends being tracked: {total_friends}\n"
        if private_accounts > 0:
            msg += f"🔒 {private_accounts} accounts are private\n"
        msg += f"\n<i>Bot will now notify when specific friends are added/removed with their Steam IDs.</i>"
        
        await send_telegram_message(msg)
        
        # Send summary for each account
        for steam_id, data in current_data.items():
            summary_msg = f"📋 <b>Account Summary</b>\n\n"
            summary_msg += f"Account: {data['profile_link']}\n"
            summary_msg += f"Friends: {data['count']}\n"
            await send_telegram_message(summary_msg)
    else:
        logger.info("Friend check completed")

if __name__ == '__main__':
    asyncio.run(check_accounts())
