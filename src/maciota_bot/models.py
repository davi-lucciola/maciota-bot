from sqlmodel import Field, SQLModel


class GuildWelcomeChannel(SQLModel, table=True):
    guild_id: int = Field(primary_key=True)
    channel_id: int
