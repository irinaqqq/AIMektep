from core.config import Config

def main():
    client = Config().azure_client

    assistant = client.beta.assistants.create(
        name="AIMektep Mini Assistant",
        instructions="Ты помогаешь студентам делать краткие конспекты текста на русском языке.",
        model="gpt-4o-mini",
        temperature=0.5,
        tools=[],
    )

    print(f"✅ Assistant created successfully!")
    print(f"Name: {assistant.name}")
    print(f"ID:   {assistant.id}")

if __name__ == "__main__":
    main()
