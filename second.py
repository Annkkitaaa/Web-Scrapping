from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
import pandas as pd
from datetime import datetime, timedelta

# Replace these with your actual API ID and hash
api_id=
api_hash=
phone =  # Your phone number with country code
username =  # Your Telegram username

client = TelegramClient(username, api_id, api_hash)

async def main():
    await client.start()
    print("Client Created")
    
    # Ensure you're authorized
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except Exception as e:
            print(f"Error during sign in: {e}")
            return

    print("Fetching Dialogs...")
    try:
        dialogs = await client.get_dialogs()
    except Exception as e:
        print(f"Error fetching dialogs: {e}")
        return

    groups = [d for d in dialogs if d.is_group]
    
    print("Choose a group to scrape:")
    for i, g in enumerate(groups):
        print(f"{i}. {g.name}")

    g_index = input("Enter a Number: ")
    target_group = groups[int(g_index)]

    print(f"Fetching Members from {target_group.name}...")
    all_participants = []
    all_messages = []

    try:
        all_participants = await client.get_participants(target_group)
    except Exception as e:
        print(f"Error fetching participants: {e}")
        return

    print("Fetching Messages...")
    total_count_limit = 1000  # Set this to however many messages you want to retrieve

    try:
        async for message in client.iter_messages(target_group, limit=total_count_limit):
            message_dict = message.to_dict()
            # Convert date to timezone-naive datetime
            if 'date' in message_dict:
                message_dict['date'] = message_dict['date'].replace(tzinfo=None)
            all_messages.append(message_dict)
            print(f"Retrieved {len(all_messages)} messages", end='\r')
    except Exception as e:
        print(f"Error fetching messages: {e}")

    print("\nSaving data...")
    
    # Save participants
    df_participants = pd.DataFrame([{
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
        "phone": user.phone
    } for user in all_participants])
    
    df_participants.to_excel(f"participants_{target_group.name}.xlsx", index=False)

    # Save messages
    df_messages = pd.DataFrame(all_messages)
    if 'date' in df_messages.columns:
        df_messages['date'] = pd.to_datetime(df_messages['date'])
    df_messages.to_excel(f"messages_{target_group.name}.xlsx", index=False)

    print("Data saved successfully.")

with client:
    client.loop.run_until_complete(main())