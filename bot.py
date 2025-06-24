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
    '76561199419240292','76561199528974295','76561199418027556','76561199527942381','76561199418272921','76561199420987416','76561199416899795',
    '76561199430042714','76561199432208134','76561199404392645','76561199416330702','76561199528207164','76561199444883653','76561199527719299',
    '76561199418245374','76561199419478521','76561199528252168','76561199420619445','76561199434846406','76561199417492884','76561199418972285',
    '76561199419222699','76561199527844086','76561199417331887','76561199528104750','76561199417896406','76561199435031882','76561199417449874',
    '76561199418648313','76561199420296040','76561199434904088','76561199431267566','76561199528126727','76561199430053630','76561199417783633',
    '76561199432726503','76561199431286132','76561199419937468','76561199417586074','76561199433473782','76561199433508995','76561199528368811',
    '76561199419628572','76561199418134607','76561199527800632','76561199419325827','76561199433563059','76561199527611344','76561199420430794',
    '76561199418039488','76561199527396764','76561199417703947','76561199431758617','76561199434613423','76561199421315946','76561199528316816',
    '76561199433770220','76561199419040559','76561199431510092','76561199416386954','76561199444460905','76561199417703947','76561199420348905',
    '76561199419777845','76561199528324051','76561199404766318','76561199432979383','76561199418614186','76561199420066485','76561199434267626',
    '76561199433056341','76561199419550381','76561199417701336','76561199528886386','76561199434000454','76561199419058378','76561199527883112',
    '76561199528037890','76561199418107172','76561199528738484','76561199433216466','76561199444407752','76561199528046657','76561199432695506',
    '76561199416913404','76561199418155999','76561199419659927','76561199418107172','76561199528738484','76561199417660795','76561199433706551',
    '76561199434000454','76561199528689443','76561199434796124','76561199443818915','76561199431668090','76561199528407826','76561199418485509',
    '76561199420529526','76561199434619303','76561199419679089','76561199419690336','76561199528179319','76561199434327859','76561199417817156',
    '76561199417302243','76561199528523007','76561199444592159','76561199432986256','76561199444681000','76561199433553388','76561199527665527',
    '76561199433553388','76561199418041369','76561199527142067','76561199528113025','76561199432729789','76561199527946571','76561199420414495',
    '76561199418700318','76561199417765824','76561199444330870','76561199431649506','76561199416799410','76561199444068009','76561199404568031',
    '76561199430542827','76561199528767663','76561199418041369','76561199527946571','76561199419410856','76561199417162976','76561199444184678',
    '76561199527737182','76561199430165425','76561199528477677','76561199527287537','76561199429708232','76561199420598343','76561199528500358',
    '76561199430281304','76561199417046195','76561199434729654','76561199417888824','76561199418617278','76561199418336966','76561199528365163',
    '76561199404993033','76561199432847032','76561199433979540','76561199418479099','76561199417163062','76561199415983354','76561199528806801',
    '76561199433303998','76561199527989318','76561199417505038','76561199433542275','76561199528300767','76561199528052127','76561199528497800',
    '76561199418225012','76561199433107105','76561199419764677','76561199431856377','76561199443887021','76561199420378997','76561199432981955',
    '76561199417806467','76561199421502761','76561199528389664','76561199443791871','76561199528075461','76561199419027924',
    '76561199419627179','76561199528247910','76561199431721475','76561199419948293','76561199430048849','76561199421438640',
    '76561199433556206','76561199527853688','76561199417516244','76561199430183139','76561199419360519','76561199420819898',
    '76561199528725730','76561199528255589','76561199417804758','76561199528210792','76561199527112323','76561199418084035',
    '76561199417580242','76561199417230883','76561199417487625','76561199429545400','76561199528188514','76561199528046858',
    '76561199419026106','76561199419400066','76561199417580242','76561199418225012','76561199434085808','76561199418807171',
    '76561199419217264','76561199419607569','76561199527998449','76561199417381288','76561199528047369','76561199417196023',
    '76561199434364777','76561199528665392','76561199418980682','76561199527495560','76561199419728897','76561199421374395',
    '76561199528077087','76561199438498281','76561199528523573','76561199529078053','76561199528690266','76561199528133667',
    '76561199430417121','76561199417682963','76561199528480269','76561199527827460','76561199419109467','76561199528234752',
    '76561199418635996','76561199418826942','76561199431520867','76561199528783061','76561199417206517','76561199432483045',
    '76561199417960105','76561199528021054','76561199527912883','76561199417396660','76561199434206641','76561199418372202',
    '76561199419179098','76561199430657188','76561199527925976','76561199417279458','76561199430186675','76561199420065391',
    '76561199431743027','76561199434684790','76561199419808220',
    '76561199444279719','76561199418481328','76561199444083622','76561199418608777','76561199417851249','76561199444117185',
    '76561199430121384','76561199528369967','76561199435568644','76561199431322717','76561199418099310','76561199527946547',
    '76561199419560155','76561199418235494','76561199421318811','76561199419034698','76561199419087163','76561199419402233',
    '76561199527801410','76561199527435177','76561199527492982','76561199417587367','76561199431682451','76561199528537629',
    '76561199436007616','76561199418387737','76561199527447547','76561199429389465','76561199433306606','76561199528821373',
    '76561199419410843','76561199419617837','76561199419929452','76561199418886498','76561199528298326','76561199418846988',
    '76561199527498933','76561199418235494','76561199419034698','76561199528411947','76561199421278132','76561199419617837',
    '76561199419929452','76561199418411329','76561199429803458','76561199418387737','76561199528360812','76561199527985587',
    '76561199418198691','76561199429900198','76561199417980302','76561199419218284','76561199418719630','76561199527913433',
    '76561199418184907','76561199417347125','76561199418213276','76561199433276184','76561199444312548','76561199417904177',
    '76561199528086490','76561199527773362','76561199430263989','76561199417911932','76561199432988763','76561199420054836',
    '76561199526895458','76561199421786200','76561199435557618','76561199528158100','76561199429501552','76561199435557618',
    '76561199429732113','76561199528375666','76561199527789927','76561199418215873','76561199527776046','76561199433931676',
    '76561199528472536','76561199417395969','76561199528234158','76561199418085934','76561199527400907','76561199528048858',
    '76561199528426803','76561199528692083','76561199417374636','76561199420441422','76561199432909766','76561199528417677',
    '76561199527914615','76561199528115460','76561199418881530','76561199527722763','76561199417384642','76561199431751365',
    '76561199528339129','76561199417956795','76561199419183946','76561199431843618','76561199443879959','76561199421936089',
    '76561199527317415','76561199526997288','76561199528312757','76561199418016959','76561199418274531','76561199528049833',
    '76561199528616236','76561199528018567','76561199528437388','76561199430251310','76561199417884426','76561199433172458',
    '76561199418415335','76561199420283844','76561199418232300','76561199527484048','76561199417971852','76561199430038688',
    '76561199417799742','76561199528872325','76561199433698159','76561199434347493','76561199419085220','76561199418655067',
    '76561199433443431','76561199432905757','76561199527725452','76561199435861768','76561199430511704','76561199420641848',
    '76561199527970524','76561199418134573','76561199418496710','76561199417130990','76561199418579135','76561199443995511',
    '76561199419066048','76561199432600738','76561199417529953','76561199432467593','76561199528278431','76561199430748672',
    '76561199421026445','76561199418428537','76561199421372260','76561199434045837','76561199527977225','76561199432467593',
    '76561199418336603','76561199527762085','76561199528278431','76561199430748672','76561199419066048','76561199417529953',
    '76561199419229261','76561199527864015','76561199431782538','76561199418174528','76561199431676221','76561199433184903',
    '76561199528879514','76561199420098770','76561199527873293','76561199444346436','76561199421737873',
    '76561199418336603','76561199419229261','76561199527864015','76561199527762085','76561199430497436','76561199444346436',
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
    logger.info(f"Total new friends collected: {len(all_new_friends)}")
    logger.info(f"First run status: {first_run}")
    
    if all_new_friends and not first_run:
        if len(all_new_friends) == 1:
            msg = f"New friend: {all_new_friends[0]}"
        else:
            msg = f"New friends detected ({len(all_new_friends)}):\n\n"
            msg += "\n".join([f"• {friend_link}" for friend_link in all_new_friends])
        
        logger.info(f"Attempting to send Telegram message: {msg[:100]}...")
        await send_telegram_message(msg)
        logger.info(f"Sent batched notification for {len(all_new_friends)} new friends")
    elif all_new_friends and first_run:
        logger.info(f"New friends detected on first run (not sending notification): {len(all_new_friends)}")
    else:
        logger.info("No new friends detected in this cycle")

    # Save current data
    save_data(current_data)

    if first_run:
        # Log initial setup (no telegram messages)
        total_accounts = len(current_data)
        private_accounts = len(STEAM_ACCOUNTS) - total_accounts
        total_friends = sum(data['count'] for data in current_data.values())
        
        logger.info(f"Steam Friend ID Monitor Setup Complete")
        logger.info(f"Monitoring {total_accounts} accounts")
        logger.info(f"Total friends being tracked: {total_friends}")
        if private_accounts > 0:
            logger.info(f"{private_accounts} accounts are private")
        logger.info("Bot will now notify when specific friends are added with their Steam IDs")
    else:
        logger.info("Friend check completed")

if __name__ == '__main__':
    asyncio.run(check_accounts())
