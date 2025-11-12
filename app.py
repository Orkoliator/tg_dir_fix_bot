from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogFiltersRequest, UpdateDialogFilterRequest
from telethon.tl.types import DialogFilter
from telethon import types
from yaml import safe_load
import asyncio

tg_peers = {
    'channels': [],
    'megagroups': [],
    'gigagroups': [],
    'groups': []
}

with open('api_parameters.yaml', 'r') as config:
    session_data = safe_load(config)
    session_name = session_data['session_name']
    api_id = session_data['api_id']
    api_hash = session_data['api_hash']
    group_folder_name = session_data['group_folder_name']
    supergroup_folder_name = session_data['supergroup_folder_name']
    channel_folder_name = session_data['channel_folder_name']

async def dialogs_process(client):
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            data = await client.get_entity(dialog.id)
            if data.broadcast:
                tg_peers['channels'].append(await client.get_input_entity(data.id))
            elif data.megagroup:
                tg_peers['megagroups'].append(await client.get_input_entity(data.id))
            elif data.gigagroup:
                tg_peers['gigagroups'].append(await client.get_input_entity(data.id))
            else:
                print(f'{data.title} type cannot be identified')
        elif dialog.is_group and not dialog.is_channel:
            data = await client.get_entity(dialog.id)
            tg_peers['groups'].append(await client.get_input_entity(data.id))

async def updateFilter(client, folder_id, folder_title, peers):
    await client(UpdateDialogFilterRequest(
        id=folder_id,
        filter=DialogFilter(
            id=folder_id,
            title=types.TextWithEntities(text=folder_title, entities=[types.MessageEntityUnknown(offset=folder_id, length=folder_id)]),
            pinned_peers=[],
            exclude_peers=[],
            include_peers=peers,
            contacts=False,
            non_contacts=False,
            groups=False,
            broadcasts=False,
            bots=False
        )
    ))

async def modifyFilter(client, tg_peers):
    request = await client(GetDialogFiltersRequest())
    for dialog_filter in request.filters[1:]:
        if dialog_filter.title.text == group_folder_name:
            await updateFilter(client, dialog_filter.id, group_folder_name, tg_peers['groups'])
        elif dialog_filter.title.text == supergroup_folder_name:
            await updateFilter(client, dialog_filter.id, supergroup_folder_name, tg_peers['megagroups']+tg_peers['gigagroups'])
        elif dialog_filter.title.text == channel_folder_name:
            await updateFilter(client, dialog_filter.id, channel_folder_name, tg_peers['channels'])

async def main():
    async with TelegramClient(session_name, api_id, api_hash) as client:
        await dialogs_process(client)
        await modifyFilter(client, tg_peers)
        print('done')

if __name__ == "__main__":
    asyncio.run(main())