import asyncio

from task.clients.client import DialClient
from task.clients.custom_client import CustomDialClient
from task.constants import DEFAULT_SYSTEM_PROMPT
from task.models.conversation import Conversation
from task.models.message import Message
from task.models.role import Role


async def start(stream: bool) -> None:
    deployment_name = "gpt-5-nano-2025-08-07"  # you can change it to any available deployment_name
    dial_client = DialClient(deployment_name)
    custom_dial_client = CustomDialClient(deployment_name)
    client = custom_dial_client  # you can change it to dial_client to use the client from the aidial-client library

    conversation = Conversation()
    prompt = input("Provide System prompt or press 'enter' to continue.\n> ").strip()
    
    if prompt:
        conversation.add_message(Message(Role.SYSTEM, prompt))
        print("System prompt successfully added to conversation.")
    else:
        conversation.add_message(Message(Role.SYSTEM, DEFAULT_SYSTEM_PROMPT))
        print(f"No System prompt provided. Will be used default System prompt: '{DEFAULT_SYSTEM_PROMPT}'")

    while True:
        user_message = input("You: ").strip()
        if user_message.lower() == "exit":
            print("Exiting the chat. Goodbye!")
            break

        conversation.add_message(Message(Role.USER, user_message))

        if stream:
            print("Assistant (streaming): ", end="", flush=True)
            assistant_message = await client.stream_completion(conversation.get_messages())
            print(f"Assistant: {assistant_message.content}")
            conversation.add_message(assistant_message)
        else:
            assistant_message = await client.get_completion(conversation.get_messages())
            print(f"Assistant: {assistant_message.content}")
            conversation.add_message(assistant_message)

asyncio.run(
    start(True)
)
