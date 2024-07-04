from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogFiltersRequest, UpdateDialogFilterRequest
from telethon.tl.types import DialogFilter
from yaml import safe_load

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

client = TelegramClient(session_name, api_id, api_hash)
client.start()

async def main():
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

async def updateFilter(folder_id, folder_title, peers):
    await client(UpdateDialogFilterRequest(
        id=folder_id,
        filter=DialogFilter(
            id=folder_id,
            title=folder_title,
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

async def modifyFilter(tg_peers):
    request = await client(GetDialogFiltersRequest())
    for dialog_filter in request.filters[1:]:
        if dialog_filter.title == group_folder_name:
            await updateFilter(dialog_filter.id, group_folder_name, tg_peers['groups'])
        elif dialog_filter.title == supergroup_folder_name:
            await updateFilter(dialog_filter.id, supergroup_folder_name, tg_peers['megagroups']+tg_peers['gigagroups'])
        elif dialog_filter.title == channel_folder_name:
            await updateFilter(dialog_filter.id, channel_folder_name, tg_peers['channels'])

with client:
    client.loop.run_until_complete(main())
    client.loop.run_until_complete(modifyFilter(tg_peers))
    print('done')